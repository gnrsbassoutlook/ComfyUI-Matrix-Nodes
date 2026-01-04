import os
import torch
import numpy as np
import re
from PIL import Image, ImageOps, ImageDraw, ImageFont

# ========================================================
# 1. 核心工具函数
# ========================================================

def create_placeholder(style):
    if style == "White":
        return torch.ones((1, 512, 512, 3), dtype=torch.float32)
    else:
        return torch.zeros((1, 512, 512, 3), dtype=torch.float32)

def create_error_image(text_content):
    """ 创建醒目的大红字错误提示图 """
    width, height = 512, 512
    img = Image.new('RGB', (width, height), color=(128, 128, 128))
    draw = ImageDraw.Draw(img)
    
    font_size = 60
    font = None
    
    # 尝试加载系统字体
    font_candidates = ["arial.ttf", "segoeui.ttf", "Roboto-Regular.ttf", "msyh.ttf", "simhei.ttf"]
    windows_font_paths = ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/msyh.ttf"]
    
    try:
        for font_name in font_candidates:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except: continue
        if font is None:
            for font_path in windows_font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
        if font is None:
            font = ImageFont.load_default()
    except:
        font = ImageFont.load_default()

    display_text = f"MISSING\nFILE:\n\n{text_content}"
    
    try:
        draw.multiline_text((width/2, height/2), display_text, fill=(255, 0, 0), font=font, anchor="mm", align="center")
    except:
        draw.text((20, 150), display_text, fill=(255, 0, 0), font=font)
    
    image = np.array(img).astype(np.float32) / 255.0
    image = torch.from_numpy(image)[None,]
    return image

def load_image_file(file_path):
    try:
        img = Image.open(file_path)
        img = img.convert("RGB")
        img = ImageOps.exif_transpose(img)
        image = np.array(img).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        return image
    except Exception as e:
        print(f"MatrixLoader Error: {e}")
        return None

# ========================================================
# 2. 节点：数字索引版 (Max 10)
# ========================================================
class MatrixImageLoader_Index:
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "C:/Images/Assets", "multiline": False}),
                "empty_style": (["White", "Black"], {"default": "White"}),
                
                # 1-5
                "slot1_prefix": ("STRING", {"default": "X"}), "slot1_index": ("INT", {"default": 1, "min": 0, "max": 9999}),
                "slot2_prefix": ("STRING", {"default": "Y"}), "slot2_index": ("INT", {"default": 2, "min": 0, "max": 9999}),
                "slot3_prefix": ("STRING", {"default": "Z"}), "slot3_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot4_prefix": ("STRING", {"default": "A"}), "slot4_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot5_prefix": ("STRING", {"default": "B"}), "slot5_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                
                # 6-10
                "slot6_prefix": ("STRING", {"default": "C"}), "slot6_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot7_prefix": ("STRING", {"default": "D"}), "slot7_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot8_prefix": ("STRING", {"default": "E"}), "slot8_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot9_prefix": ("STRING", {"default": "F"}), "slot9_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot10_prefix": ("STRING", {"default": "G"}), "slot10_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
            },
        }
    
    # 定义 10 个输出
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("Image_1", "Image_2", "Image_3", "Image_4", "Image_5", "Image_6", "Image_7", "Image_8", "Image_9", "Image_10")
    FUNCTION = "process"
    CATEGORY = "Custom/Matrix"

    def find_indexed_file(self, folder, prefix, index):
        supported_exts = ["png", "jpg", "jpeg", "webp", "bmp"]
        for ext in supported_exts:
            path = os.path.join(folder, f"{prefix}{index}.{ext}")
            if os.path.exists(path): return path
        for ext in supported_exts:
            path = os.path.join(folder, f"{prefix}{index:02d}.{ext}")
            if os.path.exists(path): return path
        return None

    def process(self, folder_path, empty_style, **kwargs):
        images = []
        # 循环 1 到 10
        for i in range(1, 11):
            prefix = kwargs.get(f"slot{i}_prefix")
            index = kwargs.get(f"slot{i}_index")
            if index == 0:
                images.append(create_placeholder(empty_style))
            else:
                path = self.find_indexed_file(folder_path, prefix, index)
                if path:
                    img = load_image_file(path)
                    images.append(img if img is not None else create_error_image(f"{prefix}{index}"))
                else:
                    images.append(create_error_image(f"{prefix}{index}"))
        return tuple(images)

# ========================================================
# 3. 节点：字符串直连版 (Max 10)
# ========================================================
class MatrixImageLoader_Direct:
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "C:/Images/Assets", "multiline": False}),
                "empty_style": (["White", "Black"], {"default": "White"}),
                # 10 个输入口
                "image1_input": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "image2_input": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "image3_input": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "image4_input": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "image5_input": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "image6_input": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "image7_input": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "image8_input": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "image9_input": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "image10_input": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
            },
        }
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("Image_1", "Image_2", "Image_3", "Image_4", "Image_5", "Image_6", "Image_7", "Image_8", "Image_9", "Image_10")
    FUNCTION = "process"
    CATEGORY = "Custom/Matrix"

    def find_file_fuzzy(self, folder, name_str):
        if not os.path.exists(folder): return None
        name_str = name_str.strip()
        direct_path = os.path.join(folder, name_str)
        if os.path.exists(direct_path) and os.path.isfile(direct_path): return direct_path

        supported_exts = ["png", "jpg", "jpeg", "webp", "bmp"]
        for ext in supported_exts:
            test_path = os.path.join(folder, f"{name_str}.{ext}")
            if os.path.exists(test_path): return test_path
        try:
            all_files = os.listdir(folder)
            for filename in all_files:
                if filename.startswith(name_str):
                    if any(filename.lower().endswith(ext) for ext in supported_exts):
                        return os.path.join(folder, filename)
        except: pass
        return None

    def process(self, folder_path, empty_style, **kwargs):
        images = []
        # 动态获取 kwargs 里的 imageX_input
        for i in range(1, 11):
            inp = kwargs.get(f"image{i}_input", "0")
            inp_str = str(inp).strip()
            
            if inp_str == "0" or inp_str == "" or inp_str.lower() == "none":
                images.append(create_placeholder(empty_style))
                continue
            
            path = self.find_file_fuzzy(folder_path, inp_str)
            if path:
                img = load_image_file(path)
                if img is not None:
                    images.append(img)
                else:
                    images.append(create_error_image(f"Error Loading:\n{inp_str}"))
            else:
                images.append(create_error_image(inp_str))
        return tuple(images)

# ========================================================
# 4. 节点：文本拆分器 (Max 10)
# ========================================================
class MatrixPromptSplitter:
    """
    (增强版 Max 10) 文本拆分器
    """
    def __init__(self): pass

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_input": ("STRING", {"default": "", "multiline": True, "forceInput": True}),
                
                "bracket_style": ([
                    "[]", "{}", "()", "<>", "''", '""', 
                    "【】", "《》", "（）", "“”",
                ], {"default": "[]"}),
                
                "separator": ([
                    "|", ",", "-", "_", "+", "=", "&", "@", "#", "$", "%", "^", "*", "~",
                ], {"default": "|"}),

                "bracket_index": ("INT", {"default": 1, "min": 1, "max": 99}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("Str_1", "Str_2", "Str_3", "Str_4", "Str_5", "Str_6", "Str_7", "Str_8", "Str_9", "Str_10")
    FUNCTION = "split_text"
    CATEGORY = "Custom/Matrix"

    def split_text(self, text_input, bracket_style, separator, bracket_index):
        left_char = bracket_style[0]
        right_char = bracket_style[1]
        pattern = f"{re.escape(left_char)}(.*?){re.escape(right_char)}"
        
        matches = re.findall(pattern, text_input, re.DOTALL)
        target_idx = bracket_index - 1
        
        # 初始化 10 个 "0"
        final_parts = ["0"] * 10

        if target_idx >= 0 and target_idx < len(matches):
            content = matches[target_idx]
            parts = [p.strip() for p in content.split(separator)]
            
            # 填充数据
            for i in range(10):
                if i < len(parts):
                    val = parts[i]
                    final_parts[i] = val if val else "0"
                else:
                    final_parts[i] = "0"
        else:
            print(f"MatrixSplitter Warning: Group {bracket_index} not found.")

        return tuple(final_parts)

# ========================================================
# 注册所有节点
# ========================================================
NODE_CLASS_MAPPINGS = {
    "MatrixImageLoader_Index": MatrixImageLoader_Index,
    "MatrixImageLoader_Direct": MatrixImageLoader_Direct,
    "MatrixPromptSplitter": MatrixPromptSplitter
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixImageLoader_Index": "Matrix Image Loader (Index 10)",
    "MatrixImageLoader_Direct": "Matrix Image Loader (String 10)",
    "MatrixPromptSplitter": "Matrix Prompt Splitter (10)"
}