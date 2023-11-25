#! /usr/bin/env python3
# -*- coding: utf-8 -*-
from sparkdesk_web.core import SparkWeb


class XinghuoWeb:
    def __init__(self, xhconf=None) -> None:

        self._sparkWeb = SparkWeb(
            cookie=xhconf["cookie"],
            fd=xhconf["fd"],
            GtToken=xhconf["GtToken"],
        )
        self._chat = self._sparkWeb.create_continuous_chat()
        # 如果有提示词
        if xhconf["prompt"]:
            self._chat.chat(xhconf["prompt"])

    def __repr__(self):
        return 'XinghuoWeb'

    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf:
            return all(conf.values())
        return False

    def get_answer(self, msg: str, sender: str = None) -> str:
        answer = self._chat.chat(msg)
        return answer


if __name__ == "__main__":
    from configuration import Config
    c = Config()
    xinghuo = XinghuoWeb(c.XINGHUO_WEB)
    rsp = xinghuo.get_answer("你还活着？")
    print(rsp)
