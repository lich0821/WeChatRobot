#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import google.generativeai as genai

class BardAssistant:
    def __init__(self, conf: dict) -> None:
        self._api_key = conf["api_key"]
        self._model_name = conf["model_name"]
        genai.configure(api_key=self._api_key)
        self._bard = genai.GenerativeModel(self._model_name)

    
    def __repr__(self):
        return 'BardAssistant'

    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf:
            return all(conf.values())
        return False

    def get_answer(self, msg: str, sender: str = None) -> str:
        response = self._bard.generate_content(msg)
        return response.text

if __name__ == "__main__":
    from configuration import Config
    config = Config().BardAssistant
    if not config:
        exit(0)

    bard_assistant = BardAssistant(config)
    rsp = BardAssistant.get_answer("who are you?")
    print(rsp)
