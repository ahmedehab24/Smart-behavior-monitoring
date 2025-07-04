# ptt_processor.py

import numpy as np

def calculate_ptt(ecg_peaks, ppg_peaks, ecg_fs, ppg_fs):
    """
    Calculates the average Pulse Transit Time (PTT) between ECG and PPG signals.
    """
    valid_ptts = []
    
    # Use a copy of ppg_peaks to manipulate
    ppg_peak_times = list(ppg_peaks / ppg_fs)

    for ecg_peak in ecg_peaks:
        ecg_time = ecg_peak / ecg_fs
        
        # Find the first PPG peak that occurs AFTER the current ECG peak
        # within a reasonable physiological window.
        for ppg_time in ppg_peak_times:
            if ppg_time > ecg_time:
                ptt = ppg_time - ecg_time
                
                # PTT must be within a physiological range (e.g., 100ms to 600ms)
                if 0.1 <= ptt <= 0.6:
                    valid_ptts.append(ptt)
                    
                    # Remove this ppg_time so it's not paired with another ECG peak
                    ppg_peak_times.remove(ppg_time)
                    
                    # Move to the next ECG peak
                    break 

    if not valid_ptts:
        return None
        
    return np.mean(valid_ptts)


# ptt_processor.py

# ... (your working calculate_ptt function is above) ...

def estimate_bp(ptt):
    """
    Estimates blood pressure from PTT using your personal calibration.
    """
    # === FINAL, CORRECT CONSTANTS ===
    # Calibrated using your BP (105/71) and your measured PTT of 0.3560s
    A_sbp = 30.26
    B_sbp = 20.0
    A_dbp = 14.596
    B_dbp = 30.0
    # ================================

    if ptt is None or ptt == 0:
        return 0, 0

    sbp = A_sbp / ptt + B_sbp
    dbp = A_dbp / ptt + B_dbp

    return round(sbp, 1), round(dbp, 1)
