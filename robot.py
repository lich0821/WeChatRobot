# -*- coding: utf-8 -*-

import logging
import re
import time
import xml.etree.ElementTree as ET
from queue import Empty
from threading import Thread
import os
import random
import shutil
from base.func_zhipu import ZhiPu
from image import CogView, AliyunImage, GeminiImage

from wcferry import Wcf, WxMsg

from base.func_bard import BardAssistant
from base.func_chatglm import ChatGLM
from base.func_ollama import Ollama
from base.func_chatgpt import ChatGPT
from base.func_deepseek import DeepSeek
from base.func_chengyu import cy
from base.func_weather import Weather
from base.func_news import News
from base.func_tigerbot import TigerBot
from base.func_xinghuo_web import XinghuoWeb
from configuration import Config
from constants import ChatType
from job_mgmt import Job

__version__ = "39.2.4.0"


class Robot(Job):
    """个性化自己的机器人
    """

    def __init__(self, config: Config, wcf: Wcf, chat_type: int) -> None:
        self.wcf = wcf
        self.config = config
        self.LOG = logging.getLogger("Robot")
        self.wxid = self.wcf.get_self_wxid()
        self.allContacts = self.getAllContacts()
        self._msg_timestamps = []

        if ChatType.is_in_chat_types(chat_type):
            if chat_type == ChatType.TIGER_BOT.value and TigerBot.value_check(self.config.TIGERBOT):
                self.chat = TigerBot(self.config.TIGERBOT)
            elif chat_type == ChatType.CHATGPT.value and ChatGPT.value_check(self.config.CHATGPT):
                self.chat = ChatGPT(self.config.CHATGPT)
            elif chat_type == ChatType.XINGHUO_WEB.value and XinghuoWeb.value_check(self.config.XINGHUO_WEB):
                self.chat = XinghuoWeb(self.config.XINGHUO_WEB)
            elif chat_type == ChatType.CHATGLM.value and ChatGLM.value_check(self.config.CHATGLM):
                self.chat = ChatGLM(self.config.CHATGLM)
            elif chat_type == ChatType.BardAssistant.value and BardAssistant.value_check(self.config.BardAssistant):
                self.chat = BardAssistant(self.config.BardAssistant)
            elif chat_type == ChatType.ZhiPu.value and ZhiPu.value_check(self.config.ZhiPu):
                self.chat = ZhiPu(self.config.ZhiPu)
            elif chat_type == ChatType.OLLAMA.value and Ollama.value_check(self.config.OLLAMA):
                self.chat = Ollama(self.config.OLLAMA)
            elif chat_type == ChatType.DEEPSEEK.value and DeepSeek.value_check(self.config.DEEPSEEK):
                self.chat = DeepSeek(self.config.DEEPSEEK)
            else:
                self.LOG.warning("未配置模型")
                self.chat = None
        else:
            if TigerBot.value_check(self.config.TIGERBOT):
                self.chat = TigerBot(self.config.TIGERBOT)
            elif ChatGPT.value_check(self.config.CHATGPT):
                self.chat = ChatGPT(self.config.CHATGPT)
            elif Ollama.value_check(self.config.OLLAMA):
                self.chat = Ollama(self.config.OLLAMA)
            elif XinghuoWeb.value_check(self.config.XINGHUO_WEB):
                self.chat = XinghuoWeb(self.config.XINGHUO_WEB)
            elif ChatGLM.value_check(self.config.CHATGLM):
                self.chat = ChatGLM(self.config.CHATGLM)
            elif BardAssistant.value_check(self.config.BardAssistant):
                self.chat = BardAssistant(self.config.BardAssistant)
            elif ZhiPu.value_check(self.config.ZhiPu):
                self.chat = ZhiPu(self.config.ZhiPu)
            elif DeepSeek.value_check(self.config.DEEPSEEK):
                self.chat = DeepSeek(self.config.DEEPSEEK)
            else:
                self.LOG.warning("未配置模型")
                self.chat = None

        self.LOG.info(f"已选择: {self.chat}")

        # 初始化图像生成服务
        self.cogview = None
        self.aliyun_image = None
        self.gemini_image = None
        
        # 优先初始化Gemini图像生成服务 - 确保默认启用
        try:
            # 不管配置如何，都强制初始化Gemini服务
            if hasattr(self.config, 'GEMINI_IMAGE'):
                self.gemini_image = GeminiImage(self.config.GEMINI_IMAGE)
            else:
                # 如果没有配置，使用空字典初始化，会使用默认值和环境变量
                self.gemini_image = GeminiImage({})
            
            if self.gemini_image.enable:
                self.LOG.info("谷歌Gemini图像生成功能已初始化并启用")
            else:
                self.LOG.info("谷歌AI画图功能未启用，未配置API密钥")
        except Exception as e:
            self.LOG.error(f"初始化谷歌Gemini图像生成服务失败: {str(e)}")
        
        # 初始化CogView和AliyunImage服务
        if hasattr(self.config, 'COGVIEW') and self.config.COGVIEW.get('enable', False):
            try:
                self.cogview = CogView(self.config.COGVIEW)
                self.LOG.info("智谱CogView文生图功能已初始化")
            except Exception as e:
                self.LOG.error(f"初始化智谱CogView文生图服务失败: {str(e)}")
        if hasattr(self.config, 'ALIYUN_IMAGE') and self.config.ALIYUN_IMAGE.get('enable', False):
            try:
                self.aliyun_image = AliyunImage(self.config.ALIYUN_IMAGE)
                self.LOG.info("阿里云文生图功能已初始化")
            except Exception as e:
                self.LOG.error(f"初始化阿里云文生图服务失败: {str(e)}")
                
    @staticmethod
    def value_check(args: dict) -> bool:
        if args:
            return all(value is not None for key, value in args.items() if key != 'proxy')
        return False

    def handle_image_generation(self, service_type, prompt, receiver, at_user=None):
        """处理图像生成请求的通用函数
        :param service_type: 服务类型，'cogview'/'aliyun'/'gemini'
        :param prompt: 图像生成提示词
        :param receiver: 接收者ID
        :param at_user: 被@的用户ID，用于群聊
        :return: 处理状态，True成功，False失败
        """
        if service_type == 'cogview':
            if not self.cogview or not hasattr(self.config, 'COGVIEW') or not self.config.COGVIEW.get('enable', False):
                self.LOG.info(f"收到智谱文生图请求但功能未启用: {prompt}")
                fallback_to_chat = self.config.COGVIEW.get('fallback_to_chat', False) if hasattr(self.config, 'COGVIEW') else False
                if not fallback_to_chat:
                    self.sendTextMsg("报一丝，智谱文生图功能没有开启，请联系管理员开启此功能。（可以贿赂他开启）", receiver, at_user)
                    return True
                return False
            service = self.cogview
            wait_message = "正在生成图像，请稍等..."
        elif service_type == 'aliyun':
            if not self.aliyun_image or not hasattr(self.config, 'ALIYUN_IMAGE') or not self.config.ALIYUN_IMAGE.get('enable', False):
                self.LOG.info(f"收到阿里文生图请求但功能未启用: {prompt}")
                fallback_to_chat = self.config.ALIYUN_IMAGE.get('fallback_to_chat', False) if hasattr(self.config, 'ALIYUN_IMAGE') else False
                if not fallback_to_chat:
                    self.sendTextMsg("报一丝，阿里文生图功能没有开启，请联系管理员开启此功能。（可以贿赂他开启）", receiver, at_user)
                    return True
                return False
            service = self.aliyun_image
            model_type = self.config.ALIYUN_IMAGE.get('model', '')
            if model_type == 'wanx2.1-t2i-plus':
                wait_message = "当前模型为阿里PLUS模型，生成速度较慢，请耐心等候..."
            elif model_type == 'wanx-v1':
                wait_message = "当前模型为阿里V1模型，生成速度非常慢，可能需要等待较长时间，请耐心等候..."
            else:
                wait_message = "正在生成图像，请稍等..."
        elif service_type == 'gemini':
            if not self.gemini_image:
                # 服务实例不存在的情况
                self.LOG.info(f"收到谷歌AI画图请求但服务未初始化: {prompt}")
                self.sendTextMsg("谷歌文生图服务初始化失败，请联系管理员检查日志", receiver, at_user)
                return True
                
            # 直接检查API密钥是否有效
            if not getattr(self.gemini_image, 'api_key', ''):
                self.LOG.info(f"收到谷歌AI画图请求但API密钥未配置: {prompt}")
                self.sendTextMsg("谷歌文生图功能需要配置API密钥，请联系管理员设置API密钥", receiver, at_user)
                return True
                
            service = self.gemini_image
            wait_message = "正在通过谷歌AI生成图像，请稍等..."
        else:
            self.LOG.error(f"未知的图像生成服务类型: {service_type}")
            return False
            
        self.LOG.info(f"收到图像生成请求 [{service_type}]: {prompt}")
        self.sendTextMsg(wait_message, receiver, at_user)
        
        image_url = service.generate_image(prompt)
        
        if image_url and (image_url.startswith("http") or os.path.exists(image_url)):
            try:
                self.LOG.info(f"开始处理图片: {image_url}")
                # 谷歌API直接返回本地文件路径，无需下载
                if service_type == 'gemini':
                    image_path = image_url
                else:
                    image_path = service.download_image(image_url)
                
                if image_path:
                    # 创建一个临时副本，避免文件占用问题
                    temp_dir = os.path.dirname(image_path)
                    file_ext = os.path.splitext(image_path)[1]
                    temp_copy = os.path.join(
                        temp_dir,
                        f"temp_{service_type}_{int(time.time())}_{random.randint(1000, 9999)}{file_ext}"
                    )
                    
                    try:
                        # 创建文件副本
                        shutil.copy2(image_path, temp_copy)
                        self.LOG.info(f"创建临时副本: {temp_copy}")
                        
                        # 发送临时副本
                        self.LOG.info(f"发送图片到 {receiver}: {temp_copy}")
                        self.wcf.send_image(temp_copy, receiver)
                        
                        # 等待一小段时间确保微信API完成处理
                        time.sleep(1.5)
                        
                    except Exception as e:
                        self.LOG.error(f"创建或发送临时副本失败: {str(e)}")
                        # 如果副本处理失败，尝试直接发送原图
                        self.LOG.info(f"尝试直接发送原图: {image_path}")
                        self.wcf.send_image(image_path, receiver)
                    
                    # 安全删除文件
                    self._safe_delete_file(image_path)
                    if os.path.exists(temp_copy):
                        self._safe_delete_file(temp_copy)
                                   
                else:
                    self.LOG.warning(f"图片下载失败，发送URL链接作为备用: {image_url}")
                    self.sendTextMsg(f"图像已生成，但无法自动显示，点链接也能查看:\n{image_url}", receiver, at_user)
            except Exception as e:
                self.LOG.error(f"发送图片过程出错: {str(e)}")
                self.sendTextMsg(f"图像已生成，但发送过程出错，点链接也能查看:\n{image_url}", receiver, at_user)
        else:
            self.LOG.error(f"图像生成失败: {image_url}")
            self.sendTextMsg(f"图像生成失败: {image_url}", receiver, at_user)
        
        return True

    def _safe_delete_file(self, file_path, max_retries=3, retry_delay=1.0):
        """安全删除文件，带有重试机制
        
        :param file_path: 要删除的文件路径
        :param max_retries: 最大重试次数
        :param retry_delay: 重试间隔(秒)
        :return: 是否成功删除
        """
        if not os.path.exists(file_path):
            return True
            
        for attempt in range(max_retries):
            try:
                os.remove(file_path)
                self.LOG.info(f"成功删除文件: {file_path}")
                return True
            except Exception as e:
                if attempt < max_retries - 1:
                    self.LOG.warning(f"删除文件 {file_path} 失败, 将在 {retry_delay} 秒后重试: {str(e)}")
                    time.sleep(retry_delay)
                else:
                    self.LOG.error(f"无法删除文件 {file_path} 经过 {max_retries} 次尝试: {str(e)}")
        
        return False

    def toAt(self, msg: WxMsg) -> bool:
        """处理被 @ 消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        # CogView触发词
        cogview_trigger = self.config.COGVIEW.get('trigger_keyword', '牛智谱') if hasattr(self.config, 'COGVIEW') else '牛智谱'
        # 阿里文生图触发词
        aliyun_trigger = self.config.ALIYUN_IMAGE.get('trigger_keyword', '牛阿里') if hasattr(self.config, 'ALIYUN_IMAGE') else '牛阿里'
        # 谷歌AI画图触发词
        gemini_trigger = self.config.GEMINI_IMAGE.get('trigger_keyword', '牛谷歌') if hasattr(self.config, 'GEMINI_IMAGE') else '牛谷歌'
        
        content = re.sub(r"@.*?[\u2005|\s]", "", msg.content).replace(" ", "")
        
        # 阿里文生图处理
        if content.startswith(aliyun_trigger):
            prompt = content[len(aliyun_trigger):].strip()
            if prompt:
                result = self.handle_image_generation('aliyun', prompt, msg.roomid, msg.sender)
                if result:
                    return True
                
        # CogView处理
        elif content.startswith(cogview_trigger):
            prompt = content[len(cogview_trigger):].strip()
            if prompt:
                result = self.handle_image_generation('cogview', prompt, msg.roomid, msg.sender)
                if result:
                    return True
        
        # 谷歌AI画图处理
        elif content.startswith(gemini_trigger):
            prompt = content[len(gemini_trigger):].strip()
            if prompt:
                return self.handle_image_generation('gemini', prompt, msg.roomid or msg.sender, msg.sender if msg.roomid else None)
            else:
                self.sendTextMsg(f"请在{gemini_trigger}后面添加您想要生成的图像描述", msg.roomid or msg.sender, msg.sender if msg.roomid else None)
                return True
        
        return self.toChitchat(msg)

    def toChengyu(self, msg: WxMsg) -> bool:
        """
        处理成语查询/接龙消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        status = False
        texts = re.findall(r"^([#?？])(.*)$", msg.content)
        # [('#', '天天向上')]
        if texts:
            flag = texts[0][0]
            text = texts[0][1]
            if flag == "#":  # 接龙
                if cy.isChengyu(text):
                    rsp = cy.getNext(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True
            elif flag in ["?", "？"]:  # 查词
                if cy.isChengyu(text):
                    rsp = cy.getMeaning(text)
                    if rsp:
                        self.sendTextMsg(rsp, msg.roomid)
                        status = True

        return status

    def toChitchat(self, msg: WxMsg) -> bool:
        """闲聊，接入 ChatGPT
        """
        if not self.chat:  # 没接 ChatGPT，固定回复
            rsp = "你@我干嘛？"
        else:  # 接了 ChatGPT，智能回复
            q = re.sub(r"@.*?[\u2005|\s]", "", msg.content).replace(" ", "")
            rsp = self.chat.get_answer(q, (msg.roomid if msg.from_group() else msg.sender))

        if rsp:
            if msg.from_group():
                self.sendTextMsg(rsp, msg.roomid, msg.sender)
            else:
                self.sendTextMsg(rsp, msg.sender)

            return True
        else:
            self.LOG.error(f"无法从 ChatGPT 获得答案")
            return False

    def processMsg(self, msg: WxMsg) -> None:
        """当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        此处可进行自定义发送的内容,如通过 msg.content 关键字自动获取当前天气信息，并发送到对应的群组@发送者
        群号：msg.roomid  微信ID：msg.sender  消息内容：msg.content
        content = "xx天气信息为："
        receivers = msg.roomid
        self.sendTextMsg(content, receivers, msg.sender)
        """

        # 群聊消息
        if msg.from_group():
            # 如果在群里被 @
            if msg.roomid not in self.config.GROUPS:  # 不在配置的响应的群列表里，忽略
                return

            if msg.is_at(self.wxid):  # 被@
                self.toAt(msg)

            else:  # 其他消息
                self.toChengyu(msg)

            return  # 处理完群聊信息，后面就不需要处理了

        # 非群聊信息，按消息类型进行处理
        if msg.type == 37:  # 好友请求
            self.autoAcceptFriendRequest(msg)

        elif msg.type == 10000:  # 系统信息
            self.sayHiToNewFriend(msg)

        elif msg.type == 0x01:
            if msg.from_self():
                if msg.content == "^更新$":
                    self.config.reload()
                    self.LOG.info("已更新")
            else:
                # 阿里文生图触发词处理
                aliyun_trigger = self.config.ALIYUN_IMAGE.get('trigger_keyword', '牛阿里') if hasattr(self.config, 'ALIYUN_IMAGE') else '牛阿里'
                if msg.content.startswith(aliyun_trigger):
                    prompt = msg.content[len(aliyun_trigger):].strip()
                    if prompt:
                        result = self.handle_image_generation('aliyun', prompt, msg.sender)
                        if result:
                            return
                
                # CogView触发词处理
                cogview_trigger = self.config.COGVIEW.get('trigger_keyword', '牛智谱') if hasattr(self.config, 'COGVIEW') else '牛智谱'
                if msg.content.startswith(cogview_trigger):
                    prompt = msg.content[len(cogview_trigger):].strip()
                    if prompt:
                        result = self.handle_image_generation('cogview', prompt, msg.sender)
                        if result:
                            return
                
                # 谷歌AI画图触发词处理
                gemini_trigger = self.config.GEMINI_IMAGE.get('trigger_keyword', '牛谷歌') if hasattr(self.config, 'GEMINI_IMAGE') else '牛谷歌'
                if msg.content.startswith(gemini_trigger):
                    prompt = msg.content[len(gemini_trigger):].strip()
                    if prompt:
                        result = self.handle_image_generation('gemini', prompt, msg.sender)
                        if result:
                            return

                self.toChitchat(msg)  # 闲聊

    def onMsg(self, msg: WxMsg) -> int:
        try:
            self.LOG.info(msg)
            self.processMsg(msg)
        except Exception as e:
            self.LOG.error(e)

        return 0

    def enableRecvMsg(self) -> None:
        self.wcf.enable_recv_msg(self.onMsg)

    def enableReceivingMsg(self) -> None:
        def innerProcessMsg(wcf: Wcf):
            while wcf.is_receiving_msg():
                try:
                    msg = wcf.get_msg()
                    self.LOG.info(msg)
                    self.processMsg(msg)
                except Empty:
                    continue  # Empty message
                except Exception as e:
                    self.LOG.error(f"Receiving message error: {e}")

        self.wcf.enable_receiving_msg()
        Thread(target=innerProcessMsg, name="GetMessage", args=(self.wcf,), daemon=True).start()

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = "") -> None:
        """ 发送消息
        :param msg: 消息字符串
        :param receiver: 接收人wxid或者群id
        :param at_list: 要@的wxid, @所有人的wxid为：notify@all
        """
        # 随机延迟0.3-1.3秒，并且一分钟内发送限制
        time.sleep(float(str(time.time()).split('.')[-1][-2:]) / 100.0 + 0.3)
        now = time.time()
        if self.config.SEND_RATE_LIMIT > 0:
            # 清除超过1分钟的记录
            self._msg_timestamps = [t for t in self._msg_timestamps if now - t < 60]
            if len(self._msg_timestamps) >= self.config.SEND_RATE_LIMIT:
                self.LOG.warning(f"发送消息过快，已达到每分钟{self.config.SEND_RATE_LIMIT}条上限。")
                return
            self._msg_timestamps.append(now)

        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            if at_list == "notify@all":  # @所有人
                ats = " @所有人"
            else:
                wxids = at_list.split(",")
                for wxid in wxids:
                    # 根据 wxid 查找群昵称
                    ats += f" @{self.wcf.get_alias_in_chatroom(wxid, receiver)}"

        # {msg}{ats} 表示要发送的消息内容后面紧跟@，例如 北京天气情况为：xxx @张三
        if ats == "":
            self.LOG.info(f"To {receiver}: {msg}")
            self.wcf.send_text(f"{msg}", receiver, at_list)
        else:
            self.LOG.info(f"To {receiver}: {ats}\r{msg}")
            self.wcf.send_text(f"{ats}\n\n{msg}", receiver, at_list)

    def getAllContacts(self) -> dict:
        """
        获取联系人（包括好友、公众号、服务号、群成员……）
        格式: {"wxid": "NickName"}
        """
        contacts = self.wcf.query_sql("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
        return {contact["UserName"]: contact["NickName"] for contact in contacts}

    def keepRunningAndBlockProcess(self) -> None:
        """
        保持机器人运行，不让进程退出
        """
        while True:
            self.runPendingJobs()
            time.sleep(1)

    def autoAcceptFriendRequest(self, msg: WxMsg) -> None:
        try:
            xml = ET.fromstring(msg.content)
            v3 = xml.attrib["encryptusername"]
            v4 = xml.attrib["ticket"]
            scene = int(xml.attrib["scene"])
            self.wcf.accept_new_friend(v3, v4, scene)

        except Exception as e:
            self.LOG.error(f"同意好友出错：{e}")

    def sayHiToNewFriend(self, msg: WxMsg) -> None:
        nickName = re.findall(r"你已添加了(.*)，现在可以开始聊天了。", msg.content)
        if nickName:
            # 添加了好友，更新好友列表
            self.allContacts[msg.sender] = nickName[0]
            self.sendTextMsg(f"Hi {nickName[0]}，我自动通过了你的好友请求。", msg.sender)

    def newsReport(self) -> None:
        receivers = self.config.NEWS
        if not receivers:
            return

        news = News().get_important_news()
        for r in receivers:
            self.sendTextMsg(news, r)

    def weatherReport(self) -> None:
        receivers = self.config.WEATHER
        if not receivers or not self.config.CITY_CODE:
            self.LOG.warning("未配置天气城市代码或接收人")
            return

        report = Weather(self.config.CITY_CODE).get_weather()
        for r in receivers:
            self.sendTextMsg(report, r)
