"""Posts queued rows (sent=0) to AWS and marks them sent:
  session - one summary per POST /sessions
  spot    - YX110 readings, in batches of 100 to POST /measurements (rejected ones get sent=-1)
Needs SENSORS_API and SENSORS_API_KEY in the environment (source ~/.sensors_env)."""

import json
import os
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

BATCH = 100
MAX_SPOTS = 1000  # shortcut: caps one cron run at 10 requests, a big backlog drains over several minutes


def post(path, body):
    req = urllib.request.Request(f"{os.environ['SENSORS_API']}{path}", data=body.encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "x-api-key": os.environ["SENSORS_API_KEY"]})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)


def to_measurement(key, ts, payload):
    """Queue row -> spot_measurement_schema.json (the server adds user_id). PI is dropped: the YX110 always says 6.0."""
    p = json.loads(payload)
    return {"measurement_id": key, "timestamp": ts, "type": "spo2", "source_device": p["source"],
            "spo2_pct": p["spo2_pct"], "pulse_bpm": p["pulse_bpm"]}


def main(db):
    for key, payload in db.execute("SELECT key, payload FROM queue WHERE kind = 'session' AND sent = 0").fetchall():
        try:
            post("/sessions", payload)
        except urllib.error.HTTPError as exc:  # rejected (e.g. schema): keep it unsent, show why
            print(key, exc.code, exc.read()[:300])
            continue
        except OSError as exc:  # offline: try again next run
            print("offline:", exc)
            return
        db.execute("UPDATE queue SET sent = 1 WHERE key = ?", (key,))
        db.commit()
        print("sent", key)

    rows = db.execute("SELECT key, ts, payload FROM queue WHERE kind = 'spot' AND sent = 0 ORDER BY ts LIMIT ?",
                      (MAX_SPOTS,)).fetchall()
    for i in range(0, len(rows), BATCH):
        chunk = rows[i:i + BATCH]
        try:
            result = post("/measurements", json.dumps([to_measurement(*r) for r in chunk]))
        except urllib.error.HTTPError as exc:  # whole batch refused: keep it unsent, show why
            print("spot", exc.code, exc.read()[:300])
            return
        except OSError as exc:
            print("offline:", exc)
            return
        rejected = {r["measurement_id"] for r in result["rejected"]}
        db.executemany("UPDATE queue SET sent = ? WHERE key = ?", [(-1 if k in rejected else 1, k) for k, _, _ in chunk])
        db.commit()
        print(f"sent {len(chunk) - len(rejected)} spot readings", *result["rejected"])


if __name__ == "__main__":
    main(sqlite3.connect(Path(__file__).parent / "queue.db"))
