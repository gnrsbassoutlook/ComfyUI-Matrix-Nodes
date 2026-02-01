import os
import shutil
import subprocess
import torch
import torch.nn.functional as F
import numpy as np
import folder_paths
import soundfile as sf
from PIL import Image
import random

class MatrixVideoCombine:
    """
    【🧩 矩阵-视频合成】
    功能：视频编码 (MP4/WebP/GIF)。
    升级：
    1. 画面比例强制控制：解决 1088px 黑边问题。
    2. 支持裁切/拉伸两种模式。
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
                "frame_rate": ("INT", {"default": 24, "min": 1, "max": 120, "step": 1}),
                "loop_count": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1, "tooltip": "0=无限循环"}),
                "filename_prefix": ("STRING", {"default": "Matrix_Video"}),
                "format": (["video/h264-mp4", "video/webp", "image/gif"],),
                "crf": ("INT", {"default": 20, "min": 0, "max": 51, "tooltip": "视频质量"}),
                
                # 新增：比例控制
                "aspect_ratio": (["Original", "16:9", "4:3", "3:2", "9:16", "3:4", "2:3", "1:1", "21:9"], {"default": "Original"}),
                "resize_mode": (["Crop Center", "Stretch"], {"default": "Crop Center", "tooltip": "Crop: 裁切多余边缘(推荐); Stretch: 强制拉伸(会变形)"}),
                
                "preview_gif": ("BOOLEAN", {"default": True, "tooltip": "生成WebP动图预览"}),
            },
            "optional": {
                "audio": ("AUDIO", ), 
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("Video_Path",)
    OUTPUT_NODE = True
    CATEGORY = "Custom/Matrix"
    FUNCTION = "combine_video"

    def get_ffmpeg_path(self):
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path: return ffmpeg_path
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        possible_paths = [
            os.path.join(base_path, "ffmpeg/bin/ffmpeg.exe"),
            os.path.join(base_path, "ffmpeg/ffmpeg-exe/bin/ffmpeg.exe"),
            os.path.join(base_path, "venv/Scripts/ffmpeg.exe"),
        ]
        for path in possible_paths:
            if os.path.exists(path): return path
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except: pass
        return None

    def process_aspect_ratio(self, images, aspect_ratio, resize_mode):
        """
        处理画面比例
        images: Tensor [B, H, W, C]
        返回: Tensor [B, NewH, NewW, C]
        """
        if aspect_ratio == "Original":
            return images

        _, curr_h, curr_w, _ = images.shape
        
        # 解析目标比例
        try:
            w_ratio, h_ratio = map(int, aspect_ratio.split(":"))
            target_ratio = w_ratio / h_ratio
        except:
            return images

        # 计算目标尺寸 (逻辑：锁定宽度，计算高度；或者锁定高度计算宽度？)
        # 策略：为了最大化保留画面，我们计算“适配盒”
        
        # 目标尺寸计算 1：保持宽度，算高度
        target_h_by_w = int(curr_w / target_ratio)
        # 目标尺寸计算 2：保持高度，算宽度
        target_w_by_h = int(curr_h * target_ratio)

        if resize_mode == "Crop Center":
            # 裁切逻辑：目标框必须在原图内部
            if target_h_by_w <= curr_h:
                # 宽度填满，高度太高 -> 切高度 (1920x1088 -> 16:9 -> 1920x1080)
                final_w, final_h = curr_w, target_h_by_w
            else:
                # 高度填满，宽度太宽 -> 切宽度
                final_w, final_h = target_w_by_h, curr_h
                
            # 确保偶数 (ffmpeg友好)
            final_w = final_w - (final_w % 2)
            final_h = final_h - (final_h % 2)
            
            # 执行裁切
            center_y, center_x = curr_h // 2, curr_w // 2
            start_y = max(0, center_y - final_h // 2)
            start_x = max(0, center_x - final_w // 2)
            
            # Slicing: [:, y:y+h, x:x+w, :]
            images = images[:, start_y:start_y+final_h, start_x:start_x+final_w, :]
            
        elif resize_mode == "Stretch":
            # 拉伸逻辑：直接算出目标尺寸并 Resize
            # 这里我们选择“保持宽度”作为基准，因为通常宽度决定了清晰度标准(1080p/4k)
            # 1920x1088 -> 16:9 -> 1920x1080
            final_w = curr_w
            final_h = int(curr_w / target_ratio)
            
            # 确保偶数
            final_w = final_w - (final_w % 2)
            final_h = final_h - (final_h % 2)
            
            # Permute for torch interpolate: [B, H, W, C] -> [B, C, H, W]
            img_permuted = images.permute(0, 3, 1, 2)
            
            # Resize
            img_resized = F.interpolate(img_permuted, size=(final_h, final_w), mode="bilinear", align_corners=False)
            
            # Permute back: [B, C, H, W] -> [B, H, W, C]
            images = img_resized.permute(0, 2, 3, 1)

        return images

    def combine_video(self, images, frame_rate, loop_count, filename_prefix, format, crf, preview_gif, aspect_ratio, resize_mode, audio=None):
        ffmpeg_path = self.get_ffmpeg_path()
        if ffmpeg_path is None:
            raise RuntimeError("Matrix Video Error: ffmpeg.exe not found!")

        # 0. 预处理：应用宽高比修正 (在转 Numpy 之前处理 Tensor 更快)
        images = self.process_aspect_ratio(images, aspect_ratio, resize_mode)

        # 1. 路径准备
        output_dir = folder_paths.get_output_directory()
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, output_dir, images[0].shape[1], images[0].shape[0])
        
        ext = {"video/h264-mp4": "mp4", "video/webp": "webp", "image/gif": "gif"}.get(format, "mp4")
        file_name = f"{filename}_{counter:05}_.{ext}"
        file_path = os.path.join(full_output_folder, file_name)

        # 转 Numpy
        if isinstance(images, torch.Tensor):
            images_np = images.cpu().numpy()
        else:
            images_np = images
        
        images_np = (np.clip(images_np, 0, 1) * 255).astype(np.uint8)
        batch, height, width, channels = images_np.shape

        # 再次兜底偶数修正 (防止自定义计算出错)
        if format == "video/h264-mp4" and (width % 2 != 0 or height % 2 != 0):
            width -= width % 2
            height -= height % 2
            images_np = images_np[:, :height, :width, :]

        # 2. 音频处理
        audio_args = []
        temp_audio_path = None
        if audio is not None:
            try:
                waveform = audio['waveform'].squeeze().cpu().numpy()
                sample_rate = audio['sample_rate']
                if waveform.ndim == 2 and waveform.shape[0] < waveform.shape[1]: waveform = waveform.T
                temp_audio_path = os.path.join(folder_paths.get_temp_directory(), f"matrix_audio_{counter}.wav")
                sf.write(temp_audio_path, waveform, sample_rate)
                audio_args = ["-i", temp_audio_path, "-c:a", "aac", "-shortest"] 
            except: pass

        # 3. FFmpeg 主视频编码
        args = [
            ffmpeg_path, "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
            "-s", f"{width}x{height}", "-pix_fmt", "rgb24", "-r", str(frame_rate), "-i", "-" 
        ]
        if audio_args: args.extend(audio_args)

        if format == "video/h264-mp4":
            args += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), "-preset", "slow"]
        elif format == "video/webp":
            args += ["-c:v", "libwebp", "-loop", str(loop_count), "-lossless", "0", "-quality", str(100 - crf*2)]
        else:
            args += ["-f", "gif", "-loop", str(loop_count)]

        args.append(file_path)

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        try:
            p = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            for i in range(batch):
                p.stdin.write(images_np[i].tobytes())
            p.communicate()
        finally:
            if temp_audio_path and os.path.exists(temp_audio_path): os.remove(temp_audio_path)

        # 4. 生成预览 WebP
        ui_results = {"text": [file_path]}
        if preview_gif:
            rand_id = random.randint(1000, 9999)
            pre_name = f"matrix_pre_{counter}_{rand_id}.webp"
            pre_path = os.path.join(folder_paths.get_temp_directory(), pre_name)
            
            # 抽帧优化
            max_frames = 20
            step = max(1, batch // max_frames)
            
            frames = []
            for i in range(0, batch, step):
                img = Image.fromarray(images_np[i])
                img.thumbnail((256, 256)) 
                frames.append(img)
            
            if frames:
                frames[0].save(
                    pre_path,
                    format='WEBP',
                    save_all=True,
                    append_images=frames[1:],
                    duration=100, 
                    loop=0,
                    quality=80,
                    method=6 
                )
                
                ui_results["images"] = [{"filename": pre_name, "subfolder": "", "type": "temp"}]

        return {"ui": ui_results, "result": (file_path,)}

NODE_CLASS_MAPPINGS = {
    "MatrixVideoCombine": MatrixVideoCombine
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixVideoCombine": "🧩 Matrix Video Combine | 矩阵-视频合成"
}