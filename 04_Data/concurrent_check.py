"""
Connects to Muse 2, Magene H303 and Yuwell YX110 on ONE Bluetooth adapter at
the same time and reports, per device, how many notifications arrived, the
rate, the longest silence and any disconnects. Run it on the dev PC and on the
Raspberry Pi to see whether the adapter can hold all three.

Usage (from 05_Data/, any of the sensor venvs works):
    python3 concurrent_check.py [--minutes 10]

The YX110 only talks while a finger is in it and switches itself off after a
measurement, so its disconnects are expected; Muse and H303 should stay up.
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

from bleak import BleakClient, BleakScanner

sys.path.insert(0, str(Path(__file__).parent / "muse2"))
from decode import CONTROL_UUID, SENSORS, encode_command  # noqa: E402

DEVICES = {
    "muse2": {"address": None, "name": "Muse", "notify": list(SENSORS) + [CONTROL_UUID]},
    "h303": {"address": "D9:94:F2:69:20:DE", "notify": ["00002a37-0000-1000-8000-00805f9b34fb"]},
    "yx110": {"address": "E4:15:E4:C8:E0:40", "notify": ["0000ffe4-0000-1000-8000-00805f9b34fb"]},
}
stats = {k: {"packets": 0, "first": None, "last": None, "max_gap": 0.0, "connects": 0, "drops": 0} for k in DEVICES}


scan_lock = asyncio.Lock()  # BlueZ allows one active scan at a time


async def find(cfg):
    async with scan_lock:
        if cfg["address"]:
            return await BleakScanner.find_device_by_address(cfg["address"], timeout=20)
        return await BleakScanner.find_device_by_filter(
            lambda d, _: bool(d.name and d.name.startswith(cfg["name"])), timeout=20)


async def run_device(key, cfg, deadline):
    s = stats[key]

    def on_data(_, data):
        now = time.monotonic()
        if s["last"] is not None:
            s["max_gap"] = max(s["max_gap"], now - s["last"])
        s["first"] = s["first"] or now
        s["last"] = now
        s["packets"] += 1

    while time.monotonic() < deadline:
        device = await find(cfg)
        if device is None:
            print(f"{time.strftime('%H:%M:%S')} [{key}] not found, retrying", flush=True)
            continue
        try:
            async with BleakClient(device) as client:
                s["connects"] += 1
                print(f"{time.strftime('%H:%M:%S')} [{key}] connected", flush=True)
                available = {c.uuid for sv in client.services for c in sv.characteristics}
                for uuid in cfg["notify"]:
                    if uuid in available:
                        await client.start_notify(uuid, on_data)
                if key == "muse2":
                    for cmd in ("h", "p50", "s", "d"):
                        await client.write_gatt_char(CONTROL_UUID, encode_command(cmd), response=False)
                        await asyncio.sleep(0.2)
                while client.is_connected and time.monotonic() < deadline:
                    await asyncio.sleep(1)
                if time.monotonic() < deadline:
                    s["drops"] += 1
                    print(f"{time.strftime('%H:%M:%S')} [{key}] DROPPED", flush=True)
        except Exception as exc:
            s["drops"] += 1
            print(f"{time.strftime('%H:%M:%S')} [{key}] error: {exc}", flush=True)
        await asyncio.sleep(2)


async def main(minutes):
    deadline = time.monotonic() + minutes * 60
    await asyncio.gather(*(run_device(k, c, deadline) for k, c in DEVICES.items()))
    print("\ndevice  connects drops packets  rate/s  longest_silence_s")
    for k, s in stats.items():
        span = (s["last"] - s["first"]) if s["first"] and s["last"] and s["last"] > s["first"] else 0
        rate = s["packets"] / span if span else 0
        print(f"{k:7} {s['connects']:8} {s['drops']:5} {s['packets']:7} {rate:7.1f} {s['max_gap']:10.1f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minutes", type=float, default=10)
    asyncio.run(main(parser.parse_args().minutes))
