from flask import Flask, request, render_template, redirect, url_for, jsonify
import serial
import threading
import time

SERIAL_PORT = 'COM20'
BAUD_RATE = 9600
TIMEOUT = 1

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
    'status': ''
}

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
    if request.method == 'POST':
        button_action = request.form.get('button')
        if button_action == 'Y':
            return render_template('setting.html')
        elif button_action == 'N':
            return render_template('main.html')
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
    humidity = request.form.get('humidity')
    hot_temperature = request.form.get('hot_temperature')
    cold_temperature = request.form.get('cold_temperature')
    indoor_light = request.form.get('indoor_light')
    pm = request.form.get('pm')
    pm25 = 0

    print(f"Received settings - Humidity: {humidity}, Hot Temp: {hot_temperature}, Cold Temp: {cold_temperature}, Indoor Light: {indoor_light}, PM: {pm}")

    serial_write(data='y')
    settings_data = f"H:{humidity},T_H:{hot_temperature},T_C:{cold_temperature},L:{indoor_light},PM:{pm}"
    time.sleep(1.5)
    serial_write(data=humidity)
    time.sleep(1.5)
    serial_write(data=hot_temperature)
    time.sleep(1.5)
    serial_write(data=cold_temperature)
    time.sleep(1.5)

    if (int(pm) >= 0):
        pm25 = 20
    elif (int(pm) >= 20):
        pm25 = 50
    elif (int(pm) >= 80):
        pm25 = 100
    elif (int(pm) >= 160):
        pm25 = 160
    
    serial_write(data=str(pm25))
    time.sleep(1.5)
    serial_write(data=indoor_light)
    time.sleep(1.5)

    updated_settings = {
        'humidity': humidity,
        'hot_temperature': hot_temperature,
        'cold_temperature': cold_temperature,
        'indoor_light': indoor_light,
        'pm': pm
    }

    print(f"Updated settings - {updated_settings}")

    return redirect(url_for('index', **updated_settings))

def serial_write(data=None):
    """Arduino로 데이터를 전송하는 함수."""
    if data is not None:
        print(f"Arduino로 전송: {data}")
        ser.write(data.encode())

@app.route('/get_sensor_data', methods=['GET'])
def get_sensor_data():
    """현재 메모리에 저장된 센서 데이터를 반환하는 엔드포인트."""
    return jsonify(sensor_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
