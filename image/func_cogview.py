import logging
import os
import requests
import tempfile
import time
from zhipuai import ZhipuAI

class CogView():
    def __init__(self, conf: dict) -> None:
        self.api_key = conf.get("api_key")
        self.model = conf.get("model", "cogview-4-250304") # 默认使用最新模型
        self.quality = conf.get("quality", "standard")
        self.size = conf.get("size", "1024x1024")
        self.enable = conf.get("enable", True)
        
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_img_dir = os.path.join(project_dir, "zhipuimg")
        self.temp_dir = conf.get("temp_dir", default_img_dir)
        
        self.LOG = logging.getLogger("CogView")
        
        if self.api_key:
            self.client = ZhipuAI(api_key=self.api_key)
            self.LOG.info(f"CogView 初始化成功，模型：{self.model}，质量：{self.quality}，图片保存目录：{self.temp_dir}")
        else:
            self.LOG.warning("未配置智谱API密钥，图像生成功能无法使用")
            self.client = None
        
        os.makedirs(self.temp_dir, exist_ok=True)
    
    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf and conf.get("api_key") and conf.get("enable", True):
            return True
        return False
    
    def __repr__(self):
        return 'CogView'
    
    def generate_image(self, prompt: str) -> str:
        """
        生成图像并返回图像URL
        
        Args:
            prompt (str): 图像描述
            
        Returns:
            str: 生成的图像URL或错误信息
        """
        if not self.client or not self.enable:
            return "图像生成功能未启用或API密钥未配置"
        
        try:
            response = self.client.images.generations(
                model=self.model,
                prompt=prompt,
                quality=self.quality,
                size=self.size,
            )
            
            if response and response.data and len(response.data) > 0:
                return response.data[0].url
            else:
                return "图像生成失败，未收到有效响应"
        except Exception as e:
            error_str = str(e)
            self.LOG.error(f"图像生成出错: {error_str}")
            
            if "Error code: 500" in error_str or "HTTP/1.1 500" in error_str or "code\":\"1234\"" in error_str:
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
                file_path = os.path.join(self.temp_dir, f"cogview_{int(time.time())}.jpg")
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
