#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import logging
import time
from datetime import datetime

import requests
from lxml import etree


class News(object):
    def __init__(self) -> None:
        self.LOG = logging.getLogger(__name__)
        self.week = {0: "周一", 1: "周二", 2: "周三", 3: "周四", 4: "周五", 5: "周六", 6: "周日"}
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0"}

    def get_important_news(self):
        url = "https://www.cls.cn/api/sw?app=CailianpressWeb&os=web&sv=7.7.5"
        data = {"type": "telegram", "keyword": "你需要知道的隔夜全球要闻", "page": 0,
                "rn": 1, "os": "web", "sv": "7.7.5", "app": "CailianpressWeb"}
        try:
            rsp = requests.post(url=url, headers=self.headers, data=data)
            data = json.loads(rsp.text)["data"]["telegram"]["data"][0]
            news = data["descr"]
            timestamp = data["time"]
            ts = time.localtime(timestamp)
            weekday_news = datetime(*ts[:6]).weekday()
        except Exception as e:
            self.LOG.error(e)
            return ""

        weekday_now = datetime.now().weekday()
        if weekday_news != weekday_now:
            return ""  # 旧闻，观察发现周二～周六早晨6点半左右发布

        fmt_time = time.strftime("%Y年%m月%d日", ts)

        news = re.sub(r"(\d{1,2}、)", r"\n\1", news)
        fmt_news = "".join(etree.HTML(news).xpath(" // text()"))
        fmt_news = re.sub(r"周[一|二|三|四|五|六|日]你需要知道的", r"", fmt_news)

        return f"{fmt_time} {self.week[weekday_news]}\n{fmt_news}"


if __name__ == "__main__":
    news = News()
    print(news.get_important_news())
