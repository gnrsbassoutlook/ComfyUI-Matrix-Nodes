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
    """
    
    # 【新增】 详细说明文案
    DESCRIPTION = """
    【🧩 矩阵-视频合成】
    功能：将图片序列编码为高清视频。
    
    🚀 核心特性：
    1. 零垃圾：内存直通 FFmpeg，不产生中间图片文件。
    2. 比例修正：支持 Crop(裁切)/Stretch(拉伸)，完美解决 1088px 黑边问题。
    3. 动图预览：生成临时的 WebP 动图，解决界面预览不动的问题。
    4. 音频混流：支持输入 Audio 节点，自动合成音视频。
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "输入的图片序列"}),
                "frame_rate": ("INT", {"default": 24, "min": 1, "max": 120, "step": 1, "tooltip": "视频帧率 (FPS)"}),
                "loop_count": ("INT", {"default": 0, "min": 0, "max": 100, "step": 1, "tooltip": "循环次数 (0=无限，仅限GIF/WebP)"}),
                "filename_prefix": ("STRING", {"default": "Matrix_Video", "tooltip": "保存文件名前缀 (支持子文件夹)"}),
                "format": (["video/h264-mp4", "video/webp", "image/gif"], {"tooltip": "输出格式"}),
                "crf": ("INT", {"default": 20, "min": 0, "max": 51, "tooltip": "画质控制 (数值越小画质越好，推荐 18-24)"}),
                "aspect_ratio": (["Original", "16:9", "4:3", "3:2", "9:16", "3:4", "2:3", "1:1", "21:9"], {"default": "Original", "tooltip": "强制输出宽高比"}),
                "resize_mode": (["Crop Center", "Stretch"], {"default": "Crop Center", "tooltip": "比例不符时的处理：裁切或拉伸"}),
                "preview_gif": ("BOOLEAN", {"default": True, "tooltip": "是否在节点上显示动图预览 (生成临时WebP)"}),
            },
            "optional": {
                "audio": ("AUDIO", {"tooltip": "音频输入 (可选)"}), 
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
        if aspect_ratio == "Original": return images
        _, curr_h, curr_w, _ = images.shape
        try:
            w_ratio, h_ratio = map(int, aspect_ratio.split(":"))
            target_ratio = w_ratio / h_ratio
        except: return images
        target_h_by_w = int(curr_w / target_ratio)
        target_w_by_h = int(curr_h * target_ratio)
        if resize_mode == "Crop Center":
            if target_h_by_w <= curr_h:
                final_w, final_h = curr_w, target_h_by_w
            else:
                final_w, final_h = target_w_by_h, curr_h
            final_w -= final_w % 2
            final_h -= final_h % 2
            center_y, center_x = curr_h // 2, curr_w // 2
            start_y = max(0, center_y - final_h // 2)
            start_x = max(0, center_x - final_w // 2)
            images = images[:, start_y:start_y+final_h, start_x:start_x+final_w, :]
        elif resize_mode == "Stretch":
            final_w = curr_w
            final_h = int(curr_w / target_ratio)
            final_w -= final_w % 2
            final_h -= final_h % 2
            img_permuted = images.permute(0, 3, 1, 2)
            img_resized = F.interpolate(img_permuted, size=(final_h, final_w), mode="bilinear", align_corners=False)
            images = img_resized.permute(0, 2, 3, 1)
        return images

    def combine_video(self, images, frame_rate, loop_count, filename_prefix, format, crf, preview_gif, aspect_ratio, resize_mode, audio=None):
        ffmpeg_path = self.get_ffmpeg_path()
        if ffmpeg_path is None:
            raise RuntimeError("Matrix Video Error: ffmpeg.exe not found!")

        images = self.process_aspect_ratio(images, aspect_ratio, resize_mode)
        output_dir = folder_paths.get_output_directory()
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, output_dir, images[0].shape[1], images[0].shape[0])
        
        ext = {"video/h264-mp4": "mp4", "video/webp": "webp", "image/gif": "gif"}.get(format, "mp4")
        file_name = f"{filename}_{counter:05}_.{ext}"
        file_path = os.path.join(full_output_folder, file_name)

        if isinstance(images, torch.Tensor): images_np = images.cpu().numpy()
        else: images_np = images
        images_np = (np.clip(images_np, 0, 1) * 255).astype(np.uint8)
        batch, height, width, channels = images_np.shape

        if format == "video/h264-mp4" and (width % 2 != 0 or height % 2 != 0):
            width -= width % 2
            height -= height % 2
            images_np = images_np[:, :height, :width, :]

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

        args = [ffmpeg_path, "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-s", f"{width}x{height}", "-pix_fmt", "rgb24", "-r", str(frame_rate), "-i", "-"]
        if audio_args: args.extend(audio_args)
        if format == "video/h264-mp4": args += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), "-preset", "slow"]
        elif format == "video/webp": args += ["-c:v", "libwebp", "-loop", str(loop_count), "-lossless", "0", "-quality", str(100 - crf*2)]
        else: args += ["-f", "gif", "-loop", str(loop_count)]
        args.append(file_path)

        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            p = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo)
            for i in range(batch): p.stdin.write(images_np[i].tobytes())
            p.communicate()
        finally:
            if temp_audio_path and os.path.exists(temp_audio_path): os.remove(temp_audio_path)

        ui_results = {"text": [file_path]}
        if preview_gif:
            rand_id = random.randint(1000, 9999)
            pre_name = f"matrix_pre_{counter}_{rand_id}.webp"
            pre_path = os.path.join(folder_paths.get_temp_directory(), pre_name)
            max_frames = 20
            step = max(1, batch // max_frames)
            frames = []
            for i in range(0, batch, step):
                img = Image.fromarray(images_np[i])
                img.thumbnail((256, 256)) 
                frames.append(img)
            if frames:
                frames[0].save(pre_path, format='WEBP', save_all=True, append_images=frames[1:], duration=100, loop=0, quality=80, method=6)
                ui_results["images"] = [{"filename": pre_name, "subfolder": "", "type": "temp"}]

        return {"ui": ui_results, "result": (file_path,)}

NODE_CLASS_MAPPINGS = {"MatrixVideoCombine": MatrixVideoCombine}
NODE_DISPLAY_NAME_MAPPINGS = {"MatrixVideoCombine": "🧩 Matrix Video Combine | 矩阵-视频合成"}