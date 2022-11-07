# -*- coding: utf-8 -*-

import re
import time
import logging
import xml.etree.ElementTree as ET

from wcferry import Wcf

from configuration import Config
from func_chengyu import cy
from job_mgmt import Job



class Robot(Job):
    """个性化自己的机器人
    """

    def __init__(self, wcf: Wcf) -> None:
        self.wcf = wcf
        self.config = Config()
        self.LOG = logging.getLogger("Robot")
        self.wxid = self.wcf.get_self_wxid()
        #self.allContacts = self.getAllContacts() 
        
        
    def toAt(self, msg: Wcf.WxMsg) -> bool:
        """
        处理被 @ 消息，现在只固定回复: "你@我干嘛？"
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        status = True
        rsp = "你@我干嘛？"
        self.sendTextMsg(rsp, msg.roomid, msg.sender)

        return status

    def toChengyu(self, msg: Wcf.WxMsg) -> bool:
        """
        处理成语查询/接龙消息
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        status = False
        texts = re.findall(r"^([#|?|？])(.*)$", msg.content)
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

    def toChitchat(self, msg: Wcf.WxMsg):
        """闲聊，目前未实现
        """
        pass

    def processMsg(self, msg: Wcf.WxMsg) -> None:
        """当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        """
        
        """ 此处可进行自定义发送的内容,如通过关键字自动获取当前天气信息，并发送到对应的群组@发送者
        群号：msg.roomid  微信ID：msg.sender  消息内容：msg.content
        content = "天气查询"
        receivers = msg.roomid
        self.sendTextMsg(content, receivers, msg.sender)
        """

        
        # 群聊消息
        if msg.from_group():
            # 如果在群里被 @，回复发信人：“收到你的消息了！” 并 @他
            if msg.roomid not in self.config.GROUPS:  # 不在配置的响应的群列表里，忽略
                return

            if msg.is_at(self.wxid):   # 被@
                self.toAt(msg)

            else:                # 其他消息
                self.toChengyu(msg)

        # 非群聊信息
        elif msg.type == 37:     # 好友请求
            self.autoAcceptFriendRequest(msg)

        elif msg.type == 10000:  # 系统信息
            self.sayHiToNewFriend(msg)

        elif msg.type == 0x01:   # 文本消息
            # 让配置加载更灵活，自己可以更新配置。也可以利用定时任务更新。
            if msg.from_self() and msg.content == "^更新$":
                self.config.reload()
                self.LOG.info("已更新")
                return

            # 闲聊
            self.toChitchat(msg)

    def onMsg(self, msg: Wcf.WxMsg) -> int:
        self.LOG.info(msg)  # 打印信息
        
        try:
            self.processMsg(msg)
        except Exception as e:
            self.LOG.error(e)

        return 0

    def enableRecvMsg(self) -> None:
        self.wcf.enable_recv_msg(self.onMsg)

    def sendTextMsg(self, msg: str, receiver: str, at_list: str = ""):
        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            wxids = at_list.split(",")
            for wxid in wxids:
                # 这里偷个懒，直接 @昵称
                        
                """ 若出现直接 @wxid，则要通过 MicroMsg.db 里的 ChatRoom 表解析群昵称，取消此处注释，并注释141行
                userInfo = self.getAllContacts()
                everyUser = {'notify@all': '所有人'}
                userInfo.update(everyUser) # 追加dict @所有人所需字段
                ats = f" @{userInfo[wxid]}"
                """
                ats = f" @{self.allContacts.get(wxid, '')}"

        self.LOG.info(f"To {receiver}: {msg}{ats}")
        self.wcf.send_text(f"{msg}{ats}", receiver, at_list)

    def getAllContacts(self):
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

    def autoAcceptFriendRequest(self, msg: Wcf.WxMsg):
        try:
            xml = ET.fromstring(msg.content)
            v3 = xml.attrib["encryptusername"]
            v4 = xml.attrib["ticket"]
            self.wcf.accept_new_friend(v3, v4)

        except Exception as e:
            self.LOG.error(f"同意好友出错：{e}")

    def sayHiToNewFriend(self, msg: Wcf.WxMsg):
        nickName = re.findall(r"你已添加了(.*)，现在可以开始聊天了。", msg.content)
        if nickName:
            # 添加了好友，更新好友列表
            self.allContacts[msg.sender] = nickName[0]
            self.sendTextMsg(f"Hi {nickName[0]}，我自动通过了你的好友请求。", msg.sender)
