import os
import json
import numpy as np
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import folder_paths
import torch

class MatrixDatasetSaver:
    """
    【🧩 矩阵-数据集保存器】
    功能：专为模型训练设计。保存图片的同时，保存同名的 .txt 描述文件。
    """
    
    # 【新增】 详细说明文案
    DESCRIPTION = """
    【🧩 矩阵-数据集保存器】
    功能：一键保存“图片 + 同名TXT文本”，专为 LoRA/大模型训练集准备。
    
    🚀 核心特性：
    1. 格式自由：支持 PNG (无损), JPG (小体积), WebP。
    2. 自动同步：输入的 text 会被写入同名 .txt 文件。
    3. 训练就绪：配合 Text Extractor 使用，可直接把提取的 Prompt 存为训练 Tag。
    """
    
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "要保存的图片流"}),
                "text": ("STRING", {"default": "", "multiline": True, "forceInput": True, "tooltip": "要保存到txt文件的内容(Tag/Caption)"}),
                "filename_prefix": ("STRING", {"default": "train_data/img", "tooltip": "保存路径前缀 (支持子文件夹)"}),
                "format": (["png", "jpg", "webp"], {"default": "png", "tooltip": "保存格式"}),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100, "tooltip": "JPG/WebP 的压缩质量 (100为最高)"}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ()
    FUNCTION = "save_dataset"
    OUTPUT_NODE = True
    CATEGORY = "Custom/Matrix"

    def save_dataset(self, images, text, filename_prefix="train_data/img", format="png", quality=95, prompt=None, extra_pnginfo=None):
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()
        
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            file_stem = f"{filename}_{counter:05}_"
            
            if format == "png":
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))
                img_filename = f"{file_stem}.png"
                img.save(os.path.join(full_output_folder, img_filename), pnginfo=metadata, compress_level=4)
                
            elif format == "jpg":
                img_filename = f"{file_stem}.jpg"
                if img.mode == 'RGBA': img = img.convert('RGB')
                img.save(os.path.join(full_output_folder, img_filename), quality=quality, optimize=True)
                
            elif format == "webp":
                img_filename = f"{file_stem}.webp"
                img.save(os.path.join(full_output_folder, img_filename), quality=quality, lossless=False)

            txt_filename = f"{file_stem}.txt"
            with open(os.path.join(full_output_folder, txt_filename), 'w', encoding='utf-8') as f:
                f.write(text)

            results.append({
                "filename": img_filename,
                "subfolder": subfolder,
                "type": self.type
            })
            counter += 1

        return {"ui": {"images": results}}

NODE_CLASS_MAPPINGS = {
    "MatrixDatasetSaver": MatrixDatasetSaver
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixDatasetSaver": "🧩 Matrix Dataset Saver | 矩阵-数据集保存"
}