# Magene H303 BLE reader

Reads heart rate and RR intervals from the Magene H303 ECG chest strap over
BLE (MAC `D9:94:F2:69:20:DE`) and shows them on a local dashboard.

## Protocol

Standard Bluetooth SIG Heart Rate Service (`0x180D`), Heart Rate Measurement
characteristic `0x2A37` (notify). No pairing needed — `bluetoothctl pair`
fails with `AuthenticationFailed`, but connecting directly over GATT works.

| Flags bit | Meaning |
|---|---|
| 0 | HR is u16 (else u8) |
| 1-2 | sensor contact detected / supported |
| 3 | energy expended (u16) present |
| 4 | RR intervals present (u16 each, units of 1/1024 s) |

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Dashboard

```bash
python3 dashboard_server.py   # opens http://localhost:8081/index.html
```

Uses ports 8081/8766 so it can run alongside the YX110 dashboard
(8080/8765). Every packet is saved to `raw_captures/`.
