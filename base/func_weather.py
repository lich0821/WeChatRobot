import requests, json
import logging

class Weather:
    def __init__(self, city_code: str) -> None:
        self.city_code = city_code
        self.LOG = logging.getLogger("Weather")

    def get_weather(self) -> str:
        # api地址
        url = 'http://t.weather.sojson.com/api/weather/city/'

        # 网络请求，传入请求api+城市代码
        self.LOG.info(f"获取天气: {url + str(self.city_code)}")
        try:
            response = requests.get(url + str(self.city_code))
            self.LOG.info(f"获取天气成功: {str(response.text)}")
        except Exception as e:
            self.LOG.error(f"获取天气失败: {str(e)}")
            return "由于网络原因，获取天气失败"

        # 将数据以json形式返回，这个d就是返回的json数据
        d = response.json()

        # 当返回状态码为200，输出天气状况
        if(d['status'] == 200):
            return f"城市：{d['cityInfo']['parent']}/{d['cityInfo']['city']}\n时间：{d['time']} {d['data']['forecast'][0]['week']}\n温度：{d['data']['forecast'][0]['high']} {d['data']['forecast'][0]['low']}\n天气：{d['data']['forecast'][0]['type']}"
        else:
            return "获取天气失败"

if __name__ == "__main__":
    w = Weather("101010100")  # 北京
    print(w.get_weather())  # 北京
