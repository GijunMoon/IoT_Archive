from flask import Flask, request, render_template, redirect, url_for, jsonify, Response
import serial
import threading
import time
import asyncio
from datetime import datetime
from threading import Lock
import sources.weather as weather
import sources.read_csv as CAMdata
import sources.camera as CAMwrite
import sources.actuator as actuator
import sources.mse as mse


SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
TIMEOUT = 1

STOP  = 0
OPEN  = 1
CLOSE = 2

CH1 = 0

# 시리얼 포트를 전역적으로 엽니다.
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)

# 전역 변수로 센서 데이터를 저장하기 위한 딕셔너리
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

updated_settings = {
    'humidity': '80',
    'hot_temperature': '26',
    'cold_temperature': '24',
    'indoor_light': '40',
    'pm': '150'
}

isSet = False

open_time = None
close_time = None

# Lock 객체 생성
data_lock = Lock()

def serial_read():
    """Arduino에서 데이터를 읽어와 콘솔에 출력하고 처리하는 함수."""
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8').strip()
            print(f"Arduino에서 받은 데이터: {data}")
            with data_lock:
                if "10avg" in data:
                    process_10min_data(data)
                else:
                    process_sensor_data(data)
                if "Received value: 1" in data:
                    serial_write(data='1')
                    time.sleep(2)
                    serial_write(data='1')

def process_sensor_data(data):
    """실시간 센서 데이터를 가공하여 전역 변수에 저장."""
    global sensor_data
    try: #외부습도/외부온도/실내습도/실내온도/조도 (밝기 문자열)/비(문자열/pm2.5 값/실외불쾌지수/실내불쾌지수/ 실내불쾌지수 상태(문자열)
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
        
        print(sensor_data)
    except Exception as e:
        pass
        #print(f"데이터 처리 오류: {e}")

def process_10min_data(data):
    """10분 경과 시 수신되는 데이터를 가공하여 전역 변수에 저장."""
    global sensor_data
    try: #외부습도/외부온도/실내습도/실내온도/조도 (밝기 문자열)/비(문자열/pm2.5 값/실외불쾌지수/실내불쾌지수/ 실내불쾌지수 상태(문자열)
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
            sensor_data['door_status'] = t[10]
            if (t[10] == '5'):
                door_control('open')
                print("open")
                sensor_data['door_status'] = 'door Opened'
            elif (t[10] == '6'):
                door_control('close')
                print("close")
                sensor_data['door_status'] = 'door Closed'
            elif (t[10] == '7'):
                print("neutral")
                sensor_data['door_status'] = 'door Neutral'
    except Exception as e:
        print(f"10분 데이터 처리 오류: {e}")


# 백그라운드 스레드에서 시리얼 읽기 함수 시작
thread = threading.Thread(target=serial_read, daemon=True)
thread.start()

def door_control(param):
    if param == 'open':
        serial_write(data='0')
        time.sleep(2)
        serial_write(data='0')
        time.sleep(3)
        actuator.setMotor(CH1, 100, OPEN)
        time.sleep(8)
        serial_write(data='1')
    elif param == 'close':
        serial_write(data='0')
        time.sleep(2)
        serial_write(data='0')
        time.sleep(3)
        actuator.setMotor(CH1, 100, CLOSE)
        time.sleep(8)
        serial_write(data='1')

app = Flask(__name__, template_folder='templates')

@app.route('/', methods=['GET', 'POST'])
def index():
    global sensor_data
    global updated_settings

    if request.method == 'POST':
        button_action = request.form.get('button')
        if button_action == 'Y':
            return render_template('setting.html')
        elif button_action == 'N':
            serial_write(data='n')
            return render_template('main.html')
        elif button_action == 'OPEN':
            door_control('open')
            with data_lock:
                sensor_data['door_status'] = "door Opened"
        elif button_action == 'CLOSE':
            door_control('close')
            with data_lock:
                sensor_data['door_status'] = "door Closed"
        elif button_action == 'WEATHER':
            weather_data = weather.proc_weather()
            print(weather_data)
            return jsonify(weather_data)
        elif button_action == 'CAMdata':
            print(CAMdata.view_csv())
            cam_data = CAMdata.view_csv()
            return jsonify(cam_data)
        elif button_action == 'CAMwrite':
            CAMwrite.startCAM()
            
        actuator.cleanup_gpio()

        return jsonify(success=True)

    updated_settings = {
        'humidity': request.args.get('humidity', '80'),
        'hot_temperature': request.args.get('hot_temperature', '26'),
        'cold_temperature': request.args.get('cold_temperature', '24'),
        'indoor_light': request.args.get('indoor_light', '40'),
        'pm': request.args.get('pm', '150')
    }
    return render_template('main.html', updated_settings=updated_settings)

@app.route('/settings', methods=['POST'])
def settings():
    global open_time, close_time
    global updated_settings
    global isSet

    # Fetch form data and print for debugging
    humidity = request.form.get('humidity')
    hot_temperature = request.form.get('hot_temperature')
    cold_temperature = request.form.get('cold_temperature')
    indoor_light = request.form.get('indoor_light')
    pm = request.form.get('pm')
    
    open_time = request.form.get('open_time')
    close_time = request.form.get('close_time')
    
    if request.method == 'POST':
        button_action = request.form.get('button')
        if button_action == 'Y':
            return render_template('setting.html')

    print(f"Received settings - Humidity: {humidity}, Hot Temp: {hot_temperature}, Cold Temp: {cold_temperature}, Indoor Light: {indoor_light}, PM: {pm}, Open Time: {open_time}, Close Time: {close_time}")

    try:
        if isSet == False:
            serial_write(data='y')
            time.sleep(10)  # Ensure enough time for processing
            serial_write(data=humidity)
            time.sleep(2)
            serial_write(data=hot_temperature)
            time.sleep(2)
            serial_write(data=cold_temperature)
            time.sleep(2)
        
            pm25 = calculate_pm25(int(pm))
            serial_write(data=str(pm25))
            time.sleep(2)

            serial_write(data=indoor_light)
            time.sleep(1.5)
            isSet = True
        else:
            serial_write(data='y')
            time.sleep(5)
            serial_write(data='y')
            time.sleep(10)  # Ensure enough time for processing
            serial_write(data=humidity)
            time.sleep(2)
            serial_write(data=hot_temperature)
            time.sleep(2)
            serial_write(data=cold_temperature)
            time.sleep(2)
        
            pm25 = calculate_pm25(int(pm))
            serial_write(data=str(pm25))
            time.sleep(2)

            serial_write(data=indoor_light)
            time.sleep(1.5)
            isSet = True			
    except Exception as e:
        print(f"Serial communication error: {e}")

    # Update settings
    updated_settings = {
        'humidity': humidity,
        'hot_temperature': hot_temperature,
        'cold_temperature': cold_temperature,
        'indoor_light': indoor_light,
        'pm': pm,
        'open_time': open_time,
        'close_time': close_time
    }

    print(f"Updated settings - {updated_settings}")

    # Fetch latest sensor data after settings update
    #sensor_data = get_sensor_data().json

    return render_template('main.html', updated_settings=updated_settings)

@app.route('/calibrate_sensor_data', methods=['GET'])
def get_calibrated_sensor_data():
    external_weather = weather.fetch_external_weather()
    
    with data_lock:
        calibrated_data = mse.calibrate_sensor_data(sensor_data, external_weather)
        
    return jsonify(calibrated_data)


def calculate_pm25(pm):
    """PM 값을 기준으로 PM2.5 범위를 계산."""
    if pm < 20:
        return 20
    elif pm < 80:
        return 50
    elif pm < 160:
        return 100
    else:
        return 160

def serial_write(data=None):
    """Arduino로 데이터를 전송하는 함수."""
    if data is not None:
        print(f"Arduino로 전송: {data}")
        ser.write(data.encode())

@app.route('/get_weather_data', methods=['GET'])
def get_weather_data():
    weather_data = weather.proc_weather()
    return jsonify(weather_data)

@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    """현재 메모리에 저장된 센서 데이터를 반환하는 엔드포인트."""
    with data_lock:
        return jsonify(sensor_data)
    
@app.route('/get_setting_data', methods=['GET'])
def get_setting_data():
    """현재 메모리에 저장된 세팅 데이터를 반환하는 엔드포인트."""
    with data_lock:
        return jsonify(updated_settings)

def check_reservation_times():
    """예약된 시간에 맞춰 창문을 여닫는 함수."""
    global open_time, close_time
    current_time = datetime.now().strftime("%H:%M")
    
    if open_time and current_time == open_time:
        print(f"PDLC 창문을 {open_time}에 열었습니다.")
        serial_write(data="3")

    if close_time and current_time == close_time:
        print(f"PDLC 창문을 {close_time}에 닫았습니다.")
        serial_write(data="4")

def periodic_check():
    while True:
        check_reservation_times()
        time.sleep(60)

def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame is None:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(CAMwrite.VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_cam_data')
def detect_data():
    data = CAMdata.view_csv()
    return jsonify(data)

if __name__ == '__main__':
    reservation_thread = threading.Thread(target=periodic_check, daemon=True)
    reservation_thread.start()
    app.run(host='0.0.0.0')
