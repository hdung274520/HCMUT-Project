"""
Draws the two report figures for one session_timer.py recording:
  alpha-psd: EEG power spectrum of all 4 channels, eyes closed vs eyes open.
  nhip-tim:  heart rate over time from Muse PPG, H303 and YX110, with the phases shaded.

Usage (needs numpy, scipy, matplotlib):
    python plot_session.py session_marks_X.json muse.jsonl h303.jsonl yx110.jsonl OUT_DIR
Writes OUT_DIR/alpha-psd.{pdf,png} and OUT_DIR/nhip-tim.{pdf,png}.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, find_peaks, sosfiltfilt, welch

TRIM = 10  # seconds dropped after each phase change, same as analyze_session.py
EEG_HZ, PPG_HZ = 256, 64
PHASE_VI = {"settle": "Nghỉ", "eyes_open": "Mở mắt", "eyes_closed": "Nhắm mắt", "yx110": "Kẹp YX110"}
PHASE_COLOR = {"eyes_open": "#fde68a", "eyes_closed": "#bfdbfe"}


def ts(s):
    return datetime.fromisoformat(s)


def load(path):
    return [d for d in map(json.loads, open(path)) if d.get("type") == "packet"]


def samples(packets, sensor, key, t0, t1):
    out = []
    for d in packets:
        if d.get("sensor") == sensor and t0 <= ts(d["timestamp"]) < t1:
            out.extend(d["reading"][key])
    return np.array(out, dtype=float)


def psd(x):
    """Spectrum divided by its 1-40 Hz total, the same relative scale as the alpha ratio in analyze_session.py."""
    f, p = welch(x - x.mean(), EEG_HZ, nperseg=EEG_HZ * 4)
    return f, p / p[(f >= 1) & (f <= 40)].sum()


def ppg_bpm(x):
    y = sosfiltfilt(butter(3, [0.7, 3.0], "band", fs=PPG_HZ, output="sos"), x)
    peaks, _ = find_peaks(y, distance=PPG_HZ * 0.4, prominence=y.std() * 0.5)
    return 60 * PPG_HZ / np.median(np.diff(peaks)) if len(peaks) > 5 else np.nan


def plot_alpha(muse, phases, out):
    # laid out like the head seen from above: forehead (AF) on top, behind the ears (TP) below
    fig, axes = plt.subplots(2, 2, figsize=(10, 6.5), sharex=True, sharey=True)
    for ax, ch in zip(axes.flat, ("AF7", "AF8", "TP9", "TP10")):
        for name, label, color in (("eyes_open", "Mở mắt", "#d97706"), ("eyes_closed", "Nhắm mắt", "#2563eb")):
            # average the spectra of every phase of this kind (each phase on its own, no gap stitching)
            spectra = [psd(samples(muse, f"eeg_{ch.lower()}", "samples_uv", t0, t1))
                       for n, t0, t1 in phases if n == name]
            f = spectra[0][0]
            p = np.mean([s[1] for s in spectra], axis=0)
            keep = (f >= 1) & (f <= 30)
            ax.semilogy(f[keep], p[keep], color=color, label=label, lw=1.6)
        ax.axvspan(8, 12, color="#e5e7eb", zorder=0)
        ax.text(10, 0.97, "alpha", ha="center", va="top", transform=ax.get_xaxis_transform(), fontsize=9)
        ax.set_title(f"Kênh {ch} ({'trán' if ch.startswith('AF') else 'sau tai'})")
        ax.grid(alpha=0.3)
    for ax in axes[1]:
        ax.set_xlabel("Tần số (Hz)")
    for ax in axes[:, 0]:
        ax.set_ylabel("Công suất tương đối")
    axes[0, 0].legend()
    fig.tight_layout()
    save(fig, out / "alpha-psd")


def plot_heart_rate(muse, h303, yx, marks, out):
    t_start, t_end = ts(marks[0]["start_utc"]), ts(marks[-1]["start_utc"])
    minutes = lambda t: (t - t_start).total_seconds() / 60

    fig, ax = plt.subplots(figsize=(10, 4))
    for m, n in zip(marks, marks[1:]):
        x0, x1 = minutes(ts(m["start_utc"])), minutes(ts(n["start_utc"]))
        ax.axvspan(x0, x1, color=PHASE_COLOR.get(m["phase"], "#f3f4f6"), zorder=0)
        ax.text((x0 + x1) / 2, 0.98, PHASE_VI[m["phase"]], ha="center", va="top",
                transform=ax.get_xaxis_transform(), fontsize=9)

    for packets, label, color in ((h303, "H303 (ECG)", "#dc2626"), (yx, "YX110", "#16a34a")):
        pts = [(minutes(ts(d["timestamp"])), d["reading"]["pulse_bpm"]) for d in packets
               if d["reading"].get("pulse_bpm") and t_start <= ts(d["timestamp"]) < t_end]
        ax.plot(*zip(*pts), color=color, label=label, lw=1.2)

    # Muse PPG: one estimate per 20 s window, every 5 s
    ppg = [(ts(d["timestamp"]), d["reading"]["samples"]) for d in muse if d.get("sensor") == "ppg_infrared"]
    pts, t = [], t_start
    while t + timedelta(seconds=20) <= t_end:
        x = np.array([v for tt, s in ppg if t <= tt < t + timedelta(seconds=20) for v in s], dtype=float)
        if len(x) > PPG_HZ * 15:
            pts.append((minutes(t + timedelta(seconds=10)), ppg_bpm(x)))
        t += timedelta(seconds=5)
    ax.plot(*zip(*pts), "o", color="#6b7280", ms=3, label="Muse 2 (PPG, cửa sổ 20 s)")

    ax.set_xlim(0, minutes(t_end))
    ax.set_xlabel("Thời gian từ lúc bắt đầu (phút)")
    ax.set_ylabel("Nhịp tim (BPM)")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    save(fig, out / "nhip-tim")


def save(fig, stem):
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".png"), dpi=200)
    plt.close(fig)
    print("wrote", stem.with_suffix(".pdf"), stem.with_suffix(".png"))


if __name__ == "__main__":
    marks = json.load(open(sys.argv[1]))
    muse, h303, yx = load(sys.argv[2]), load(sys.argv[3]), load(sys.argv[4])
    out = Path(sys.argv[5])
    out.mkdir(parents=True, exist_ok=True)
    phases = [(m["phase"], ts(m["start_utc"]) + timedelta(seconds=TRIM), ts(n["start_utc"]))
              for m, n in zip(marks, marks[1:])]
    plot_alpha(muse, phases, out)
    plot_heart_rate(muse, h303, yx, marks, out)
