"""
One process on the Raspberry Pi that reads Muse 2, Magene H303 and Yuwell YX110
at the same time and writes, once per second, the features to an offline SQLite
queue (queue.db):
  eeg   - 72 EEG features over the last 4 s (see features.py)
  hr    - HR/HRV from the H303 RR intervals (last 60 s), and HR from Muse PPG
  spot  - SpO2 + pulse from the YX110, as it reports them
Each run is one session: every BLE notification goes to sessions/<id>.jsonl,
and on exit (timeout, Ctrl+C or SIGTERM) a summary in the shape of
active_session_schema.json goes to sessions/<id>_summary.json and the queue
(kind 'session').
Rows have a unique key, so re-inserting the same reading is a no-op; `sent`
stays 0 until the uploader (Milestone 2) posts them to AWS.

Usage (from 05_Data/gateway/):
    venv/bin/python gateway.py [--minutes N] [--type meditation]   # default: run until Ctrl+C
"""

import argparse
import asyncio
import importlib.util
import json
import signal
import sqlite3
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from bleak import BleakClient, BleakScanner

from features import EEG_HZ, PPG_HZ, eeg_features, hrv, ppg_bpm
from session import summarize

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "muse2"))
from decode import CONTROL_UUID, SENSORS, decode, encode_command  # noqa: E402


def _load(path, name):  # the three dashboards share a module name, so load by path
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parse_heart_rate = _load(ROOT / "magene_h303/dashboard_server.py", "h303_server").parse_heart_rate
parse_yx110 = _load(ROOT / "yuwell_yx110/dashboard_server.py", "yx110_server").parse_packet

H303_ADDR, YX110_ADDR = "D9:94:F2:69:20:DE", "E4:15:E4:C8:E0:40"
HR_UUID, YX110_UUID = "00002a37-0000-1000-8000-00805f9b34fb", "0000ffe4-0000-1000-8000-00805f9b34fb"
CHANNELS = ("eeg_tp9", "eeg_af7", "eeg_af8", "eeg_tp10")

eeg = {c: deque(maxlen=EEG_HZ * 4) for c in CHANNELS}
ppg = deque(maxlen=PPG_HZ * 30)
rr = deque()  # (monotonic time, rr_ms)
h303_bpm = None
SESSIONS_DIR = Path(__file__).parent / "sessions"
raw_file = None
devices = set()  # schema device names that connected during the session
collected = {"h303_bpm": [], "ppg_bpm": [], "rmssd_ms": [], "eeg": []}


def raw(device, uuid, data):
    raw_file.write(json.dumps({"t": datetime.now(timezone.utc).isoformat(), "device": device,
                               "uuid": uuid, "raw_hex": bytes(data).hex()}) + "\n")


class Queue:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS queue (
            key TEXT PRIMARY KEY, kind TEXT, ts TEXT, payload TEXT, sent INTEGER DEFAULT 0)""")

    def put(self, kind, ts, payload, source=""):
        self.db.execute("INSERT OR IGNORE INTO queue (key, kind, ts, payload) VALUES (?, ?, ?, ?)",
                        (f"{kind}:{source}:{ts}", kind, ts, json.dumps(payload)))
        self.db.commit()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(key, msg):
    print(f"{time.strftime('%H:%M:%S')} [{key}] {msg}", flush=True)


def on_muse(characteristic, data):
    raw("muse2", characteristic.uuid, data)
    sensor = SENSORS.get(characteristic.uuid)
    if sensor in eeg:
        eeg[sensor].extend(decode(sensor, bytes(data))["samples_uv"])
    elif sensor == "ppg_infrared":
        ppg.extend(decode(sensor, bytes(data))["samples"])


def on_h303(characteristic, data):
    global h303_bpm
    raw("magene_h303", characteristic.uuid, data)
    r = parse_heart_rate(bytes(data))
    h303_bpm = r["pulse_bpm"]
    rr.extend((time.monotonic(), v) for v in r["rr_ms"])


def make_on_yx110(q):
    def on_yx110(characteristic, data):
        raw("yuwell_yx110", characteristic.uuid, data)
        r = parse_yx110(bytes(data))
        if r and r["spo2_pct"] and r["pulse_bpm"]:
            q.put("spot", now(), {"source": "yuwell_yx110", **r}, "yx110")
    return on_yx110


scan_lock = asyncio.Lock()  # BlueZ allows one active scan at a time


async def run_device(key, find, notify, on_connect=None):
    while True:
        async with scan_lock:
            device = await find()
        if device is None:
            log(key, "not found, retrying")
            continue
        try:
            async with BleakClient(device) as client:
                log(key, "connected")
                devices.add({"h303": "magene_h303", "yx110": "yuwell_yx110"}.get(key, key))
                for uuid, handler in notify.items():
                    await client.start_notify(uuid, handler)
                if on_connect:
                    await on_connect(client)
                while client.is_connected:
                    await asyncio.sleep(1)
                log(key, "disconnected")
        except Exception as exc:
            log(key, f"error: {exc}")
        await asyncio.sleep(2)


async def start_muse(client):
    for cmd in ("h", "p50", "s", "d"):  # halt, EEG+PPG preset, status, start
        await client.write_gatt_char(CONTROL_UUID, encode_command(cmd), response=False)
        await asyncio.sleep(0.2)


async def features_loop(q):
    while True:
        await asyncio.sleep(1)
        raw_file.flush()
        ts = now()
        n = min(len(b) for b in eeg.values())
        if n >= EEG_HZ * 2:
            f = eeg_features([list(b)[-n:] for b in eeg.values()])
            collected["eeg"].append(f)
            q.put("eeg", ts, {"features": f}, "muse2")
        cutoff = time.monotonic() - 60
        while rr and rr[0][0] < cutoff:
            rr.popleft()
        if (h := hrv([v for _, v in rr])) or h303_bpm:
            if h303_bpm:
                collected["h303_bpm"].append(h303_bpm)
            if h:
                collected["rmssd_ms"].append(h["rmssd_ms"])
            q.put("hr", ts, {"source": "magene_h303", "pulse_bpm": h303_bpm, **(h or {})}, "h303")
        if bpm := ppg_bpm(ppg):
            collected["ppg_bpm"].append(bpm)
            q.put("hr", ts, {"source": "muse2_ppg", "hr_bpm": bpm}, "muse2")


async def main(minutes, session_type):
    global raw_file
    q = Queue(Path(__file__).parent / "queue.db")
    start = datetime.now(timezone.utc)
    session_id = f"{start.astimezone():%Y%m%d_%H%M%S}"
    SESSIONS_DIR.mkdir(exist_ok=True)
    raw_file = open(SESSIONS_DIR / f"{session_id}.jsonl", "w")
    try:
        await run_all(q, minutes)
    finally:
        raw_file.close()
        summary = summarize(session_id, session_type, start, datetime.now(timezone.utc), devices,
                            collected["h303_bpm"], collected["ppg_bpm"], collected["rmssd_ms"], collected["eeg"])
        (SESSIONS_DIR / f"{session_id}_summary.json").write_text(json.dumps(summary, indent=2))
        q.put("session", summary["metadata"]["timestamp_start"], summary)
        print(f"Session {session_id} saved: {summary['metadata']['duration_seconds']} s, "
              f"HR {summary['summary_insights']['average_vitals']['heart_rate_bpm']}", flush=True)


async def run_all(q, minutes):
    muse_notify = {u: on_muse for u in SENSORS} | {CONTROL_UUID: lambda *_: None}
    tasks = [
        run_device("muse2", lambda: BleakScanner.find_device_by_filter(
            lambda d, _: bool(d.name and d.name.startswith("Muse")), timeout=20), muse_notify, start_muse),
        run_device("h303", lambda: BleakScanner.find_device_by_address(H303_ADDR, timeout=20),
                   {HR_UUID: on_h303}),
        run_device("yx110", lambda: BleakScanner.find_device_by_address(YX110_ADDR, timeout=20),
                   {YX110_UUID: make_on_yx110(q)}),
        features_loop(q),
    ]
    if minutes:
        await asyncio.wait_for(asyncio.gather(*tasks), minutes * 60)
    else:
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minutes", type=float, default=0)
    parser.add_argument("--type", default="meditation",
                        choices=["sleep", "meditation", "focus", "stress", "workout"])
    args = parser.parse_args()

    def stop(*_):  # pkill sends SIGTERM; turn it into Ctrl+C so the summary still gets written
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, stop)
    try:
        asyncio.run(main(args.minutes, args.type))
    except (KeyboardInterrupt, TimeoutError):
        pass
