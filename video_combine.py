import os
import shutil
import subprocess
import torch
import numpy as np
import folder_paths
import soundfile as sf
from PIL import Image
import random

class MatrixVideoCombine:
    """
    【🧩 矩阵-视频合成】
    功能：视频编码 (MP4/WebP/GIF)。
    预览优化：预览动图强制降速至 10fps，确保画面看清且浏览器能渲染。
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
                "preview_gif": ("BOOLEAN", {"default": True, "tooltip": "生成预览动图"}),
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

    def combine_video(self, images, frame_rate, loop_count, filename_prefix, format, crf, preview_gif, audio=None):
        ffmpeg_path = self.get_ffmpeg_path()
        if ffmpeg_path is None:
            raise RuntimeError("Matrix Video Error: ffmpeg.exe not found!")

        output_dir = folder_paths.get_output_directory()
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, output_dir, images[0].shape[1], images[0].shape[0])
        
        ext = {"video/h264-mp4": "mp4", "video/webp": "webp", "image/gif": "gif"}.get(format, "mp4")
        file_name = f"{filename}_{counter:05}_.{ext}"
        file_path = os.path.join(full_output_folder, file_name)

        if isinstance(images, torch.Tensor):
            images_np = images.cpu().numpy()
        else:
            images_np = images
        
        images_np = (np.clip(images_np, 0, 1) * 255).astype(np.uint8)
        batch, height, width, channels = images_np.shape

        if format == "video/h264-mp4":
            if width % 2 != 0 or height % 2 != 0:
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

        # 4. 生成预览 WebP (慢速版)
        ui_results = {"text": [file_path]}
        if preview_gif:
            rand_id = random.randint(1000, 9999)
            # 依然使用 .webp，兼容性最好
            pre_name = f"matrix_pre_{counter}_{rand_id}.webp"
            pre_path = os.path.join(folder_paths.get_temp_directory(), pre_name)
            
            # 限制最多 20 帧，尺寸 256
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
                    # 【关键修改】 强制每帧 100ms (即 10fps)，确保慢下来
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