#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import re

from func_chengyu import cy
import robot.sdk.wcferry as WxSDK
from robot.base_robot import BaseRobot
from robot.configuration import Config


class Robot(BaseRobot):
    """个性化自己的机器人
    """

    def __init__(self, sdk: WxSDK, config: Config) -> None:
        super().__init__(sdk)
        self.config = config

    def toAt(self, msg) -> bool:
        """
        处理被 @ 消息，现在只固定回复: "你@我干嘛？"
        :param msg: 微信消息结构
        :return: 处理状态，`True` 成功，`False` 失败
        """
        status = True
        rsp = "你@我干嘛？"
        self.sendTextMsg(msg.roomId, rsp, msg.wxId)

        return status

    def toChengyu(self, msg) -> bool:
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
                        self.sendTextMsg(msg.roomId, rsp)
                        status = True
            elif flag in ["?", "？"]:  # 查词
                if cy.isChengyu(text):
                    rsp = cy.getMeaning(text)
                    if rsp:
                        self.sendTextMsg(msg.roomId, rsp)
                        status = True

        return status

    def toChitchat(self, msg):
        """闲聊，目前未实现
        """
        pass

    def processMsg(self, msg) -> None:
        """当接收到消息的时候，会调用本方法。如果不实现本方法，则打印原始消息。
        """

        self.printRawMsg(msg)  # 打印信息

        # 群聊消息
        if self.isGroupChat(msg):
            # 如果在群里被 @，回复发信人：“收到你的消息了！” 并 @他
            if msg.roomId not in self.config.GROUPS:  # 不在配置的响应的群列表里，忽略
                return

            if self.isAt(msg):   # 被@
                self.toAt(msg)

            else:                # 其他消息
                self.toChengyu(msg)

        # 非群聊信息
        elif msg.type == 37:     # 好友请求
            self.autoAcceptFriendRequest(msg)

        elif msg.type == 10000:  # 系统信息
            nickName = re.findall(r"你已添加了(.*)，现在可以开始聊天了。", msg.content)
            if nickName:
                # 添加了好友，更新好友列表
                self.allContacts[msg.wxId] = nickName

        elif msg.type == 0x01:   # 文本消息
            # 让配置加载更灵活，自己可以更新配置。也可以利用定时任务更新。
            if msg.self and msg.content == "^更新$":
                self.config.reload()
                self.LOG.info("已更新")
                return

            # 闲聊
            self.toChitchat(msg)


def weather_report(robot: Robot):
    """模拟发送天气预报
    """
    # 获取接收人
    receivers = ["filehelper"]

    # 获取天气，需要自己实现，可以参考 https://gitee.com/lch0821/WeatherScrapy 获取天气。
    report = "这就是获取到的天气情况了"

    for r in receivers:
        robot.sendTextMsg(r, report)


def main():
    robot = Robot(WxSDK, Config())

    # 初始化机器人
    robot.initSDK()

    # 接收消息
    robot.enableRecvMsg()

    # 每天7点发送天气预报
    robot.onEveryTime("07:00", weather_report, robot=robot)

    # 让机器人一直跑
    robot.keepRunningAndBlockProcess()


if __name__ == "__main__":
    main()
