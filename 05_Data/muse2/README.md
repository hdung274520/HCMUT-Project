# Muse 2 BLE reader

Streams everything a Muse 2 offers over BLE and shows it on a local dashboard.
Not hardware-tested yet: written from the public Muse GATT protocol (as used
by muse-js / muselsl), so the first run may need tweaks.

## Protocol

Vendor service `0xFE8D`, characteristics `273e00xx-4c4d-454d-96be-f03bac821358`.
Commands go to `273e0001` as length-prefixed ASCII ending in `\n`; the server
sends `h` (halt), the preset, `v1` (version), `s` (status), `d` (start).

| Char | Stream | Rate | Packet |
|---|---|---|---|
| `0003-0007` | EEG TP9, AF7, AF8, TP10, AUX | 256 Hz | index (u16) + 12 x 12-bit, 0.48828125 µV/LSB (AUX is usually empty) |
| `000f/0010/0011` | PPG ambient / infrared / red | 64 Hz | index + 6 x u24 raw ADC |
| `000a` | Accelerometer | 52 Hz | index + 3 x (x,y,z) i16, 0.0000610352 g/LSB |
| `0009` | Gyroscope | 52 Hz | index + 3 x (x,y,z) i16, 0.0074768 °/s/LSB |
| `000b` | Telemetry | ~0.1 Hz | index, battery (/512 = %), fuel gauge, ADC, temperature |
| `0001` | Control replies | on demand | JSON in length-prefixed fragments |

Presets: `p50` (default) = EEG + PPG on Muse 2; `p21` = EEG only. PPG only
streams with the right preset, so if the PPG traces stay hidden try another.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 test_decode.py        # decoder self-check, prints "ok"
```

## Dashboard

```bash
python3 dashboard_server.py   # opens http://localhost:8082/index.html
```

Uses ports 8082/8767 so it runs alongside the YX110 (8080/8765) and H303
(8081/8766) dashboards. Finds the first device named `Muse*`; pass
`--address` to pin one. Every notification is saved to `raw_captures/` as
JSONL (raw hex plus decoded values), so a capture can be replayed or
re-decoded later.
