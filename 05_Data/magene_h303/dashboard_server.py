"""
Connects to the Magene H303 chest strap, decodes the standard BLE Heart Rate
Measurement characteristic (0x2A37), pushes readings to connected browser
clients over a local WebSocket, and serves the dashboard page.

Usage:
    python3 dashboard_server.py [--address D9:94:F2:69:20:DE]
"""

import argparse
import asyncio
import json
import webbrowser
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import websockets
from bleak import BleakClient, BleakScanner

HEART_RATE_MEASUREMENT_UUID = "00002a37-0000-1000-8000-00805f9b34fb"
RAW_CAPTURES_DIR = Path(__file__).parent / "raw_captures"
HTTP_PORT = 8081
WS_PORT = 8766
clients = set()


def parse_heart_rate(data: bytes):
    """Heart Rate Measurement per the Bluetooth SIG Heart Rate Service spec."""
    flags = data[0]
    i = 1
    if flags & 0x01:
        hr = int.from_bytes(data[i:i + 2], "little")
        i += 2
    else:
        hr = data[i]
        i += 1

    contact_supported = bool(flags & 0x04)
    sensor_contact = bool(flags & 0x02) if contact_supported else None

    if flags & 0x08:
        i += 2  # energy expended, unused

    rr_ms = []
    if flags & 0x10:
        while i + 1 < len(data):
            rr_ms.append(round(int.from_bytes(data[i:i + 2], "little") * 1000 / 1024))
            i += 2

    return {"pulse_bpm": hr or None, "rr_ms": rr_ms, "sensor_contact": sensor_contact}


async def find_device(address: str, timeout: float = 20.0):
    print(f"Scanning for {address} ({timeout}s)...")
    device = await BleakScanner.find_device_by_address(address, timeout=timeout)
    if device:
        print(f"Found {device.name} ({device.address})")
    return device


async def broadcast(message: dict):
    if not clients:
        return
    payload = json.dumps(message)
    await asyncio.gather(*(ws.send(payload) for ws in clients), return_exceptions=True)


async def ws_handler(websocket):
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.discard(websocket)


async def ble_loop(address: str):
    while True:
        device = await find_device(address)
        if device is None:
            await broadcast({"type": "status", "connected": False, "message": "Device not found, retrying..."})
            await asyncio.sleep(3)
            continue

        try:
            async with BleakClient(device) as client:
                await broadcast({"type": "status", "connected": True, "message": f"Connected to {device.address}"})
                print(f"Connected to {device.address}")

                RAW_CAPTURES_DIR.mkdir(exist_ok=True)
                log_file = open(RAW_CAPTURES_DIR / f"{datetime.now():%Y%m%d_%H%M%S}.jsonl", "w")
                loop = asyncio.get_running_loop()

                def handler(characteristic, data: bytearray):
                    record = {
                        "type": "packet",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "characteristic_uuid": characteristic.uuid,
                        "raw_hex": data.hex(),
                        "reading": parse_heart_rate(bytes(data)),
                    }
                    print(f"{record['timestamp']} {record['raw_hex']} {record['reading']}", flush=True)
                    log_file.write(json.dumps(record) + "\n")
                    log_file.flush()
                    asyncio.run_coroutine_threadsafe(broadcast(record), loop)

                await client.start_notify(HEART_RATE_MEASUREMENT_UUID, handler)
                print("Subscribed to Heart Rate Measurement")

                while client.is_connected:
                    await asyncio.sleep(1)
                log_file.close()
                print("Disconnected")
        except Exception as exc:
            print(f"BLE error: {exc}")

        await broadcast({"type": "status", "connected": False, "message": "Disconnected, retrying..."})
        await asyncio.sleep(3)


def serve_http():
    directory = Path(__file__).parent

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

    server = ThreadingHTTPServer(("localhost", HTTP_PORT), Handler)
    server.serve_forever()


async def main(address: str):
    Thread(target=serve_http, daemon=True).start()
    url = f"http://localhost:{HTTP_PORT}/index.html"
    print(f"Dashboard: {url}")
    webbrowser.open(url)

    async with websockets.serve(ws_handler, "localhost", WS_PORT):
        await ble_loop(address)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", default="D9:94:F2:69:20:DE", help="H303 BLE MAC address")
    args = parser.parse_args()

    asyncio.run(main(args.address))
