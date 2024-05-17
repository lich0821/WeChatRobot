#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime

import httpx
from openai import APIConnectionError, APIError, AuthenticationError, AzureOpenAI


class Azure():
    def __init__(self, conf: dict) -> None:
        key = conf.get("key")
        endpoint = conf.get("endpoint")
        prompt = conf.get("prompt")
        api_version = conf.get("api_version")
        self.model = conf.get("deployment_name")
        self.LOG = logging.getLogger("Azure")
        self.client = AzureOpenAI(api_key=key, azure_endpoint=endpoint, api_version=api_version)
        self.conversation_list = {}
        self.system_content_msg = {"role": "system", "content": prompt}

    def __repr__(self):
        return 'Azure'

    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf:
            if conf.get("key") and conf.get("endpoint") and conf.get("prompt") and conf.get("deployment_name") and conf.get("api_version"):
                return True
        return False

    def get_answer(self, question: str, wxid: str) -> str:
        # wxid或者roomid,个人时为微信id，群消息时为群id
        self.updateMessage(wxid, question, "user")
        rsp = ""
        try:
            ret = self.client.chat.completions.create(model=self.model,
                                                      messages=self.conversation_list[wxid],
                                                      temperature=0.5)
            rsp = ret.choices[0].message.content
            rsp = rsp[2:] if rsp.startswith("\n\n") else rsp
            rsp = rsp.replace("\n\n", "\n")
            self.updateMessage(wxid, rsp, "assistant")
        except AuthenticationError:
            self.LOG.error("Azure API 认证失败，请检查 API 密钥是否正确")
        except APIConnectionError:
            self.LOG.error("无法连接到 Azure API，请检查网络连接")
        except APIError as e1:
            self.LOG.error(f"Azure API 返回了错误：{str(e1)}")
        except Exception as e0:
            self.LOG.error(f"发生未知错误：{str(e0)}")

        return rsp

    def updateMessage(self, wxid: str, question: str, role: str) -> None:
        time_mk = "-"
        # 初始化聊天记录,组装系统信息
        if wxid not in self.conversation_list.keys():
            question_ = [
                self.system_content_msg,
                {"role": "system", "content": "" + time_mk}
            ]
            self.conversation_list[wxid] = question_

        # 当前问题
        content_question_ = {"role": role, "content": question}
        self.conversation_list[wxid].append(content_question_)
        # for cont in self.conversation_list[wxid]:
        #     if cont["role"] != "system":
        #         continue
        #     if cont["content"].startswith(time_mk):
        #         cont["content"] = time_mk
        # 只存储10条记录，超过滚动清除
        i = len(self.conversation_list[wxid])
        if i > 10:
            print("滚动清除微信记录：" + wxid)
            # 删除多余的记录，倒着删，且跳过第一个的系统消息
            del self.conversation_list[wxid][1]


if __name__ == "__main__":
    from configuration import Config
    config = Config().AZURE
    if not config:
        exit(0)

    chat = Azure(config)

    while True:
        q = input(">>> ")
        try:
            time_start = datetime.now()  # 记录开始时间
            print(chat.get_answer(q, "wxid"))
            time_end = datetime.now()  # 记录结束时间
            print(f"{round((time_end - time_start).total_seconds(), 2)}s")  # 计算的时间差为程序的执行时间，单位为秒/s
        except Exception as e:
            print(e)
