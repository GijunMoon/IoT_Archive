import RPi.GPIO as GPIO
from time import sleep

# 모터 상태
STOP  = 0
OPEN  = 1
CLOSE = 2

# 모터 채널
CH1 = 0

# PIN 입출력 설정
OUTPUT = 1
INPUT = 0

# PIN 설정
HIGH = 1
LOW = 0

# Pi4 핀 정의
#PWM PIN
ENA = 21  #21 pin

#GPIO PIN
IN1 = 20  #20 pin
IN2 = 16  #16 pin

# 핀 설정 함수
def setPinConfig(EN, INA, INB):        
    GPIO.setup(EN, GPIO.OUT)
    GPIO.setup(INA, GPIO.OUT)    
    # 100khz 로 PWM 동작 시킴 
    pwm = GPIO.PWM(EN, 100) 

    # 우선 PWM 멈춤.   
    pwm.start(0) 
    return pwm

# 모터 제어 함수
def setMotorContorl(pwm, INA, INB, speed, stat):

    #모터 속도 제어 PWM
    pwm.ChangeDutyCycle(speed)  

    #열림
    if stat == OPEN:
        GPIO.output(INA, HIGH)
        GPIO.output(INB, LOW)

    #닫힘
    elif stat == CLOSE:
        GPIO.output(INA, LOW)
        GPIO.output(INB, HIGH)

    #정지
    elif stat == STOP:
        GPIO.output(INA, LOW)
        GPIO.output(INB, LOW)


# 모터 제어함수 핸들러
def setMotor(ch, speed, stat):
    if ch == CH1:
        #pwmA는 핀 설정 후 pwm 핸들을 리턴 받은 값이다.
        setMotorContorl(pwmA, IN1, IN2, speed, stat)


# GPIO 모드 설정 
GPIO.setmode(GPIO.BCM)

#모터 핀 설정
#핀 설정후 PWM 핸들 얻어옴 
pwmA = setPinConfig(ENA, IN1, IN2)


#제어 시작
#setMotor(CH1, 100, OPEN)

#액추에이터 가동 시간 고려 (변경 가능)
#sleep(5)

#setMotor(CH1, 100, CLOSE)
#sleep(5)

# 종료
#GPIO.cleanup()