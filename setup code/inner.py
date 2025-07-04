import cv2
from ultralytics import YOLO
import requests
import base64
import threading
import time

# Load configuration
def load_config(path='config.txt'):
    config = {}
    with open(path, 'r') as f:
        for line in f:
            key, value = line.strip().split('=', 1)
            config[key] = value
    return config

config = load_config()
plate = config.get("plate", "UNKNOWN")
model_name = config.get("model", "InteriorCam")
server_ip = config.get("server_ip", "127.0.0.1")
server_url = f"http://{server_ip}:5000/trigger"

# Labels for illegal activities
illegal_labels = {
    0: 'drinking',
    1: 'eating',
    2: 'mobile use',
    4: 'sleep',
    5: 'smoking'
}

# Load YOLO model
model = YOLO("C:/Users/Ahmed ehab/OneDrive - Future University in Egypt/Desktop/mpnitoring app/best.pt")

# Initialize camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# Function to send data to server
def send_data(data):
    try:
        response = requests.post(server_url, json=data)
        print(f"✅ Sent '{data['cv_label']}' to {server_url}: {response.json()}")
    except Exception as e:
        print("❌ Error:", e)

frame_skip = 1  # Process every frame
frame_count = 0
last_sent_time = 0
send_interval = 10  # seconds

# Main loop
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    if frame_count % frame_skip != 0:
        continue

    small_frame = cv2.resize(frame, (640, 480))
    results = model(small_frame)

    current_time = time.time()

    for r in results:
        boxes = r.boxes
        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                class_id = int(box.cls[0])
                if class_id in illegal_labels and current_time - last_sent_time >= send_interval:
                    label = illegal_labels[class_id]
                    _, buffer = cv2.imencode('.jpg', frame)
                    img_base64 = base64.b64encode(buffer).decode('utf-8')

                    data = {
                        "plate": plate,
                        "model": model_name,
                        "cv_label": label,
                        "cv_image": img_base64,
                        "source": "interior"
                    }

                    threading.Thread(target=send_data, args=(data,)).start()
                    last_sent_time = current_time

    frame_with_boxes = r.plot()
    cv2.imshow("YOLO Detection", frame_with_boxes)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
