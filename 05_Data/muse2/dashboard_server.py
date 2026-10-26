"""
Connects to a Muse 2, starts every stream it offers (4 EEG channels at 256 Hz,
3 PPG channels at 64 Hz, accelerometer, gyroscope, battery/telemetry, control
replies), pushes decoded packets to browser clients over a local WebSocket and
serves the dashboard page. Every notification is saved to raw_captures/.

Usage:
    python3 dashboard_server.py [--address XX:XX:XX:XX:XX:XX] [--preset p50]
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

from decode import CONTROL_UUID, SENSORS, ControlReassembler, decode, encode_command

RAW_CAPTURES_DIR = Path(__file__).parent / "raw_captures"
HTTP_PORT = 8082
WS_PORT = 8767
clients = set()


async def find_device(address: str | None, timeout: float = 20.0):
    print(f"Scanning for {address or 'a Muse'} ({timeout}s)...")
    if address:
        device = await BleakScanner.find_device_by_address(address, timeout=timeout)
    else:
        device = await BleakScanner.find_device_by_filter(
            lambda d, _: bool(d.name and d.name.startswith("Muse")), timeout=timeout)
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


async def stream(client: BleakClient, preset: str, log_file):
    loop = asyncio.get_running_loop()
    control = ControlReassembler()

    def emit(record: dict):
        log_file.write(json.dumps(record) + "\n")
        asyncio.run_coroutine_threadsafe(broadcast(record), loop)

    def packet(sensor: str, uuid: str, data: bytes, reading: dict):
        emit({"type": "packet", "timestamp": datetime.now(timezone.utc).isoformat(),
              "sensor": sensor, "characteristic_uuid": uuid, "raw_hex": data.hex(), "reading": reading})

    def on_sensor(characteristic, data: bytearray):
        sensor = SENSORS[characteristic.uuid]
        try:
            packet(sensor, characteristic.uuid, bytes(data), decode(sensor, bytes(data)))
        except Exception as exc:  # keep streaming, keep the raw bytes
            packet(sensor, characteristic.uuid, bytes(data), {"decode_error": str(exc)})

    def on_control(characteristic, data: bytearray):
        reply = control.feed(bytes(data))
        packet("control", characteristic.uuid, bytes(data), reply or {})
        if reply is not None:
            print(f"control reply: {reply}", flush=True)

    available = {c.uuid for s in client.services for c in s.characteristics}
    for uuid in SENSORS:
        if uuid in available:
            await client.start_notify(uuid, on_sensor)
        else:
            print(f"Characteristic {SENSORS[uuid]} ({uuid}) not offered by this device")
    await client.start_notify(CONTROL_UUID, on_control)

    # halt, choose preset, request version + status, start streaming
    for cmd in ("h", preset, "v1", "s", "d"):
        await client.write_gatt_char(CONTROL_UUID, encode_command(cmd), response=False)
        await asyncio.sleep(0.2)
    print(f"Streaming (preset {preset})")

    while client.is_connected:
        log_file.flush()
        await asyncio.sleep(1)


async def ble_loop(address: str | None, preset: str):
    while True:
        device = await find_device(address)
        if device is None:
            await broadcast({"type": "status", "connected": False, "message": "Device not found, retrying..."})
            await asyncio.sleep(3)
            continue

        log_file = None
        try:
            async with BleakClient(device) as client:
                await broadcast({"type": "status", "connected": True, "message": f"Connected to {device.name} {device.address}"})
                RAW_CAPTURES_DIR.mkdir(exist_ok=True)
                log_file = open(RAW_CAPTURES_DIR / f"{datetime.now():%Y%m%d_%H%M%S}.jsonl", "w")
                await stream(client, preset, log_file)
                print("Disconnected")
        except Exception as exc:
            print(f"BLE error: {exc}")
        finally:
            if log_file:
                log_file.close()

        await broadcast({"type": "status", "connected": False, "message": "Disconnected, retrying..."})
        await asyncio.sleep(3)


def serve_http():
    directory = Path(__file__).parent

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(directory), **kwargs)

    ThreadingHTTPServer(("localhost", HTTP_PORT), Handler).serve_forever()


async def main(address: str | None, preset: str):
    Thread(target=serve_http, daemon=True).start()
    url = f"http://localhost:{HTTP_PORT}/index.html"
    print(f"Dashboard: {url}")
    webbrowser.open(url)

    async with websockets.serve(ws_handler, "localhost", WS_PORT):
        await ble_loop(address, preset)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--address", help="Muse BLE MAC address (default: first device named Muse*)")
    parser.add_argument("--preset", default="p50", help="p50 = EEG + PPG on Muse 2, p21 = EEG only")
    args = parser.parse_args()

    asyncio.run(main(args.address, args.preset))
