"""Feature extraction for the gateway: 72 EEG features, HRV from RR intervals, HR from Muse PPG."""

import numpy as np
from scipy.signal import butter, find_peaks, iirnotch, sosfiltfilt, filtfilt, welch

EEG_HZ, PPG_HZ = 256, 64
BANDS = {"delta": (1, 4), "theta": (4, 8), "alpha": (8, 12), "beta": (12, 30), "gamma": (30, 45)}
# Per channel (TP9, AF7, AF8, TP10), 18 values -> 72:
#   5 log10 band powers, 5 relative powers, 3 ratios (theta/alpha, alpha/beta, theta/beta),
#   3 Hjorth (activity, mobility, complexity), spectral edge 95%, spectral entropy.
N_EEG_FEATURES = 72
_notch = iirnotch(50, 30, EEG_HZ)
_hp = butter(2, 1.0, "high", fs=EEG_HZ, output="sos")


def _channel_features(x):
    x = filtfilt(*_notch, x)
    x = sosfiltfilt(_hp, x)
    f, p = welch(x, EEG_HZ, nperseg=min(len(x), EEG_HZ * 2))
    band = {k: p[(f >= lo) & (f < hi)].sum() + 1e-12 for k, (lo, hi) in BANDS.items()}
    total = sum(band.values())
    dx, ddx = np.diff(x), np.diff(x, 2)
    activity, mobility = x.var(), np.sqrt(dx.var() / x.var())
    complexity = np.sqrt(ddx.var() / dx.var()) / mobility
    m = (f >= 1) & (f < 45)
    pn = p[m] / p[m].sum()
    cum = np.cumsum(pn)
    return [*np.log10(list(band.values())), *(v / total for v in band.values()),
            band["theta"] / band["alpha"], band["alpha"] / band["beta"], band["theta"] / band["beta"],
            activity, mobility, complexity, f[m][np.searchsorted(cum, 0.95)],
            -(pn * np.log2(pn + 1e-12)).sum() / np.log2(len(pn))]


def eeg_features(window):
    """window: array (4, n) in uV, >= ~2 s at 256 Hz. Returns 72 floats."""
    window = np.asarray(window, dtype=float)
    if window.shape[0] != 4 or window.shape[1] < EEG_HZ * 2:
        raise ValueError("need 4 channels x at least 2 s")
    return [float(v) for ch in window for v in _channel_features(ch)]


def hrv(rr_ms):
    """HR, RMSSD and SDNN from RR intervals in ms. Needs >= 10 beats, else None."""
    rr = np.asarray(rr_ms, dtype=float)
    rr = rr[(rr > 300) & (rr < 2000)]  # drop physiologically impossible beats
    if len(rr) < 10:
        return None
    return {"hr_bpm": float(60000 / rr.mean()), "rmssd_ms": float(np.sqrt(np.mean(np.diff(rr) ** 2))),
            "sdnn_ms": float(rr.std(ddof=1))}


def ppg_bpm(ir):
    """Heart rate from >= 20 s of Muse infrared PPG, or None when the signal is too noisy."""
    x = np.asarray(ir, dtype=float)
    if len(x) < PPG_HZ * 20:
        return None
    y = sosfiltfilt(butter(3, [0.7, 3.0], "band", fs=PPG_HZ, output="sos"), x)
    peaks, _ = find_peaks(y, distance=PPG_HZ * 0.4, prominence=y.std() * 0.5)
    if len(peaks) <= 5:
        return None
    iv = np.diff(peaks)
    # Irregular beat spacing means motion/missed peaks; on the 2026-10-28 session this cut
    # >5 bpm errors vs the H303 from 13% to 3% while keeping 83% of seconds.
    if np.subtract(*np.percentile(iv, [75, 25])) / np.median(iv) > 0.15:
        return None
    bpm = 60 * PPG_HZ / np.median(iv)
    return float(bpm) if 40 <= bpm <= 180 else None
