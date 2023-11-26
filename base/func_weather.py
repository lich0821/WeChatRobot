import requests

class Weather(object):
    def __init__(self, loc, key) -> None:
        self.url = "https://www.tianqiapi.com/api/?version=v1&appid=23035388&appsecret=5w8qXQ4X&city=北京"    
        self.headers = {
            "user-agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.42'
        }
        self.loc = loc
        self.weather_key = key

    def get_weather(self):
        url_3d = f'https://devapi.qweather.com/v7/weather/3d?location={self.loc}&key={self.weather_key}'
        url_now = f'https://devapi.qweather.com/v7/weather/now?location={self.loc}&key={self.weather_key}'
        res_3d = requests.get(url=url_3d, headers=self.headers).json()
        res_now = requests.get(url=url_now, headers=self.headers).json()
        weather_3d = res_3d["daily"][0]
        weather_now = res_now["now"]
        day_w = weather_3d['textDay']
        night_w = weather_3d['textNight']
        if day_w != night_w:
            weather = weather_3d['textDay'] + '转' + weather_3d['textNight']
        else:
            weather = weather_3d['textDay']
        # return weather, weather_now['temp'], weather_3d['tempMax'], weather_3d['tempMin'], weather_3d['sunrise'], weather_3d['sunset']
        return f'今天天气:{weather}\n当前温度:{weather_now["temp"]}℃\n最高温度:{weather_3d["tempMax"]}℃\n最低温度:{weather_3d["tempMin"]}℃\n日出时间:{weather_3d["sunrise"]}\n日落时间:{weather_3d["sunset"]}'

if __name__ == "__main__":

    loc = ""
    key = ""
    weather = Weather(loc, key)
    print(weather.get_weather())
    