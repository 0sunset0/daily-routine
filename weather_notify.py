import urllib.request
import json
import os
from datetime import datetime
import pytz

API_KEY = os.environ["OPENWEATHER_API_KEY"]
SLACK_WEBHOOK = os.environ["SLACK_WEBHOOK"]
RAIN_THRESHOLD = 30
KST = pytz.timezone("Asia/Seoul")

LAT, LON = 36.019, 129.343

url = (
    f"https://api.openweathermap.org/data/2.5/forecast"
    f"?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric&lang=kr&cnt=8"
)
req = urllib.request.Request(url, headers={"User-Agent": "WeatherBot/1.0"})
data = json.loads(urllib.request.urlopen(req, timeout=15).read())

today_str = datetime.now(KST).strftime("%Y-%m-%d")
items = [i for i in data["list"] if i["dt_txt"].startswith(today_str)]

if not items:
    items = data["list"][:4]

max_temp = max(i["main"]["temp_max"] for i in items)
min_temp = min(i["main"]["temp_min"] for i in items)
desc = items[0]["weather"][0]["description"]

def rain_chance(item):
    return int(item.get("pop", 0) * 100)

morning = [i for i in items if "06:00" <= i["dt_txt"][11:] <= "11:59"]
afternoon = [i for i in items if "12:00" <= i["dt_txt"][11:] <= "18:00"]

morning_rain = any(rain_chance(i) >= RAIN_THRESHOLD for i in morning)
afternoon_rain = any(rain_chance(i) >= RAIN_THRESHOLD for i in afternoon)

if morning_rain:
    umbrella_msg = "☔ *오전부터 비가 예상됩니다! 우산을 꼭 챙기세요.*"
elif afternoon_rain:
    umbrella_msg = "🌂 *오전은 괜찮지만 오후에 비가 옵니다. 우산을 챙겨가세요!*"
else:
    umbrella_msg = "☀️ 오늘은 비 소식이 없어요. 우산은 필요 없습니다!"

rain_parts = [
    f"{i['dt_txt'][11:16]} {rain_chance(i)}%"
    for i in items if rain_chance(i) > 0
]
rain_summary = " | ".join(rain_parts) if rain_parts else "없음"

message = (
    f"🌤 *포항 오늘 날씨* ({today_str})\n{umbrella_msg}\n\n"
    f"🌡 기온: {min_temp:.0f}℃ ~ {max_temp:.0f}℃\n"
    f"☁️ 날씨: {desc}\n"
    f"🌧 시간별 강수확률: {rain_summary}"
)

payload = json.dumps({"text": message}).encode()
req = urllib.request.Request(
    SLACK_WEBHOOK,
    data=payload,
    headers={"Content-Type": "application/json"},
)
urllib.request.urlopen(req, timeout=15)
print("Slack 전송 완료!")
print(message)
