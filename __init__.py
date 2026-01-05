import os
import torch
import numpy as np
import re
from PIL import Image, ImageOps, ImageDraw, ImageFont

# ========================================================
# 尝试引入 Qwen 节点
# ========================================================
try:
    from .qwen_encode import NODE_CLASS_MAPPINGS as Qwen_Mappings, NODE_DISPLAY_NAME_MAPPINGS as Qwen_Display_Mappings
    HAS_QWEN = True
except ImportError:
    HAS_QWEN = False
    print("MatrixNodes Info: qwen_encode.py not found, Qwen nodes will be disabled.")

# ========================================================
# 1. 核心工具函数
# ========================================================

def create_placeholder(style):
    if style == "White":
        return torch.ones((1, 512, 512, 3), dtype=torch.float32)
    else:
        return torch.zeros((1, 512, 512, 3), dtype=torch.float32)

def create_error_image(text_content):
    width, height = 512, 512
    img = Image.new('RGB', (width, height), color=(128, 128, 128))
    draw = ImageDraw.Draw(img)
    font_size = 60
    font = None
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
# 2. 节点：数字索引版 (MatrixImageLoader_Index)
# ========================================================
class MatrixImageLoader_Index:
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "C:/Images/Assets", "multiline": False}),
                "empty_style": (["White", "Black"], {"default": "White"}),
            },
            # 将插槽移至 optional，防止不连接报错
            "optional": {
                "slot1_prefix": ("STRING", {"default": "X"}), "slot1_index": ("INT", {"default": 1, "min": 0, "max": 9999}),
                "slot2_prefix": ("STRING", {"default": "Y"}), "slot2_index": ("INT", {"default": 2, "min": 0, "max": 9999}),
                "slot3_prefix": ("STRING", {"default": "Z"}), "slot3_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot4_prefix": ("STRING", {"default": "A"}), "slot4_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot5_prefix": ("STRING", {"default": "B"}), "slot5_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot6_prefix": ("STRING", {"default": "C"}), "slot6_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot7_prefix": ("STRING", {"default": "D"}), "slot7_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot8_prefix": ("STRING", {"default": "E"}), "slot8_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot9_prefix": ("STRING", {"default": "F"}), "slot9_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot10_prefix": ("STRING", {"default": "G"}), "slot10_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
            }
        }
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
        for i in range(1, 11):
            # 使用 kwargs.get 并设置默认值，应对未连接的情况
            prefix = kwargs.get(f"slot{i}_prefix", "X")
            index = kwargs.get(f"slot{i}_index", 0)
            
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
# 3. 节点：字符串直连版 (Max 10) - 智能全字母 ID 版
# ========================================================
class MatrixImageLoader_Direct:
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "C:/Images/Assets", "multiline": False}),
                "empty_style": (["White", "Black"], {"default": "White"}),
            },
            # 【关键修改】将 image_input 移入 optional，允许不连线！
            "optional": {
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
            }
        }
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("Image_1", "Image_2", "Image_3", "Image_4", "Image_5", "Image_6", "Image_7", "Image_8", "Image_9", "Image_10")
    FUNCTION = "process"
    CATEGORY = "Custom/Matrix"

    def parse_id(self, text):
        match = re.match(r'^([a-zA-Z]+)(\d+)([a-zA-Z]?)$', text.strip())
        if match:
            prefix = match.group(1).lower()
            number = int(match.group(2)) 
            suffix = match.group(3).lower() 
            return prefix, number, suffix
        return None, None, None

    def parse_filename(self, filename):
        match = re.match(r'^([a-zA-Z]+)(\d+)([a-zA-Z]?)(?:[.\-_ \u4e00-\u9fa5].*)?$', filename)
        if match:
            prefix = match.group(1).lower()
            number = int(match.group(2))
            suffix = match.group(3).lower()
            return prefix, number, suffix
        return None, None, None

    def find_file_smart(self, folder, input_str):
        if not os.path.exists(folder): return None
        input_str = input_str.strip()
        
        inp_prefix, inp_num, inp_suffix = self.parse_id(input_str)
        supported_exts = ["png", "jpg", "jpeg", "webp", "bmp"]
        
        try:
            all_files = os.listdir(folder)
            
            if inp_prefix is not None:
                for filename in all_files:
                    if not any(filename.lower().endswith(ext) for ext in supported_exts):
                        continue
                    name_stem = os.path.splitext(filename)[0]
                    f_prefix, f_num, f_suffix = self.parse_filename(name_stem)
                    if f_prefix is None: continue
                    if (inp_prefix == f_prefix and 
                        inp_num == f_num and 
                        inp_suffix == f_suffix):
                        return os.path.join(folder, filename)

            direct_path = os.path.join(folder, input_str)
            if os.path.exists(direct_path) and os.path.isfile(direct_path): return direct_path

            for ext in supported_exts:
                test_path = os.path.join(folder, f"{input_str}.{ext}")
                if os.path.exists(test_path): return test_path
            
            if inp_prefix is None: 
                for filename in all_files:
                    if filename.startswith(input_str):
                        if any(filename.lower().endswith(ext) for ext in supported_exts):
                            return os.path.join(folder, filename)
                            
        except Exception as e:
            print(f"MatrixLoader Error: {e}")
        return None

    def process(self, folder_path, empty_style, **kwargs):
        images = []
        for i in range(1, 11):
            # 如果没连线，kwargs.get 会取到默认值 "0"
            inp = kwargs.get(f"image{i}_input", "0")
            inp_str = str(inp).strip()
            
            if inp_str == "0" or inp_str == "" or inp_str.lower() == "none":
                images.append(create_placeholder(empty_style))
                continue
            
            path = self.find_file_smart(folder_path, inp_str)
            if path:
                img = load_image_file(path)
                images.append(img if img is not None else create_error_image(f"Error Loading:\n{inp_str}"))
            else:
                images.append(create_error_image(inp_str))
        return tuple(images)

# ========================================================
# 4. 节点：文本拆分器 (Max 10)
# ========================================================
class MatrixPromptSplitter:
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_input": ("STRING", {"default": "", "multiline": True, "forceInput": True}),
                "bracket_style": (["[]", "{}", "()", "<>", "''", '""', "【】", "《》", "（）", "“”"], {"default": "[]"}),
                "separator": (["|", ",", "-", "_", "+", "=", "&", "@", "#", "$", "%", "^", "*", "~"], {"default": "|"}),
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
        final_parts = ["0"] * 10
        if target_idx >= 0 and target_idx < len(matches):
            content = matches[target_idx]
            parts = [p.strip() for p in content.split(separator)]
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
if HAS_QWEN:
    NODE_CLASS_MAPPINGS.update(Qwen_Mappings)

NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixImageLoader_Index": "Matrix Image Loader (Index 10)",
    "MatrixImageLoader_Direct": "Matrix Image Loader (String 10)",
    "MatrixPromptSplitter": "Matrix Prompt Splitter (10)"
}
if HAS_QWEN:
    NODE_DISPLAY_NAME_MAPPINGS.update(Qwen_Display_Mappings)