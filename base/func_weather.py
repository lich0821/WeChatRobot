import requests, json

def get_weather(city: str) -> str:
    # api地址
    url = 'http://t.weather.sojson.com/api/weather/city/'

    # 读取json文件
    f = open('C:\\Users\\PengHeng\\Documents\\#appCode\\Python\\WeChatRobot\\base\\city.json', 'rb')

    # 使用json模块的load方法加载json数据，返回一个字典
    cities = json.load(f)

    # 通过城市的中文获取城市代码
    city = cities.get(city)

    # 网络请求，传入请求api+城市代码
    response = requests.get(url + city)

    # 将数据以json形式返回，这个d就是返回的json数据
    d = response.json()

    # 当返回状态码为200，输出天气状况
    if(d['status'] == 200):
        return f"城市：{d['cityInfo']['parent']} {d['cityInfo']['city']}\n时间：{d['time']} {d['data']['forecast'][0]['week']}\n温度：{d['data']['forecast'][0]['high']} {d['data']['forecast'][0]['low']}\n天气：{d['data']['forecast'][0]['type']}"
    else:
        return "获取天气失败"

if __name__ == "__main__":
    print(get_weather('北京'))
