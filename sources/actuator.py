# sources/actuator.py

import RPi.GPIO as GPIO

# 모터 상태
STOP  = 0
OPEN  = 1
CLOSE = 2

# 모터 채널
CH1 = 0

# GPIO 핀 정의
ENA = 21  # PWM 핀
IN1 = 20  # 모터 제어 핀 1
IN2 = 16  # 모터 제어 핀 2

# 초기화 플래그
gpio_initialized = False

def initialize_gpio():
    """ GPIO를 초기화하는 함수. """
    global gpio_initialized
    if not gpio_initialized:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(ENA, GPIO.OUT)
        GPIO.setup(IN1, GPIO.OUT)
        GPIO.setup(IN2, GPIO.OUT)
        gpio_initialized = True

# 모터 핸들러
pwm = None

def setup_motor():
    """ 모터 설정 함수. """
    global pwm
    if not gpio_initialized:
        initialize_gpio()
    pwm = GPIO.PWM(ENA, 100)  # 100Hz PWM 생성
    pwm.start(0)  # 초기 PWM 비율 0%

def setMotorContorl(pwm, INA, INB, speed, stat):
    """ 모터를 제어하는 함수 """
    if not gpio_initialized:
        initialize_gpio()

    # 모터 속도 제어
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
    """ 모터 제어 핸들러 """
    if not gpio_initialized:
        initialize_gpio()

    if ch == CH1:
        setMotorContorl(pwm, IN1, IN2, speed, stat)

def cleanup_gpio():
    """ GPIO를 정리하는 함수 """
    global gpio_initialized
    if gpio_initialized:
        if pwm is not None:
            pwm.stop()
        GPIO.cleanup()
        gpio_initialized = False
