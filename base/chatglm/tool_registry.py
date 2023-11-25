import inspect
import json
import random
import re
import traceback
from copy import deepcopy
from datetime import datetime
from types import GenericAlias
from typing import Annotated, get_origin

from base.chatglm.comfyUI_api import ComfyUIApi
from base.func_news import News
from zhdate import ZhDate

_TOOL_HOOKS = {}
_TOOL_DESCRIPTIONS = {}


def extract_code(text: str) -> str:
    pattern = r'```([^\n]*)\n(.*?)```'
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[-1][1]


def register_tool(func: callable):
    tool_name = func.__name__
    tool_description = inspect.getdoc(func).strip()
    python_params = inspect.signature(func).parameters
    tool_params = []
    for name, param in python_params.items():
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            raise TypeError(f"Parameter `{name}` missing type annotation")
        if get_origin(annotation) != Annotated:
            raise TypeError(
                f"Annotation type for `{name}` must be typing.Annotated")

        typ, (description, required) = annotation.__origin__, annotation.__metadata__
        typ: str = str(typ) if isinstance(typ, GenericAlias) else typ.__name__
        if not isinstance(description, str):
            raise TypeError(f"Description for `{name}` must be a string")
        if not isinstance(required, bool):
            raise TypeError(f"Required for `{name}` must be a bool")

        tool_params.append({
            "name": name,
            "description": description,
            "type": typ,
            "required": required
        })
    tool_def = {
        "name": tool_name,
        "description": tool_description,
        "params": tool_params
    }

    # print("[registered tool] " + pformat(tool_def))
    _TOOL_HOOKS[tool_name] = func
    _TOOL_DESCRIPTIONS[tool_name] = tool_def

    return func


def dispatch_tool(tool_name: str, tool_params: dict) -> str:
    if tool_name not in _TOOL_HOOKS:
        return f"Tool `{tool_name}` not found. Please use a provided tool."
    tool_call = _TOOL_HOOKS[tool_name]
    try:
        ret = tool_call(**tool_params)
    except BaseException:
        ret = traceback.format_exc()
    return ret


def get_tools() -> dict:
    return deepcopy(_TOOL_DESCRIPTIONS)

# Tool Definitions

# @register_tool
# def random_number_generator(
#     seed: Annotated[int, 'The random seed used by the generator', True],
#     range: Annotated[tuple[int, int], 'The range of the generated numbers', True],
# ) -> int:
#     """
#     Generates a random number x, s.t. range[0] <= x < range[1]
#     """
#     if not isinstance(seed, int):
#         raise TypeError("Seed must be an integer")
#     if not isinstance(range, tuple):
#         raise TypeError("Range must be a tuple")
#     if not isinstance(range[0], int) or not isinstance(range[1], int):
#         raise TypeError("Range must be a tuple of integers")

#     import random
#     return random.Random(seed).randint(*range)


@register_tool
def get_weather(
    city_name: Annotated[str, 'The name of the city to be queried', True],
) -> str:
    """
    Get the current weather for `city_name`
    """
    if not isinstance(city_name, str):
        raise TypeError("City name must be a string")

    key_selection = {
        "current_condition": ["temp_C", "FeelsLikeC", "humidity", "weatherDesc", "observation_time"],
    }
    import requests
    try:
        resp = requests.get(f"https://wttr.in/{city_name}?format=j1")
        resp.raise_for_status()
        resp = resp.json()
        ret = {k: {_v: resp[k][0][_v] for _v in v}
               for k, v in key_selection.items()}
    except BaseException:
        import traceback
        ret = "Error encountered while fetching weather data!\n" + traceback.format_exc()

    return str(ret)


@register_tool
def get_confyui_image(prompt: Annotated[str, '要生成图片的提示词,注意必须是英文', True]) -> dict:
    '''
    生成图片
    '''
    with open("chatglm\\base.json", "r", encoding="utf-8") as f:
        data2 = json.load(f)
        data2['prompt']['3']['inputs']['seed'] = ''.join(
            random.sample('123456789012345678901234567890', 14))
        # 模型名称
        data2['prompt']['4']['inputs']['ckpt_name'] = 'chilloutmix_NiPrunedFp32Fix.safetensors'
        data2['prompt']['6']['inputs']['text'] = prompt  # 正向提示词
        # data2['prompt']['7']['inputs']['text']=''         #反向提示词
        cfui = ComfyUIApi(server_address="127.0.0.1:8188")  # 根据自己comfyUI地址修改
        images = cfui.get_images(data2['prompt'])
        return {'res': images[0]['image'], 'res_type': 'image', 'filename': images[0]['filename']}


@register_tool
def get_news() -> str:
    '''
    获取最新新闻
    '''
    news = News()
    return news.get_important_news()


@register_tool
def get_time() -> str:
    '''
    获取当前日期，时间，农历日期，星期几
    '''
    time = datetime.now()
    date2 = ZhDate.from_datetime(time)
    week_list = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

    return '{} {} {}'.format(time.strftime("%Y年%m月%d日 %H:%M:%S"), week_list[time.weekday()], '农历:' + date2.chinese())


if __name__ == "__main__":
    print(dispatch_tool("get_weather", {"city_name": "beijing"}))
    print(get_tools())
