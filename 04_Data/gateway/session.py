"""Builds the end-of-session summary in the shape of 05_Data/schemas/active_session_schema.json."""

import statistics

# Per-channel feature layout from features.py: indices 5..9 are relative delta, theta, alpha, beta, gamma.
REL = {"delta": 5, "theta": 6, "alpha": 7, "beta": 8}
PER_CHANNEL = 18


def _mean(values):
    return round(statistics.fmean(values), 1) if values else None


def summarize(session_id, session_type, start, end, devices, h303_bpm, ppg_bpm, rmssd_ms, eeg_rows):
    """start/end: aware datetimes. eeg_rows: lists of 72 features. Returns a dict for POST /sessions."""
    use_h303 = bool(h303_bpm)
    vitals = {
        "heart_rate_bpm": _mean(h303_bpm if use_h303 else ppg_bpm) or 0,
        # shortcut: H303 RR arrives at a fixed 2 Hz with repeated values, so this RMSSD is not
        # a true HRV yet; replace once beat-to-beat RR is confirmed or PPG HRV exists.
        "hrv_ms": _mean(rmssd_ms) or 0,
        "heart_rate_source": "magene_h303" if use_h303 else "muse2_ppg",
    }
    eeg = {band: round(statistics.fmean(row[ch * PER_CHANNEL + i] for row in eeg_rows for ch in range(4)), 4)
           if eeg_rows else 0 for band, i in REL.items()}
    return {
        "metadata": {
            "session_id": session_id,
            "session_type": session_type,
            "devices": sorted(d for d in devices if d in ("muse2", "magene_h303")),
            "timestamp_start": start.isoformat(timespec="seconds"),
            "timestamp_end": end.isoformat(timespec="seconds"),
            "duration_seconds": int((end - start).total_seconds()),
            "user_context": {},
        },
        "summary_insights": {
            "overall_score": 0,  # shortcut: no scoring model yet, 0 = not computed
            "average_vitals": vitals,
            "average_eeg": eeg,
            "ai_summary_bullets": [],
        },
        "cognitive_states": {"state_distribution": {}, "state_blocks": []},
    }
