import math
import torch
import comfy.utils
import node_helpers

def is_valid_image(img):
    if img is None: return False
    if img.numel() == 0: return False
    min_val = img.min().item()
    max_val = img.max().item()
    if min_val == max_val and (min_val == 0.0 or min_val == 1.0):
        return False
    return True

# ========================================================
# 节点 1: 5图标准版
# ========================================================
class MatrixTextEncodeQwen5:
    """
    Qwen Text Encode (5 Images)
    🚀 核心升级：动态重排逻辑
    不管你选中哪张图做 Align，本节点都会把它偷偷挪到 Picture 1 的位置送给模型。
    这能完美解决“只有 Image 1 能对齐”的问题。
    """
    
    DESCRIPTION = """
    【Qwen-VL 编码器 (5图版)】
    🚀 智能重排技术：
    无论你选择 Image 3 还是 Image 5 作为对齐底板，
    本节点都会自动将其调整为模型眼中的“第一张图”。
    彻底解决非 Image 1 无法对齐的痛点！
    """

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "clip": ("CLIP", ),
            "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True}),
            "negative_prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}), 
            "smart_input": ("BOOLEAN", {"default": False}), 
            "align_latent": (["disabled", "image1", "image2", "image3", "image4", "image5"], {"default": "image1"}), 
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
        raw_inputs = [image1, image2, image3, image4, image5]
        
        # 1. 确定谁是主角 (Align Target)
        target_img = None
        other_images = []
        
        target_idx = -1
        if align_latent != "disabled":
            try:
                target_idx = int(align_latent.replace("image", "")) - 1
            except: pass

        # 2. 构建重排后的列表 (valid_images)
        # 逻辑：如果指定了 Target 且有效，把它放到列表第一位 (index 0)
        # 其他有效图片跟在后面
        
        for idx, img in enumerate(raw_inputs):
            if is_valid_image(img):
                if idx == target_idx:
                    target_img = img # 找到主角了
                else:
                    other_images.append(img) # 配角先排队
        
        final_images = []
        output_latent = None
        
        if target_img is not None:
            # 主角插队到第一位！
            final_images.append(target_img)
            # 计算 Latent
            if vae is not None:
                output_latent = vae.encode(target_img[:, :, :, :3])
        
        # 把其他配角接在后面
        final_images.extend(other_images)
        
        # 3. 开始编码 (此时 final_images[0] 一定是我们要对齐的那张图)
        ref_latents = []
        images_vl = []
        llama_template = "<|im_start|>system\nDescribe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input where appropriate.<|im_end|>\n<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n"
        image_prompt = ""
        
        size = 384
        if smart_input:
            size = 1024
            if len(final_images) > 2:
                size = 384
            elif len(final_images) > 1:
                size = 512
        
        for i, image in enumerate(final_images):
            samples = image.movedim(-1, 1)
            total = int(size * size)
            scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
            width = round(samples.shape[3] * scale_by)
            height = round(samples.shape[2] * scale_by)
            s = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
            images_vl.append(s.movedim(1, -1))
            
            if vae is not None:
                l = vae.encode(image[:, :, :, :3])
                ref_latents.append(l)
                
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
# 节点 2: 10图试验版
# ========================================================
class MatrixTextEncodeQwen10:
    """
    Qwen Text Encode (10 Images) - Experimental
    同样的重排逻辑。
    """
    
    DESCRIPTION = """
    【Qwen-VL 编码器 (10图试验版)】
    功能：扩展了输入上限，支持自由选择 1-10 任意一张作为底图（自动重排到第一位）。
    """

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "clip": ("CLIP", ),
            "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True}),
            "negative_prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}), 
            "smart_input": ("BOOLEAN", {"default": False}), 
            "align_latent": (["disabled", "image1", "image2", "image3", "image4", "image5", "image6", "image7", "image8", "image9", "image10"], {"default": "image1"}), 
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
        raw_inputs = [image1, image2, image3, image4, image5, image6, image7, image8, image9, image10]
        
        target_img = None
        other_images = []
        target_idx = -1
        
        if align_latent != "disabled":
            try:
                target_idx = int(align_latent.replace("image", "")) - 1
            except: pass

        for idx, img in enumerate(raw_inputs):
            if is_valid_image(img):
                if idx == target_idx:
                    target_img = img
                else:
                    other_images.append(img)
        
        final_images = []
        output_latent = None
        
        if target_img is not None:
            final_images.append(target_img)
            if vae is not None:
                output_latent = vae.encode(target_img[:, :, :, :3])
        
        final_images.extend(other_images)
        
        ref_latents = []
        images_vl = []
        llama_template = "<|im_start|>system\nDescribe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input where appropriate.<|im_end|>\n<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n"
        image_prompt = ""
        
        size = 384
        if smart_input:
            size = 1024
            if len(final_images) > 2:
                size = 384
            elif len(final_images) > 1:
                size = 512
        
        for i, image in enumerate(final_images):
            samples = image.movedim(-1, 1)
            total = int(size * size)
            scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
            width = round(samples.shape[3] * scale_by)
            height = round(samples.shape[2] * scale_by)
            s = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
            images_vl.append(s.movedim(1, -1))
            
            if vae is not None:
                l = vae.encode(image[:, :, :, :3])
                ref_latents.append(l)
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