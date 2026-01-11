import math
import comfy.utils
import node_helpers

class MatrixTextEncodeQwen5:
    """
    Qwen Text Encode (5 Images) - 修正版
    1. 恢复 smart_input 和 align_latent 全名以保证清晰度。
    2. 保持 img_1-5 和 cond+ 等缩写以节省空间。
    """
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "clip": ("CLIP", ),
            "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True}),
            "neg_prompt": ("STRING", {"multiline": True, "dynamicPrompts": True, "default": ""}), # 保持缩写
            "smart_input": ("BOOLEAN", {"default": False, "tooltip": "Choose an appropriate encoding size based on the number of input images."}), # 恢复全名
            "align_latent": (["disabled", "image1_only", "all"], {"default": "image1_only", "tooltip": "Do not pre-scale the reference latents."}), # 恢复全名
            },
            "optional": {
                "vae": ("VAE", ),
                # 保持图片输入缩写
                "img_1": ("IMAGE", ),
                "img_2": ("IMAGE", ),
                "img_3": ("IMAGE", ),
                "img_4": ("IMAGE", ),
                "img_5": ("IMAGE", ),
            }}
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT",)
    RETURN_NAMES = ("cond+", "cond-", "latent") # 保持输出缩写
    FUNCTION = "encode"
    
    CATEGORY = "Custom/Matrix"
    
    def encode(self, clip, prompt, neg_prompt, smart_input, align_latent, vae=None, img_1=None, img_2=None, img_3=None, img_4=None, img_5=None):
        ref_latents = []
        
        images = [img for img in [img_1, img_2, img_3, img_4, img_5] if img is not None]
        
        images_vl = []
        llama_template = "<|im_start|>system\nDescribe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input where appropriate.<|im_end|>\n<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n"
        image_prompt = ""
        output_latent = None
        
        # === 恢复使用 smart_input 参数名 ===
        size = 384
        if smart_input:
            size = 1024
            if len(images) > 2:
                size = 384
            elif len(images) > 1:
                size = 512
        # =================================
        
        for i, image in enumerate(images):
            samples = image.movedim(-1, 1)
            total = int(size * size)
            
            scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
            width = round(samples.shape[3] * scale_by)
            height = round(samples.shape[2] * scale_by)
            
            s = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
            images_vl.append(s.movedim(1, -1))
            
            if vae is not None:
                # === 恢复使用 align_latent 参数名 ===
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
    "MatrixTextEncodeQwen5": MatrixTextEncodeQwen5
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixTextEncodeQwen5": "Qwen Encode (5 Imgs)"
}