from enum import IntEnum, unique


@unique
class ChatType(IntEnum):
    UnKnown = 0  # 未知, 即未设置
    TIGER_BOT = 1  # TigerBot
    CHATGPT = 2  # ChatGPT
    XINGHUO_WEB = 3  # 讯飞星火
