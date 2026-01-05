import math
import comfy.utils
import node_helpers

class MatrixTextEncodeQwen6:
    """
    魔改版 Qwen VL Text Encode 节点
    1. 剥离了 API 依赖，纯本地运行。
    2. 支持 1-6 张图片输入。
    3. 专为 Matrix 工作流优化。
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
                "image6": ("IMAGE", ), # 新增 Image 6
            }}
    
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "LATENT",)
    RETURN_NAMES = ("conditioning+", "conditioning-", "latent")
    FUNCTION = "encode"
    
    CATEGORY = "Custom/Matrix" # 归类到你的 Matrix 目录下
    
    def encode(self, clip, prompt, negative_prompt, smart_input, align_latent, vae=None, image1=None, image2=None, image3=None, image4=None, image5=None, image6=None):
        ref_latents = []
        # 收集所有非空的图片输入 (1-6)
        images = [img for img in [image1, image2, image3, image4, image5, image6] if img is not None]
        
        images_vl = []
        # Qwen-VL 特有的 Prompt 模板
        llama_template = "<|im_start|>system\nDescribe the key features of the input image (color, shape, size, texture, objects, background), then explain how the user's text instruction should alter or modify the image. Generate a new image that meets the user's requirements while maintaining consistency with the original input where appropriate.<|im_end|>\n<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n"
        image_prompt = ""
        output_latent = None
        
        # 智能分辨率逻辑
        size = 384
        if smart_input:
            size = 1024
            if len(images) > 2:
                size = 384
            elif len(images) > 1:
                size = 512
        
        for i, image in enumerate(images):
            samples = image.movedim(-1, 1)
            
            # 计算缩放比例
            total = int(size * size)
            scale_by = math.sqrt(total / (samples.shape[3] * samples.shape[2]))
            width = round(samples.shape[3] * scale_by)
            height = round(samples.shape[2] * scale_by)
            
            # 上采样处理
            s = comfy.utils.common_upscale(samples, width, height, "area", "disabled")
            images_vl.append(s.movedim(1, -1))
            
            # 处理 VAE Latent 对齐
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
            
            # 构建 Vision Prompt 标记
            image_prompt += "Picture {}: <|vision_start|><|image_pad|><|vision_end|>".format(i + 1)
                
        # CLIP 编码
        tokens = clip.tokenize(image_prompt + prompt, images=images_vl, llama_template=llama_template)
        conditioning = clip.encode_from_tokens_scheduled(tokens)
        
        tokensN = clip.tokenize(image_prompt + negative_prompt, images=images_vl, llama_template=llama_template)
        conditioningN = clip.encode_from_tokens_scheduled(tokensN)
        
        # 注入 Reference Latents
        if len(ref_latents) > 0:
            conditioning = node_helpers.conditioning_set_values(conditioning, {"reference_latents": ref_latents}, append=True)
            conditioningN = node_helpers.conditioning_set_values(conditioningN, {"reference_latents": ref_latents}, append=True)
        
        return (conditioning, conditioningN, {"samples": output_latent}, )

NODE_CLASS_MAPPINGS = {
    "MatrixTextEncodeQwen6": MatrixTextEncodeQwen6
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MatrixTextEncodeQwen6": "Qwen Text Encode (6 Images)"
}