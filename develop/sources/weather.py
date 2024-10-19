#TODO
# 기상청 api 받아오기 (V)
# 기상청 이외의 날씨 api 받아오기 (X)
# api key / token 보안 처리 (V)
# 선형회귀 알고리즘 (X)
# 오차 보정 확인 (X)
# main.py와 통합 (V)
import sys
import os

# Append the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime
import xmltodict
import apikeys #api키 보안처리 {변경금지}

def get_current_date_string():
    current_date = datetime.now().date()
    return current_date.strftime("%Y%m%d")

def get_current_hour_string():
    now = datetime.now()
    if now.minute<45: # base_time와 base_date 구하는 함수
        if now.hour==0:
            base_time = "2330"
        else:
            pre_hour = now.hour-1
            if pre_hour<10:
                base_time = "0" + str(pre_hour) + "30"
            else:
                base_time = str(pre_hour) + "30"
    else:
        if now.hour < 10:
            base_time = "0" + str(now.hour) + "30"
        else:
            base_time = str(now.hour) + "30"

    return base_time

keys = apikeys.KEY
url = 'http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst'
params ={'serviceKey' : keys, 
         'pageNo' : '1', 
         'numOfRows' : '1000', 
         'dataType' : 'XML', 
         'base_date' : get_current_date_string(), 
         'base_time' : get_current_hour_string(), 
         'nx' : '81', 
         'ny' : '75' }

url_pm = 'https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty'
params_pm ={'serviceKey' : keys, 
         'returnType' : 'XML', 
         'numOfRows' : '100', 
         'pageNo' : '1', 
         'sidoName' : '경남', 
         'ver' : '1.0'
        }

def forecast():
    # 값 요청 (웹 브라우저 서버에서 요청 - url주소와 파라미터)
    res = requests.get(url, params = params)
    if res.status_code != 200:
        print(f"응답 실패! {res.status_code}")
        return None


    #XML -> 딕셔너리
    xml_data = res.text
    dict_data = xmltodict.parse(xml_data)

    #값 가져오기
    weather_data = dict()
    for item in dict_data.get('response', {}).get('body', {}).get('items', {}).get('item', []):
        # 기온
        if item['category'] == 'T1H':
            weather_data['tmp'] = item['fcstValue']
        # 습도
        if item['category'] == 'REH':
            weather_data['hum'] = item['fcstValue']
        # 하늘상태: 맑음(1) 구름많은(3) 흐림(4)
        if item['category'] == 'SKY':
            weather_data['sky'] = item['fcstValue']
        # 강수형태: 없음(0), 비(1), 비/눈(2), 눈(3), 빗방울(5), 빗방울눈날림(6), 눈날림(7)
        if item['category'] == 'PTY':
            weather_data['sky2'] = item['fcstValue']

    return weather_data

def proc_weather():
    dict_sky = forecast()

    str_sky = "진주시 가호동 "
    if dict_sky['sky'] != None or dict_sky['sky2'] != None:
        str_sky = str_sky + "날씨 : "
        if dict_sky['sky2'] == '0':
            if dict_sky['sky'] == '1':
                str_sky = str_sky + "맑음"
            elif dict_sky['sky'] == '3':
                str_sky = str_sky + "구름많음"
            elif dict_sky['sky'] == '4':
                str_sky = str_sky + "흐림"
        elif dict_sky['sky2'] == '1':
            str_sky = str_sky + "비"
        elif dict_sky['sky2'] == '2':
            str_sky = str_sky + "비와 눈"
        elif dict_sky['sky2'] == '3':
            str_sky = str_sky + "눈"
        elif dict_sky['sky2'] == '5':
            str_sky = str_sky + "빗방울이 떨어짐"
        elif dict_sky['sky2'] == '6':
            str_sky = str_sky + "빗방울과 눈이 날림"
        elif dict_sky['sky2'] == '7':
            str_sky = str_sky + "눈이 날림"
        str_sky = str_sky + " / "
    if dict_sky['tmp'] != None:
        str_sky = str_sky + "온도 : " + dict_sky['tmp'] + 'ºC / '
    if dict_sky['hum'] != None:
        str_sky = str_sky + "습도 : " + dict_sky['hum'] + '% / '
    pm25 = pm()
    str_sky = str_sky + "미세먼지 농도 : " + pm25

    return str_sky

def pm():
    # 값 요청 (웹 브라우저 서버에서 요청 - url주소와 파라미터)
    res = requests.get(url_pm, params = params_pm)

    #XML -> 딕셔너리
    xml_data = res.text
    dict_data = xmltodict.parse(xml_data)

    pm_data = dict()
    pm_data = dict_data.get('response', {}).get('body', {}).get('items', {}).get('item', [])

    for item in pm_data:
            if item.get('stationName') == '상대동(진주)':
                pm25_value = item.get('pm25Value')
                #print(f"PM2.5 Value for 상대동(진주): {pm25_value}")

                return str(pm25_value)
    else:
        print(f"Request failed with status code {res.status_code}")

def fetch_external_weather():
    #dict_sky = forecast()
    #pm25 = pm()
    try:
        weather_data = {
            'temperature': 16,#dict_sky['tmp'],
            'humidity': 50,#dict_sky['hum'],
            'pm_25': 44
        }
        return weather_data
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None
