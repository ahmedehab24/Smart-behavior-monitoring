# respiration_calc.py

import numpy as np
from scipy.signal import butter, filtfilt, find_peaks

def bandpass_filter(signal, fs, low=0.1, high=0.4, order=4):
    nyquist = 0.5 * fs
    low /= nyquist
    high /= nyquist
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, signal)

def estimate_respiration(ir_signal, sampling_rate):
    # Apply bandpass filter to isolate breathing
    filtered = bandpass_filter(ir_signal, sampling_rate)

    # Find breathing peaks with at least 1.5s between
    peaks, _ = find_peaks(filtered, distance=int(sampling_rate * 1.5))

    duration_sec = len(ir_signal) / sampling_rate
    breaths_per_min = len(peaks) * (60 / duration_sec)

    return round(breaths_per_min , 2)
