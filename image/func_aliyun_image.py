#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import time
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from pathlib import PurePosixPath

import requests
from dashscope import ImageSynthesis
import dashscope

class AliyunImage():
    """阿里文生图API调用
    """

    @staticmethod
    def value_check(args: dict) -> bool:
        try:
            return bool(args and args.get("api_key", "") and args.get("model", ""))
        except Exception:
            return False

    def __init__(self, config={}) -> None:
        self.LOG = logging.getLogger("AliyunImage")
        if not config:
            raise Exception("缺少配置信息")
            
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "wanx2.1-t2i-turbo")
        self.size = config.get("size", "1024*1024")
        self.enable = config.get("enable", True)
        self.n = config.get("n", 1)
        self.temp_dir = config.get("temp_dir", "./temp")
        
        # 确保临时目录存在
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            
        # 设置API密钥
        dashscope.api_key = self.api_key
        
        self.LOG.info("AliyunImage 已初始化")

    def generate_image(self, prompt: str) -> str:
        """生成图像并返回图像URL
        
        Args:
            prompt (str): 图像描述
            
        Returns:
            str: 生成的图像URL或错误信息
        """
        if not self.enable or not self.api_key:
            return "阿里文生图功能未启用或API密钥未配置"
        
        try:
            rsp = ImageSynthesis.call(
                api_key=self.api_key,
                model=self.model,
                prompt=prompt,
                n=self.n,
                size=self.size
            )
            
            if rsp.status_code == HTTPStatus.OK and rsp.output and rsp.output.results:
                return rsp.output.results[0].url
            else:
                self.LOG.error(f"图像生成失败: {rsp.code}, {rsp.message}")
                return f"图像生成失败: {rsp.message}"
        except Exception as e:
            error_str = str(e)
            self.LOG.error(f"图像生成出错: {error_str}")
            
            if "Error code: 500" in error_str or "HTTP/1.1 500" in error_str:
                self.LOG.warning(f"检测到违规内容请求: {prompt}")
                return "很抱歉，您的请求可能包含违规内容，无法生成图像"

            return "图像生成失败，请调整您的描述后重试"

    def download_image(self, image_url: str) -> str:
        """
        下载图片并返回本地文件路径
        
        Args:
            image_url (str): 图片URL
            
        Returns:
            str: 本地图片文件路径，下载失败则返回None
        """
        try:
            response = requests.get(image_url, stream=True, timeout=30)
            if response.status_code == 200:
                file_path = os.path.join(self.temp_dir, f"aliyun_image_{int(time.time())}.jpg")
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                self.LOG.info(f"图片已下载到: {file_path}")
                return file_path
            else:
                self.LOG.error(f"下载图片失败，状态码: {response.status_code}")
                return None
        except Exception as e:
            self.LOG.error(f"下载图片过程出错: {str(e)}")
            return None
