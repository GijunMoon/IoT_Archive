from flask import Flask, request, render_template
import serial
import time

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
            return render_template('settings.html')
        elif button_action == 'N':
            serial_data = serial_read()
            return render_template('main.html', serial_data=serial_data)
    return render_template('main.html')

@app.route('/settings', methods=['POST'])
def settings():
    if request.method == 'POST':
        humidity = request.form.get('humidity')
        hot_temperature = request.form.get('hot_temperature')
        cold_temperature = request.form.get('cold_temperature')
        indoor_light = request.form.get('indoor_light')
        pm = request.form.get('pm')

        serial_write(data='y')

        # Arduino에 설정값 전송
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
        return render_template('main.html', serial_data=f"Settings updated: {settings_data}")

if __name__ == '__main__':
    app.run(host='0.0.0.0')