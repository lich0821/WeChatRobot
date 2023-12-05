# WeChatRobot
一个基于 [WeChatFerry](https://github.com/lich0821/WeChatFerry) 的微信机器人示例。

|[📖 文档](https://wechatferry.readthedocs.io/)|[📺 视频教程](https://mp.weixin.qq.com/s/APdjGyZ2hllXxyG_sNCfXQ)|[🙋 FAQ](https://mp.weixin.qq.com/s/mFUwK2cJJrajVqYiM-GlDA)|[🚨【微信机器人】沙雕行为合集](https://mp.weixin.qq.com/s/mc8O5iuhy46X4Bgqs80E8g)|
|:-:|:-:|:-:|:-:|

|![碲矿](https://s2.loli.net/2023/09/25/fub5VAPSa8srwyM.jpg)|![赞赏](https://s2.loli.net/2023/09/25/gkh9uWZVOxzNPAX.jpg)|
|:-:|:-:|
|后台回复 `WeChatFerry` 加群交流|如果你觉得有用|

## Quick Start
0. 遇到问题先看看上面的文档、教程和 FAQ。
    - 按照步骤来，版本保持一致，少走弯路。
    - 按照步骤来，版本保持一致，少走弯路。
    - 按照步骤来，版本保持一致，少走弯路。
1. 安装 Python>=3.9（Python 12 需要自己编译依赖，慎选），例如 [3.10.11](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe)
2. 安装微信 `3.9.2.23`，下载地址在 [这里](https://github.com/lich0821/WeChatFerry/releases/latest)；也可以从 [WeChatSetup](https://gitee.com/lch0821/WeChatSetup) 找到。
3. 克隆项目
```sh
git clone https://github.com/lich0821/WeChatRobot.git

# 如果网络原因打不开，可以科学上网，或者使用gitee
git clone https://gitee.com/lch0821/WeChatRobot.git
```

如果觉得克隆复杂，也可以直接下载 [最新版](https://github.com/lich0821/WeChatRobot/releases/latest) 到本地解压。

4. 安装依赖
```sh
# 升级 pip
python -m pip install -U pip
# 安装必要依赖
pip install -r requirements.txt
# ChatGLM 还需要安装一个 kernel
ipython kernel install --name chatglm3 --user
```

5. 运行

我们需要运行两次 `main.py` 第一次是生成配置文件 `config.yaml`, 第二次是真正跑你的机器人。
直接运行程序会自动拉起微信，如果微信未打开，会自动打开微信；如果版本不对，也会有提示；其他报错，请进群交流。

下面代码为第一次运行：第一次运行 `main.py` 会在 WeChatRobot 目录下生成一个 `config.yaml` 文件，参照修改配置进行修改。

其中 chatgpt、tigerbot、chatglm 和 xinghuo_web 是四种模型的配置信息，你需要配置它们的参数，不知道的可以加群交流。

```sh
python main.py

# 需要停止按 Ctrl+C
```

启动之后，可以正常接收消息但不会响应群消息。参考下方 [修改配置](#config) 进行配置，以便响应特定群聊。

下面代码为第二次运行：你可以通过命令行参数选择模型，默认是不选择，这样你配置了什么参数就跑什么模型。正因如此你需要配置前面所说四种模型中的至少一种（当然也可以都配置，想跑那个模型就选什么参数）, 然后就可以开始使用你的机器人了。
```sh
python main.py

# 需要停止按 Ctrl+C
```

如果你配置了多个模型（不需要将其他配置注释或者移除），下面的内容才对你有帮助否则略过，通过 `python main.py -h` 通过参数可以选择要跑的模型。
```sh
# 查看帮助
python main.py -h
#optional arguments:
#  -h, --help            show this help message and exit
#  -c C, --chat_model C  选择要使用的AI模型，默认不选择，可选参数：1. tigerbot 模型 2. chatgpt 模型 3. 讯飞星火模型 4. chatglm 模型
```

```sh
# 例: 我想运行选择chatgpt的机器人
python main.py -c 2

# 需要停止按 Ctrl+C
```

> python main.py -c C 其中参数 C 可选择如下所示
>> 1. tigerbot 模型
>> 2. chatgpt 模型
>> 3. 讯飞星火模型
>> 4. chatglm 模型

6. 停止

不要那么粗暴，温柔点儿；

不要直接关闭窗口，温柔点儿。

输入：`Ctrl+C`。否则，会出现各种奇怪问题。

### <a name="config"></a>修改配置
ℹ️ *修改配置后，需要重新启动，以便让配置生效。*

配置文件 `config.yaml` 是运行程序后自动从模板复制过来的，功能默认关闭。

#### 响应被 @ 消息
为了响应群聊消息，需要添加相应的 `roomId`。

第一次运行的时候，可以在手机上往需要响应的群里发消息，打印的消息中方括号里的就是；多个群用 `,` 分隔。
```yaml
groups:
  enable: [] # 允许响应的群 roomId，大概长这样：2xxxxxxxxx3@chatroom, 多个群用 `,` 分隔
```

#### 配置 AI 模型
为了使用 AI 模型，需要对相应模型并进行配置。

使用 ChatGLM 见注意事项 [README.MD](base/chatglm/README.MD)

```yaml
chatgpt:  # -----chatgpt配置这行不填-----
  key:  # 填写你 ChatGPT 的 key
  api: https://api.openai.com/v1  # 如果你不知道这是干嘛的，就不要改
  proxy:  # 如果你在国内，你可能需要魔法，大概长这样：http://域名或者IP地址:端口号
  prompt: 你是智能聊天机器人，你叫 wcferry  # 根据需要对角色进行设定

chatglm:  # -----chatglm配置这行不填-----
  key: sk-012345678901234567890123456789012345678901234567 # 这个应该不用动
  api: http://localhost:8000/v1  # 根据自己的chatglm地址修改
  proxy:  # 如果你在国内，你可能需要魔法，大概长这样：http://域名或者IP地址:端口号
  prompt: 你是智能聊天机器人，你叫小薇  # 根据需要对角色进行设定
  file_path: C:/Pictures/temp  #设定生成图片和代码使用的文件夹路径

tigerbot:  # -----tigerbot配置这行不填-----
  key:  # key
  model:  # tigerbot-7b-sft

# 抓取方式详见文档：https://www.bilibili.com/read/cv27066577
xinghuo_web:  # -----讯飞星火web模式api配置这行不填-----
  cookie:  # cookie
  fd:  # fd
  GtToken:  # GtToken
  prompt: 你是智能聊天机器人，你叫 wcferry。请用这个角色回答我的问题  # 根据需要对角色进行设定
```

## HTTP
如需要使用 HTTP 接口，请参考 [wcfhttp](https://wechatferry.readthedocs.io/zh/latest/?badge=latest)。

[![PyPi](https://img.shields.io/pypi/v/wcfhttp.svg)](https://pypi.python.org/pypi/wcfhttp) [![Downloads](https://static.pepy.tech/badge/wcfhttp)](https://pypi.python.org/pypi/wcfhttp) [![Documentation Status](https://readthedocs.org/projects/wechatferry/badge/?version=latest)](https://wechatferry.readthedocs.io/zh/latest/?badge=latest)
