import cv2
from ultralytics import YOLO
import requests
#import base64
import threading
import time
import re

# Load configuration from config.txt
def load_config(path='config.txt'):
    config = {}
    with open(path, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key] = value
    return config

config = load_config()
plate = config.get("plate", "UNKNOWN")
model_name = config.get("model", "UNKNOWN")
server_ip = config.get("server_ip", "127.0.0.1")
server_url = f"http://{server_ip}:5000/trigger"

# Load YOLO model (your traffic sign detector)
model = YOLO("traffic_sign_detector.pt")

# Open camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Send data to server
def send_data(data):
    try:
        response = requests.post(server_url, json=data)
        print(f"✅ Sent speed data to {server_url}: {response.status_code} - {response.text}")
    except Exception as e:
        print("❌ Error:", e)

# Utility to extract speed from label
def extract_speed(label):
    match = re.search(r"Speed Limit (\d+)", label)
    return float(match.group(1)) if match else 0.0

# Frame loop
frame_skip = 1
frame_count = 0
last_sent_time = 0
send_interval = 10  # seconds

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % frame_skip != 0:
        continue

    resized_frame = cv2.resize(frame, (640, 480))
    results = model(resized_frame)

    current_time = time.time()
    target_speed = 0.0

    for r in results:
        boxes = r.boxes
        names = model.names

        if boxes is not None:
            for i in range(len(boxes)):
                class_id = int(boxes.cls[i])
                label = names[class_id]

                if label.lower().startswith("speed limit"):
                    target_speed = extract_speed(label)

    # If any speed limit detected and enough time passed
    if target_speed > 0 and (current_time - last_sent_time >= send_interval):
        # 👇 Replace this with actual IMU integration result
        actual_speed = 22.5  # ← replace with your own IMU-derived value

        data = {
            "plate": plate,
            "model": model_name,
            "actual_speed": actual_speed,
            "target_speed": target_speed
        }

        threading.Thread(target=send_data, args=(data,)).start()
        last_sent_time = current_time

    # Show frame with annotations
    frame_with_boxes = r.plot()
    cv2.imshow("Speed Limit Detection", frame_with_boxes)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
