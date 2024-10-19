import RPi.GPIO as GPIO
import time

# Motor states
STOP = 0
OPEN = 1
CLOSE = 2

# Motor channel
CH1 = 0

# GPIO pin definitions
ENA = 21  # PWM pin
IN1 = 16  # Motor control pin 1
IN2 = 20  # Motor control pin 2

# Initialization flag
gpio_initialized = False

# Disable GPIO warnings
GPIO.setwarnings(False)

def initialize_gpio():
    global gpio_initialized
    if not gpio_initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(ENA, GPIO.OUT)
        GPIO.setup(IN1, GPIO.OUT)
        GPIO.setup(IN2, GPIO.OUT)
        gpio_initialized = True

# Motor handler
pwm = None

def setup_motor():
    global pwm
    if not gpio_initialized:
        initialize_gpio()
    if pwm is None:
        pwm = GPIO.PWM(ENA, 100)  # 100Hz PWM
        pwm.start(0)  # Initial PWM duty cycle 0%

def setMotorControl(pwm, INA, INB, speed, stat):
    pwm.ChangeDutyCycle(speed)
    if stat == OPEN:
        GPIO.output(INA, GPIO.HIGH)
        GPIO.output(INB, GPIO.LOW)
    elif stat == CLOSE:
        GPIO.output(INA, GPIO.LOW)
        GPIO.output(INB, GPIO.HIGH)
    elif stat == STOP:
        GPIO.output(INA, GPIO.LOW)
        GPIO.output(INB, GPIO.LOW)

def setMotor(ch, speed, stat):
    if not gpio_initialized:
        initialize_gpio()
    if ch == CH1:
        setup_motor()  # Ensure motor is set up before use
        setMotorControl(pwm, IN1, IN2, speed, stat)

def cleanup_gpio():
    global gpio_initialized
    if gpio_initialized:
        if pwm is not None:
            pwm.stop()
        GPIO.cleanup()
        gpio_initialized = False

def open_a():
    try:
        print("Opening the door...")
        setMotor(CH1, 100, OPEN)  # Start motor
        time.sleep(8)  # Run for 8 seconds
        setMotor(CH1, 0, STOP)  # Stop motor
        print("Door opened.")
    finally:
        cleanup_gpio()  # Ensure cleanup happens

def close_a():
    try:
        print("Closing the door...")
        setMotor(CH1, 100, CLOSE)  # Start motor
        time.sleep(8)  # Run for 8 seconds
        setMotor(CH1, 0, STOP)  # Stop motor
        print("Door closed.")
    finally:
        cleanup_gpio()  # Ensure cleanup happens
        
# Ensure GPIO cleanup when the program exits
import atexit
atexit.register(cleanup_gpio)
