# WeChatRobot
一个基于 [WeChatFerry](https://github.com/lich0821/WeChatFerry) 的微信机器人示例。

## Quick Start
0. 安装 32 位 Python，例如 [3.7.9](https://www.python.org/ftp/python/3.7.9/python-3.7.9.exe)
1. 安装微信 `3.7.0.30`，下载地址在[这里](https://github.com/lich0821/WeChatFerry/releases/download/v3.7.0.30.11/WeChatSetup-3.7.0.30.exe)；也可以从 [WeChatSetup](https://gitee.com/lch0821/WeChatSetup) 找到。
2. 安装依赖
```sh
# 升级 pip
python -m pip install -U pip
# 安装必要依赖
pip install -r requirements.txt
```

3. 按需修改配置

从配置模板 `config.yaml.template` 复制一份配置文件 `config.yaml`，按需修改其中的配置。
为了响应群聊消息，需要添加相应的 `roomId`：
```yaml
groups:
  enable: [] # 允许响应的群 roomId，可以通过 WxGetContacts 获取
```

4. 运行
```sh
python main.py
# 如果微信未打开，会自动打开微信；如果版本不对，也会有提示；其他报错，请进群交流。
```

![Demo](demo.gif)

👉 [视频教程](https://mp.weixin.qq.com/s/omuSBeZRKSjo0PEtjwey7A)

欢迎加群交流，后台回复 `WeChatFerry `：

![碲矿](TEQuant.jpeg)
