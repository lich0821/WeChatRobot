# ChatGLM3 集成使用说明

1. 需要取消配置中 chatglm 的注释， 并配置对应信息，使用 [ChatGLM3](https://github.com/THUDM/ChatGLM3), 启用最新版 ChatGLM3 根目录下 openai_api.py 获取 api 地址：
```yaml
# 如果要使用 chatglm，取消下面的注释并填写相关内容
chatglm:
  key: sk-012345678901234567890123456789012345678901234567 # 根据需要自己做key校验
  api: http://localhost:8000/v1 # 根据自己的chatglm地址修改
  proxy:  # 如果你在国内，你可能需要魔法，大概长这样：http://域名或者IP地址:端口号
  prompt: 你是智能聊天机器人，你叫小薇 # 根据需要对角色进行设定
  file_path: F:/Pictures/temp  #设定生成图片和代码使用的文件夹路径
```

2. 修改 chatglm/tool_registry.py 工具里面的一下配置，comfyUI 地址或者根据需要自己配置一些工具，函数名上需要加 @register_tool, 函数里面需要叫'''函数描述'''，参数需要用 Annotated[str,'',True] 修饰，分别是类型，参数说明，是否必填，再加 ->加上对应的返回类型
```python
@register_tool
def get_confyui_image(prompt: Annotated[str, '要生成图片的提示词,注意必须是英文', True]) -> dict:
    '''
    生成图片
    '''
    with open("func_chatglm\\base.json", "r", encoding="utf-8") as f:
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

```

3. 使用 Code Interpreter 还需要安装 Jupyter 内核，默认名称叫 chatglm3：
```
ipython kernel install --name chatglm3 --user
```

如果名称需要自定义，可以配置系统环境变量：IPYKERNEL 或者修改 chatglm/code_kernel.py
```
IPYKERNEL = os.environ.get('IPYKERNEL', 'chatglm3')
```

4. 启动后，发送 #帮助 可以查看 模式和常用指令
