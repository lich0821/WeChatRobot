#! /usr/bin/env python3
# -*- coding: utf-8 -*-
import bardapi
import requests

class BardAssistant:
    def __init__(self, conf: dict) -> None:
        self._token = conf["token"]
        self._bard = bardapi.core.Bard(self._token)


    def __repr__(self):
        return 'BardAssistant'

    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf:
            return all(conf.values())
        return False

    def get_answer(self, msg: str, sender: str = None) -> str:
        response = self._bard.get_answer(msg)
        return response['content']

if __name__ == "__main__":
    from configuration import Config
    config = Config().BardAssistant
    if not config:
        exit(0)

    bard_assistant = BardAssistant(config)
    rsp = BardAssistant.get_answer("who are you?")
    print(rsp)