from enum import IntEnum, unique


@unique
class ChatType(IntEnum):
    # UnKnown = 0  # 未知, 即未设置
    TIGER_BOT = 1  # TigerBot
    CHATGPT = 2  # ChatGPT
    XINGHUO_WEB = 3  # 讯飞星火
    CHATGLM = 4  # ChatGLM

    @staticmethod
    def is_in_chat_types(chat_type: int) -> bool:
        if chat_type in [ChatType.TIGER_BOT.value, ChatType.CHATGPT.value,
                         ChatType.XINGHUO_WEB.value, ChatType.CHATGLM.value]:
            return True
        return False

    @staticmethod
    def help_hint() -> str:
        return str({member.value: member.name for member in ChatType}).replace('{', '').replace('}', '')

