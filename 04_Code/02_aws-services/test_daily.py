import os
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
for name in ("SESSIONS_TABLE", "SPOT_TABLE", "DAILY_TABLE"):
    os.environ.setdefault(name, "test")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-southeast-1")

import daily  # noqa: E402

DAY = date(2026, 10, 28)
NOW = "2026-10-29T17:05:00+00:00"


def session(ts, bpm, source="magene_h303"):  # DynamoDB hands numbers back as Decimal
    return {"metadata": {"timestamp_start": ts},
            "summary_insights": {"average_vitals": {"heart_rate_bpm": Decimal(str(bpm)), "heart_rate_source": source}}}


def spot(ts, spo2, pulse=72):
    return {"timestamp": ts, "type": "spo2", "source_device": "yuwell_yx110",
            "spo2_pct": Decimal(spo2), "pulse_bpm": Decimal(pulse)}


def test_day_is_vietnam_time():
    assert daily.day_range(DAY) == ("2026-10-27T17:00:00+00:00", "2026-10-28T16:59:59+00:00")


def test_summary_from_sessions_and_spots():
    r = daily.summarize(DAY, [session("2026-10-28T15:21:29+00:00", 75.2), session("2026-10-28T15:23:12+00:00", 73.7),
                              session("2026-10-28T15:58:29+00:00", 0)],
                        [spot("2026-10-28T15:21:33+00:00", 98), spot("2026-10-28T15:21:59+00:00", 99),
                         spot("2026-10-28T15:22:10+00:00", 100)], NOW)
    assert r["daily_summary"] == {"resting_heart_rate_bpm": 74, "average_blood_oxygen_pct": Decimal("99.0")}
    assert [h["bpm"] for h in r["heart_rate_log"]] == [75, 74]  # HR = 0 session left out
    assert [m["spo2_pct"] for m in r["blood_oxygen_log"]] == [99, 100]  # last reading of each minute
    assert "activities" not in r and "sleep_summary" not in r["daily_summary"]


def test_nothing_measured_gives_none():
    assert daily.summarize(DAY, [session("2026-10-28T15:58:29+00:00", 0)], [], NOW) is None


def test_muse_only_day_has_no_resting_hr():
    r = daily.summarize(DAY, [session("2026-10-28T15:21:29+00:00", 70, "muse2_ppg")], [], NOW)
    assert r["daily_summary"] == {} and r["heart_rate_log"][0]["source_device"] == "muse2_ppg"
