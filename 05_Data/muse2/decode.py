"""Muse 2 BLE packet decoders (service 0xFE8D, characteristics 273e00xx-4c4d-454d-96be-f03bac821358)."""

import json
import struct

UUID_FMT = "273e{:04x}-4c4d-454d-96be-f03bac821358"
CONTROL_UUID = UUID_FMT.format(0x0001)

# characteristic uuid -> sensor name
SENSORS = {
    UUID_FMT.format(0x0003): "eeg_tp9",
    UUID_FMT.format(0x0004): "eeg_af7",
    UUID_FMT.format(0x0005): "eeg_af8",
    UUID_FMT.format(0x0006): "eeg_tp10",
    UUID_FMT.format(0x0007): "eeg_aux",
    UUID_FMT.format(0x0009): "gyro",
    UUID_FMT.format(0x000a): "accel",
    UUID_FMT.format(0x000b): "telemetry",
    UUID_FMT.format(0x000f): "ppg_ambient",
    UUID_FMT.format(0x0010): "ppg_infrared",
    UUID_FMT.format(0x0011): "ppg_red",
}

EEG_UV_PER_LSB = 0.48828125
ACCEL_G_PER_LSB = 0.0000610352
GYRO_DPS_PER_LSB = 0.0074768


def encode_command(cmd: str) -> bytes:
    """Control commands are length-prefixed ASCII terminated by a newline."""
    return bytes([len(cmd) + 1]) + cmd.encode() + b"\n"


def decode_eeg(data: bytes):
    """2-byte packet index + 12 big-endian 12-bit samples, in microvolts."""
    bits = int.from_bytes(data[2:20], "big")
    samples = [(bits >> (132 - 12 * i)) & 0xFFF for i in range(12)]
    return {"packet_index": int.from_bytes(data[:2], "big"),
            "samples_uv": [(s - 2048) * EEG_UV_PER_LSB for s in samples]}


def decode_ppg(data: bytes):
    """2-byte packet index + 6 big-endian unsigned 24-bit samples (raw ADC counts)."""
    return {"packet_index": int.from_bytes(data[:2], "big"),
            "samples": [int.from_bytes(data[2 + 3 * i:5 + 3 * i], "big") for i in range(6)]}


def decode_motion(data: bytes, scale: float):
    """2-byte packet index + 3 samples of (x, y, z) int16."""
    vals = struct.unpack(">9h", data[2:20])
    return {"packet_index": int.from_bytes(data[:2], "big"),
            "samples": [[round(v * scale, 6) for v in vals[i:i + 3]] for i in (0, 3, 6)]}


def decode_telemetry(data: bytes):
    idx, battery, fuel, adc, temp = struct.unpack(">5H", data[:10])
    return {"packet_index": idx, "battery_pct": battery / 512, "fuel_gauge_mv": fuel * 2.2,
            "adc_raw": adc, "temperature_raw": temp}


def decode(sensor: str, data: bytes):
    if sensor.startswith("eeg_"):
        return decode_eeg(data)
    if sensor.startswith("ppg_"):
        return decode_ppg(data)
    if sensor == "accel":
        return decode_motion(data, ACCEL_G_PER_LSB)
    if sensor == "gyro":
        return decode_motion(data, GYRO_DPS_PER_LSB)
    return decode_telemetry(data)


class ControlReassembler:
    """Control replies are JSON split over several notifications, each prefixed by a length byte."""

    def __init__(self):
        self.buf = ""

    def feed(self, data: bytes):
        self.buf += data[1:1 + data[0]].decode("ascii", errors="replace")
        if "}" not in self.buf:
            return None
        text, self.buf = self.buf, ""
        try:
            return json.loads(text)
        except ValueError:
            return {"unparsed": text}
