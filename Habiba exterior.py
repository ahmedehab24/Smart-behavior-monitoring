import cv2
import torch
import numpy as np
import time
import os
import threading
import xml.etree.ElementTree as ET
import osmnx as ox
import math
import base64
import json
import requests
from collections import deque
from torchvision.transforms import Compose, Resize, ToTensor, Normalize
from PIL import Image

# ---------- Config Loader ----------
def load_config(path='config.txt'):
    config = {}
    with open(path, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                config[key.strip()] = value.strip()
    return config

config = load_config()
PLATE = config.get("plate", "UNKNOWN")
MODEL = config.get("model", "ExteriorCam")
SERVER_IP = config.get("server_ip", "127.0.0.1")
APP_URL = f"http://{SERVER_IP}:5000/trigger"

# ---------- MiDaS Setup ----------
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

midas = torch.hub.load("intel-isl/MiDaS", "DPT_Large")
midas.to(device).eval()

midas_transforms = torch.hub.load("intel-isl/MiDaS", "transforms")
midas_transform = midas_transforms.dpt_transform

# ---------- YOLOv5 Setup ----------
yolo_model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
yolo_model.to(device).eval()

# ---------- Parameters ----------
COLLISION_THRESHOLD = 4.3
FRAME_SKIP = 2
DEPARTURE_WINDOW = 30  # seconds
MAX_DEPARTURES = 2
FOLDER = "."  # Folder to watch for GPX files
PROCESSED = set()

# ---------- App Integration ----------
def send_event_to_app(label, image):
    _, buffer = cv2.imencode('.jpg', image)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    payload = {
        "cv_label": label,
        "cv_image": img_base64,
        "vd_label": label,
        "plate": PLATE,
        "model": MODEL,
        "source": "exterior"
    }
    try:
        requests.post(APP_URL, json=payload)
    except Exception as e:
        print(f"⚠️ Failed to send to app: {e}")

# The rest of the code remains the same (no need to repeat it here unless editing further).
