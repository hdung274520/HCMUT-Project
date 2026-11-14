"""Run: python3 test_decode.py"""

from decode import ControlReassembler, decode_eeg, decode_motion, decode_ppg, decode_telemetry, encode_command

assert encode_command("d") == b"\x02d\n"

vals = [0, 2048, 4095, 1, 2, 3, 4, 5, 6, 7, 8, 9]
bits = 0
for v in vals:
    bits = (bits << 12) | v
eeg = decode_eeg((7).to_bytes(2, "big") + bits.to_bytes(18, "big"))
assert eeg["packet_index"] == 7
assert eeg["samples_uv"][:3] == [-2048 * 0.48828125, 0.0, 2047 * 0.48828125]

ppg = decode_ppg(b"\x00\x01" + b"".join(v.to_bytes(3, "big") for v in (1, 2, 0xFFFFFF, 4, 5, 6)))
assert ppg["samples"] == [1, 2, 0xFFFFFF, 4, 5, 6]

motion = decode_motion(b"\x00\x02" + b"".join(v.to_bytes(2, "big", signed=True) for v in (1, -1, 2, 3, 4, 5, 6, 7, 8)), 1.0)
assert motion["samples"] == [[1, -1, 2], [3, 4, 5], [6, 7, 8]]

tel = decode_telemetry(b"\x00\x03" + (512 * 80).to_bytes(2, "big") + b"\x00\x64\x00\x00\x00\x00")
assert tel["battery_pct"] == 80

r = ControlReassembler()
assert r.feed(b'\x06{"rc"') is None
assert r.feed(b'\x05:0}\n'[:5]) == {"rc": 0}
print("ok")
