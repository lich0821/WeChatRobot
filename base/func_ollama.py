#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
import re

import ollama


class Ollama():
    def __init__(self, conf: dict) -> None:
        enable = conf.get("enable")
        self.model = conf.get("model")
        self.prompt = conf.get("prompt")

        self.LOG = logging.getLogger("Ollama")
        self.conversation_list = {}


    def __repr__(self):
        return 'Ollama'

    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf:
            if conf.get("enable") and conf.get("model") and conf.get("prompt"):
                return True
        return False

    def get_answer(self, question: str, wxid: str) -> str:
        try:
            self.conversation_list[wxid]
        except KeyError:
            res=ollama.generate(model=self.model, prompt=self.prompt, keep_alive="30m")
            self.updateMessage(wxid, res["context"], "assistant")
        # wxid或者roomid,个人时为微信id，群消息时为群id
        rsp = ""
        try:
            res=ollama.generate(model=self.model, prompt=question, context=self.conversation_list[wxid], keep_alive="30m")
            self.updateMessage(wxid, res["context"], "user")
            res_message = res["response"]
            # 去除<think>标签对与内部内容
            # res_message = res_message.split("</think>")[-1]
            # 去除开头的\n和空格
            # return res_message[2:]
            return res_message
        except Exception as e0:
            print(e0)
            self.LOG.error(f"发生未知错误：{str(e0)}")

        return rsp

    def updateMessage(self, wxid: str, context: str, role: str) -> None:
        # 当前问题
        self.conversation_list[wxid] = context

if __name__ == "__main__":
    from configuration import Config
    config = Config().OLLAMA
    if not config:
        exit(0)

    chat = Ollama(config)

    while True:
        q = input(">>> ")
        try:
            time_start = datetime.now()  # 记录开始时间
            print(chat.get_answer(q, "wxid"))
            time_end = datetime.now()  # 记录结束时间

            print(f"{round((time_end - time_start).total_seconds(), 2)}s")  # 计算的时间差为程序的执行时间，单位为秒/s
        except Exception as e:
            print(e)
