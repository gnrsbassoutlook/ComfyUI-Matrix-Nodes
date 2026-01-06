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
# 2. 节点：数字索引版 (Index)
# ========================================================
class MatrixImageLoader_Index:
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "C:/Images/Assets", "multiline": False, "tooltip": "图片所在的文件夹绝对路径"}),
                "empty_style": (["White", "Black"], {"default": "White", "tooltip": "当索引为0或找不到文件时，生成的占位图颜色"}),
            },
            "optional": {
                "slot1_prefix": ("STRING", {"default": "X", "tooltip": "第1组图片的前缀 (如 X)"}),
                "slot1_index": ("INT", {"default": 1, "min": 0, "max": 9999, "tooltip": "第1组图片的序号 (0代表留空)"}),
                "slot2_prefix": ("STRING", {"default": "Y", "tooltip": "第2组图片的前缀"}),
                "slot2_index": ("INT", {"default": 2, "min": 0, "max": 9999}),
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
# 3. 节点：字符串直连版 (String)
# ========================================================
class MatrixImageLoader_Direct:
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "C:/Images/Assets", "multiline": False, "tooltip": "图片所在的文件夹绝对路径"}),
                "empty_style": (["White", "Black"], {"default": "White", "tooltip": "当输入为0、None或找不到文件时，生成的占位图颜色"}),
            },
            "optional": {
                "image1_input": ("STRING", {"default": "0", "multiline": False, "forceInput": True, "tooltip": "输入文件名、ID(如X1)或关键词。输入0留空。"}),
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
            # 强制排序
            all_files = sorted(os.listdir(folder))
            
            if inp_prefix is not None:
                candidates = []
                for filename in all_files:
                    if not any(filename.lower().endswith(ext) for ext in supported_exts):
                        continue
                    name_stem = os.path.splitext(filename)[0]
                    f_prefix, f_num, f_suffix = self.parse_filename(name_stem)
                    if f_prefix is None: continue
                    if (inp_prefix == f_prefix and inp_num == f_num and inp_suffix == f_suffix):
                        candidates.append(filename)
                
                # 优先最短匹配
                if candidates:
                    candidates.sort(key=len)
                    return os.path.join(folder, candidates[0])

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
# 4. 节点：文本拆分器 (Splitter)
# ========================================================
class MatrixPromptSplitter:
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_input": ("STRING", {"default": "", "multiline": True, "forceInput": True, "tooltip": "输入包含中括号的长文本"}),
                "bracket_style": (["[]", "{}", "()", "<>", "''", '""', "【】", "《》", "（）", "“”"], {"default": "[]", "tooltip": "选择文本中使用的括号类型"}),
                "separator": (["|", ",", "-", "_", "+", "=", "&", "@", "#", "$", "%", "^", "*", "~"], {"default": "|", "tooltip": "选择括号内部使用的分隔符"}),
                "bracket_index": ("INT", {"default": 1, "min": 1, "max": 99, "tooltip": "提取文本中第几组括号的内容 (1代表第1组)"}),
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
# 5. 节点：文本 ID 提取器 (Extractor)
# ========================================================
class MatrixTextExtractor:
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        char_types = ["Any (A-Z,0-9)", "Letter (A-Z)", "Upper (A-Z)", "Lower (a-z)", "Digit (0-9)"]
        char_types_opt = ["Ignore (End)", "Any (A-Z,0-9)", "Letter (A-Z)", "Upper (A-Z)", "Lower (a-z)", "Digit (0-9)"]
        
        return {
            "required": {
                "text_input": ("STRING", {"default": "", "multiline": True, "forceInput": True, "tooltip": "待提取的源文本"}),
                "search_mode": (["Auto (Smart 3-5 chars)", "Custom (Define Slots)"], {"default": "Auto (Smart 3-5 chars)", "tooltip": "Auto: 智能提取3-5位ID; Custom: 自定义5位规则"}),
                "match_index": ("INT", {"default": 1, "min": 1, "max": 99, "step": 1, "tooltip": "如果文本中有多个符合条件的ID，提取第几个？(1代表第1个)"}),
                "remainder_length": ("INT", {"default": 0, "min": 0, "max": 9999, "step": 1, "tooltip": "截取ID后多少个字符作为描述。0 = 无限(全部提取)"}),
            },
            "optional": {
                "char_1_type": (char_types, {"default": "Any (A-Z,0-9)", "tooltip": "[Custom模式] 第1位字符类型"}),
                "char_2_type": (char_types, {"default": "Any (A-Z,0-9)", "tooltip": "[Custom模式] 第2位字符类型"}),
                "char_3_type": (char_types, {"default": "Any (A-Z,0-9)", "tooltip": "[Custom模式] 第3位字符类型"}),
                "char_4_type": (char_types_opt, {"default": "Ignore (End)", "tooltip": "[Custom模式] 第4位字符类型 (可选)"}),
                "char_5_type": (char_types_opt, {"default": "Ignore (End)", "tooltip": "[Custom模式] 第5位字符类型 (可选)"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("ID_String", "Remainder_Text", "Combined_Text")
    FUNCTION = "extract"
    CATEGORY = "Custom/Matrix"

    def get_regex_for_type(self, type_str):
        if "Ignore" in type_str: return ""
        if "Any" in type_str: return "[a-zA-Z0-9]"
        if "Letter" in type_str and "Upper" not in type_str and "Lower" not in type_str: return "[a-zA-Z]"
        if "Upper" in type_str: return "[A-Z]"
        if "Lower" in type_str: return "[a-z]"
        if "Digit" in type_str: return "[0-9]"
        return "."

    def extract(self, text_input, search_mode, match_index, remainder_length, char_1_type, char_2_type, char_3_type, char_4_type, char_5_type):
        extracted_id = "0"
        remainder = ""
        combined = "0"
        matches = []
        if search_mode == "Auto (Smart 3-5 chars)":
            candidates = re.finditer(r'[a-zA-Z0-9]+', text_input)
            for m in candidates:
                val = m.group(0)
                if 3 <= len(val) <= 5:
                    if val.isalpha(): continue 
                    matches.append(m)
        else: # Custom Mode
            p1 = self.get_regex_for_type(char_1_type)
            p2 = self.get_regex_for_type(char_2_type)
            p3 = self.get_regex_for_type(char_3_type)
            p4 = self.get_regex_for_type(char_4_type)
            p5 = self.get_regex_for_type(char_5_type)
            pattern_str = f"({p1}{p2}{p3}{p4}{p5})"
            matches = list(re.finditer(pattern_str, text_input))

        target_idx = match_index - 1
        if target_idx >= 0 and target_idx < len(matches):
            target_match = matches[target_idx]
            if search_mode.startswith("Auto"):
                extracted_id = target_match.group(0)
            else:
                extracted_id = target_match.group(1)
            raw_remainder = text_input[target_match.end():]
            remainder = re.sub(r'^[ :：\-_.]+', '', raw_remainder).strip()
            if remainder_length > 0:
                if len(remainder) > remainder_length:
                    remainder = remainder[:remainder_length]
            if remainder:
                combined = f"{extracted_id} {remainder}"
            else:
                combined = extracted_id
        else:
            print(f"MatrixTextExtractor: Match Index {match_index} out of range.")
        return (extracted_id, remainder, combined)

# ========================================================
# 6. 节点：字符切割刀 (String Slicer) - 逻辑修正版
# ========================================================
class MatrixStringChopper:
    """
    字符串切割刀：截取两个自定义符号之间的文本
    """
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_input": ("STRING", {"default": "", "multiline": True, "forceInput": True, "tooltip": "待切割的源文本"}),
                "left_delimiter": ("STRING", {"default": "-", "multiline": False, "tooltip": "左侧截断符号 (例如 - )"}),
                "right_delimiter": ("STRING", {"default": "]", "multiline": False, "tooltip": "右侧截断符号 (例如 ] )"}),
                "match_index": ("INT", {"default": 1, "min": 1, "max": 99, "step": 1, "tooltip": "如果有多组符合的符号，使用第几组？"}),
                "include_delimiters": ("BOOLEAN", {"default": False, "tooltip": "输出结果是否包含截断符号本身？"}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("Middle_Part", "Left_Part", "Right_Part", "Left_Right_Concat")
    FUNCTION = "chop"
    CATEGORY = "Custom/Matrix"

    def chop(self, text_input, left_delimiter, right_delimiter, match_index, include_delimiters):
        if not text_input or not left_delimiter or not right_delimiter:
            return ("N/A", "N/A", "N/A", "N/A")

        # 1. 寻找第 N 个左符号
        start_pos = -1
        current_pos = 0
        for _ in range(match_index):
            found = text_input.find(left_delimiter, current_pos)
            if found == -1:
                return ("N/A", "N/A", "N/A", "N/A")
            start_pos = found
            current_pos = found + len(left_delimiter)

        # 2. 寻找右符号
        content_start = start_pos + len(left_delimiter)
        end_pos = text_input.find(right_delimiter, content_start)

        if end_pos == -1:
            return ("N/A", "N/A", "N/A", "N/A")

        # 3. 核心切割逻辑 (修复版)
        right_delim_end = end_pos + len(right_delimiter)

        if include_delimiters:
            # 模式：包含符号
            # Middle: -[... Content ...]
            middle_part = text_input[start_pos : right_delim_end]
            # Left: 004 (Before the left symbol)
            left_part = text_input[:start_pos]
            # Right: -Tail (After the right symbol)
            right_part = text_input[right_delim_end:]
        else:
            # 模式：不包含符号 (因果律消除)
            # Middle: [... Content ...]
            middle_part = text_input[content_start : end_pos]
            # Left: 004 (Stop before left symbol)
            left_part = text_input[:start_pos]
            # Right: -Tail (Start after right symbol)
            right_part = text_input[right_delim_end:]

        # 4. 组合输出 (Left + Right, 也就是挖空后的结果)
        concat_part = left_part + right_part

        return (middle_part, left_part, right_part, concat_part)

# ========================================================
# 注册所有节点 (中文美化版)
# ========================================================
NODE_CLASS_MAPPINGS = {
    "MatrixImageLoader_Index": MatrixImageLoader_Index,
    "MatrixImageLoader_Direct": MatrixImageLoader_Direct,
    "MatrixPromptSplitter": MatrixPromptSplitter,
    "MatrixTextExtractor": MatrixTextExtractor,
    "MatrixStringChopper": MatrixStringChopper
}
if HAS_QWEN:
    NODE_CLASS_MAPPINGS.update(Qwen_Mappings)

NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixImageLoader_Index": "Matrix Image Loader (Index 10) | 矩阵-滑块加载器",
    "MatrixImageLoader_Direct": "Matrix Image Loader (String 10) | 矩阵-字符加载器",
    "MatrixPromptSplitter": "Matrix Prompt Splitter (10) | 矩阵-文本拆分器",
    "MatrixTextExtractor": "Matrix Smart ID Extractor | 矩阵-ID智能提取",
    "MatrixStringChopper": "Matrix String Slicer | 矩阵-字符切割刀"
}
if HAS_QWEN:
    Qwen_Display_Mappings["MatrixTextEncodeQwen5"] = "Qwen Text Encode (5 Images) | Qwen-VL编码器"
    NODE_DISPLAY_NAME_MAPPINGS.update(Qwen_Display_Mappings)