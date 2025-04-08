#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import logging
import os
import mimetypes
import time
import random
from io import BytesIO
from PIL import Image

# 替换为官方推荐的 SDK
from google import genai
from google.genai import types

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
        
        # 强制启用，忽略配置中的enable字段
        self.enable = True
        
        # API密钥可以从环境变量获取或配置文件
        self.api_key = config.get("api_key", "") or os.environ.get("GEMINI_API_KEY", "")
        self.model = config.get("model", "gemini-2.0-flash-exp-image-generation")
        # 读取代理设置
        self.proxy = config.get("proxy", "")
        
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
            self.enable = False
        else:
            try:
                # 配置API密钥和代理
                if self.proxy:
                    os.environ["HTTP_PROXY"] = self.proxy
                    os.environ["HTTPS_PROXY"] = self.proxy
                
                # 使用新SDK的配置方式
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                self.LOG.error(f"初始化Gemini API失败: {str(e)}")
                self.enable = False
    
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
            # 确保每次生成图像时都应用代理设置
            if self.proxy:
                os.environ["HTTP_PROXY"] = self.proxy
                os.environ["HTTPS_PROXY"] = self.proxy
            
            # 修改提示词格式，明确指示生成图像
            image_prompt = f"生成一张高质量的图片: {prompt}。请直接提供图像，不需要描述。"
            
            self.LOG.info(f"使用google-genai SDK发送请求: {image_prompt}")
            
            # 使用新SDK的API调用方式
            response = self.client.models.generate_content(
                model=self.model,
                contents=image_prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['Text', 'Image']
                )
            )
            
            # 添加详细日志，记录响应结构
            self.LOG.info(f"收到API响应: {type(response)}")
            
            # 新SDK响应结构的处理
            if hasattr(response, 'candidates') and response.candidates:
                self.LOG.info(f"找到候选结果: {len(response.candidates)}个")
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        content = candidate.content
                        self.LOG.info(f"处理候选内容: {type(content)}")
                        
                        if hasattr(content, 'parts'):
                            parts = content.parts
                            self.LOG.info(f"内容包含 {len(parts)} 个部分")
                            
                            # 遍历所有部分寻找图片
                            for part in parts:
                                # 检查是否为图像数据
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    self.LOG.info(f"找到图像数据: {part.inline_data.mime_type}")
                                    
                                    # 保存图片到临时文件
                                    file_name = f"gemini_image_{int(time.time())}_{random.randint(1000, 9999)}"
                                    file_extension = mimetypes.guess_extension(part.inline_data.mime_type) or ".png"
                                    file_path = os.path.join(self.temp_dir, f"{file_name}{file_extension}")
                                    
                                    with open(file_path, "wb") as f:
                                        f.write(part.inline_data.data)
                                    
                                    self.LOG.info(f"图片已保存到: {file_path}")
                                    return file_path
                                # 检查文本内容部分
                                elif hasattr(part, 'text') and part.text:
                                    self.LOG.info(f"包含文本部分: {part.text[:100]}...")
            
            # 检查是否返回了纯文本而不是图像
            text_content = None
            try:
                text_content = response.text
            except (AttributeError, TypeError):
                pass
            
            if not text_content and hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content'):
                        for part in candidate.content.parts:
                            if hasattr(part, 'text') and part.text:
                                text_content = part.text
                                break
            
            if text_content:
                self.LOG.warning(f"模型仅返回了文本而非图像: {text_content[:100]}...")
                return f"模型未能生成图像，仅返回了文本: {text_content[:100]}..."
                
            # 记录完整响应信息以便调试
            self.LOG.error(f"未知响应格式或未找到图像: {repr(response)[:500]}")
            self.LOG.info("检查是否需要更新模型或调整提示词")
            
            return "图像生成失败，使用的模型可能不支持图像生成。请尝试使用'gemini-1.5-flash-latest'或其他支持图像生成的模型。"
        
        except Exception as e:
            error_str = str(e)
            self.LOG.error(f"图像生成出错: {error_str}")
            
            # 添加额外错误上下文
            if "timeout" in error_str.lower() or "time" in error_str.lower():
                proxy_status = f"当前代理: {self.proxy or '未设置'}"
                self.LOG.info(f"超时错误，{proxy_status}")
                return f"图像生成超时，请检查网络或代理设置。{proxy_status}"
                
            if "violated" in error_str.lower() or "policy" in error_str.lower() or "inappropriate" in error_str.lower():
                self.LOG.warning(f"检测到违规内容请求: {prompt}")
                return "很抱歉，您的请求可能包含违规内容，无法生成图像"
            
            # 改进API相关错误信息
            if "config" in error_str.lower() or "modalities" in error_str.lower():
                return f"API调用错误: {error_str}。请尝试更新google-genai库: pip install -U google-genai"
                
            import traceback
            self.LOG.error(f"详细异常信息: {traceback.format_exc()}")
            return f"图像生成失败: {error_str}"
    
    def download_image(self, image_path: str) -> str:
        """
        因为Gemini API直接返回图像数据，所以这里直接返回图像路径
        
        Args:
            image_path (str): 图片路径
            
        Returns:
            str: 本地图片文件路径
        """
        return image_path