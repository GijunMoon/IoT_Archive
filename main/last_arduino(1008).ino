#include <dht.h>         // DHT 온습도 센서를 사용하기 위한 라이브러리 포함
#include <pm2008_i2c.h>  // PM2008 미세먼지 센서를 I2C 통신으로 제어하기 위한 라이브러리 포함
#include <Servo.h>       // 서보 모터 제어를 위한 Servo 라이브러리 포함


int Relaypin = 4;  // 릴레이 핀 정의

// 객체 인스턴스화
dht DHT;                // DHT 센서 객체
PM2008_I2C pm2008_i2c;  // PM2008 미세먼지 센서 객체
Servo myservo;          // 서보 모터 객체

// 상수 정의
#define DHT21_PIN 5   // DHT 21 (AM2302) - 연결된 핀
#define DHT21_PIN2 3  // DHT 21 (AM2302) - 두 번째 센서 핀
#define LEDPIN 11     // LED 제어 핀 (PWM 사용)
#define LIGHTPIN A0   // 조도 센서 입력 핀
#define RAINPIN A1    // 빗물 감지 센서 입력 핀
#define PIEZO 7       // 피에조 버저 핀
#define INTERVAL 10   // 10분 간격
#define SERVO 10      // 서보 모터 핀

// 변수 선언
float hum;              // 실외 습도 값
float temp;             // 실외 온도 값
float hum2;             // 실내 습도 값
float temp2;            // 실내 온도 값
float userHumi = 50.0;  // 기본 설정 기본 습도
float userHot = 24.0;   // 기본 설정 기본 더운 온도
float userCool = 22.0;  // 기본 설정 기본 추운 온도
float userDust = 10;    // 기본 설정 기본 미세먼지 농도
float userLight = 60;   // 기본 설정 기본 조도
float reading;          // 조도 값
int rainValue;          // 빗물 감지 값
float pm25Value;        // PM2.5 미세먼지 농도 값

int currentIndex = 0;              // 현재 배열 인덱스
unsigned long lastSampleTime = 0;  // 마지막 샘플링 시간
String inputCommand = "";          // 사용자 입력 저장 변수
unsigned long before = 0;          // 10분 타이머 추적
int pos = 0;                       // 서보 위치

// 10분 동안 센서 값을 저장하는 배열
float humValues[INTERVAL] = { 0 };    // 실외 습도 값 배열
float tempValues[INTERVAL] = { 0 };   // 실외 온도 값 배열
float hum2Values[INTERVAL] = { 0 };   // 실내 습도 값 배열
float temp2Values[INTERVAL] = { 0 };  // 실내 온도 값 배열
float lightValues[INTERVAL] = { 0 };  // 조도 값 배열
float rainValues[INTERVAL] = { 0 };   // 빗물감지 값 배열
float pm25Values[INTERVAL] = { 0 };   // 미세먼지 농도 값 배열


// 시리얼 버퍼 지우기 함수
void clearSerialBuffer() {          //clearSerialBuffer함수 정의
  while (Serial.available() > 0) {  //입력 데이터에 정보가 있다면
    Serial.read();                  // 버퍼 지우기
  }
}

// 유효한 실수 입력을 받는 함수
float getValidFloatInput(String prompt) {  //getValidFloatInput함수 정의
  Serial.println(prompt);                  //프롬프트 출력

  clearSerialBuffer();  // 버퍼 지우기

  while (true) {                          //true값이 들어오는 동안
    if (Serial.available() > 0) {         //입력 데이터에 정보가 있다면
      float value = Serial.parseFloat();  // 실수 입력 읽기

      // 디버그 메시지
      Serial.print(F("Received value: "));  //설정값 입력창
      Serial.println(value);                //입력값 출력

      if (value > 0) {                                            // 0보다 큰 값만 허용
        return value;                                             //사용자에게 입력받은 value 전달
      } else {                                                    //0보다 큰 값이 아니라면
        Serial.println(F("Invalid value. Please enter again."));  //다시 입력하라는 문자 출력
        Serial.println(prompt);                                   // 프롬프트 다시 출력
      }

      clearSerialBuffer();  // 입력 버퍼 지우기
    }
    delay(100);  // 입력 대기
  }
}

// 사용자 설정 입력 함수
void setUserHumi() {                                                                // 습도 설정 함수 정의
  userHumi = getValidFloatInput(F("\nSet the humidity (float greater than 0): "));  //사용자에게 입력받은 기준 습도 기준 저장
  Serial.print(F("Set humidity: "));                                                //설정된 습도값
  Serial.println(userHumi);                                                         //습도 변수 출력
}

void setUserHot() {                                                                       // 고온 설정 함수 정의
  userHot = getValidFloatInput(F("\nSet the hot temperature (float greater than 0): "));  //사용자에게 입력받은 기준 고온 기준 userHot변수에 저장
  Serial.print(F("Set hot temperature: "));                                               //설정된 고온 기준
  Serial.println(userHot);                                                                //userHot변수 출력
}

void setUserCool() {                                                                        // 저온 설정 함수 정의
  userCool = getValidFloatInput(F("\nSet the cool temperature (float greater than 0): "));  //사용자에게 입력받은 기준 저온 기준 userCool변수에 저장
  Serial.print(F("Set cool temperature: "));                                                //설정된 저온 기준
  Serial.println(userCool);                                                                 //userCool변수 출력
}

void setUserDust() {                                                            // 미세먼지 설정 함수 정의
  userDust = getValidFloatInput(F("\nSet the dust (float greater than 0): "));  //사용자에게 입력받은 기준 저온 기준 userDust변수에 저장
  Serial.print(F("Set dust: "));                                                //설정된 미세먼지 기준
  Serial.println(userDust);                                                     //userDust변수 출력
}

void setUserLight() {                                                             // 조도 설정 함수 정의
  userLight = getValidFloatInput(F("\nSet the light (float greater than 0): "));  //사용자에게 입력받은 기준 저온 기준 userLight변수에 저장
  Serial.print(F("Set light: "));                                                 //설정된 조도 기준
  Serial.println(userLight);                                                      //userLight변수 출력
}


// 사용자 설정 입력 여부 묻기
void askToSetValues() {                                       //입력 여부 질문 함수 정의
  Serial.println(F(" "));                                     //공백
  Serial.println(F("Do you want to set the values? (y/n)"));  //값을 초기화하기 원하는지 질문

  while (true) {                                       //true값이 들어오는 동안
    if (Serial.available() > 0) {                      //입력데이터에 정보가 있다면
      String response = Serial.readStringUntil('\n');  //줄이 바뀌기 전까지의 입력 데이터 읽기
      response.trim();                                 //문자열 response의 앞뒤 공백을 제거

      // 추가로 공백 및 특수 문자 제거
      response.replace("\r", "");  //커서를 현재 줄의 맨 앞으로 이동하는 문자 제거
      response.replace("\n", "");  //줄바꿈 문자 제거
      response.replace("\t", "");  //일정한 간격으로 공백을 삽입하는 문자 제거

      Serial.print(F("Received value: "));  // 디버그 메시지
      Serial.println(response);             //사용자가 입력한 response값 출력

      if (response.equalsIgnoreCase("y")) {                       //사용자가 입력한 값이 y일 경우
        setUserHumi();                                            // 습도 설정 함수 호출
        setUserHot();                                             // 고온 설정 함수 호출
        setUserCool();                                            // 저온 설정 함수 호출
        setUserDust();                                            // 미세먼지 설정 함수 호출
        setUserLight();                                           // 조도 설정 함수 호출
        Serial.println(F("\n10 minute timer has been reset."));   // 10분 타이머 재설정
        break;                                                    //멈춤
      } else if (response.equalsIgnoreCase("n")) {                //사용자가 입력한 값이 n일 경우
        Serial.println(F("Running with initial values."));        // 초기 설정대로 진행
        break;                                                    //멈춤
      } else {                                                    //사용자가 입력한 값이 y/n 이외일 경우
        Serial.println(F("Invalid value. Please enter again."));  //다시 입력하라는 문자 출력
      }
    }
    delay(100);  // 입력 대기
  }
}


// 사용사 설정 재입력 함수
void processUserInput() {                         //설정 재입력 함수 정의
  if (Serial.available() > 0) {                   //입력 데이터에 정보가 있다면
    inputCommand = Serial.readStringUntil('\n');  //줄이 바뀌기 전까지의 입력 데이터 읽기
    inputCommand.trim();                          // 여분의 공백 제거

    // 디버그 메시지
    Serial.print(F("Received value: "));  //입력된 값 표시
    Serial.println(inputCommand);         //inputCommand변수 출력

    if (inputCommand.equalsIgnoreCase("y")) {  //설정이라는 단어를 입력받은 경우
      delay(1000);                                //1초 동안 프로그램 일시 중지
      // 초기 상태로 복귀 설정
      currentIndex = 0;     //currrentIndex 0으로 초기화
      lastSampleTime = 0;   //lastSampleTime 0으로 초기화
      before = millis();    // 타이머 재설정을 위해 현재 시간 저장
      clearSerialBuffer();  // 시리얼 버퍼 지우기
      askToSetValues();     //입력 여부 질문 함수 호출
    }
  }
}

// 불쾌지수 계산 함수
float calculateDiscomfortIndex(float temp, float hum) {                                           //불쾌지수 계산 함수 정의
  return (9.0 / 5.0) * temp - 0.55 * (1.0 - (hum / 100.0)) * ((9.0 / 5.0) * temp - 26.0) + 32.0;  //불쾌지수 계산 식
}


// 센서 값 출력 함수
void printSensorReadings() {        //아두이노 센서 값 출력 함수 정의
  Serial.print(F("Humidity 1: "));  //현재 실외 습도
  Serial.print(hum2, 1);             //실외 습도값 소수점 이하 1자리만 출력
  Serial.println(F("%"));           //습도 단위 출력

  Serial.print(F("Temperature 1: "));  //현재 실외 습도
  Serial.print(temp2, 1);               //실외 온도값 소수점 이하 1자리만 출력
  Serial.println(F("°C"));             //온도 단위 출력

  Serial.print(F("Humidity 2: "));  // 현재 실내 습도
  Serial.print(hum, 1);            //실내 습도값 소수점 이하 1자리만 출력
  Serial.println(F("%"));           //습도 단위 출력

  Serial.print(F("Temperature 2: "));  // 현재 실내 온도
  Serial.print(temp, 1);              //실내 온도값 소수점 이하 1자리만 출력
  Serial.println(F("°C"));             //온도 단위 출력

  Serial.print(F("Light Level: "));  // 현재 조도
  Serial.println(reading, 2);        // 조도값 소수점 이하 2자리까지 출력

  if (reading >= 200) {                          // 조도 값이 400 이상일 경우
    Serial.println(F("Very Light"));             // "매우 밝음" 출력
  } else if (reading >= 20 && reading < 200) {  // 조도 값이 200 이상, 400 미만일 경우
    Serial.println(F("Normal Light"));           //"보통" 출력
  } else if (reading < 20) {                    // 조도 값이 200 미만일 경우
    Serial.println(F("Very Dark"));              //"매우 어두움" 출력
  }

  Serial.print(F("Rain Level: "));  // 현재 빗물
  Serial.println(rainValue);        //빗물값 출력

  if (rainValue < 500) {                             // 빗물 감지 값이 500 미만일 ruddn
    Serial.println(F("Heavy Rain"));                 //"Heavy Rain" 출력
  } else if (rainValue >= 500 && rainValue < 900) {  // 빗물 감지 값이 500 이상, 900 미만일 경우
    Serial.println(F("Moderate Rain"));              //"Moderate Rain" 출력
  } else {                                           // 빗물 감지 값이 900 이상일 경우
    Serial.println(F("No Rain"));                    //"No Rain" 출력
  }

  Serial.print(F("PM2.5 Level: "));  // 현재 미세먼지
  Serial.println(pm25Value, 2);      //미세먼지 농도 소수점 이하 2자리까지 출력

  if (pm25Value >= 0 && pm25Value < 30) {                       // 미세먼지 값이 0 이상, 30 미만일 경우
    Serial.println(F("Fine dust concentration is very good"));  //"미세먼지 상태 매우 좋음" 출력
  } else if (pm25Value >= 30 && pm25Value < 80) {               // 미세먼지 값이 30 이상, 80 미만일 경우
    Serial.println(F("Fine dust concentration is normal"));     //"미세먼지 상태 보통" 출력
  } else if (pm25Value >= 80 && pm25Value < 150) {              // 미세먼지 값이 80 이상, 150 미만일 경우
    Serial.println(F("Fine dust concentration is bad"));        //"미세먼지 상태 나쁨" 출력
  } else if (pm25Value >= 150) {                                // 미세먼지 값이 150 이상일 경우
    Serial.println(F("Fine dust concentration is very bad"));   //"미세먼지 상태 매우 나쁨" 출력
  }

  float discomfortIndex1 = calculateDiscomfortIndex(temp2, hum2);    //실외 불쾌지수 저장
  float discomfortIndex2 = calculateDiscomfortIndex(temp, hum);  //실내 불쾌지수 저장

  Serial.print(F("Discomfort Index 1: "));  //현재 실외 불쾌지수
  Serial.println(discomfortIndex1, 2);      //실외 불쾌지수 소수점 이하 2자리까지 출력

  if (discomfortIndex1 >= 80) {                               // 불쾌지수 값이 80 이상일 경우
    Serial.println(F("The discomfort index is very high!"));  //"불쾌지수 매우 높음" 출력
  } else if (discomfortIndex1 >= 75) {                        // 불쾌지수 값이 75 이상일 경우
    Serial.println(F("The discomfort index is high"));        //"불쾌지수 높음" 출력
  } else if (discomfortIndex1 >= 68) {                        // 불쾌지수 값이 68 이상일 경우
    Serial.println(F("It's comfortable outside"));            //"쾌적함" 출력
  } else {                                                    // 불쾌지수 값이 68 미만일 경우
    Serial.println(F("It's very comfortable outside!"));      //"매우 쾌적함" 출력
  }

  Serial.print(F("Discomfort Index 2: "));  //현재 실내 불쾌지수
  Serial.println(discomfortIndex2, 2);      //실내 불쾌지수 소수점 이하 2자리까지 출력

  if (discomfortIndex2 >= 80) {                                 // 불쾌지수 값이 80 이상일 경우
    Serial.println(F("The discomfort index is very high!\n"));  //"불쾌지수 매우 높음" 출력
  } else if (discomfortIndex2 >= 75) {                          // 불쾌지수 값이 75 이상일 경우
    Serial.println(F("The discomfort index is high\n"));        //"불쾌지수 높음" 출력
  } else if (discomfortIndex2 >= 68) {                          // 불쾌지수 값이 68 이상일 경우
    Serial.println(F("The interior is comfort\n"));             //"쾌적함" 출력
  } else {                                                      // 불쾌지수 값이 68 미만일 경우
    Serial.println(F("The interior is very comfort!\n"));       //"매우 쾌적함" 출력
  }
}


// 평균 값 계산 함수
float calculateAverage(float* arr, int length) {  //평균 값 계산 함수 정의
  float sum = 0;                                  //sum 0으로 초기화
  int count = 0;                                  //count 0으로 초기화
  for (int i = 0; i < length; i++) {              //배열이 끝날때까지 i값에 1씩 추가
    if (arr[i] != 0) {                            // 0이 아닌 값만 고려함
      sum += arr[i];                              //sum변수에 i번째 배열값 추가
      count++;                                    //count변수에 숫자 1 증가
    }
  }
  return (count > 0) ? (sum / count) : 0;  // 0으로 나누지 않게 함
}

// 서보 제어 함수
void controlServoBasedOnAverage(float avgTemp, float avgHum, float avgTemp2, float avgHum2) {  //센서에 따른 서보 제어 함수 정의
  float discomfortIndex1 = calculateDiscomfortIndex(avgTemp, avgHum);                          //실외 불쾌지수 평균 저장
  float discomfortIndex2 = calculateDiscomfortIndex(avgTemp2, avgHum2);                          //실내 불쾌지수 평균 저장

  Serial.print(F("10 minute average discomfort index 1: "));  //현재 실외 불쾌지수 평균
  Serial.println(discomfortIndex1, 2);                        //실외 불쾌지수 평균 소수점 이하 2자리까지 출력

  Serial.print(F("10 minute average discomfort index 2: "));  //현재 실내 불쾌지수 평균
  Serial.println(discomfortIndex2, 2);                        //실내 불쾌지수 평균 소수점 이하 2자리까지 출력

  if (avgTemp2 > userHot || avgHum2 > userHumi || discomfortIndex2 < discomfortIndex1) {
    //사용자 설정 온도보다 실내 온도가 높거나 설정 습도보다 실내 습도가 높거나 실외 불쾌지수가 실내 불쾌지수보다 낮거나 조건을 하나 이상 충족할 경우
    //myservo.write(180);  // 서보를 열림 위치로 회전
    Serial.println(5);  //문을 열라는 문자 출력

  } else if (temp2 < userCool || pm25Value > userDust || (discomfortIndex1 > discomfortIndex2 || discomfortIndex1 >= 70 || temp >= 30 || hum2 >= 80 || rainValue < 900 || pm25Value >= 81)) {
    //사용자 설정 온도보다 실내온도가 낮거나 설정 미세먼지보다 실외 미세먼지가 높거나 실외 불쾌지수가 실내 불쾌지수보다 높거나 실외 불쾌지수가 70이상이거나 실외 온도가 30이상이거나 실외 습도가 80이상이거나 빗물값이 900이하이거나 미세먼지가 81이상이거나 조건 하나 이상 출족할 경우
    // myservo.write(0);  // 서보를 닫힘 위치로 회전
    Serial.println(6);   //문을 닫으라는 문자 출력
  } else {                              //위의 경우에 모두 해당하지 않는다면
                                        // myservo.write(90);  // 중립 위치
    Serial.println(7);  //문이 중립이라는 문자 출력
  }

  if (reading > userLight) {              //조도 감지 센서의 입력값이 사용자 설정값보다 큰 경우
    for (pos = 65; pos >= 0; pos -= 1) {  // 65도에서 0도까지 이동
      myservo.write(pos);                 // 서보를 'pos' 위치로 이동
      break;                              // 서보가 위치에 도달할 때까지 15ms 대기
    }
  }
}



void setup() {                // 초기 설정 함수
  Serial.begin(9600);         // 시리얼 통신 시작
  pinMode(LIGHTPIN, INPUT);   // 조도 센서 핀을 입력으로 설정
  pinMode(LEDPIN, OUTPUT);    // LED 핀을 출력으로 설정
  pinMode(RAINPIN, INPUT);    // 빗물 감지 센서 핀을 입력으로 설정
  pinMode(PIEZO, OUTPUT);     // 피에조 핀을 출력으로 설정
  pinMode(Relaypin, OUTPUT);  // 릴레이 핀을 출력으로 설정
  myservo.attach(SERVO);      // 서보 모터 핀 연결

  // PM2008 센서 초기화
  pm2008_i2c.begin();    // 미세먼지 센서 시작
  pm2008_i2c.command();  //pm2008 정보 읽기
  delay(10);             //0.01초 동안 프로그램 일시 중지


  askToSetValues();  //입력 여부 질문 함수 호출
}


// 메인 함수
void loop() {                    //계속 반복
  unsigned long now = millis();  // 현재 시간 업데이트

  //시리얼 통신
  String command = Serial.readStringUntil('\n');  //줄이 바뀌기 전까지의 입력 데이터 읽기
  command.trim();                                 //여분의 공백 제거

  // 10분 타이머 확인
  if (now - before >= 60000) {                                            // 10분 = 600,000밀리초
    Serial.println(F("------------10 minutes have passed.------------"));  //10분이 지났다는 문자 출력
    loop_10avg();
    // 10분 후에 실행할 코드를 추가
    before = now;           // 타이머 재설정
  } else {                  //10분이 지나지 않았을 경우
    printSensorReadings();  //아두이노 센서 값 출력 함수 호출
  }

  processUserInput();  // 사용자 입력 처리

  int chk = DHT.read21(DHT21_PIN);  // 첫 번째 DHT-21 센서에서 데이터 읽기
  hum = DHT.humidity;               //실외 hum 값 저장
  temp = DHT.temperature;           //실외temp 값 저장
  delay(100);

  chk = DHT.read21(DHT21_PIN2);  // 두 번째 DHT-21 센서에서 데이터 읽기
  hum2 = DHT.humidity;           //실내 hum 값 저장
  temp2 = DHT.temperature;       //실내temp 값 저장

  reading = analogRead(LIGHTPIN);         // 주변광 센서에서 조도 값 읽기
  float square_ratio = reading / 1023.0;  // 조도 값을 0에서 1023까지의 범위에서 0.0에서 1.0까지의 비율로 변환
  square_ratio = pow(square_ratio, 2.0);  //숫자를 제곱하여 비선형 변환으로 작은 값의 영향을 줄임

  analogWrite(LEDPIN, 255.0 * square_ratio);  // 상대적으로 LED 밝기 조절

  // 빗물 감지 센서 값 읽기 및 시리얼 모니터에 상태 출력
  rainValue = analogRead(RAINPIN);  // A1 핀에서 비 센서 읽기

  uint8_t ret = pm2008_i2c.read();            // PM2008 센서에서 데이터 읽기
  if (ret == 0) {                             //ret이 0일 경우
    pm25Value = pm2008_i2c.number_of_2p5_um;  // PM2.5 농도를 pm25Value 변수에 저장
  }


  //----------------------------------------------------------------------



  // 1분 간격으로 배열에 값 저장
  if (now - lastSampleTime >= 6000) {     // 1분 = 60,000밀리초
    humValues[currentIndex] = hum;         // 실외 습도 값 저장
    tempValues[currentIndex] = temp;       // 실외 온도 값 저장
    hum2Values[currentIndex] = hum2;       // 실내 습도 값 저장
    temp2Values[currentIndex] = temp2;     // 실내 온도 값 저장
    lightValues[currentIndex] = reading;   // 조도 값 저장
    rainValues[currentIndex] = rainValue;  // 빗물 감지 값 저장
    pm25Values[currentIndex] = pm25Value;  // 미세먼지 농도 값 저장

    currentIndex++;        //현재 인덱스 1 증가
    lastSampleTime = now;  //마지막 배열 값을 현재 시간으로 초기화

    // 인덱스가 간격을 초과하면 재설정
    if (currentIndex >= INTERVAL) {  //인덱스의 수가 간격보가 클 경우
      currentIndex = 0;              //인덱스를 0으로 초기화
    }
  }
  delay(500);  //0.5초 동안 프로그램 일시 중지

  //----------------------------------------------------------------------

  //솔레노이드 잠금 장치 제어
  /*아두이노 우노 - 라즈베리파이간 시리얼 통신.
    REQUIRED!: 9600BAUD 
    솔레노이드는 전원이 내려가면 잠기고 (POP) 전원이 올라가면 열림 (DOWN) */

  if (command == "3") {  //PDLC 타이머 제어
    //open
    for (pos = 0; pos <= 65; pos += 1) {  // 0도에서 65도까지 이동
      myservo.write(pos);                 // 서보를 'pos' 위치로 이동
      break;                              // 서보가 위치에 도달할 때까지 15ms 대기
    }

  } else if (command == "4") {
    //close
    for (pos = 130; pos >= 0; pos -= 1) {  // 65도에서 0도까지 이동
      myservo.write(pos);                 // 서보를 'pos' 위치로 이동
      break;                              // 서보가 위치에 도달할 때까지 15ms 대기
    }
  }
  
  if (command == "1") {  // 라즈베리파이에서 명령을 받아 "1"일 경우

    //숫자를 문자열로 바꾸지 말 것
    /*1 : 잠김
    0 : 열림 */

    digitalWrite(Relaypin, LOW);   // Relaypin을 LOW로 설정하여 잠금 상태로 전환
  } else if (command == "0"){                         // 명령이 "0"일 경우
    digitalWrite(Relaypin, HIGH);  // 릴레이 핀을 HIGH로 설정하여 잠금 해제
  }
}

  // 10분 평균 계산 설정 함수
  void loop_10avg() {                              //// 10분 평균 계산 및 서보 제어 함수 정의
    Serial.println(F("Calculating averages..."));  // 평균 계산 문구 출력

    float avgHum = calculateAverage(hum2Values, INTERVAL);      // 실외 습도 평균 값 계산
    float avgTemp = calculateAverage(temp2Values, INTERVAL);    // 실외 온도 평균 값 계산
    float avgHum2 = calculateAverage(humValues, INTERVAL);    // 실내 습도 평균 값 계산
    float avgTemp2 = calculateAverage(tempValues, INTERVAL);  // 실내 온도 평균 값 계산
    float avgLight = calculateAverage(lightValues, INTERVAL);  // 조도 평균 값 계산
    float avgRain = calculateAverage(rainValues, INTERVAL);    // 빗물 감지 평균 값 계산
    float avgPM25 = calculateAverage(pm25Values, INTERVAL);    // 미세먼지 농도 평균 값 계산

    delay(100);  //0.1초 동안 프로그램 일시 중지

    // 디버그용 평균 값 출력
    Serial.print(F("Average Humidity (Sensor 1): "));     // 실외 습도 평균 표시 출력
    Serial.println(avgHum);                               //실외 습도 평균 값 출력
    Serial.print(F("Average Temperature (Sensor 1): "));  // 실외 온도 평균 표시 출력
    Serial.println(avgTemp);                              // 실외 온도 평균 값 출력
    Serial.print(F("Average Humidity (Sensor 2): "));     // 실내 습도 평균 표시 출력
    Serial.println(avgHum2);                              // 실내 습도 평균 값 출력
    Serial.print(F("Average Temperature (Sensor 2): "));  // 실내 온도 평균 표시 출력
    Serial.println(avgTemp2);                             // 실내 온도 평균 값 출력
    Serial.print(F("Average Light Level: "));             // 조도 평균 표시 출력
    Serial.println(avgLight);                             // 조도 평균 값 출력
    Serial.print(F("Average Rain Level: "));              // 빗물 감지 평균 표시 출력
    Serial.println(avgRain);                              // 빗물 감지 평균 값 출력
    Serial.print(F("Average PM2.5 Level: "));             // 미세먼지 농도 평균 표시 출력
    Serial.println(avgPM25);                              // 미세먼지 농도 평균 값 출력

    delay(100);  //0.1초 동안 프로그램 일시 중지
    // PDLC 제어
    if (avgLight >= 50) {                   //50보다 조도값이 크거나 같을 경우
      for (pos = 130; pos >= 0; pos -= 1) {  // 65도에서 0도까지 이동
        myservo.write(pos);                 // 서보를 'pos' 위치로 이동
        break;                              // 서보가 위치에 도달할 때까지 15ms 대기
      }
    } else {                                //50보다 조도값이 작을 경우
      for (pos = 0; pos <= 65; pos += 1) {  // 0도에서 65도까지 이동
        myservo.write(pos);                 // 서보를 'pos' 위치로 이동
        break;                              // 서보가 위치에 도달할 때까지 15ms 대기
      }
    }
    controlServoBasedOnAverage(avgTemp, avgHum, avgTemp2, avgHum2);  // 평균 값에 따라 서보 제어

    currentIndex = 0;  // 인덱스 재설정을 위해 0으로 초기화
  }
