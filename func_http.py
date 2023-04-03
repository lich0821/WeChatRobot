#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Any
import uvicorn
import threading
from fastapi import FastAPI
from wcferry import Wcf


class Http(FastAPI):
    """将 wcferry 能力转成 HTTP 协议的示例"""

    def __init__(self, wcf: Wcf, **extra: Any) -> None:
        super().__init__(**extra)
        self.wcf = wcf
        self.LOG = logging.getLogger(__name__)
        self.add_api_route("/send", self.send_text, methods=["GET"])

    def send_text(self, msg: str, receiver: str, aters: str = "") -> dict:
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
