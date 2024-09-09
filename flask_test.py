from flask import Flask, request, render_template
import serial

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
        if button_action == 'send':
            serial_write(data='1')
        elif button_action == 'get':
            serial_data = serial_read()
            print(f"Data from Arduino: {serial_data}")
            return render_template('main.html', serial_data=serial_data)
    return render_template('main.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0')
