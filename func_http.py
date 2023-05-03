#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Any
import uvicorn
import threading
from fastapi import FastAPI
from fastapi import Body
from wcferry import Wcf


class Http(FastAPI):
    """将 wcferry 能力转成 HTTP 协议的示例"""

    def __init__(self, wcf: Wcf, **extra: Any) -> None:
        super().__init__(**extra)
        self.wcf = wcf
        self.LOG = logging.getLogger(__name__)
        self.add_api_route("/text", self.send_text, methods=["POST"], summary="发送文本消息")
        self.add_api_route("/image", self.send_image, methods=["POST"], summary="发送图片消息")
        self.add_api_route("/file", self.send_file, methods=["POST"], summary="发送文件消息")
        self.add_api_route("/send", self.send_text_deprecated, methods=["GET"], summary="【已过时，不要再使用】发送消息")

    def send_text(self, msg: str = Body("消息"), receiver: str = Body("filehelper"), aters: str = Body("")) -> dict:
        """ 发送消息，可参考：robot.py 里 sendTextMsg
        """
        ret = self.wcf.send_text(msg, receiver, aters)
        return {"status": ret}

    def send_image(self,
                   path: str = Body("C:\\Projs\\WeChatRobot\\TEQuant.jpeg", description="本地图片路径，不支持网络路径"),
                   receiver: str = Body("filehelper", description="roomid 或者 wxid")) -> dict:
        ret = self.wcf.send_image(path, receiver)
        return {"status": ret}

    def send_file(self,
                  path: str = Body("C:\\Projs\\WeChatRobot\\TEQuant.jpeg", description="本地文件路径，不支持网络路径"),
                  receiver: str = Body("filehelper", description="roomid 或者 wxid")) -> dict:
        ret = self.wcf.send_file(path, receiver)
        return {"status": ret}

    def send_text_deprecated(self, msg: str, receiver: str, aters: str = "") -> dict:
        ret = self.wcf.send_text(msg, receiver, aters)

        return {"status": ret, "msg": msg, "receiver": receiver, "aters": aters}

    @staticmethod
    def start(http, host, port):
        threading.Thread(name="HTTP",
                         target=uvicorn.run,
                         kwargs={"app": http, "host": host, "port": port}).start()


if __name__ == "__main__":
    import time
    import signal

    from configuration import Config
    c = Config().HTTP
    if not c:
        exit(0)

    def handler(sig, frame):
        exit(0)

    signal.signal(signal.SIGINT, handler)

    wcf = Wcf("tcp://127.0.0.1:10086")
    home = "https://github.com/lich0821/WeChatFerry"
    http = Http(wcf=wcf,
                title="API for send text",
                description=f"Github: <a href='{home}'>WeChatFerry</a>",)
    Http.start(http, c.get("host", "0.0.0.0"), c.get("port", 9999))

    while True:
        time.sleep(1)
