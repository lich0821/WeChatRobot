#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import logging
import os
import mimetypes
import time
import random
import google.generativeai as genai
from google.generativeai import types

class GeminiImage:
    """谷歌AI画图API调用
    """

    @staticmethod
    def value_check(args: dict) -> bool:
        try:
            # 修改检查逻辑，如果配置存在就返回True
            return bool(args)
        except Exception:
            return False

    def __init__(self, config={}) -> None:
        self.LOG = logging.getLogger("GeminiImage")
        
        # 默认值
        self.enable = True
        
        # API密钥可以从环境变量获取或配置文件
        self.api_key = config.get("api_key", "") or os.environ.get("GEMINI_API_KEY", "")
        self.model = config.get("model", "gemini-2.0-flash-exp-image-generation")
        
        # 确定临时目录
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_img_dir = os.path.join(project_dir, "geminiimg")
        self.temp_dir = config.get("temp_dir", default_img_dir)
        
        # 确保临时目录存在
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            self.LOG.info(f"创建Gemini图像临时目录: {self.temp_dir}")
        
        # 验证API密钥是否有效
        if not self.api_key:
            self.LOG.warning("未配置谷歌Gemini API密钥，请在config.yaml中设置GEMINI_IMAGE.api_key或设置环境变量GEMINI_API_KEY")
            # 虽然没有API密钥，但仍然保持服务启用，以便在handle_image_generation中显示友好错误消息
        else:
            self.LOG.info("谷歌Gemini图像生成功能已初始化并默认开启")
    
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
            
            # 使用流式模式生成图片
            response_text = ""
            image_path = None
            
            # 使用流式API获取响应
            for chunk in client.models.generate_content_stream(
                model=self.model,
                contents=contents,
                config=generate_content_config,
            ):
                # 处理文本部分
                if not chunk.candidates or not chunk.candidates[0].content or not chunk.candidates[0].content.parts:
                    continue
                    
                for part in chunk.candidates[0].content.parts:
                    # 处理文本
                    if hasattr(part, 'text') and part.text:
                        response_text += part.text
                    
                    # 处理图像数据
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # 保存图片到临时文件
                        file_name = f"gemini_image_{int(time.time())}_{random.randint(1000, 9999)}"
                        file_extension = mimetypes.guess_extension(part.inline_data.mime_type) or ".png"
                        file_path = os.path.join(self.temp_dir, f"{file_name}{file_extension}")
                        
                        with open(file_path, "wb") as f:
                            f.write(part.inline_data.data)
                        
                        self.LOG.info(f"图片已保存到: {file_path}")
                        image_path = file_path
            
            # 记录生成的文本响应
            if response_text:
                self.LOG.info(f"模型生成的文本响应: {response_text}")
            
            # 如果成功生成图像，返回路径
            if image_path:
                return image_path
            else:
                return "图像生成失败，未收到有效响应"
        
        except Exception as e:
            error_str = str(e)
            self.LOG.error(f"图像生成出错: {error_str}")
            
            if "violated" in error_str.lower() or "policy" in error_str.lower() or "inappropriate" in error_str.lower():
                self.LOG.warning(f"检测到违规内容请求: {prompt}")
                return "很抱歉，您的请求可能包含违规内容，无法生成图像"
                
            return f"图像生成失败，请调整您的描述后重试: {error_str}"
    
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
