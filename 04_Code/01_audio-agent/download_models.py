#!/usr/bin/env python3
"""Download local model assets (Piper voices). faster-whisper sizes auto-download
on first run, so only Piper voices need fetching ahead of time.

    python download_models.py                 # Piper voice for LANGUAGE in .env
    python download_models.py --all           # both vi and en Piper voices
"""
from __future__ import annotations

import argparse
import urllib.request
from pathlib import Path

from src.config import CONFIG

BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# voice key -> (relative path on the HF repo)
VOICES = {
    "vi_VN-vais1000-medium": "vi/vi_VN/vais1000/medium/vi_VN-vais1000-medium",
    "en_US-amy-medium": "en/en_US/amy/medium/en_US-amy-medium",
}

LANG_VOICE = {"vi": "vi_VN-vais1000-medium", "en": "en_US-amy-medium"}


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"  ✓ already have {dest.name}")
        return
    print(f"  ⬇ {dest.name} ...", flush=True)
    urllib.request.urlretrieve(url, dest)
    print(f"  ✓ {dest.name}")


def fetch_voice(voice: str) -> None:
    rel = VOICES[voice]
    out_dir = CONFIG.models_dir / "piper"
    print(f"Piper voice: {voice}")
    _download(f"{BASE}/{rel}.onnx", out_dir / f"{voice}.onnx")
    _download(f"{BASE}/{rel}.onnx.json", out_dir / f"{voice}.onnx.json")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="download both vi and en voices")
    args = ap.parse_args()

    if args.all:
        targets = list(VOICES)
    else:
        targets = [LANG_VOICE.get(CONFIG.language, "en_US-amy-medium")]

    for v in targets:
        fetch_voice(v)
    print("\nDone. Piper voice files are in:", CONFIG.models_dir / "piper")


if __name__ == "__main__":
    main()
