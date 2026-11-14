import json
import sqlite3
from pathlib import Path

import jsonschema

import upload

SCHEMA = json.loads((Path(__file__).parent.parent / "schemas/spot_measurement_schema.json").read_text())
SPOT = {"source": "yuwell_yx110", "spo2_pct": 97, "pulse_bpm": 72, "pi_pct": 6.0}


def queue(*rows):
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE queue (key TEXT PRIMARY KEY, kind TEXT, ts TEXT, payload TEXT, sent INTEGER DEFAULT 0)")
    db.executemany("INSERT INTO queue (key, kind, ts, payload) VALUES (?, ?, ?, ?)", rows)
    return db


def sent(db):
    return dict(db.execute("SELECT key, sent FROM queue"))


def test_spot_row_matches_schema():
    m = upload.to_measurement("spot:yx110:2026-10-29T10:00:00+00:00", "2026-10-29T10:00:00+00:00", json.dumps(SPOT))
    jsonschema.validate({**m, "user_id": "demo"}, SCHEMA)
    assert "pi_pct" not in m


def test_marks_saved_and_rejected(monkeypatch):
    posts = []

    def fake_post(path, body):
        posts.append(path)
        return {"saved": ["a"], "rejected": [{"measurement_id": "b", "error": "x"}]} if path == "/measurements" else {}

    monkeypatch.setattr(upload, "post", fake_post)
    db = queue(("s", "session", "t0", "{}"), ("a", "spot", "t1", json.dumps(SPOT)), ("b", "spot", "t2", json.dumps(SPOT)))
    upload.main(db)
    assert posts == ["/sessions", "/measurements"]
    assert sent(db) == {"s": 1, "a": 1, "b": -1}


def test_offline_keeps_everything_unsent(monkeypatch):
    def offline(path, body):
        raise OSError("timed out")

    monkeypatch.setattr(upload, "post", offline)
    db = queue(("s", "session", "t0", "{}"), ("a", "spot", "t1", json.dumps(SPOT)))
    upload.main(db)
    assert sent(db) == {"s": 0, "a": 0}
