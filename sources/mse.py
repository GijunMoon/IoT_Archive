import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import sys
import os

# Append the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sources.weather as weather

# Simulate receiving the same external weather data multiple times
weather_data = weather.fetch_external_weather()

external_weather_example = {'temperature': weather_data['temperature'], 'humidity': weather_data['humidity'], 'pm_25': weather_data['pm_25']}
num_samples = 5  # Number of repeated measurements

# Create arrays from repeated external weather values
external_temp_train = np.full(num_samples, external_weather_example['temperature'], dtype=float)
external_humidity_train = np.full(num_samples, external_weather_example['humidity'], dtype=float)
external_pm25_train = np.full(num_samples, external_weather_example['pm_25'], dtype=float)

# Simulate sensor data corresponding to these external conditions
sensor_temp_train = external_temp_train - 1  # Assuming sensor reads 1 degree lower
sensor_humidity_train = external_humidity_train - 1  # Assuming sensor reads 1% lower
sensor_pm25_train = external_pm25_train * 0.9  # Assuming sensor reads 10% lower

# Prepare the data
X_train = np.column_stack((external_temp_train, external_humidity_train, external_pm25_train))
y_temp_train = sensor_temp_train
y_humidity_train = sensor_humidity_train
y_pm25_train = sensor_pm25_train

# Standardize features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# Train linear regression models
model_temp = LinearRegression().fit(X_train_scaled, y_temp_train)
model_humidity = LinearRegression().fit(X_train_scaled, y_humidity_train)
model_pm25 = LinearRegression().fit(X_train_scaled, y_pm25_train)

def calibrate_sensor_data(sensor_data, external_weather):
    """Calibrate sensor data using trained linear regression models."""
    calibrated_data = sensor_data.copy()
    
    # Prepare new data for prediction
    if all(k in external_weather for k in ['temperature', 'humidity', 'pm_25']):
        X_new = np.array([[float(sensor_data['temperature_1'][:4]), float(sensor_data['humidity_1'][:4]), float(sensor_data['pm2_5'])]])
        X_new_scaled = scaler.transform(X_new)  # Scale the new data
        
        # Predict and update the calibrated data
        calibrated_data['temperature_1'] = str(model_temp.predict(X_new_scaled)[0])
        calibrated_data['humidity_1'] = str(model_humidity.predict(X_new_scaled)[0])
        calibrated_data['pm2_5'] = str(model_pm25.predict(X_new_scaled)[0])
    
    return calibrated_data

"""
# Example usage
sensor_data_example = {'temperature_1': '21.0', 'humidity_1': '45.0', 'pm2_5': '13.5'}
calibrated_data = calibrate_sensor_data(sensor_data_example, external_weather_example)
print(calibrated_data)
"""
