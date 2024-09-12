from flask import Flask, request, render_template, redirect, url_for
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
            return render_template('setting.html')
        elif button_action == 'N':
            serial_data = serial_read()
            return render_template('main.html', serial_data=serial_data)
    # Fetch updated settings from query parameters if present
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

if __name__ == '__main__':
    app.run(host='0.0.0.0')
