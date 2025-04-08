#! /usr/bin/env python3
# -*- coding: utf-8 -*-

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

    def __init__(self, config={}) -> None:
        self.LOG = logging.getLogger("GeminiImage")
        
        self.enable = config.get("enable", True)
        self.api_key = config.get("api_key", "") or os.environ.get("GEMINI_API_KEY", "")
        self.model = config.get("model", "gemini-2.0-flash-exp-image-generation")
        self.proxy = config.get("proxy", "")
        
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.temp_dir = config.get("temp_dir", os.path.join(project_dir, "geminiimg"))
        
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        
        if not self.api_key:
            self.enable = False
            return
            
        try:
            # 设置代理
            if self.proxy:
                os.environ["HTTP_PROXY"] = self.proxy
                os.environ["HTTPS_PROXY"] = self.proxy
            
            # 初始化客户端
            self.client = genai.Client(api_key=self.api_key)
        except Exception:
            self.enable = False
    
    def generate_image(self, prompt: str) -> str:
        """生成图像并返回图像文件路径
        """
        try:
            # 设置代理
            if self.proxy:
                os.environ["HTTP_PROXY"] = self.proxy
                os.environ["HTTPS_PROXY"] = self.proxy
            
            image_prompt = f"生成一张高质量的图片: {prompt}。请直接提供图像，不需要描述。"
            
            # 发送请求
            response = self.client.models.generate_content(
                model=self.model,
                contents=image_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['Text', 'Image']
                )
            )
            
            # 处理响应
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, 'inline_data') and part.inline_data:
                                # 保存图像
                                file_name = f"gemini_image_{int(time.time())}_{random.randint(1000, 9999)}"
                                file_extension = mimetypes.guess_extension(part.inline_data.mime_type) or ".png"
                                file_path = os.path.join(self.temp_dir, f"{file_name}{file_extension}")
                                
                                with open(file_path, "wb") as f:
                                    f.write(part.inline_data.data)
                                
                                return file_path
            
            # 如果没有找到图像，尝试获取文本响应
            try:
                text_content = response.text
                if text_content:
                    return f"模型未能生成图像: {text_content[:100]}..."
            except (AttributeError, TypeError):
                pass
                
            return "图像生成失败，可能需要更新模型或调整提示词"
        
        except Exception as e:
            error_str = str(e)
            self.LOG.error(f"图像生成出错: {error_str}")
            
            # 处理500错误
            if "500 INTERNAL" in error_str:
                self.LOG.error("遇到谷歌服务器内部错误")
                return "谷歌AI服务器临时故障，请稍后再试。这是谷歌服务器的问题，不是你的请求有误。"
            
            if "timeout" in error_str.lower():
                return "图像生成超时，请检查网络或代理设置"
                
            if "violated" in error_str.lower() or "policy" in error_str.lower():
                return "请求包含违规内容，无法生成图像"
            
            # 其他常见错误类型处理
            if "quota" in error_str.lower() or "rate" in error_str.lower():
                return "API使用配额已用尽或请求频率过高，请稍后再试"
                
            if "authentication" in error_str.lower() or "auth" in error_str.lower():
                return "API密钥验证失败，请联系管理员检查配置"
                
            return f"图像生成失败，错误原因: {error_str.split('.')[-1] if '.' in error_str else error_str}"