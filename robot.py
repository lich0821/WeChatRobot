# -*- coding: utf-8 -*-

import logging
import re
import time
import xml.etree.ElementTree as ET
from queue import Empty
from threading import Thread
import os
from base.func_zhipu import ZhiPu
from base.func_cogview import CogView

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

        if hasattr(self.config, 'COGVIEW') and CogView.value_check(self.config.COGVIEW):
            self.cogview = CogView(self.config.COGVIEW)
            self.LOG.info("图像生成服务已初始化")
        else:
            self.cogview = None
            if hasattr(self.config, 'COGVIEW'):
                self.LOG.info("图像生成服务未启用或配置不正确")
            else:
                self.LOG.info("配置中未找到COGVIEW配置部分")

    @staticmethod
    def value_check(args: dict) -> bool:
        if args:
            return all(value is not None for key, value in args.items() if key != 'proxy')
        return False

    def toAt(self, msg: WxMsg) -> bool:
        """处理被 @ 消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        trigger = self.config.COGVIEW.get('trigger_keyword', '画一张') if hasattr(self.config, 'COGVIEW') else '画一张'
        content = re.sub(r"@.*?[\u2005|\s]", "", msg.content).replace(" ", "")
        if content.startswith(trigger):
            if self.cogview and hasattr(self.config, 'COGVIEW') and self.config.COGVIEW.get('enable', False):
                prompt = content[len(trigger):].strip()
                if prompt:
                    self.LOG.info(f"群聊中收到图像生成请求: {prompt}")
                    self.sendTextMsg("正在生成图像，请稍等...", msg.roomid, msg.sender)
                    image_url = self.cogview.generate_image(prompt)
                    
                    if image_url and image_url.startswith("http"):
                        try:
                            self.LOG.info(f"开始下载图片: {image_url}")
                            image_path = self.cogview.download_image(image_url)
                            
                            if image_path:
                                self.LOG.info(f"发送图片到群: {image_path}")
                                self.wcf.send_image(image_path, msg.roomid)
                                os.remove(image_path)  # 发送后删除临时文件
                            else:
                                self.LOG.warning(f"图片下载失败，发送URL链接作为备用: {image_url}")
                                self.sendTextMsg(f"图像已生成，但无法自动显示，点链接也能查看:\n{image_url}", msg.roomid, msg.sender)
                        except Exception as e:
                            self.LOG.error(f"发送图片过程出错: {str(e)}")
                            self.sendTextMsg(f"图像已生成，但发送过程出错，点链接也能查看:\n{image_url}", msg.roomid, msg.sender)
                    else:
                        self.LOG.error(f"图像生成失败: {image_url}")
                        self.sendTextMsg(f"图像生成失败: {image_url}", msg.roomid, msg.sender)
                    return True
            else:
                self.LOG.info("群聊中收到图像生成请求但功能未启用")
                
                fallback_to_chat = self.config.COGVIEW.get('fallback_to_chat', False) if hasattr(self.config, 'COGVIEW') else False
                
                if fallback_to_chat and self.chat:
                    self.LOG.info("将画图请求转发给聊天模型处理")
                    return self.toChitchat(msg)
                else:
                    self.sendTextMsg("报一丝，图像生成功能没有开启，请联系管理员开启此功能。（可以贿赂他开启）", msg.roomid, msg.sender)
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
                trigger = self.config.COGVIEW.get('trigger_keyword', '画一张') if hasattr(self.config, 'COGVIEW') else '画一张'
                if msg.content.startswith(trigger):
                    if self.cogview and hasattr(self.config, 'COGVIEW') and self.config.COGVIEW.get('enable', False):
                        prompt = msg.content[len(trigger):].strip()
                        if prompt:
                            self.LOG.info(f"收到图像生成请求: {prompt}")
                            self.sendTextMsg("正在生成图像，请稍等...", msg.sender)
                            image_url = self.cogview.generate_image(prompt)

                            if image_url and image_url.startswith("http"):
                                try:
                                    self.LOG.info(f"开始下载图片: {image_url}")
                                    image_path = self.cogview.download_image(image_url)

                                    if image_path:
                                        self.LOG.info(f"发送图片: {image_path}")
                                        self.wcf.send_image(image_path, msg.sender)
                                        os.remove(image_path)  # 发送后删除临时文件
                                    else:
                                        self.LOG.warning(f"图片下载失败，发送URL链接作为备用: {image_url}")
                                        self.sendTextMsg(f"图像已生成，但无法自动显示，点链接也能查看:\n{image_url}", msg.sender)
                                except Exception as e:
                                    self.LOG.error(f"发送图片过程出错: {str(e)}")
                                    self.sendTextMsg(f"图像已生成，但发送过程出错，点链接也能查看:\n{image_url}", msg.sender)
                            else:
                                self.LOG.error(f"图像生成失败: {image_url}")
                                self.sendTextMsg(f"图像生成失败: {image_url}", msg.sender)
                            return
                    else:
                        self.LOG.info("私聊中收到图像生成请求但功能未启用")
                        
                        fallback_to_chat = self.config.COGVIEW.get('fallback_to_chat', False) if hasattr(self.config, 'COGVIEW') else False
                        
                        if fallback_to_chat and self.chat:
                            self.LOG.info("将画图请求转发给聊天模型处理")
                            return self.toChitchat(msg)
                        else:
                            self.sendTextMsg("报一丝，图像生成功能没有开启，请联系管理员开启此功能。（可以贿赂他开启）", msg.sender)
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
