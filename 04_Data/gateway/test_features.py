import numpy as np
from features import EEG_HZ, N_EEG_FEATURES, PPG_HZ, eeg_features, hrv, ppg_bpm

rng = np.random.default_rng(0)


def test_alpha_dominates_10hz_signal():
    t = np.arange(EEG_HZ * 4) / EEG_HZ
    w = np.array([np.sin(2 * np.pi * 10 * t) * 20 + rng.normal(0, 2, t.size) for _ in range(4)])
    f = eeg_features(w)
    assert len(f) == N_EEG_FEATURES
    assert f[5 + 2] > 0.8  # relative alpha, channel 0


def test_hrv_matches_hand_calculation():
    r = hrv([800, 810, 800, 810, 800, 810, 800, 810, 800, 810])
    assert abs(r["rmssd_ms"] - 10) < 1e-9 and abs(r["hr_bpm"] - 60000 / 805) < 1e-9
    assert hrv([800] * 5) is None


def test_ppg_bpm_72():
    t = np.arange(PPG_HZ * 30) / PPG_HZ
    assert abs(ppg_bpm(np.sin(2 * np.pi * 1.2 * t) + rng.normal(0, .1, t.size)) - 72) < 2


def test_ppg_noise_rejected():
    assert ppg_bpm(rng.normal(0, 1, PPG_HZ * 30)) is None


def test_short_window_rejected():
    try:
        eeg_features(np.zeros((4, 100)))
    except ValueError:
        return
    raise AssertionError
