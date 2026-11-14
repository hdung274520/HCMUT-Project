"""
Countdown for the Muse 2 + H303 + YX110 recording session. Prints what to do
now, beeps at each change, and saves the UTC start time of every phase so the
analysis can cut the recordings by phase.

Usage (4th terminal, start it when all three dashboards show Connected):
    python3 session_timer.py
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PHASES = [  # (name, instruction, seconds)
    ("settle", "SETTLE - ngoi yen, khong nhai", 60),
    ("eyes_open", "EYES OPEN - nhin mot diem", 120),
    ("eyes_closed", "EYES CLOSED - nham mat", 120),
    ("eyes_open", "EYES OPEN - nhin mot diem", 120),
    ("eyes_closed", "EYES CLOSED - nham mat", 120),
    ("yx110", "YX110 - kep ngon tay (tay khong deo gi, giu yen)", 90),
    ("done", "DONE - bam Ctrl+C o ca 3 dashboard", 0),
]

marks = []
for name, text, secs in PHASES:
    marks.append({"phase": name, "start_utc": datetime.now(timezone.utc).isoformat()})
    print(f"\a\n>>> {text}  ({secs}s)", flush=True)
    end = time.monotonic() + secs
    while (left := end - time.monotonic()) > 0:
        sys.stdout.write(f"\r    con {int(left) // 60}:{int(left) % 60:02d}   ")
        sys.stdout.flush()
        time.sleep(0.5)

out = Path(__file__).parent / f"session_marks_{datetime.now():%Y%m%d_%H%M%S}.json"
out.write_text(json.dumps(marks, indent=2))
print(f"\nSaved {out}")
