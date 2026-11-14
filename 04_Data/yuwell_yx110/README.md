# Yuwell YX110 BLE reader

Reads SpO2 and pulse from the Yuwell YX110 pulse oximeter over BLE
(device `Yuwell BO-YX110-E040`, MAC `E4:15:E4:C8:E0:40`) and shows them on
a local dashboard. Eventual target format:
`05_Data/schemas/spot_measurement_schema.json` (`type: spo2`,
`source_device: yuwell_yx110`).

## Protocol

Not the standard Pulse Oximeter Service (0x1822). Readings arrive as
notifications on `0000ffe4` (service `0000ffe0`), ~1 per second, no pairing
and no start command needed. Subscribing to `0000fff3` makes the device drop
the connection, so only subscribe to `ffe4`.

Layout matches `OximeterManager.f()` in the HealthCare+ v2.0.0.8 APK:

| Byte | Meaning |
|---|---|
| 0 | `0xFE` header |
| 1 | packet length (`0x0A`) |
| 2 | message id: `0x55` reading, `0x56` pulse waveform |
| 3-4 | pulse rate, bpm (u16 big-endian) |
| 5 | SpO2 % (app rejects ≥ 101) |
| 6-7 | PI × 1000 (always 6000 on the YX110 — likely a placeholder) |
| 8 | rolling counter |
| 9 | checksum = sum of bytes 0-8 & 0xFF |

`0` for SpO2 or pulse means the reading isn't ready yet.

## Dashboard

```bash
python3 dashboard_server.py   # opens http://localhost:8080/index.html
```

Shows live SpO2 and pulse plus the raw packet stream, and saves every packet
to `raw_captures/`.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
