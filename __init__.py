import os
import torch
import numpy as np
import re
from PIL import Image, ImageOps, ImageDraw, ImageFont

# ========================================================
# 尝试引入子模块
# ========================================================
try:
    from .qwen_encode import NODE_CLASS_MAPPINGS as Qwen_Mappings, NODE_DISPLAY_NAME_MAPPINGS as Qwen_Display_Mappings
    HAS_QWEN = True
except ImportError:
    HAS_QWEN = False
    print("MatrixNodes Info: qwen_encode.py not found.")

try:
    from .matrix_grid import NODE_CLASS_MAPPINGS as Grid_Mappings, NODE_DISPLAY_NAME_MAPPINGS as Grid_Display_Mappings
    HAS_GRID = True
except ImportError:
    HAS_GRID = False
    print("MatrixNodes Info: matrix_grid.py not found.")

try:
    from .video_combine import NODE_CLASS_MAPPINGS as Video_Mappings, NODE_DISPLAY_NAME_MAPPINGS as Video_Display_Mappings
    HAS_VIDEO = True
except ImportError:
    HAS_VIDEO = False
    print("MatrixNodes Info: video_combine.py not found.")

try:
    from .matrix_dataset import NODE_CLASS_MAPPINGS as Dataset_Mappings, NODE_DISPLAY_NAME_MAPPINGS as Dataset_Display_Mappings
    HAS_DATASET = True
except ImportError:
    HAS_DATASET = False
    print("MatrixNodes Info: matrix_dataset.py not found.")

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
    try: font = ImageFont.truetype("arial.ttf", 60)
    except: font = ImageFont.load_default()
    draw.text((20, 200), f"MISSING:\n{text_content}", fill=(255, 0, 0), font=font)
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
# 2. 通用基类
# ========================================================

class BaseMatrixLoaderIndex:
    def process_common(self, folder_path, empty_style, count, **kwargs):
        images = []
        for i in range(1, count + 1):
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

    def find_indexed_file(self, folder, prefix, index):
        supported_exts = ["png", "jpg", "jpeg", "webp", "bmp"]
        for ext in supported_exts:
            path = os.path.join(folder, f"{prefix}{index}.{ext}")
            if os.path.exists(path): return path
        for ext in supported_exts:
            path = os.path.join(folder, f"{prefix}{index:02d}.{ext}")
            if os.path.exists(path): return path
        return None

class BaseMatrixLoaderDirect:
    def process_common(self, folder_path, empty_style, count, **kwargs):
        images = []
        for i in range(1, count + 1):
            inp = kwargs.get(f"img_txt_{i}", "0")
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

# ========================================================
# 3. 节点实现：Loader (Index)
# ========================================================

class MatrixImageLoader_Index5(BaseMatrixLoaderIndex):
    DESCRIPTION = "【🧩 矩阵-滑块加载器 (5图版)】"
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "C:/Images/Assets", "multiline": False, "tooltip": "路径"}),
                "empty_style": (["White", "Black"], {"default": "White"}),
            },
            "optional": {
                "slot1_prefix": ("STRING", {"default": "X"}), "slot1_index": ("INT", {"default": 1, "min": 0, "max": 9999}),
                "slot2_prefix": ("STRING", {"default": "Y"}), "slot2_index": ("INT", {"default": 2, "min": 0, "max": 9999}),
                "slot3_prefix": ("STRING", {"default": "Z"}), "slot3_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot4_prefix": ("STRING", {"default": "A"}), "slot4_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
                "slot5_prefix": ("STRING", {"default": "B"}), "slot5_index": ("INT", {"default": 0, "min": 0, "max": 9999}),
            }
        }
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("Img_1", "Img_2", "Img_3", "Img_4", "Img_5")
    FUNCTION = "process"
    CATEGORY = "Custom/Matrix"
    def process(self, folder_path, empty_style, **kwargs):
        return self.process_common(folder_path, empty_style, 5, **kwargs)

class MatrixImageLoader_Index10(BaseMatrixLoaderIndex):
    DESCRIPTION = "【🧩 矩阵-滑块加载器 (10图版)】"
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "C:/Images/Assets", "multiline": False}),
                "empty_style": (["White", "Black"], {"default": "White"}),
            },
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
    RETURN_NAMES = ("Img_1", "Img_2", "Img_3", "Img_4", "Img_5", "Img_6", "Img_7", "Img_8", "Img_9", "Img_10")
    FUNCTION = "process"
    CATEGORY = "Custom/Matrix"
    def process(self, folder_path, empty_style, **kwargs):
        return self.process_common(folder_path, empty_style, 10, **kwargs)

# ========================================================
# 4. 节点实现：Loader (Direct)
# ========================================================

class MatrixImageLoader_Direct5(BaseMatrixLoaderDirect):
    DESCRIPTION = "【🧩 矩阵-字符加载器 (5图版)】"
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "C:/Images/Assets", "multiline": False, "tooltip": "路径"}),
                "empty_style": (["White", "Black"], {"default": "White"}),
            },
            "optional": {
                "img_txt_1": ("STRING", {"default": "0", "multiline": False, "forceInput": True, "tooltip": "输入文件名/ID"}),
                "img_txt_2": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "img_txt_3": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "img_txt_4": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "img_txt_5": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
            }
        }
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("Img_1", "Img_2", "Img_3", "Img_4", "Img_5") 
    FUNCTION = "process"
    CATEGORY = "Custom/Matrix"
    def process(self, folder_path, empty_style, **kwargs):
        return self.process_common(folder_path, empty_style, 5, **kwargs)

class MatrixImageLoader_Direct10(BaseMatrixLoaderDirect):
    DESCRIPTION = "【🧩 矩阵-字符加载器 (10图版)】"
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "C:/Images/Assets", "multiline": False}),
                "empty_style": (["White", "Black"], {"default": "White"}),
            },
            "optional": {
                "img_txt_1": ("STRING", {"default": "0", "multiline": False, "forceInput": True, "tooltip": "输入文件名/ID"}),
                "img_txt_2": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "img_txt_3": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "img_txt_4": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "img_txt_5": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "img_txt_6": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "img_txt_7": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "img_txt_8": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "img_txt_9": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
                "img_txt_10": ("STRING", {"default": "0", "multiline": False, "forceInput": True}),
            }
        }
    RETURN_TYPES = ("IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE", "IMAGE")
    RETURN_NAMES = ("Img_1", "Img_2", "Img_3", "Img_4", "Img_5", "Img_6", "Img_7", "Img_8", "Img_9", "Img_10")
    FUNCTION = "process"
    CATEGORY = "Custom/Matrix"
    def process(self, folder_path, empty_style, **kwargs):
        return self.process_common(folder_path, empty_style, 10, **kwargs)

# ========================================================
# 5. 新节点：Matrix Folder Iterator (文件夹遍历器)
# ========================================================

class MatrixFolderIterator:
    """
    【🧩 矩阵-文件夹遍历器】
    功能：遍历文件夹中的图片，支持关键词过滤和索引控制。
    """
    
    DESCRIPTION = """
    【🧩 矩阵-文件夹遍历器】
    功能：从指定文件夹中加载特定 Index 的图片。
    
    🚀 核心用法：
    1. 配合 EasyUse Loop: 将 image_index 转换为输入，连接 Loop 节点的 index 输出。
    2. 过滤功能: 只加载包含(或不包含)特定字符的图片 (例如只加载带 "LF" 的)。
    3. 自动循环: 内置取模逻辑。如果有 5 张图，输入 Index 6 会自动加载 Index 1。
    4. 统计输出: 输出符合条件的图片总数 (Count)，用于控制 Loop 的结束条件。
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "folder_path": ("STRING", {"default": "C:/Images", "multiline": False, "tooltip": "图片所在的文件夹路径"}),
                "image_index": ("INT", {"default": 0, "min": 0, "max": 99999, "step": 1, "tooltip": "要加载第几张图 (支持 Loop 输入)"}),
                "filter_mode": (["Contains", "Not Contains"], {"default": "Contains", "tooltip": "筛选模式：包含关键词 / 不包含关键词"}),
                "filter_text": ("STRING", {"default": "", "multiline": False, "tooltip": "筛选关键词 (留空则匹配所有)"}),
                "extension": (["All", "png", "jpg", "jpeg", "webp", "bmp"], {"default": "All", "tooltip": "只匹配特定后缀的文件"}),
                "empty_style": (["White", "Black"], {"default": "White", "tooltip": "如果文件夹为空或找不到文件，输出的占位图颜色"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT")
    RETURN_NAMES = ("Image", "Filename", "Count")
    FUNCTION = "load_image_by_index"
    CATEGORY = "Custom/Matrix"

    def load_image_by_index(self, folder_path, image_index, filter_mode, filter_text, extension, empty_style):
        if not os.path.exists(folder_path):
            print(f"MatrixIterator Error: Path not found {folder_path}")
            return (create_placeholder(empty_style), "None", 0)

        # 1. 获取所有文件并过滤后缀
        try:
            files = os.listdir(folder_path)
        except Exception as e:
            print(f"MatrixIterator Error reading dir: {e}")
            return (create_placeholder(empty_style), "Error", 0)
            
        valid_exts = [".png", ".jpg", ".jpeg", ".webp", ".bmp"]
        if extension != "All":
            valid_exts = [f".{extension}"]

        filtered_files = []
        for f in files:
            # 后缀检查
            if not any(f.lower().endswith(ext) for ext in valid_exts):
                continue
            
            # 关键词过滤
            if filter_text:
                if filter_mode == "Contains":
                    if filter_text not in f: continue
                else: # Not Contains
                    if filter_text in f: continue
            
            filtered_files.append(f)

        # 2. 排序 (保证 Index 对应关系稳定)
        filtered_files.sort()
        count = len(filtered_files)

        if count == 0:
            print("MatrixIterator: No matching files found.")
            return (create_placeholder(empty_style), "None", 0)

        # 3. 计算实际 Index (取模循环)
        # 例如 count=5, index=0 -> 0; index=4 -> 4; index=5 -> 0
        actual_index = image_index % count
        
        target_filename = filtered_files[actual_index]
        full_path = os.path.join(folder_path, target_filename)

        # 4. 加载图片
        image = load_image_file(full_path)
        if image is None:
             image = create_error_image(target_filename)

        return (image, target_filename, count)

# ========================================================
# 6. 其他节点
# ========================================================

class MatrixPromptSplitter5:
    DESCRIPTION = "【🧩 矩阵-文本拆分器 (5路)】"
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
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("Text_1", "Text_2", "Text_3", "Text_4", "Text_5")
    FUNCTION = "split_text"
    CATEGORY = "Custom/Matrix"
    def split_text(self, text_input, bracket_style, separator, bracket_index):
        left_char = bracket_style[0]
        right_char = bracket_style[1]
        pattern = f"{re.escape(left_char)}(.*?){re.escape(right_char)}"
        matches = re.findall(pattern, text_input, re.DOTALL)
        target_idx = bracket_index - 1
        final_parts = ["0"] * 5
        if target_idx >= 0 and target_idx < len(matches):
            content = matches[target_idx]
            parts = [p.strip() for p in content.split(separator)]
            for i in range(5):
                if i < len(parts):
                    val = parts[i]
                    final_parts[i] = val if val else "0"
        return tuple(final_parts)

class MatrixPromptSplitter10:
    DESCRIPTION = "【🧩 矩阵-文本拆分器 (10路)】"
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
    RETURN_NAMES = ("Text_1", "Text_2", "Text_3", "Text_4", "Text_5", "Text_6", "Text_7", "Text_8", "Text_9", "Text_10")
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
        return tuple(final_parts)

class MatrixTextExtractor:
    DESCRIPTION = "【🧩 矩阵-ID智能提取】"
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        char_types = ["Any (A-Z,0-9)", "Letter (A-Z)", "Upper (A-Z)", "Lower (a-z)", "Digit (0-9)"]
        char_types_opt = ["Ignore (End)", "Any (A-Z,0-9)", "Letter (A-Z)", "Upper (A-Z)", "Lower (a-z)", "Digit (0-9)"]
        return {
            "required": {
                "text_input": ("STRING", {"default": "", "multiline": True, "forceInput": True}),
                "search_mode": (["Auto (Smart 3-5 chars)", "Custom (Define Slots)"], {"default": "Auto (Smart 3-5 chars)"}),
                "match_index": ("INT", {"default": 1, "min": 1, "max": 99}),
                "remainder_length": ("INT", {"default": 0, "min": 0, "max": 9999}),
            },
            "optional": {
                "char_1_type": (char_types, {"default": "Any (A-Z,0-9)"}),
                "char_2_type": (char_types, {"default": "Any (A-Z,0-9)"}),
                "char_3_type": (char_types, {"default": "Any (A-Z,0-9)"}),
                "char_4_type": (char_types_opt, {"default": "Ignore (End)"}),
                "char_5_type": (char_types_opt, {"default": "Ignore (End)"}),
            }
        }
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("ID", "Remainder", "Combined")
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
        else:
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
            combined = f"{extracted_id} {remainder}" if remainder else extracted_id
        return (extracted_id, remainder, combined)

class MatrixStringChopper:
    DESCRIPTION = "【🧩 矩阵-字符切割刀】"
    def __init__(self): pass
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text_input": ("STRING", {"default": "", "multiline": True, "forceInput": True}),
                "left_delimiter": ("STRING", {"default": "-", "multiline": False}),
                "right_delimiter": ("STRING", {"default": "]", "multiline": False}),
                "match_index": ("INT", {"default": 1, "min": 1, "max": 99}),
                "include_delimiters": ("BOOLEAN", {"default": False}),
            }
        }
    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("Middle", "L_Part", "R_Part", "L+R")
    FUNCTION = "chop"
    CATEGORY = "Custom/Matrix"
    def chop(self, text_input, left_delimiter, right_delimiter, match_index, include_delimiters):
        if not text_input or not left_delimiter or not right_delimiter:
            return ("N/A", "N/A", "N/A", "N/A")
        start_pos = -1
        current_pos = 0
        for _ in range(match_index):
            found = text_input.find(left_delimiter, current_pos)
            if found == -1: return ("N/A", "N/A", "N/A", "N/A")
            start_pos = found
            current_pos = found + len(left_delimiter)
        content_start = start_pos + len(left_delimiter)
        end_pos = text_input.find(right_delimiter, content_start)
        if end_pos == -1: return ("N/A", "N/A", "N/A", "N/A")
        right_delim_end = end_pos + len(right_delimiter)
        if include_delimiters:
            middle_part = text_input[start_pos : right_delim_end]
            left_part = text_input[:start_pos]
            right_part = text_input[right_delim_end:]
        else:
            middle_part = text_input[content_start : end_pos]
            left_part = text_input[:start_pos]
            right_part = text_input[right_delim_end:]
        concat_part = left_part + right_part
        return (middle_part, left_part, right_part, concat_part)

# ========================================================
# 注册所有节点
# ========================================================
NODE_CLASS_MAPPINGS = {
    "MatrixImageLoader_Index5": MatrixImageLoader_Index5,
    "MatrixImageLoader_Index10": MatrixImageLoader_Index10,
    "MatrixImageLoader_Direct5": MatrixImageLoader_Direct5,
    "MatrixImageLoader_Direct10": MatrixImageLoader_Direct10,
    "MatrixFolderIterator": MatrixFolderIterator, # New Node
    "MatrixPromptSplitter5": MatrixPromptSplitter5,
    "MatrixPromptSplitter10": MatrixPromptSplitter10,
    "MatrixTextExtractor": MatrixTextExtractor,
    "MatrixStringChopper": MatrixStringChopper,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixImageLoader_Index5": "🧩 Matrix Loader (Index 5) | 矩阵-滑块",
    "MatrixImageLoader_Index10": "🧩 Matrix Loader (Index 10) | 矩阵-滑块",
    "MatrixImageLoader_Direct5": "🧩 Matrix Loader (String 5) | 矩阵-字符",
    "MatrixImageLoader_Direct10": "🧩 Matrix Loader (String 10) | 矩阵-字符",
    "MatrixFolderIterator": "🧩 Matrix Folder Iterator | 矩阵-文件夹遍历", # New Name
    "MatrixPromptSplitter5": "🧩 Matrix Splitter (5) | 矩阵-拆分",
    "MatrixPromptSplitter10": "🧩 Matrix Splitter (10) | 矩阵-拆分",
    "MatrixTextExtractor": "🧩 Matrix ID Extractor | 矩阵-ID提取",
    "MatrixStringChopper": "🧩 Matrix String Slicer | 矩阵-切割刀",
}

if HAS_QWEN:
    NODE_CLASS_MAPPINGS.update(Qwen_Mappings)
    Qwen_Display_Mappings["MatrixTextEncodeQwen5"] = "🧩 Matrix Qwen Encode (5) | Qwen-VL编码"
    Qwen_Display_Mappings["MatrixTextEncodeQwen10"] = "🧩 Matrix Qwen Encode (10 Experimental) | Qwen-VL编码"
    NODE_DISPLAY_NAME_MAPPINGS.update(Qwen_Display_Mappings)

if HAS_GRID:
    NODE_CLASS_MAPPINGS.update(Grid_Mappings)
    NODE_DISPLAY_NAME_MAPPINGS.update(Grid_Display_Mappings)

if HAS_VIDEO:
    NODE_CLASS_MAPPINGS.update(Video_Mappings)
    NODE_DISPLAY_NAME_MAPPINGS.update(Video_Display_Mappings)

if HAS_DATASET:
    NODE_CLASS_MAPPINGS.update(Dataset_Mappings)
    NODE_DISPLAY_NAME_MAPPINGS.update(Dataset_Display_Mappings)