#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import random
from datetime import datetime
from typing import Optional

import openai
from base.chatglm.code_kernel import CodeKernel, execute
from base.chatglm.tool_registry import dispatch_tool, extract_code, get_tools
from wcferry import Wcf

functions = get_tools()


class ChatGLM:

    def __init__(self, config={}, wcf: Optional[Wcf] = None, max_retry=5) -> None:
        openai.api_key = config.get("key", "empty")
        # 自己搭建或第三方代理的接口
        openai.api_base = config["api"]
        proxy = config.get("proxy")
        if proxy:
            openai.proxy = {"http": proxy, "https": proxy}
        self.conversation_list = {}
        self.chat_type = {}
        self.max_retry = max_retry
        self.wcf = wcf
        self.filePath = config["file_path"]
        self.kernel = CodeKernel()
        self.system_content_msg = {"chat": [{"role": "system", "content": config["prompt"]}],
                                   "tool": [{"role": "system", "content": "Answer the following questions as best as you can. You have access to the following tools:"}],
                                   "code": [{"role": "system", "content": "你是一位智能AI助手，你叫ChatGLM，你连接着一台电脑，但请注意不能联网。在使用Python解决任务时，你可以运行代码并得到结果，如果运行结果有错误，你需要尽可能对代码进行改进。你可以处理用户上传到电脑上的文件，文件默认存储路径是{}。".format(self.filePath)}]}

    def __repr__(self):
        return 'ChatGLM'

    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf:
            if conf.get("api") and conf.get("prompt") and conf.get("file_path"):
                return True
        return False

    def get_answer(self, question: str, wxid: str) -> str:
        # wxid或者roomid,个人时为微信id，群消息时为群id
        if '#帮助' == question:
            return '本助手有三种模式，#聊天模式 = #1 ，#工具模式 = #2 ，#代码模式 = #3 , #清除模式会话 = #4 , #清除全部会话 = #5 可用发送#对应模式 或者 #编号 进行切换'
        elif '#聊天模式' == question or '#1' == question:
            self.chat_type[wxid] = 'chat'
            return '已切换#聊天模式'
        elif '#工具模式' == question or '#2' == question:
            self.chat_type[wxid] = 'tool'
            return '已切换#工具模式 \n工具有：查看天气，日期，新闻,comfyUI文生图。例如：\n帮我生成一张小鸟的图片，提示词必须是英文'
        elif '#代码模式' == question or '#3' == question:
            self.chat_type[wxid] = 'code'
            return '已切换#代码模式 \n代码模式可以用于写python代码，例如：\n用python画一个爱心'
        elif '#清除模式会话' == question or '#4' == question:
            self.conversation_list[wxid][self.chat_type[wxid]
                                         ] = self.system_content_msg[self.chat_type[wxid]]
            return '已清除'
        elif '#清除全部会话' == question or '#5' == question:
            self.conversation_list[wxid] = self.system_content_msg
            return '已清除'

        self.updateMessage(wxid, question, "user")

        try:
            params = dict(model="chatglm3", temperature=1.0,
                          messages=self.conversation_list[wxid][self.chat_type[wxid]], stream=False)
            if 'tool' == self.chat_type[wxid]:
                params["functions"] = functions
            response = openai.ChatCompletion.create(**params)
            for _ in range(self.max_retry):
                if response.choices[0].message.get("function_call"):
                    function_call = response.choices[0].message.function_call
                    print(
                        f"Function Call Response: {function_call.to_dict_recursive()}")

                    function_args = json.loads(function_call.arguments)
                    observation = dispatch_tool(
                        function_call.name, function_args)
                    if isinstance(observation, dict):
                        res_type = observation['res_type'] if 'res_type' in observation else 'text'
                        res = observation['res'] if 'res_type' in observation else str(
                            observation)
                        if res_type == 'image':
                            filename = observation['filename']
                            filePath = os.path.join(self.filePath, filename)
                            res.save(filePath)
                            self.wcf and self.wcf.send_image(filePath, wxid)
                        tool_response = '[Image]' if res_type == 'image' else res
                    else:
                        tool_response = observation if isinstance(
                            observation, str) else str(observation)
                    print(f"Tool Call Response: {tool_response}")

                    params["messages"].append(response.choices[0].message)
                    params["messages"].append(
                        {
                            "role": "function",
                            "name": function_call.name,
                            "content": tool_response,  # 调用函数返回结果
                        }
                    )
                    self.updateMessage(wxid, tool_response, "function")
                    response = openai.ChatCompletion.create(**params)
                elif response.choices[0].message.content.find('interpreter') != -1:
                    output_text = response.choices[0].message.content
                    code = extract_code(output_text)
                    self.wcf and self.wcf.send_text('代码如下：\n' + code, wxid)
                    self.wcf and self.wcf.send_text('执行代码...', wxid)
                    try:
                        res_type, res = execute(code, self.kernel)
                    except Exception as e:
                        rsp = f'代码执行错误: {e}'
                        break
                    if res_type == 'image':
                        filename = '{}.png'.format(''.join(random.sample(
                            'abcdefghijklmnopqrstuvwxyz1234567890', 8)))
                        filePath = os.path.join(self.filePath, filename)
                        res.save(filePath)
                        self.wcf and self.wcf.send_image(filePath, wxid)
                    else:
                        self.wcf and self.wcf.send_text("执行结果:\n" + res, wxid)
                    tool_response = '[Image]' if res_type == 'image' else res
                    print("Received:", res_type, res)
                    params["messages"].append(response.choices[0].message)
                    params["messages"].append(
                        {
                            "role": "function",
                            "name": "interpreter",
                            "content": tool_response,  # 调用函数返回结果
                        }
                    )
                    self.updateMessage(wxid, tool_response, "function")
                    response = openai.ChatCompletion.create(**params)
                else:
                    rsp = response.choices[0].message.content
                    break

            self.updateMessage(wxid, rsp, "assistant")
        except Exception as e0:
            rsp = "发生未知错误：" + str(e0)

        return rsp

    def updateMessage(self, wxid: str, question: str, role: str) -> None:
        now_time = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        # 初始化聊天记录,组装系统信息
        if wxid not in self.conversation_list.keys():
            self.conversation_list[wxid] = self.system_content_msg
        if wxid not in self.chat_type.keys():
            self.chat_type[wxid] = 'chat'

        # 当前问题
        content_question_ = {"role": role, "content": question}
        self.conversation_list[wxid][self.chat_type[wxid]].append(
            content_question_)

        # 只存储10条记录，超过滚动清除
        i = len(self.conversation_list[wxid][self.chat_type[wxid]])
        if i > 10:
            print("滚动清除微信记录：" + wxid)
            # 删除多余的记录，倒着删，且跳过第一个的系统消息
            del self.conversation_list[wxid][self.chat_type[wxid]][1]


if __name__ == "__main__":
    from configuration import Config
    config = Config().CHATGLM
    if not config:
        exit(0)

    chat = ChatGLM(config)

    while True:
        q = input(">>> ")
        try:
            time_start = datetime.now()  # 记录开始时间
            print(chat.get_answer(q, "wxid"))
            time_end = datetime.now()  # 记录结束时间

            # 计算的时间差为程序的执行时间，单位为秒/s
            print(f"{round((time_end - time_start).total_seconds(), 2)}s")
        except Exception as e:
            print(e)
