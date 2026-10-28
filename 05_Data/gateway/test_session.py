import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jsonschema

from session import summarize

SCHEMA = json.loads((Path(__file__).parent.parent / "schemas/active_session_schema.json").read_text())
START = datetime(2026, 10, 28, 14, 0, tzinfo=timezone.utc)


def test_summary_matches_schema_and_prefers_h303():
    s = summarize("x", "meditation", START, START + timedelta(minutes=10), {"muse2", "magene_h303", "yuwell_yx110"},
                  [70, 72], [60], [6.0], [[0.25] * 72])
    jsonschema.validate(s, SCHEMA)
    v = s["summary_insights"]["average_vitals"]
    assert v["heart_rate_bpm"] == 71 and v["heart_rate_source"] == "magene_h303"
    assert s["metadata"]["duration_seconds"] == 600 and s["metadata"]["devices"] == ["magene_h303", "muse2"]


def test_empty_session_still_valid():
    s = summarize("x", "focus", START, START, set(), [], [65], [], [])
    jsonschema.validate(s, SCHEMA)
    assert s["summary_insights"]["average_vitals"]["heart_rate_source"] == "muse2_ppg"
