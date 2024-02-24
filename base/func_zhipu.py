from zhipuai import ZhipuAI


class ZhiPu():
    def __init__(self, conf: dict) -> None:
        self.api_key = conf.get("api_key")
        self.model = conf.get("model", "glm-4")  # 默认使用 glm-4 模型
        self.client = ZhipuAI(api_key=self.api_key)
        self.converstion_list = {}

    @staticmethod
    def value_check(conf: dict) -> bool:
        if conf and conf.get("api_key"):
            return True
        return False

    def __repr__(self):
        return 'ZhiPu'

    def get_answer(self, msg: str, wxid: str, **args) -> str:
        self._update_message(wxid, str(msg), "user")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.converstion_list[wxid]
        )
        resp_msg = response.choices[0].message
        answer = resp_msg.content
        self._update_message(wxid, answer, "assistant")
        return answer

    def _update_message(self, wxid: str, msg: str, role: str) -> None:
        if wxid not in self.converstion_list.keys():
            self.converstion_list[wxid] = []
        content = {"role": role, "content": str(msg)}
        self.converstion_list[wxid].append(content)


if __name__ == "__main__":
    from configuration import Config
    config = Config().ZHIPU
    if not config:
        exit(0)

    zhipu = ZhiPu(config)
    rsp = zhipu.get_answer("你好")
    print(rsp)
