import math
import comfy.utils
import node_helpers

# ========================================================
# 节点 1: 5图标准版 (推荐)
# ========================================================
class MatrixTextEncodeQwen5:
    """
    Qwen Text Encode (5 Images)
    标准版：最稳健的配置，官方推荐 Sweet Spot。
    """
    
    DESCRIPTION = """
    【Qwen-VL 编码器 (5图版)】
    功能：专为 Qwen-VL 模型设计的文本+图像编码节点。
    特性：
    1. 纯本地运行：移除了所有 API 依赖，无需联网。
    2. 5图支持：优化后的注意力机制，支持 1-5 张参考图。
    3. 智能分辨率：Smart Input 开启后自动调整编码尺寸。
    """

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "clip": ("CLIP", ),
            "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "tooltip": "正向提示词"}),
            "neg_prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": "", "tooltip": "负向提示词"}), 
            "smart_input": ("BOOLEAN", {"default": False, "tooltip": "智能分辨率：根据图片数量自动选择最佳编码尺寸。"}), 
            "align_latent": (["disabled", "image1_only", "all"], {"default": "image1_only", "tooltip": "Latent对齐策略：决定哪些图片参与 VAE 编码对齐。"}), 
            },
            "optional": {
                "vae": ("VAE", ),
                "img_1": ("IMAGE", ),
                "img_2": ("IMAGE", ),
                "img_3": ("IMAGE", ),
                "img_4": ("IMAGE", ),
                "img_5": ("IMAGE", ),
            }}
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT",)
    RETURN_NAMES = ("cond+", "cond-", "latent") 
    FUNCTION = "encode"
    
    CATEGORY = "Custom/Matrix"
    
    def encode(self, clip, prompt, neg_prompt, smart_input, align_latent, vae=None, img_1=None, img_2=None, img_3=None, img_4=None, img_5=None):
        ref_latents = []
        
        images = [img for img in [img_1, img_2, img_3, img_4, img_5] if img is not None]
        
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
        tokensN = clip.tokenize(image_prompt + neg_prompt, images=images_vl, llama_template=llama_template)
        conditioningN = clip.encode_from_tokens_scheduled(tokensN)
        
        if len(ref_latents) > 0:
            conditioning = node_helpers.conditioning_set_values(conditioning, {"reference_latents": ref_latents}, append=True)
            conditioningN = node_helpers.conditioning_set_values(conditioningN, {"reference_latents": ref_latents}, append=True)
        
        return (conditioning, conditioningN, {"samples": output_latent}, )

# ========================================================
# 节点 2: 10图试验版 (新增!)
# ========================================================
class MatrixTextEncodeQwen10:
    """
    Qwen Text Encode (10 Images) - Experimental
    试验性节点：支持多达 10 张图片输入。
    注意：输入过多图片可能会稀释模型注意力，导致效果下降。
    """
    
    DESCRIPTION = """
    【Qwen-VL 编码器 (10图试验版)】
    *** EXPERIMENTAL / 试验性功能 ***
    功能：扩展了输入上限，支持 1-10 张参考图。
    警告：Qwen 模型最佳效果通常在 5 张图以内。输入过多图片可能会导致指令跟随能力下降或画面混乱。请谨慎使用。
    """

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "clip": ("CLIP", ),
            "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "tooltip": "正向提示词"}),
            "neg_prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": "", "tooltip": "负向提示词"}), 
            "smart_input": ("BOOLEAN", {"default": False, "tooltip": "智能分辨率：图片>2张时会自动降低分辨率以节省显存。"}), 
            "align_latent": (["disabled", "image1_only", "all"], {"default": "image1_only", "tooltip": "Latent对齐策略"}), 
            },
            "optional": {
                "vae": ("VAE", ),
                "img_1": ("IMAGE", ),
                "img_2": ("IMAGE", ),
                "img_3": ("IMAGE", ),
                "img_4": ("IMAGE", ),
                "img_5": ("IMAGE", ),
                "img_6": ("IMAGE", ),
                "img_7": ("IMAGE", ),
                "img_8": ("IMAGE", ),
                "img_9": ("IMAGE", ),
                "img_10": ("IMAGE", ),
            }}
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT",)
    RETURN_NAMES = ("cond+", "cond-", "latent") 
    FUNCTION = "encode"
    
    CATEGORY = "Custom/Matrix"
    
    def encode(self, clip, prompt, neg_prompt, smart_input, align_latent, vae=None, img_1=None, img_2=None, img_3=None, img_4=None, img_5=None, img_6=None, img_7=None, img_8=None, img_9=None, img_10=None):
        ref_latents = []
        
        # 收集 10 张图
        images = [img for img in [img_1, img_2, img_3, img_4, img_5, img_6, img_7, img_8, img_9, img_10] if img is not None]
        
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
        tokensN = clip.tokenize(image_prompt + neg_prompt, images=images_vl, llama_template=llama_template)
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
    "MatrixTextEncodeQwen5": "Qwen Encode (5 Imgs)",
    "MatrixTextEncodeQwen10": "Qwen Encode (10 Imgs) (Experimental)"
}