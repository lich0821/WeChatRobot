# -*- coding: utf-8 -*-

import os
import random

import pandas as pd


class Chengyu(object):
    def __init__(self) -> None:
        root = os.path.dirname(os.path.abspath(__file__))
        self.df = pd.read_csv(f"{root}/chengyu.csv", delimiter="\t")
        self.cys, self.zis, self.yins = self._build_data()

    def _build_data(self):
        df = self.df.copy()
        df["shouzi"] = df["chengyu"].apply(lambda x: x[0])
        df["mozi"] = df["chengyu"].apply(lambda x: x[-1])

        df["shouyin"] = df["pingyin"].apply(lambda x: x.split(" ")[0])
        df["moyin"] = df["pingyin"].apply(lambda x: x.split(" ")[-1])

        cys = dict(zip(df["chengyu"], df["moyin"]))
        zis = df.groupby("shouzi").agg({"chengyu": set})["chengyu"].to_dict()
        yins = df.groupby("shouyin").agg({"chengyu": set})["chengyu"].to_dict()

        return cys, zis, yins

    def isChengyu(self, cy: str) -> bool:
        return self.cys.get(cy, None) is not None

    def getNext(self, current_idiom: str, allow_homophone: bool = True) -> str:
        """获取下一个成语
            current_idiom: 当前成语
            allow_homophone: 是否允许同音字
        """
        last_char = current_idiom[-1]
        candidates = list(self.zis.get(last_char, {}))
        try:
            candidates.remove(current_idiom)  # 移除当前成语
        except ValueError:
            pass  # Just ignore...

        if candidates:
            return random.choice(candidates)

        # 如果找不到同字，允许同音
        if allow_homophone:
            pronunciation = self.cys.get(current_idiom)
            candidates = list(self.yins.get(pronunciation, {}))
            try:
                candidates.remove(current_idiom)  # 移除当前成语
            except ValueError:
                pass  # Just ignore...

            if candidates:
                return random.choice(candidates)

        return None

    def getMeaning(self, chengyu: str) -> str:
        ress = self.df[self.df["chengyu"] == chengyu].to_dict(orient="records")
        if ress:
            res = ress[0]
            rsp = res["chengyu"] + "\n" + res["pingyin"] + "\n" + res["jieshi"]
            if res["chuchu"] and res["chuchu"] != "无":
                rsp += "\n出处：" + res["chuchu"]
            if res["lizi"] and res["lizi"] != "无":
                rsp += "\n例子：" + res["lizi"]
            return rsp
        return None


cy = Chengyu()

if __name__ == "__main__":
    answer = cy.getNext("便宜行事")
    print(answer)
