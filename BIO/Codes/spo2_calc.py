# spo2_calc.py
# Modified to further empirically adjust the SpO2 formula coefficients

import numpy as np

def calculate_spo2(red_signal, ir_signal):
    # Remove DC offset
    # Ensure signals are numpy arrays first if they aren't already (main.py does this)
    red_signal = np.asarray(red_signal)
    ir_signal = np.asarray(ir_signal)

    red = red_signal - np.mean(red_signal)
    ir = ir_signal - np.mean(ir_signal)

    # Calculate AC using RMS
    red_ac = np.sqrt(np.mean(np.square(red)))
    ir_ac = np.sqrt(np.mean(np.square(ir)))

    # DC values
    red_dc = np.mean(red_signal)
    ir_dc = np.mean(ir_signal)

    # Avoid divide-by-zero
    if ir_ac == 0 or ir_dc == 0 or red_dc == 0:
        print("Warning: Division by zero avoided in SpO2 calculation.")
        return None

    # Calculate the ratio of ratios
    ratio = (red_ac / red_dc) / (ir_ac / ir_dc)

    # Empirical SpO2 calculation formula adjustment
    # Adjusted formula: Further changed the multiplier for the ratio (18 -> 16).
    # This should further increase SpO2 values for the same 'ratio'.
    spo2 = 110 - 12* ratio # Changed 18 to 16

    # Ensure SpO2 is within the valid range [0, 100]
    return round(max(0, min(100, spo2)), 2)
