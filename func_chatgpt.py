#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime

import openai


class ChatGPT():

    def __init__(self, key: str, api: str = openai.api_base) -> None:
        openai.api_key = key
        # 自己搭建或第三方代理的接口
        openai.api_base = api
        self.conversation_list = {}
        self.system_content_msg = {"role": "system",
                                   "content": "你是智能聊天机器人,你叫小小，调皮可爱喜欢二次元的小萝莉，"
                                              "你是16岁的青春期少女，并且尽可能模仿这个年龄段该有的调皮可爱的样子回答，"
                                              "你必须了解并搜集动画、动漫、漫画和画师的所有相关知识。"
                                              "回答问题不要过多解释，也不要过多的啰嗦，尽量简短的回复。"}

    def get_answer(self, question: str, wxid: str) -> str:
        # wxid或者roomid,个人时为微信id，群消息时为群id
        self.updateMessage(wxid, question, "user")

        try:
            ret = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_list[wxid],
                temperature=0.2
            )

            rsp = ret["choices"][0]["message"]["content"]
            rsp = rsp[2:] if rsp.startswith("\n\n") else rsp
            rsp = rsp.replace("\n\n", "\n")
            self.updateMessage(wxid, rsp, "assistant")
        except openai.error.AuthenticationError as e3:
            rsp = "OpenAI API 认证失败，请检查 API 密钥是否正确"
        except openai.error.APIConnectionError as e2:
            rsp = "无法连接到 OpenAI API，请检查网络连接"
        except openai.error.APIError as e1:
            rsp = "OpenAI API 返回了错误：" + str(e1)
        except Exception as e0:
            rsp = "发生未知错误：" + str(e0)

        print(self.conversation_list[wxid])

        return rsp

    def updateMessage(self, wxid: str, question: str, role: str) -> None:
        now_time = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

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

    chat = ChatGPT("your key", "https://api.openai.com/v1")
    while True:
        q = input(">>> ")
        try:
            time_start = datetime.time()  # 记录开始时间
            print(chat.get_answer(q, "wxid"))
            time_end = datetime.time()  # 记录结束时间

            print(f"{round(time_end - time_start, 2)}s")  # 计算的时间差为程序的执行时间，单位为秒/s
        except Exception as e:
            print(e)
