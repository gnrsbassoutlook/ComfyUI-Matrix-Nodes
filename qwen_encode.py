import math
import torch
import comfy.utils
import node_helpers

# ========================================================
# 辅助函数：检测是否为无效占位图
# ========================================================
def is_valid_image(img):
    """
    判断图片是否有效。
    如果图片是 None，或者检测到是纯黑/纯白的占位图，返回 False。
    """
    if img is None:
        return False
    
    # 检查 Tensor 是否为空
    if img.numel() == 0:
        return False

    # 性能优化：只检查极值。
    # Matrix 节点生成的占位图是纯 0.0 (黑) 或纯 1.0 (白)。
    # 如果 min == max，说明整张图只有一个颜色。
    # 并且这个颜色是 0 或 1，那大概率就是占位图。
    min_val = img.min().item()
    max_val = img.max().item()
    
    if min_val == max_val:
        if min_val == 0.0 or min_val == 1.0:
            return False
            
    return True

# ========================================================
# 节点 1: 5图标准版 (Strict Original + Smart Filter)
# ========================================================
class MatrixTextEncodeQwen5:
    """
    Qwen Text Encode (5 Images)
    1. 增加“智能过滤”：自动忽略纯黑/纯白占位图。
    2. 参数名保持 image1... 官方兼容。
    """
    
    DESCRIPTION = """
    【Qwen-VL 编码器 (5图版)】
    功能：专为 Qwen-VL 模型设计的文本+图像编码节点。
    
    🚀 智能特性：
    内置“占位图过滤器”。如果你连接了 Matrix Loader 的空插槽（输出纯黑/白图），
    本节点会自动将其忽略，不计入 Token。
    这意味着你可以放心地把 5 根线全连上，只用其中几张，完全不影响效果！
    """

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "clip": ("CLIP", ),
            "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True}),
            "negative_prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}), 
            "smart_input": ("BOOLEAN", {"default": False, "tooltip": "开启后，根据【有效图片】的数量自动调整分辨率。"}), 
            "align_latent": (["disabled", "image1_only", "all"], {"default": "image1_only"}), 
            },
            "optional": {
                "vae": ("VAE", ),
                "image1": ("IMAGE", ),
                "image2": ("IMAGE", ),
                "image3": ("IMAGE", ),
                "image4": ("IMAGE", ),
                "image5": ("IMAGE", ),
            }}
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT",)
    RETURN_NAMES = ("cond+", "cond-", "latent")
    FUNCTION = "encode"
    
    CATEGORY = "Custom/Matrix"
    
    def encode(self, clip, prompt, negative_prompt, smart_input, align_latent, vae=None, image1=None, image2=None, image3=None, image4=None, image5=None):
        ref_latents = []
        
        # === 核心修改：使用智能过滤 ===
        raw_images = [image1, image2, image3, image4, image5]
        images = [img for img in raw_images if is_valid_image(img)]
        # ===========================
        
        images_vl = []
        llama_template = "<|im_start|>system\nDescribe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input where appropriate.<|im_end|>\n<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n"
        image_prompt = ""
        output_latent = None
        
        size = 384
        if smart_input:
            size = 1024
            if len(images) > 2:
                size = 384
            elif len(images) > 1:
                size = 512
        
        for i, image in enumerate(images):
            samples = image.movedim(-1, 1)
            total = int(size * size)
            
            scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
            width = round(samples.shape[3] * scale_by)
            height = round(samples.shape[2] * scale_by)
            
            s = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
            images_vl.append(s.movedim(1, -1))
            
            if vae is not None:
                if (align_latent == "image1_only" and i == 0) or align_latent == "all":
                    l = vae.encode(image[:, :, :, :3])
                    if i == 0:
                        output_latent = l
                    ref_latents.append(l)
                else:
                    if i == 0:
                        output_latent = vae.encode(image[:, :, :, :3])
                    total = int(1024 * 1024)
                    scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
                    width = round(samples.shape[3] * scale_by / 8.0) * 8
                    height = round(samples.shape[2] * scale_by / 8.0) * 8
                    
                    s = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
                    ref_latents.append(vae.encode(s.movedim(1, -1)[:, :, :, :3]))
                
            image_prompt += "Picture {}: <|vision_start|><|image_pad|><|vision_end|>".format(i + 1)
                
        tokens = clip.tokenize(image_prompt + prompt, images=images_vl, llama_template=llama_template)
        conditioning = clip.encode_from_tokens_scheduled(tokens)
        tokensN = clip.tokenize(image_prompt + negative_prompt, images=images_vl, llama_template=llama_template)
        conditioningN = clip.encode_from_tokens_scheduled(tokensN)
        
        if len(ref_latents) > 0:
            conditioning = node_helpers.conditioning_set_values(conditioning, {"reference_latents": ref_latents}, append=True)
            conditioningN = node_helpers.conditioning_set_values(conditioningN, {"reference_latents": ref_latents}, append=True)
        
        return (conditioning, conditioningN, {"samples": output_latent}, )

# ========================================================
# 节点 2: 10图试验版 (Strict Original + Smart Filter)
# ========================================================
class MatrixTextEncodeQwen10:
    """
    Qwen Text Encode (10 Images) - Experimental
    同样增加了智能过滤。
    """
    
    DESCRIPTION = """
    【Qwen-VL 编码器 (10图试验版)】
    功能：扩展了输入上限。
    智能特性：同样内置“占位图过滤器”，自动剔除纯黑/纯白图片，减少模型干扰。
    """

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "clip": ("CLIP", ),
            "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True}),
            "negative_prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}), 
            "smart_input": ("BOOLEAN", {"default": False}), 
            "align_latent": (["disabled", "image1_only", "all"], {"default": "image1_only"}), 
            },
            "optional": {
                "vae": ("VAE", ),
                "image1": ("IMAGE", ), "image2": ("IMAGE", ), "image3": ("IMAGE", ), "image4": ("IMAGE", ), "image5": ("IMAGE", ),
                "image6": ("IMAGE", ), "image7": ("IMAGE", ), "image8": ("IMAGE", ), "image9": ("IMAGE", ), "image10": ("IMAGE", ),
            }}
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT",)
    RETURN_NAMES = ("cond+", "cond-", "latent") 
    FUNCTION = "encode"
    
    CATEGORY = "Custom/Matrix"
    
    def encode(self, clip, prompt, negative_prompt, smart_input, align_latent, vae=None, image1=None, image2=None, image3=None, image4=None, image5=None, image6=None, image7=None, image8=None, image9=None, image10=None):
        ref_latents = []
        
        # === 核心修改：使用智能过滤 ===
        raw_images = [image1, image2, image3, image4, image5, image6, image7, image8, image9, image10]
        images = [img for img in raw_images if is_valid_image(img)]
        # ===========================
        
        images_vl = []
        llama_template = "<|im_start|>system\nDescribe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input where appropriate.<|im_end|>\n<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n"
        image_prompt = ""
        output_latent = None
        
        size = 384
        if smart_input:
            size = 1024
            if len(images) > 2:
                size = 384
            elif len(images) > 1:
                size = 512
        
        for i, image in enumerate(images):
            samples = image.movedim(-1, 1)
            total = int(size * size)
            
            scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
            width = round(samples.shape[3] * scale_by)
            height = round(samples.shape[2] * scale_by)
            
            s = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
            images_vl.append(s.movedim(1, -1))
            
            if vae is not None:
                if (align_latent == "image1_only" and i == 0) or align_latent == "all":
                    l = vae.encode(image[:, :, :, :3])
                    if i == 0:
                        output_latent = l
                    ref_latents.append(l)
                else:
                    if i == 0:
                        output_latent = vae.encode(image[:, :, :, :3])
                    total = int(1024 * 1024)
                    scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
                    width = round(samples.shape[3] * scale_by / 8.0) * 8
                    height = round(samples.shape[2] * scale_by / 8.0) * 8
                    
                    s = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
                    ref_latents.append(vae.encode(s.movedim(1, -1)[:, :, :, :3]))
                
            image_prompt += "Picture {}: <|vision_start|><|image_pad|><|vision_end|>".format(i + 1)
                
        tokens = clip.tokenize(image_prompt + prompt, images=images_vl, llama_template=llama_template)
        conditioning = clip.encode_from_tokens_scheduled(tokens)
        tokensN = clip.tokenize(image_prompt + negative_prompt, images=images_vl, llama_template=llama_template)
        conditioningN = clip.encode_from_tokens_scheduled(tokensN)
        
        if len(ref_latents) > 0:
            conditioning = node_helpers.conditioning_set_values(conditioning, {"reference_latents": ref_latents}, append=True)
            conditioningN = node_helpers.conditioning_set_values(conditioningN, {"reference_latents": ref_latents}, append=True)
        
        return (conditioning, conditioningN, {"samples": output_latent}, )

NODE_CLASS_MAPPINGS = {
    "MatrixTextEncodeQwen5": MatrixTextEncodeQwen5,
    "MatrixTextEncodeQwen10": MatrixTextEncodeQwen10
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixTextEncodeQwen5": "Matrix Qwen Encode (5)",
    "MatrixTextEncodeQwen10": "Matrix Qwen Encode (10 Experimental)"
}