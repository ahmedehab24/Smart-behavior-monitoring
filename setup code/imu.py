# this code is targetting the classification of the driver behavior if aggressive , keen , normal , smooth
# and measuring the actual speed of the driver and compare it with the read sign
import time
import requests
import joblib
import pandas as pd
import numpy as np
from mpu6050 import mpu6050
import warnings
warnings.filterwarnings("ignore")

# === Load config ===
def load_config(path='/home/pop/Desktop/monitoring/config.txt'):
    config = {}
    try:
        with open(path, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    config[key.upper()] = value
    except:
        print("⚠️ Failed to read config.txt. Check file path.")
    return config

config = load_config()
plate = config.get("PLATE", "UNKNOWN")
model_name = config.get("MODEL", "GENERIC")
server_ip = config.get("SERVER_IP", "172.20.10.5")
server_url = f"http://{server_ip}:5000/trigger"

# === Initialize model and IMU ===
rf_model = joblib.load("/home/pop/Desktop/monitoring/rf_model.pkl")
imu = mpu6050(0x68)

# === Calibrate Z-axis ===
print("🛠️ Calibrating IMU bias...")
bias_samples = [imu.get_accel_data()['z'] for _ in range(100)]
bias = sum(bias_samples) / len(bias_samples)
print(f"✅ Z-axis bias: {bias:.3f} m/s^2")

# === Speed estimation params ===
speed = 0.0
last_time = time.time()
send_interval = 5
last_sent = time.time()
threshold = 0.2
max_speed_kmh = 120

# === Get VD label ===
def get_vd_label(accel, gyro):
    data = {
        'X_Gyroscope': gyro['x'],
        'Y_Gyroscope': gyro['y'],
        'X_Accelerometer': accel['x'],
        'Y_Accelerometer': accel['y'],
        'Z_Accelerometer': accel['z']
    }

    df = pd.DataFrame([data], columns=[
        'X_Gyroscope', 'Y_Gyroscope',
        'X_Accelerometer', 'Y_Accelerometer', 'Z_Accelerometer'
    ])

    prediction = rf_model.predict(df)
    return prediction[0]

# === Main loop ===
print(f"🚗 Starting VD + Speed sender for car: {plate} ({model_name}) to {server_url}")

try:
    while True:
        accel = imu.get_accel_data()
        gyro = imu.get_gyro_data()

        print("📈 IMU Readings:")
        print(f"  Gyroscope     -> X: {gyro['x']:.2f}, Y: {gyro['y']:.2f}")
        print(f"  Accelerometer -> X: {accel['x']:.2f}, Y: {accel['y']:.2f}, Z: {accel['z']:.2f}")

        # Speed estimation
        az = accel['z'] - bias
        if abs(az) < threshold:
            az = 0.0

        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time

        speed += az * dt
        speed = max(speed, 0.0)
        speed_kmh = min(speed * 3.6, max_speed_kmh)

        # VD label prediction
        vd_label = get_vd_label(accel, gyro)

        # Send every `send_interval` seconds
        if current_time - last_sent >= send_interval:
            payload = {
                "plate": plate,
                "model": model_name,
                "actual_speed": round(speed_kmh, 2),
                "vd_label": vd_label
            }

            try:
                res = requests.post(server_url, json=payload)
                print(f"✅ Sent: Speed={speed_kmh:.2f} km/h, Label={vd_label}, Status={res.status_code}")
            except Exception as e:
                print(f"❌ Failed to send: {e}")

            last_sent = current_time

        time.sleep(0.1)

except KeyboardInterrupt:
    print("🛑 Measurement stopped.")
