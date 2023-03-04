#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import openai


class ChatGPT():
    def __init__(self, key) -> None:
        openai.api_key = key

    def get_answer(self, question: str) -> str:
        try:
            ret = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": question},
                ],
                temperature=0.5,
            )
            rsp = ret["choices"][0]["message"]["content"]
            rsp = rsp[2:] if rsp.startswith("\n\n") else rsp
            rsp = rsp.replace("\n\n", "\n")
        except Exception as e:
            ret = ""

        return rsp


if __name__ == "__main__":
    from datetime import datetime
    chat = ChatGPT("your key")
    while True:
        q = input(">>> ")
        try:
            t1 = datetime.now()
            print(chat.get_answer(q))
            t2 = datetime.now()
            print(f"{t2-t1}s")
        except Exception as e:
            print(e)
