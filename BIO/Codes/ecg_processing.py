import numpy as np
from scipy.signal import butter, filtfilt, find_peaks
import matplotlib.pyplot as plt

def bandpass_filter(signal, lowcut=0.5, highcut=40.0, fs=250, order=2):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, signal)

def detect_r_peaks(filtered_signal, fs=250):
    distance = int(0.5 * fs)  # Allow HR up to ~200 bpm
    threshold = np.mean(filtered_signal) + 0.3 * np.std(filtered_signal)
    peaks, _ = find_peaks(filtered_signal, distance=distance, height=threshold)
    return peaks

def calculate_heart_rate(peaks, fs=250):
    if len(peaks) < 2:
        return None
    rr_intervals = np.diff(peaks) / fs  # In seconds
    avg_rr = np.mean(rr_intervals)
    hr = 60.0 / avg_rr
    return hr

def debug_plot(filtered_signal, peaks, heart_rate=None):
    plt.figure(figsize=(10, 4))
    plt.plot(filtered_signal, label="Filtered ECG")
    plt.plot(peaks, filtered_signal[peaks], "rx", label="R-peaks")
    title = f"Heart Rate: {heart_rate:.2f} bpm" if heart_rate else "No HR Detected"
    plt.title(title)
    plt.xlabel("Sample")
    plt.ylabel("Amplitude (V)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()
