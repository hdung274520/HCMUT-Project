"""
Checks one recording session made with session_timer.py:
  1. Alpha (8-12 Hz) power from the Muse 2 EEG, eyes closed vs eyes open.
  2. Heart rate from Muse PPG vs H303 (ECG chest strap) vs YX110, per phase.

Usage (needs numpy + scipy):
    python3 analyze_session.py session_marks_X.json muse.jsonl h303.jsonl yx110.jsonl
"""

import json
import sys
from datetime import datetime, timedelta

import numpy as np
from scipy.signal import butter, find_peaks, sosfiltfilt, welch

TRIM = 10  # seconds dropped after each phase change
EEG_HZ, PPG_HZ = 256, 64


def ts(s):
    return datetime.fromisoformat(s)


def load(path):
    return [d for d in map(json.loads, open(path)) if d.get("type") == "packet"]


marks, muse, h303, yx = sys.argv[1], load(sys.argv[2]), load(sys.argv[3]), load(sys.argv[4])
marks = json.load(open(marks))
phases = [(m["phase"], ts(m["start_utc"]) + timedelta(seconds=TRIM), ts(n["start_utc"]))
          for m, n in zip(marks, marks[1:]) if m["phase"] != "settle"]


def samples(packets, sensor, key, t0, t1):
    out = []
    for d in packets:
        if d.get("sensor") == sensor and t0 <= ts(d["timestamp"]) < t1:
            out.extend(d["reading"][key])
    return np.array(out, dtype=float)


def alpha_power(x):
    if len(x) < EEG_HZ * 20:
        return np.nan
    f, p = welch(x - x.mean(), EEG_HZ, nperseg=EEG_HZ * 4)
    return p[(f >= 8) & (f <= 12)].sum() / p[(f >= 1) & (f <= 40)].sum()  # relative alpha


def ppg_bpm(x):
    if len(x) < PPG_HZ * 20:
        return np.nan
    y = sosfiltfilt(butter(3, [0.7, 3.0], "band", fs=PPG_HZ, output="sos"), x)
    peaks, _ = find_peaks(y, distance=PPG_HZ * 0.4, prominence=y.std() * 0.5)
    return 60 * PPG_HZ / np.median(np.diff(peaks)) if len(peaks) > 5 else np.nan


def mean_bpm(packets, t0, t1):
    v = [d["reading"]["pulse_bpm"] for d in packets
         if t0 <= ts(d["timestamp"]) < t1 and d["reading"].get("pulse_bpm")]
    return np.mean(v) if v else np.nan


print(f"{'phase':<12}{'start':>9} | " + " ".join(f"alpha {c:<5}" for c in ("TP9", "AF7", "AF8", "TP10"))
      + " | bpm: muse   h303   yx110")
alpha = {}
for name, t0, t1 in phases:
    if name == "done":
        continue
    a = [alpha_power(samples(muse, f"eeg_{c.lower()}", "samples_uv", t0, t1)) for c in ("TP9", "AF7", "AF8", "TP10")]
    alpha.setdefault(name, []).append(a)
    bpm = (ppg_bpm(samples(muse, "ppg_infrared", "samples", t0, t1)),
           mean_bpm(h303, t0, t1), mean_bpm(yx, t0, t1))
    print(f"{name:<12}{t0 - timedelta(seconds=TRIM):%H:%M:%S} | " + " ".join(f"{v:>10.3f}" for v in a)
          + " | " + "  ".join(f"{v:6.1f}" for v in bpm))

if "eyes_open" in alpha and "eyes_closed" in alpha:
    r = np.nanmean(alpha["eyes_closed"], axis=0) / np.nanmean(alpha["eyes_open"], axis=0)
    print("\nalpha closed/open ratio per channel (TP9 AF7 AF8 TP10):", np.round(r, 2))
    print("Expected > ~1.3 on at least the posterior channels (TP9/TP10).")
