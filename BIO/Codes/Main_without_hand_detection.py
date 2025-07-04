import time
import threading
import numpy as np
import board
import busio
import adafruit_mlx90614
import requests

from ads1115_driver import ADS1115Reader
from max30102_driver import MAX30102
from processing import bandpass_filter, detect_r_peaks, calculate_heart_rate
from respiration_calc import estimate_respiration
from spo2_calc import calculate_spo2
from ptt_processor import calculate_ptt, estimate_bp

# ================= SETTINGS =================
fs_ecg = 250
fs_ppg = 25
duration = 30

ecg_data = []
red_data = []
ir_data = []

# ================= LOAD CONFIG =================
def load_config(path="config.txt"):
    config = {}
    try:
        with open(path, 'r') as f:
            for line in f:
                key, value = line.strip().split('=', 1)
                config[key] = value
    except Exception as e:
        print("⚠️ Could not read config.txt:", e)
    return config

config = load_config()
plate = config.get("plate", "UNKNOWN")
model_name = config.get("model", "UNKNOWN")
server_ip = config.get("server_ip", "192.168.100.14")
server_url = f"http://{server_ip}:5000/trigger"

# ================= MLX90614 SETUP =================
i2c = busio.I2C(board.SCL, board.SDA)
while not i2c.try_lock():
    pass

def safe_i2c_scan(i2c_bus):
    found = []
    for address in range(0x08, 0x78):
        try:
            i2c_bus.writeto(address, b"")
            found.append(address)
        except Exception:
            pass
    return found

devices = safe_i2c_scan(i2c)
i2c.unlock()

if 0x5A not in devices:
    print("⚠️  MLX90614 not detected at address 0x5A. Skipping temperature readings.")
    mlx = None
else:
    try:
        mlx = adafruit_mlx90614.MLX90614(i2c, address=0x5A)
    except Exception as e:
        print("Failed to initialize MLX90614:", e)
        mlx = None

# ================= DATA COLLECTION =================
def collect_ecg_data(reader, container):
    for _ in range(fs_ecg * duration):
        try:
            container.append(reader.read_voltage())
        except:
            container.append(0)
        time.sleep(1 / fs_ecg)

def collect_ppg_data(sensor, red_container, ir_container):
    zero_count = 0
    total_samples = fs_ppg * duration
    for _ in range(total_samples):
        r, i = sensor.read_fifo()
        red_container.append(r or 0)
        ir_container.append(i or 0)
        if (r or 0) == 0 and (i or 0) == 0:
            zero_count += 1
        time.sleep(1 / fs_ppg)
    if zero_count / total_samples > 0.2:
        print("⚠️ Hand likely removed during measurement.")

# ================= BIOMETRICS =================
def estimate_bac(hr, rr, spo2, temp, sys_bp=0, dia_bp=0):
    if temp is None:
        return "Unknown (Temp Error)"

    # Use Celsius values
    if rr >= 12 and 110 <= sys_bp <= 120 and 70 <= dia_bp <= 80 and 60 <= hr <= 90 and 36.1 <= temp <= 37.2:
        return "0.00% (Sober)"
    elif 10 <= rr < 12 and 120 <= sys_bp <= 125 and 80 <= dia_bp <= 85 and 90 <= hr <= 100 and 37.2 < temp <= 38.3:
        return "0.02%"
    elif 9 <= rr < 10 and 125 <= sys_bp <= 130 and 85 <= dia_bp <= 85 and 100 <= hr <= 105 and 38.3 < temp <= 38.8:
        return "0.04%"
    elif 5 <= rr < 9 and 135 <= sys_bp <= 140 and 85 <= dia_bp <= 90 and hr > 105 and temp > 38.8:
        return "0.06%"
    elif rr < 5 and sys_bp > 140 and dia_bp > 90 and hr > 105 and temp > 38.8:
        return "0.08%"
    else:
        return "Unknown (Unclassified)"

def read_core_temp():
    if not mlx:
        return None
    for attempt in range(3):
        try:
            skin_temp = mlx.object_temperature
            if 25 <= skin_temp <= 40:
                core_temp = skin_temp + 4.0
                if core_temp < 30 or core_temp > 42:
                    print(f"⚠️ Unusual body temperature reading: {core_temp:.2f} °C")
                return round(core_temp, 2)
            else:
                time.sleep(0.5)
        except Exception as e:
            print("Temp read error:", e)
            return None
    print("⚠️ Body temp reading failed or out of range after retries.")
    return None

# ================= SEND TO SERVER =================
def send_to_server(hr, spo2, rr, temp, sys_bp, dia_bp, bac):
    bio_data = {
        "heart_rate": hr or 0,
        "oxygen": spo2 or 0,
        "respiration_rate": rr or 0,
        "temperature": temp or 0,
        "alcohol": 0.08 if "0.08" in bac else (0.06 if "0.06" in bac else (0.04 if "0.04" in bac else (0.02 if "0.02" in bac else 0.0))),
        "blood_pressure": {
            "systolic": sys_bp or 0,
            "diastolic": dia_bp or 0
        }
    }

    payload = {
        "plate": plate,
        "model": model_name,
        "cv_label": "none",
        "cv_image": "",
        "vd_label": "normal",
        "bio": bio_data
    }

    try:
        res = requests.post(server_url, json=payload, timeout=3)
        print(f"✅ Sent | HR: {hr:.2f} | SpO₂: {spo2:.2f}% | RR: {rr} | Temp: {temp}°C | BP: {sys_bp:.1f}/{dia_bp:.1f} | BAC: {bac}")
    except Exception as e:
        print(f"❌ Failed to send data: {e}")

# ================= MAIN =================
def main():
    ecg_reader = ADS1115Reader(channel=0)
    max_sensor = MAX30102()

    print("📡 Starting BP + BAC estimation using PTT... Ctrl+C to stop.")

    try:
        while True:
            global ecg_data, red_data, ir_data
            ecg_data, red_data, ir_data = [], [], []

            print("\nCollecting ECG and PPG data (30s)...")
            ecg_thread = threading.Thread(target=collect_ecg_data, args=(ecg_reader, ecg_data))
            ppg_thread = threading.Thread(target=collect_ppg_data, args=(max_sensor, red_data, ir_data))

            ecg_thread.start()
            ppg_thread.start()

            ecg_thread.join()
            ppg_thread.join()

            ecg_np = np.array(ecg_data)
            red_np = np.array(red_data)
            ir_np = np.array(ir_data)

            ecg_filtered = bandpass_filter(ecg_np, fs=fs_ecg)
            ecg_peaks = detect_r_peaks(ecg_filtered, fs=fs_ecg)
            hr = calculate_heart_rate(ecg_peaks, fs=fs_ecg)
            hr = round(hr, 2) if hr else 0
            if hr:
                print(f"Heart Rate: {hr:.2f} bpm")
            else:
                print("Could not calculate heart rate.")

            ir_filtered = bandpass_filter(ir_np, fs=fs_ppg, lowcut=0.5, highcut=5)
            ppg_peaks = detect_r_peaks(ir_filtered, fs=fs_ppg)

            ptt = calculate_ptt(ecg_peaks, ppg_peaks, fs_ecg, fs_ppg)
            sys_bp = dia_bp = 0
            if ptt:
                print(f"PTT: {ptt:.4f} s")
                sys_bp, dia_bp = estimate_bp(ptt)
                print(f"Estimated BP: {sys_bp:.1f}/{dia_bp:.1f} mmHg")
            else:
                print("Could not calculate PTT.")

            spo2 = calculate_spo2(red_np, ir_np)
            spo2 = round(spo2, 2) if spo2 else 0
            if spo2:
                print(f"SpO2: {spo2:.2f}%")
            else:
                print("Could not calculate SpO2.")

            rr = estimate_respiration(ir_np, fs_ppg)
            print(f"Respiration Rate: {rr} bpm")

            body_temp = read_core_temp()
            if body_temp:
                print(f"Core Body Temperature: {body_temp:.2f} °C")
            else:
                print("Could not read temperature.")

            bac = estimate_bac(hr, rr, spo2, body_temp, sys_bp, dia_bp)
            print(f"Estimated BAC: {bac}")

            send_to_server(hr, spo2, rr, body_temp, sys_bp, dia_bp, bac)
            print("-" * 40)

    except KeyboardInterrupt:
        print("🛑 Program stopped by user.")
    finally:
        max_sensor.shutdown()

if __name__ == "__main__":
    main()
