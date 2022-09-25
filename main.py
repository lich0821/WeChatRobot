#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import time

import robot.sdk.wcferry as WxSDK
from robot.base_robot import BaseRobot
from robot.configuration import Config


class Robot(BaseRobot):
    def __init__(self, sdk: WxSDK, config: Config) -> None:
        super().__init__(sdk, config)

    def processMsg(self, msg) -> None:
        # 如果不实现本方法，则默认打印原始消息

        if self.isGroupChat(msg):  # 是群消息
            if self.isAt(msg):   # 被@
                if msg.roomId in self.config.GROUPS:  # 在配置的响应的群列表里
                    self.sendTextMsg(msg.roomId, "收到你的消息了！", msg.wxId)


def main():
    robot = Robot(WxSDK, Config())
    robot.initSDK()
    robot.enableRecvMsg()

    while True:
        time.sleep(1)
        # 不让进程退出，否则机器人就退出了


if __name__ == "__main__":
    main()
