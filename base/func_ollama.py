#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
import re

import ollama


class Ollama():
    def __init__(self, conf: dict) -> None:
        self.enable = conf.get("enable")
        self.model = conf.get("model")
        self.prompt = conf.get("prompt")

        self.conversation_list = {}
        self.system_content_msg = {"role": "system", "content": self.prompt}


    def __repr__(self):
        return 'Ollama'

    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf:
            if conf.get("enable") and conf.get("model") and conf.get("prompt"):
                return True
        return False

    def get_answer(self, question: str, wxid: str) -> str:
        # wxid或者roomid,个人时为微信id，群消息时为群id
        self.updateMessage(wxid, question, "user")
        rsp = ""
        try:
            res=ollama.chat(model="deepseek-r1:1.5b",stream=False,messages=[{"role": "user","content": question}],options={"temperature":0})
            res_message = res["message"]["content"]

            # 去除回應中的空白与回车
            # res_message = res_message.replace(" ", "")
            # res_message = res_message.replace("\n", "")

            # 去除<think>标签对与内部内容
            res_message = re.sub(r'<think>.*?</think>', '', res_message)

            return res_message
        except Exception as e0:
            self.LOG.error(f"发生未知错误：{str(e0)}")

        return rsp

    def updateMessage(self, wxid: str, question: str, role: str) -> None:
        now_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        time_mk = "当需要回答时间时请直接参考回复:"
        # 初始化聊天记录,组装系统信息
        if wxid not in self.conversation_list.keys():
            question_ = [
                self.system_content_msg,
                {"role": "system", "content": "" + time_mk + now_time}
            ]
            self.conversation_list[wxid] = question_

        # 当前问题
        content_question_ = {"role": role, "content": question}
        self.conversation_list[wxid].append(content_question_)

        for cont in self.conversation_list[wxid]:
            if cont["role"] != "system":
                continue
            if cont["content"].startswith(time_mk):
                cont["content"] = time_mk + now_time

        # 只存储10条记录，超过滚动清除
        i = len(self.conversation_list[wxid])
        if i > 10:
            print("滚动清除微信记录：" + wxid)
            # 删除多余的记录，倒着删，且跳过第一个的系统消息
            del self.conversation_list[wxid][1]


if __name__ == "__main__":
    from configuration import Config
    config = Config().CHATGPT
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
