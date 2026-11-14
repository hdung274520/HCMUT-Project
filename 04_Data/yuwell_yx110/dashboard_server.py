"""
Connects to the YX110, pushes every raw BLE notification to connected
browser clients over a local WebSocket, and serves the dashboard page.

The protocol isn't parsed yet (see README.md), so this shows the live raw
byte stream rather than real SpO2/pulse numbers — useful for watching the
device respond in real time while reverse-engineering the format.

Usage:
    python3 dashboard_server.py [--address E4:15:E4:C8:E0:40]
    Then open index.html in a browser.
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

RAW_CAPTURES_DIR = Path(__file__).parent / "raw_captures"
HTTP_PORT = 8080
WS_PORT = 8765
clients = set()


async def find_device(address: str, timeout: float = 20.0):
    print(f"Scanning for {address} ({timeout}s)...")
    device = await BleakScanner.find_device_by_address(address, timeout=timeout)
    if device:
        print(f"Found {device.name} ({device.address})")
    return device


def parse_packet(data: bytes):
    """Decode a 0x55 reading packet, matching OximeterManager.f() in the HealthCare+ app.

    fe | len | 0x55 | pulse (u16 BE) | spo2 | pi*1000 (u16 BE) | counter | checksum
    0x56 packets (pulse waveform) are ignored. A value of 0 means "not ready yet".
    The YX110 always reports PI = 6.0 regardless of reading, so it's likely a placeholder.
    """
    if len(data) < 10 or data[0] != 0xFE or data[1] != len(data) or data[2] != 0x55:
        return None
    if sum(data[:-1]) & 0xFF != data[-1]:
        return None
    spo2 = data[5]
    if spo2 > 100:
        return None
    pulse = (data[3] << 8) | data[4]
    pi = ((data[6] << 8) | data[7]) / 1000
    return {"spo2_pct": spo2 or None, "pulse_bpm": pulse or None, "pi_pct": pi}


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

                for service in client.services:
                    for char in service.characteristics:
                        print(f"  {service.uuid} / {char.uuid} {char.properties}")

                notify_chars = [
                    char
                    for service in client.services
                    for char in service.characteristics
                    if char.uuid.startswith("0000ffe4")
                ]

                RAW_CAPTURES_DIR.mkdir(exist_ok=True)
                log_file = open(RAW_CAPTURES_DIR / f"{datetime.now():%Y%m%d_%H%M%S}.jsonl", "w")

                def make_handler(loop):
                    def handler(characteristic, data: bytearray):
                        record = {
                            "type": "packet",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "characteristic_uuid": characteristic.uuid,
                            "raw_hex": data.hex(),
                            "reading": parse_packet(bytes(data)),
                        }
                        print(f"{record['timestamp']} {characteristic.uuid[4:8]} {record['raw_hex']}", flush=True)
                        log_file.write(json.dumps(record) + "\n")
                        log_file.flush()
                        asyncio.run_coroutine_threadsafe(broadcast(record), loop)

                    return handler

                handler = make_handler(asyncio.get_running_loop())
                for char in notify_chars:
                    try:
                        await client.start_notify(char, handler)
                        print(f"Subscribed to {char.uuid}")
                    except Exception as exc:
                        print(f"Could not subscribe to {char.uuid}: {exc}")

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
    parser.add_argument("--address", default="E4:15:E4:C8:E0:40", help="YX110 BLE MAC address")
    args = parser.parse_args()

    asyncio.run(main(args.address))
