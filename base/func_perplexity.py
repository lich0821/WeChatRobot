#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
from typing import Optional
import os
from openai import OpenAI


class Perplexity:
    def __init__(self, config):
        self.config = config
        self.api_key = config.get('key')
        self.api_base = config.get('api', 'https://api.perplexity.ai')
        self.proxy = config.get('proxy')
        self.prompt = config.get('prompt', '你是智能助手Perplexity')
        self.LOG = logging.getLogger('Perplexity')
        
        # 设置编码环境变量，确保处理Unicode字符
        os.environ["PYTHONIOENCODING"] = "utf-8"
        
        # 创建OpenAI客户端
        self.client = None
        if self.api_key:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base
                )
                # 如果有代理设置
                if self.proxy:
                    # OpenAI客户端不直接支持代理设置，需要通过环境变量
                    os.environ["HTTPS_PROXY"] = self.proxy
                    os.environ["HTTP_PROXY"] = self.proxy
                
                self.LOG.info("Perplexity 客户端已初始化")
            except Exception as e:
                self.LOG.error(f"初始化Perplexity客户端失败: {str(e)}")
        else:
            self.LOG.warning("未配置Perplexity API密钥")
            
    @staticmethod
    def value_check(args: dict) -> bool:
        if args:
            return all(value is not None for key, value in args.items() if key != 'proxy')
        return False
        
    def get_answer(self, prompt, session_id=None):
        """获取Perplexity回答
        
        Args:
            prompt: 用户输入的问题
            session_id: 会话ID，用于区分不同会话
            
        Returns:
            str: Perplexity的回答
        """
        try:
            if not self.api_key or not self.client:
                return "Perplexity API key 未配置或客户端初始化失败"
            
            # 构建消息列表
            messages = [
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": prompt}
            ]
            
            # 获取模型
            model = self.config.get('model', 'mixtral-8x7b-instruct')
            
            # 使用json序列化确保正确处理Unicode
            self.LOG.info(f"发送到Perplexity的消息: {json.dumps(messages, ensure_ascii=False)}")
            
            # 创建聊天完成
            response = self.client.chat.completions.create(
                model=model,
                messages=messages
            )
            
            # 返回回答内容
            return response.choices[0].message.content
                
        except Exception as e:
            self.LOG.error(f"调用Perplexity API时发生错误: {str(e)}")
            return f"发生错误: {str(e)}"
            
    def __str__(self):
        return "Perplexity" 