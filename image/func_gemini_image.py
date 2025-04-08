#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import logging
import os
import mimetypes
import time
import random
from google import genai
from google.genai import types

class GeminiImage:
    """谷歌AI画图API调用
    """

    @staticmethod
    def value_check(args: dict) -> bool:
        try:
            return bool(args and args.get("api_key", ""))
        except Exception:
            return False

    def __init__(self, config={}) -> None:
        self.LOG = logging.getLogger("GeminiImage")
        if not config:
            raise Exception("缺少配置信息")
            
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gemini-2.0-flash-exp-image-generation")
        self.enable = config.get("enable", True)
        
        # 确定临时目录
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_img_dir = os.path.join(project_dir, "geminiimg")
        self.temp_dir = config.get("temp_dir", default_img_dir)
        
        # 确保临时目录存在
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            
        self.LOG.info("GeminiImage 已初始化")
    
    def generate_image(self, prompt: str) -> str:
        """生成图像并返回图像文件路径或URL
        
        Args:
            prompt (str): 图像描述
            
        Returns:
            str: 生成的图像路径或错误信息
        """
        if not self.enable or not self.api_key:
            return "谷歌AI画图功能未启用或API密钥未配置"
        
        try:
            # 初始化Google AI客户端
            client = genai.Client(api_key=self.api_key)
            
            # 配置生成请求
            contents = [
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)],
                )
            ]
            
            generate_content_config = types.GenerateContentConfig(
                response_modalities=["image", "text"],
                response_mime_type="text/plain",
            )
            
            # 生成图片
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            )
            
            # 处理响应
            if response and response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # 保存图片到临时文件
                        file_name = f"gemini_image_{int(time.time())}_{random.randint(1000, 9999)}"
                        file_extension = mimetypes.guess_extension(part.inline_data.mime_type) or ".png"
                        file_path = os.path.join(self.temp_dir, f"{file_name}{file_extension}")
                        
                        with open(file_path, "wb") as f:
                            f.write(part.inline_data.data)
                        
                        self.LOG.info(f"图片已保存到: {file_path}")
                        return file_path
            
            return "图像生成失败，未收到有效响应"
        
        except Exception as e:
            error_str = str(e)
            self.LOG.error(f"图像生成出错: {error_str}")
            
            if "violated" in error_str.lower() or "policy" in error_str.lower() or "inappropriate" in error_str.lower():
                self.LOG.warning(f"检测到违规内容请求: {prompt}")
                return "很抱歉，您的请求可能包含违规内容，无法生成图像"
                
            return "图像生成失败，请调整您的描述后重试"
    
    def download_image(self, image_path: str) -> str:
        """
        因为Gemini API直接返回图像数据，所以这里直接返回图像路径
        
        Args:
            image_path (str): 图片路径
            
        Returns:
            str: 本地图片文件路径
        """
        return image_path

if __name__ == "__main__":
    # 测试代码
    import sys
    from configuration import Config
    
    config = Config().GEMINI_IMAGE if hasattr(Config(), 'GEMINI_IMAGE') else None
    if not config:
        print("未找到GEMINI_IMAGE配置")
        sys.exit(1)
        
    gemini = GeminiImage(config)
    prompt = "一只可爱的猫咪在阳光下玩耍"
    image_path = gemini.generate_image(prompt)
    print(f"生成图像路径: {image_path}")
