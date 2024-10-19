import os, sys
import time
import serial
import csv
import pandas as pd
from collections import defaultdict
from flask import Flask, request, render_template, redirect, url_for

SERIAL_PORT = '/dev/ttyACM0'
BAUD_RATE = 9600
TIMEOUT = 1

# Open the serial port globally
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT)

def serial_read():
    print("Read Data from Arduino...")
    return ser.readline().decode('utf-8').strip()

def serial_write(data=None):
    if data is not None:
        print(f"Print {data} to Arduino...")
        ser.write(data.encode())

app = Flask(__name__, template_folder='templates')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        button_action = request.form.get('button')
        if button_action == 'Y':
            return render_template('setting.html')
        elif button_action == 'N':
            serial_data = serial_read()
            return render_template('main2.html', serial_data=serial_data)
    # Fetch updated settings from query parameters if present
    updated_settings = {
        'humidity': request.args.get('humidity', ''),
        'hot_temperature': request.args.get('hot_temperature', ''),
        'cold_temperature': request.args.get('cold_temperature', ''),
        'indoor_light': request.args.get('indoor_light', ''),
        'pm': request.args.get('pm', '')
    }
    return render_template('main2.html', updated_settings=updated_settings)

@app.route('/settings', methods=['POST'])
def settings():
    # Collect settings from form
    humidity = request.form.get('humidity')
    hot_temperature = request.form.get('hot_temperature')
    cold_temperature = request.form.get('cold_temperature')
    indoor_light = request.form.get('indoor_light')
    pm = request.form.get('pm')

    # Debug prints to check received values
    print(f"Received settings - Humidity: {humidity}, Hot Temp: {hot_temperature}, Cold Temp: {cold_temperature}, Indoor Light: {indoor_light}, PM: {pm}")

    # Write to Arduino if needed
    serial_write(data='y')

    # Send settings to Arduino
    settings_data = f"H:{humidity},T_H:{hot_temperature},T_C:{cold_temperature},L:{indoor_light},PM:{pm}"
    time.sleep(1.5)
    serial_write(data=humidity)
    time.sleep(1.5)
    serial_write(data=hot_temperature)
    time.sleep(1.5)
    serial_write(data=cold_temperature)
    time.sleep(1.5)
    serial_write(data=indoor_light)
    time.sleep(1.5)
    serial_write(data=pm)
    time.sleep(0.5)

    # Prepare updated settings for main.html
    updated_settings = {
        'humidity': humidity,
        'hot_temperature': hot_temperature,
        'cold_temperature': cold_temperature,
        'indoor_light': indoor_light,
        'pm': pm
    }

    # Debug print to check if settings are prepared correctly
    print(f"Updated settings - {updated_settings}")

    # Redirect to index route with updated settings as query parameters
    return redirect(url_for('index', **updated_settings))
    

@app.route('/view_csv')
def view_csv():
    csv_path = '/home/user/detections.csv'        # CSV 파일이 존재하는지 확인
    if not os.path.isfile(csv_path):
        return f"CSV 파일이 {csv_path}에 존재하지 않습니다."
    try:        # pandas로 CSV 파일 읽기
        df = pd.read_csv(csv_path, header=None, names=['name','confidence'],skiprows=1)
        # CSV 파일의 첫 번째 열: 'name' (인식된 객체)        # 두 번째 열: 'confidence' (인식률)
        if 'name' not in df.columns or 'confidence' not in df.columns:
            return "CSV 파일 형식이 올바르지 않습니다. 'name'과 'confidence' 열이 필요합니다."
        # HTML 테이블로 변환하여 웹페이지에 표시
        data = df.to_html(classes='table table-striped', index=False)
        return render_template('view2.html', table=data)
    except Exception as e:        # 에러가 발생한 경우 에러 메시지 반환
        return f"데이터를 불러오는 중 오류가 발생했습니다: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

