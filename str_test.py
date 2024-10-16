야호 = "80,24,40,26,Low Light,Heavy Rain,6.0,Comfort,Not Comfort"
야호10분 = "10avg,80,24,40,26,Low Light,Heavy Rain,6.0,6"

sensor_data = {
    'humidity_1': '50.0',
    'temperature_1': '26',
    'humidity_2': 'N/A',
    'temperature_2': '24.0',
    'light_level': '400',
    'rain_level': 'N/A',
    'pm2_5': '81',
    'discomfort_index_1': 'N/A',
    'discomfort_index_2': 'N/A',
    'door_status': 'door Closed',
    'status': ''
}

def process_sensor_data(data):
    """실시간 센서 데이터를 가공하여 전역 변수에 저장."""
    global sensor_data
    try: #외부습도/외부온도/실내습도/실내온도/조도 (밝기 문자열)/비(문자열/pm2.5 값/실외불쾌지수/실내불쾌지수/ 실내불쾌지수 상태(문자열)
        #lines = data.split('\n')
        t = data.split(',')
        
        sensor_data['humidity_1'] = t[0]
        sensor_data['temperature_1'] = t[1]
        sensor_data['humidity_2'] = t[2]
        sensor_data['temperature_2'] = t[3]
        sensor_data['light_level'] = t[4]
        sensor_data['rain_level'] = t[5]
        sensor_data['pm2_5'] = t[6]
        sensor_data['discomfort_index_1'] = t[7]
        sensor_data['discomfort_index_2'] = t[8]
    except Exception as e:
        print(f"데이터 처리 오류: {e}")

def process_10min_data(data):
    """10분 경과 시 수신되는 데이터를 가공하여 전역 변수에 저장."""
    global sensor_data
    try: #외부습도/외부온도/실내습도/실내온도/조도 (밝기 문자열)/비(문자열/pm2.5 값/실외불쾌지수/실내불쾌지수/ 실내불쾌지수 상태(문자열)
        #lines = data.split('\n')
        t = data.split(',')
        
        sensor_data['humidity_1'] = t[1]
        sensor_data['temperature_1'] = t[2]
        sensor_data['humidity_2'] = t[3]
        sensor_data['temperature_2'] = t[4]
        sensor_data['light_level'] = t[5]
        sensor_data['rain_level'] = t[6]
        sensor_data['pm2_5'] = t[7]

        if(len(t) < 8):
            pass
        else:
            sensor_data['door_status'] = t[8]
            if (t[8] == '5'):
                #door_control('open')
                프린트("열림")
                sensor_data['door_status'] = 'door Opened'
            elif (t[8] == '6'):
                #door_control('close')
                프린트("닫힘")
                sensor_data['door_status'] = 'door Closed'
            elif (t[8] == '7'):
                프린트("중립")
                sensor_data['door_status'] = 'door Neutral'
    except Exception as e:
        print(f"10분 데이터 처리 오류: {e}")


def 프린트(글자):
    print(글자)

process_sensor_data(야호)
process_10min_data(야호10분)

프린트(sensor_data)