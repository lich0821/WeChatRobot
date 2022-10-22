#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import signal
from wcferry import Wcf

from robot import Robot


def weather_report(robot: Robot) -> None:
    """模拟发送天气预报
    """
    # 获取接收人
    receivers = ["filehelper"]

    # 获取天气，需要自己实现，可以参考 https://gitee.com/lch0821/WeatherScrapy 获取天气。
    report = "这就是获取到的天气情况了"

    for r in receivers:
        robot.sendTextMsg(report, r)


def main():
    wcf = Wcf()

    def handler(sig, frame):
        wcf.cleanup()  # 退出前清理环境
        exit(0)

    signal.signal(signal.SIGINT, handler)

    robot = Robot(wcf)
    robot.LOG.info("机器人已启动")

    # 接收消息
    robot.enableRecvMsg()

    # 每天7点发送天气预报
    robot.onEveryTime("07:00", weather_report, robot=robot)

    # 让机器人一直跑
    robot.keepRunningAndBlockProcess()


if __name__ == "__main__":
    main()
