# -*- coding: utf-8 -*-
import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import math

class BaseMatrixAssetGrid:
    def create_grid_common(self, thumbnail_size, columns, add_labels, count, **kwargs):
        valid_images = []
        for i in range(1, count + 1):
            key = f"img_{i}"
            img_tensor = kwargs.get(key)
            if img_tensor is not None:
                t = img_tensor[0].cpu().numpy()
                pil_img = Image.fromarray(np.clip(255. * t, 0, 255).astype(np.uint8))
                valid_images.append((i, pil_img))

        if not valid_images:
            return (torch.zeros((1, 512, 512, 3)), )

        rows = math.ceil(len(valid_images) / columns)
        cell_w = thumbnail_size
        cell_h = thumbnail_size
        text_h = 30 if add_labels else 0
        
        grid_w = columns * cell_w
        grid_h = rows * (cell_h + text_h)
        
        grid_img = Image.new('RGB', (grid_w, grid_h), color=(20, 20, 20))
        draw = ImageDraw.Draw(grid_img)
        
        try: font = ImageFont.truetype("arial.ttf", 20)
        except: font = ImageFont.load_default()

        for idx, (original_idx, pil_img) in enumerate(valid_images):
            r = idx // columns
            c = idx % columns
            x_offset = c * cell_w
            y_offset = r * (cell_h + text_h)
            
            pil_img.thumbnail((cell_w - 10, cell_h - 10))
            paste_x = x_offset + (cell_w - pil_img.width) // 2
            paste_y = y_offset + (cell_h - pil_img.height) // 2 + text_h
            
            grid_img.paste(pil_img, (paste_x, paste_y))
            
            if add_labels:
                label = f"Img {original_idx}"
                text_w = len(label) * 10 
                text_x = x_offset + (cell_w - text_w) // 2
                draw.text((text_x, y_offset + 5), label, fill=(200, 200, 200), font=font)

        output_tensor = torch.from_numpy(np.array(grid_img).astype(np.float32) / 255.0).unsqueeze(0)
        return (output_tensor,)

class MatrixAssetGrid5(BaseMatrixAssetGrid):
    """5图版拼图"""
    
    DESCRIPTION = """
    【矩阵-资产预览 (5图版)】
    功能：将 1-5 张输入图片拼接成一张网格图，方便快速预览资产。
    特点：
    1. 极低显存占用：自动生成缩略图，而非全尺寸渲染。
    2. 自动布局：根据列数自动换行。
    3. 标签显示：可选择是否显示 "Img X" 标签。
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "thumbnail_size": ("INT", {"default": 256, "min": 64, "max": 1024, "tooltip": "缩略图大小"}),
                "columns": ("INT", {"default": 5, "min": 1, "max": 5, "tooltip": "每行显示几张"}), 
                "add_labels": ("BOOLEAN", {"default": True, "tooltip": "显示图片编号"}),
            },
            "optional": {
                "img_1": ("IMAGE", ), "img_2": ("IMAGE", ), "img_3": ("IMAGE", ), 
                "img_4": ("IMAGE", ), "img_5": ("IMAGE", ),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("Grid",)
    FUNCTION = "create_grid"
    CATEGORY = "Custom/Matrix"
    def create_grid(self, thumbnail_size, columns, add_labels, **kwargs):
        return self.create_grid_common(thumbnail_size, columns, add_labels, 5, **kwargs)

class MatrixAssetGrid10(BaseMatrixAssetGrid):
    """10图版拼图"""
    
    DESCRIPTION = """
    【矩阵-资产预览 (10图版)】
    功能：将 1-10 张输入图片拼接成一张网格图。
    建议：将 thumbnail_size 设为 256 或更小，以获得最佳预览体验。
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "thumbnail_size": ("INT", {"default": 256, "min": 64, "max": 1024}),
                "columns": ("INT", {"default": 5, "min": 1, "max": 10}),
                "add_labels": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "img_1": ("IMAGE", ), "img_2": ("IMAGE", ), "img_3": ("IMAGE", ), "img_4": ("IMAGE", ), "img_5": ("IMAGE", ),
                "img_6": ("IMAGE", ), "img_7": ("IMAGE", ), "img_8": ("IMAGE", ), "img_9": ("IMAGE", ), "img_10": ("IMAGE", ),
            }
        }
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("Grid",)
    FUNCTION = "create_grid"
    CATEGORY = "Custom/Matrix"
    def create_grid(self, thumbnail_size, columns, add_labels, **kwargs):
        return self.create_grid_common(thumbnail_size, columns, add_labels, 10, **kwargs)

NODE_CLASS_MAPPINGS = {
    "MatrixAssetGrid5": MatrixAssetGrid5,
    "MatrixAssetGrid10": MatrixAssetGrid10
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixAssetGrid5": "Matrix Asset Grid (5) | 矩阵-预览",
    "MatrixAssetGrid10": "Matrix Asset Grid (10) | 矩阵-预览"
}