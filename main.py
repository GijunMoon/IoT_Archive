from flask import Flask, request, render_template, redirect, url_for, jsonify
import serial
import threading #비동기 작업 (타이머 새로고침)
import time
import sources.actuator as actuator #액추에이터 컨트롤 코드
import sources.weather as weather #날씨 api 코드
#카메라 및 YOLO
import sources.read_csv as CAMdata
import sources.write_csv as CAMwrite

SERIAL_PORT = 'COM20'
## pc환경에서 test : COM 00
## 라즈베리파이 환경에서 test : /dev/ttyACM0

BAUD_RATE = 9600
TIMEOUT = 1

# 모터 상태
STOP  = 0
OPEN  = 1
CLOSE = 2

# 모터 채널
CH1 = 0

# 시리얼 포트를 전역적으로 엽니다.
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)

# 전역 변수로 센서 데이터를 저장하기 위한 딕셔너리
sensor_data = {
    'humidity_1': 'N/A',
    'temperature_1': 'N/A',
    'humidity_2': 'N/A',
    'temperature_2': 'N/A',
    'light_level': 'N/A',
    'rain_level': 'N/A',
    'pm2_5': 'N/A',
    'discomfort_index_1': 'N/A',
    'discomfort_index_2': 'N/A',
    'door_status': 'door Closed',  # 문 상태 추가
    'status': ''
}

# 예약 시간 전역 변수
open_time = None
close_time = None

def serial_read():
    """Arduino에서 데이터를 읽어와 콘솔에 출력하고 처리하는 함수."""
    while True:
        if ser.in_waiting > 0:  # 시리얼 입력 대기열에 데이터가 있는 경우
            data = ser.readline().decode('utf-8').strip()
            print(f"Arduino에서 받은 데이터: {data}")
            process_sensor_data(data)

def process_sensor_data(data):
    """시리얼 데이터를 가공하여 전역 변수에 저장."""
    global sensor_data
    try:
        # 여러 줄의 데이터를 한 줄씩 처리
        lines = data.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("Humidity 1:"):
                sensor_data['humidity_1'] = line.split(':')[1].strip()
            elif line.startswith("Temperature 1:"):
                sensor_data['temperature_1'] = line.split(':')[1].strip()
            elif line.startswith("Humidity 2:"):
                sensor_data['humidity_2'] = line.split(':')[1].strip()
            elif line.startswith("Temperature 2:"):
                sensor_data['temperature_2'] = line.split(':')[1].strip()
            elif line.startswith("Light Level:"):
                sensor_data['light_level'] = line.split(':')[1].strip()
            elif line.startswith("Rain Level:"):
                sensor_data['rain_level'] = line.split(':')[1].strip()
            elif line.startswith("PM2.5 Level:"):
                sensor_data['pm2_5'] = line.split(':')[1].strip()
            elif line.startswith("Discomfort Index 1:"):
                sensor_data['discomfort_index_1'] = line.split(':')[1].strip()
            elif line.startswith("Discomfort Index 2:"):
                sensor_data['discomfort_index_2'] = line.split(':')[1].strip()
            elif line.startswith("Door: Opened"):
                sensor_data['door_status'] = "door Opened"
            elif line.startswith("Door: Closed"):
                sensor_data['door_status'] = "door Closed"
            elif line.startswith("Door: Netural"):
                sensor_data['door_status'] = "door Netural"
            elif "comfortable" in line or "good" in line or "Rain" in line or "Dark" in line:
                sensor_data['status'] = line
    except Exception as e:
        print(f"데이터 처리 오류: {e}")

# 백그라운드 스레드에서 시리얼 읽기 함수 시작
thread = threading.Thread(target=serial_read, daemon=True)
thread.start()

app = Flask(__name__, template_folder='templates')

@app.route('/', methods=['GET', 'POST'])
def index():
    global sensor_data

    if request.method == 'POST':
        button_action = request.form.get('button')
        if button_action == 'Y':
            return render_template('setting.html')
        elif button_action == 'N':
            return render_template('main.html')
        elif button_action == 'OPEN':
            serial_write(data='0')
            actuator.setMotor(CH1, 100, OPEN)
            time.sleep(8)
            serial_write(data='1')
            #serial_write(data='door Opened')
            sensor_data['door_status'] = "door Opened"
        elif button_action == 'CLOSE':
            serial_write(data='0')
            actuator.setMotor(CH1, 100, CLOSE)
            time.sleep(8)
            serial_write(data='1')
            #serial_write(data='door Closed')
            sensor_data['door_status'] = "door Closed"
        elif button_action == 'WEATHER':
            print(weather.proc_weather())
        elif button_action == 'CAMdata':
            print(CAMdata.view_csv())
        elif button_action == 'CAMwrite':
            CAMwrite.startCAM()
    
    updated_settings = {
        'humidity': request.args.get('humidity', ''),
        'hot_temperature': request.args.get('hot_temperature', ''),
        'cold_temperature': request.args.get('cold_temperature', ''),
        'indoor_light': request.args.get('indoor_light', ''),
        'pm': request.args.get('pm', '')
    }
    return render_template('main.html', updated_settings=updated_settings)

@app.route('/settings', methods=['POST'])
def settings():
    global open_time, close_time

    humidity = request.form.get('humidity')
    hot_temperature = request.form.get('hot_temperature')
    cold_temperature = request.form.get('cold_temperature')
    indoor_light = request.form.get('indoor_light')
    pm = request.form.get('pm')
    
    # 예약 시간 받기
    open_time = request.form.get('open_time')
    close_time = request.form.get('close_time')

    print(f"Received settings - Humidity: {humidity}, Hot Temp: {hot_temperature}, Cold Temp: {cold_temperature}, Indoor Light: {indoor_light}, PM: {pm}, Open Time: {open_time}, Close Time: {close_time}")

    # 시리얼로 설정 값 보내기
    serial_write(data='y')
    time.sleep(1.5)
    serial_write(data=humidity)
    time.sleep(1.5)
    serial_write(data=hot_temperature)
    time.sleep(1.5)
    serial_write(data=cold_temperature)
    time.sleep(1.5)
    
    # PM 값에 따른 PM2.5 범위 전송
    pm25 = calculate_pm25(int(pm))
    serial_write(data=str(pm25))
    time.sleep(1.5)

    serial_write(data=indoor_light)
    time.sleep(1.5)

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
    return redirect(url_for('index', **updated_settings))

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

@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    """현재 메모리에 저장된 센서 데이터를 반환하는 엔드포인트."""
    return jsonify(sensor_data)

def check_reservation_times():
    """예약된 시간에 맞춰 창문을 여닫는 함수."""
    global open_time, close_time
    current_time = time.strftime("%H:%M")
    
    if open_time and current_time == open_time:
        # PDLC 창문 열기
        print(f"PDLC 창문을 {open_time}에 열었습니다.")
        serial_write(data="3")

    if close_time and current_time == close_time:
        # PDLC 창문 닫기
        print(f"PDLC 창문을 {close_time}에 닫았습니다.")
        serial_write(data="4")

# 주기적으로 예약 확인
def periodic_check():
    while True:
        check_reservation_times()
        time.sleep(60)  # 1분 간격으로 예약 시간 확인

if __name__ == '__main__':
    # 예약 확인을 위한 백그라운드 작업 시작
    reservation_thread = threading.Thread(target=periodic_check)
    reservation_thread.start()

    # Flask 서버 실행
    app.run(host='0.0.0.0')
