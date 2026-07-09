"""Microphone capture (with simple energy-based VAD) and speaker playback."""
from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

from .config import CONFIG


def record_until_silence() -> np.ndarray | None:
    """Record from the default mic until the user stops talking.

    Returns float32 mono samples at CONFIG.sample_rate, or None if nothing
    above the silence threshold was captured.
    """
    sr = CONFIG.sample_rate
    block = int(sr * 0.03)  # 30 ms frames
    silence_blocks_needed = int(CONFIG.silence_duration / 0.03)
    max_blocks = int(CONFIG.max_record_seconds / 0.03)

    frames: list[np.ndarray] = []
    silent_run = 0
    started = False

    print("🎤  Đang nghe... (nói đi, im lặng để kết thúc lượt)", flush=True)
    with sd.InputStream(samplerate=sr, channels=1, dtype="float32", blocksize=block) as stream:
        for _ in range(max_blocks):
            data, _ = stream.read(block)
            mono = data[:, 0]
            rms = float(np.sqrt(np.mean(mono**2)) + 1e-9)

            if rms >= CONFIG.silence_threshold:
                started = True
                silent_run = 0
                frames.append(mono.copy())
            elif started:
                silent_run += 1
                frames.append(mono.copy())
                if silent_run >= silence_blocks_needed:
                    break

    if not started or not frames:
        return None
    audio = np.concatenate(frames)
    # Trim the trailing silence we recorded while waiting for the timeout.
    keep = max(0, len(audio) - int(silence_blocks_needed * block * 0.5))
    return audio[:keep] if keep > 0 else audio


def save_wav(audio: np.ndarray, path: Path) -> Path:
    """Write float32 mono samples to a 16-bit PCM wav file."""
    pcm = np.clip(audio, -1.0, 1.0)
    pcm16 = (pcm * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(CONFIG.sample_rate)
        wf.writeframes(pcm16.tobytes())
    return path


def play_wav(path: Path) -> None:
    """Play a wav/audio file through the default speaker, blocking until done."""
    try:
        data, sr = sf.read(str(path), dtype="float32")
        sd.play(data, sr)
        sd.wait()
    except Exception as exc:  # noqa: BLE001 - playback must never crash the loop
        print(f"⚠️  Không phát được âm thanh: {exc}", file=sys.stderr)


def play_samples(audio: np.ndarray, sr: int) -> None:
    sd.play(audio, sr)
    sd.wait()


def decode_to_mono16k(raw: bytes) -> np.ndarray:
    """Decode arbitrary audio bytes (webm/opus/wav/mp3 from a browser) into
    float32 mono samples at CONFIG.sample_rate, using ffmpeg.
    """
    import subprocess

    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error",
            "-i", "pipe:0",
            "-ar", str(CONFIG.sample_rate), "-ac", "1",
            "-f", "f32le", "pipe:1",
        ],
        input=raw,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg decode lỗi: {proc.stderr.decode(errors='ignore')[:300]}")
    return np.frombuffer(proc.stdout, dtype=np.float32)
