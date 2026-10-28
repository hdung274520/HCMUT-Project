"""Posts queued session summaries (kind='session', sent=0) to POST /sessions and marks them sent.
Needs SENSORS_API and SENSORS_API_KEY in the environment (source ~/.sensors_env)."""

import os
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

db = sqlite3.connect(Path(__file__).parent / "queue.db")
rows = db.execute("SELECT key, payload FROM queue WHERE kind = 'session' AND sent = 0").fetchall()
for key, payload in rows:
    req = urllib.request.Request(f"{os.environ['SENSORS_API']}/sessions", data=payload.encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "x-api-key": os.environ["SENSORS_API_KEY"]})
    try:
        urllib.request.urlopen(req, timeout=10)
    except urllib.error.HTTPError as exc:  # rejected (e.g. schema): keep it unsent, show why
        print(key, exc.code, exc.read()[:300])
        continue
    except OSError as exc:  # offline: try again next run
        print("offline:", exc)
        break
    db.execute("UPDATE queue SET sent = 1 WHERE key = ?", (key,))
    db.commit()
    print("sent", key)
