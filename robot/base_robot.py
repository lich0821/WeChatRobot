# -*- coding: utf-8 -*-

import re
import time
import logging
import xml.etree.ElementTree as ET

from robot.job_mgmt import Job


class BaseRobot(Job):
    """
    机器人基类。用户需要实现 `processMsg` 方法以个性化处理消息。
    """

    def __init__(self, sdk) -> None:
        self.sdk = sdk
        self.LOG = logging.getLogger("Robot")

    def onMsg(self, msg) -> int:
        try:
            self.processMsg(msg)
        except Exception as e:
            self.LOG.error(e)
            self.printRawMsg(msg)

        return 0

    def initSDK(self):
        if self.sdk.WxInitSDK() != 0:
            self.LOG.error("初始化失败")
            exit(-1)
        self.LOG.info("初始化成功")
        self.wxid = self.sdk.WxGetSelfWxid()
        self.allContacts = self.getAllContacts()

    def enableRecvMsg(self):
        self.sdk.WxEnableRecvMsg(self.onMsg)

    def sendTextMsg(self, receiver, msg, at_list=""):
        # msg 中需要有 @ 名单中一样数量的 @
        ats = ""
        if at_list:
            wxids = at_list.split(",")
            for wxid in wxids:
                # 这里偷个懒，直接 @昵称。有必要的话可以通过 MicroMsg.db 里的 ChatRoom 表，解析群昵称
                ats = f" @{self.allContacts.get(wxid, '')}"

        self.sdk.WxSendTextMsg(receiver, f"{msg}{ats}", at_list)

    def isGroupChat(self, msg):
        return msg.source == 1

    def isAt(self, msg, exclude_at_all=True):
        atall = []
        atuserlist = re.findall(f"<atuserlist>.*({self.wxid}).*</atuserlist>", msg.xml)
        if exclude_at_all:
            atall = re.findall(f"@所有人", msg.content)  # 排除@所有人

        return (len(atuserlist) > 0) and (len(atall) == 0)

    def printRawMsg(self, msg) -> None:
        rmsg = {}
        rmsg["id"] = msg.id
        rmsg["self"] = msg.self
        rmsg["wxId"] = msg.wxId
        rmsg["roomId"] = msg.roomId
        rmsg["type"] = msg.type
        rmsg["source"] = msg.source
        rmsg["xml"] = msg.xml
        rmsg["content"] = msg.content

        self.LOG.info(rmsg)

    def getAllContacts(self):
        """
        获取联系人（包括好友、公众号、服务号、群成员……）
        格式: {"wxid": "NickName"}
        """
        contacts = self.sdk.WxExecDbQuery("MicroMsg.db", "SELECT UserName, NickName FROM Contact;")
        return {contact["UserName"]: contact["NickName"] for contact in contacts}

    def autoAcceptFriendRequest(self, msg):
        try:
            xml = ET.fromstring(msg.content)
            v3 = xml.attrib["encryptusername"]
            v4 = xml.attrib["ticket"]
            self.sdk.WxAcceptNewFriend(v3, v4)

        except Exception as e:
            self.LOG.error(f"同意好友出错：{e}")

    def processMsg(self, msg) -> None:
        raise NotImplementedError("Method [processMsg] should be implemented.")

    def keepRunningAndBlockProcess(self) -> None:
        """
        保持机器人运行，不让进程退出
        """
        while True:
            self.runPendingJobs()
            time.sleep(1)
