# WeChatRobot
一个基于 [WeChatFerry](https://github.com/lich0821/WeChatFerry) 的微信机器人示例。

|[📖 文档](https://wechatferry.readthedocs.io/)|[📺 视频教程](https://mp.weixin.qq.com/s/APdjGyZ2hllXxyG_sNCfXQ)|[🙋 FAQ](https://mp.weixin.qq.com/s/5Xle4X_OcxLoIX9PJjYCmQ)|[🚨【微信机器人】沙雕行为合集](https://mp.weixin.qq.com/s/mc8O5iuhy46X4Bgqs80E8g)|
|:-:|:-:|:-:|:-:|

|![碲矿](https://s2.loli.net/2023/09/25/fub5VAPSa8srwyM.jpg)|![赞赏](https://s2.loli.net/2023/09/25/gkh9uWZVOxzNPAX.jpg)|
|:-:|:-:|
|后台回复 `WeChatFerry` 加群交流|如果你觉得有用|

## Quick Start
0. 安装 Python，例如 [3.10.11](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe)
1. 安装微信 `3.9.2.23`，下载地址在 [这里](https://github.com/lich0821/WeChatFerry/releases/download/v39.0.0/WeChatSetup-3.9.2.23.exe)；也可以从 [WeChatSetup](https://gitee.com/lch0821/WeChatSetup) 找到。
2. 克隆项目
```sh
git clone https://github.com/lich0821/WeChatRobot.git

# 如果网络原因打不开，可以科学上网，或者使用gitee
git clone https://gitee.com/lch0821/WeChatRobot.git
```

如果觉得克隆复杂，也可以直接下载[最新版](https://github.com/lich0821/WeChatRobot/releases/latest) (打不开试试[这个](https://gitee.com/lch0821/WeChatRobot/releases/latest)) 到本地解压。

3. 安装依赖
```sh
# 升级 pip
python -m pip install -U pip
# 安装必要依赖
pip install -r requirements.txt
```

4. 运行

我们需要运行两次main.py第一次是生成配置文件config.yaml, 第二次是真正跑你的机器人。  
直接运行程序会自动拉起微信,如果微信未打开，会自动打开微信；如果版本不对，也会有提示；其他报错，请进群交流。

下面代码为第一次运行: 第一次运行main.py会在WeChatRobot目录下生成一个config.yaml文件，参照修改配置进行修改。
其中chatgpt、tigerbot和xinghuo_web是三种模型的配置信息, 你需要配置它们的参数, 不知道的可以加群交流。
```sh
python main.py
```


下面代码为第二次运行: 你可以通过命令行参数选择模型，默认是不选择, 这样你配置了什么参数就跑什么模型。正因如此你需要配置前面所说三种模型中的至少一种(当然也可以都配置, 想跑那个模型就选什么参数), 然后就可以开始使用你的机器人了。
```sh
python main.py
```
如果你配置了多个模型,下面的内容才对你有帮助否则略过, 通过参数可以选择要跑的模型。
```sh
# 例: 我想运行选择chatgpt的机器人
python main.py -c 2
```
> python main.py -c C 其中参数C可选择如下所示
>> 1. tigerbot模型
>> 2. chatgpt模型 
>> 3. 讯飞星火模型
>> 4. chatglm模型
### 修改配置
配置文件 `config.yaml` 是运行程序后自动从模板复制过来的，以下功能默认关闭。

* 为了响应群聊消息，需要添加相应的 `roomId`（打印的消息中方括号里的就是）：
```yaml
groups:
  enable: [] # 允许响应的群 roomId，大概长这样：2xxxxxxxxx3@chatroom
```

* 为了使用 ChatGPT，需要取消配置中 chatgpt 的注释， 并配置 OpenAI 的 Key（以及代理）：
```yaml
# 如果要使用 ChatGPT，取消下面的注释并填写相关内容
chatgpt:
  key: 填写你 ChatGPT 的 key
  api: https://api.openai.com/v1 # 如果你不知道这是干嘛的，就不要改
  proxy: # 如果你在国内，你可能需要魔法，大概长这样：http://域名或者IP地址:端口号
  prompt: 你是智能聊天机器人，你叫wcferry # 根据需要对角色进行设定
```

* ~~为了暴露 HTTP 接口，需要取消配置中 http 的注释：~~

如有需要，推荐使用 [wcfhttp](https://wechatferry.readthedocs.io/zh/latest/?badge=latest)

[![PyPi](https://img.shields.io/pypi/v/wcfhttp.svg)](https://pypi.python.org/pypi/wcfhttp) [![Downloads](https://static.pepy.tech/badge/wcfhttp)](https://pypi.python.org/pypi/wcfhttp) [![Documentation Status](https://readthedocs.org/projects/wechatferry/badge/?version=latest)](https://wechatferry.readthedocs.io/zh/latest/?badge=latest)
