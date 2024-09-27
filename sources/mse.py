#경사하강법 선형회귀

from sklearn.preprocessing import StandardScaler
import numpy as np

# 가상의 역사 데이터 (예시)
external_temp = np.array([26, 25, 24, 23, 22])
external_humidity = np.array([52, 50, 49, 48, 47])
sensor_temp = np.array([25, 24, 23, 22, 21])
sensor_humidity = np.array([50, 48, 47, 46, 45])

# 데이터 정규화
scaler = StandardScaler()
X = np.column_stack((external_temp, external_humidity))
X_normalized = scaler.fit_transform(X)

y_temp = sensor_temp
y_humidity = sensor_humidity

# 가중치 초기화
w_temp = np.zeros(X_normalized.shape[1] + 1)
w_humidity = np.zeros(X_normalized.shape[1] + 1)

# 학습 하이퍼파라미터
learning_rate = 0.001  # 학습률을 작게 설정
epochs = 1000

def predict(X, w):
    return np.dot(X, w[1:]) + w[0]

def gradient_descent(X, y, w, learning_rate, epochs):
    m = len(y)
    for epoch in range(epochs):
        y_pred = predict(X, w)
        error = y_pred - y
        w[0] -= learning_rate * np.sum(error) / m
        w[1:] -= learning_rate * np.dot(error, X) / m
    return w

# 모델 학습
w_temp = gradient_descent(X_normalized, y_temp, w_temp, learning_rate, epochs)
w_humidity = gradient_descent(X_normalized, y_humidity, w_humidity, learning_rate, epochs)

# 학습된 가중치 출력
#print("Temperature Model Weights:", w_temp)
#print("Humidity Model Weights:", w_humidity)

def calibrate_sensor_data(sensor_data, external_weather):
    """경사 하강법을 이용한 센서 데이터 보정."""
    calibrated_data = sensor_data.copy()
    
    if external_weather:
        X_new = np.array([[float(external_weather['temperature']), float(external_weather['humidity'])]])
        X_new_normalized = StandardScaler.transform(X_new)  # 입력 데이터 정규화
        calibrated_data['temperature_1'] = str(predict(X_new_normalized, w_temp)[0])
        calibrated_data['humidity_1'] = str(predict(X_new_normalized, w_humidity)[0])
    
    return calibrated_data