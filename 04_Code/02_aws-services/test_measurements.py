import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
os.environ.setdefault("TABLE_NAME", "test")
os.environ.setdefault("AWS_DEFAULT_REGION", "ap-southeast-1")

import measurements  # noqa: E402

GOOD = {"measurement_id": "spot:yx110:t1", "timestamp": "2026-10-29T10:00:00+00:00", "type": "spo2",
        "source_device": "yuwell_yx110", "spo2_pct": 97, "pulse_bpm": 72}


class FakeTable:
    def __init__(self):
        self.items = []

    def batch_writer(self, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def put_item(self, Item):
        self.items.append(Item)


def post(body, monkeypatch):
    table = FakeTable()
    monkeypatch.setattr(measurements, "table", table)
    resp = measurements.handler({"httpMethod": "POST", "body": body}, None)
    return resp["statusCode"], json.loads(resp["body"]), table.items


def test_saves_valid_and_reports_invalid(monkeypatch):
    bad = {**GOOD, "measurement_id": "spot:yx110:t2", "pulse_bpm": 300}
    status, body, items = post(json.dumps([GOOD, bad, "junk"]), monkeypatch)
    assert status == 200 and body["saved"] == ["spot:yx110:t1"]
    assert [r["measurement_id"] for r in body["rejected"]] == ["spot:yx110:t2", None]
    assert items == [{**GOOD, "user_id": "demo"}]


def test_rejects_non_list(monkeypatch):
    assert post(json.dumps(GOOD), monkeypatch)[0] == 400
    assert post("not json", monkeypatch)[0] == 400
