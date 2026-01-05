import math
import comfy.utils
import node_helpers

class MatrixTextEncodeQwen5:
    """
    Qwen Text Encode (5 Images) - 复刻版
    严格参照 TextEncodeQwenImageEditPlusAdv 逻辑。
    支持 1-5 张图片输入，保留 smart_input 的原始分辨率计算逻辑。
    """
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {
            "clip": ("CLIP", ),
            "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True}),
            "negative_prompt": ("STRING", ),
            "smart_input": ("BOOLEAN", {"default": False, "tooltip": "Choose an appropriate encoding size based on the number of input images."}),
            "align_latent": (["disabled", "image1_only", "all"], {"default": "image1_only", "tooltip": "Do not pre-scale the reference latents."}),
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
    RETURN_NAMES = ("conditioning+", "conditioning-", "latent")
    FUNCTION = "encode"
    
    CATEGORY = "Custom/Matrix"
    
    def encode(self, clip, prompt, negative_prompt, smart_input, align_latent, vae=None, image1=None, image2=None, image3=None, image4=None, image5=None):
        ref_latents = []
        # 严格限制为 5 张图
        images = [img for img in [image1, image2, image3, image4, image5] if img is not None]
        
        images_vl = []
        llama_template = "<|im_start|>system\nDescribe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input where appropriate.<|im_end|>\n<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n"
        image_prompt = ""
        output_latent = None
        
        # === 严格复刻原版的 smart_input 逻辑 ===
        size = 384
        if smart_input:
            size = 1024
            if len(images) > 2:
                size = 384
            elif len(images) > 1:
                size = 512
        # ====================================
        
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
    "MatrixTextEncodeQwen5": MatrixTextEncodeQwen5
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixTextEncodeQwen5": "Qwen Text Encode (5 Images)"
}