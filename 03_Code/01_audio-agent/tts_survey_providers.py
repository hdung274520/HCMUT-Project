"""Lazy-loaded TTS provider wrappers for the TTS-only test harness (test2).

Kept separate from src/tts.py (production) so heavy/fragile survey-only
dependencies (Kokoro, MMS-TTS, ...) never load during normal server startup —
only the provider actually picked in the test UI gets imported, on first use.
"""
from __future__ import annotations

import io
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
_CACHE: dict = {}

PROVIDERS = {
    "piper": "Piper (VITS, ONNX)",
    "gtts": "gTTS (Google Translate, online)",
    "silero": "Silero v3_en",
    "kokoro": "Kokoro-82M (ONNX)",
    "mms": "Meta MMS-TTS (VITS)",
    "espeak": "eSpeak NG (baseline)",
}


def _wav_bytes_from_float(samples: np.ndarray, sr: int) -> bytes:
    samples = np.clip(samples, -1.0, 1.0)
    pcm16 = (samples * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm16.tobytes())
    return buf.getvalue()


def _synth_piper(text: str):
    if "piper" not in _CACHE:
        from piper import PiperVoice
        onnx = ROOT / "models" / "piper" / "en_US-amy-medium.onnx"
        _CACHE["piper"] = PiperVoice.load(str(onnx))
    voice = _CACHE["piper"]
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        with wave.open(tmp.name, "wb") as wf:
            voice.synthesize_wav(text, wf)
        data = Path(tmp.name).read_bytes()
    return data, "en_US-amy-medium"


def _synth_gtts(text: str):
    from gtts import gTTS
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        gTTS(text=text, lang="en").save(tmp.name)
        data = Path(tmp.name).read_bytes()
    Path(tmp.name).unlink(missing_ok=True)
    return data, "gtts/en", "audio/mpeg"


def _synth_silero(text: str):
    if "silero" not in _CACHE:
        import os
        import sys
        import torch

        torch.set_num_threads(os.cpu_count() or 4)
        ours = {k: v for k, v in sys.modules.items() if k == "src" or k.startswith("src.")}
        for k in ours:
            del sys.modules[k]
        project_root = str(ROOT)
        removed = [p for p in sys.path if os.path.abspath(p or ".") == project_root]
        for p in removed:
            sys.path.remove(p)
        try:
            model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models", model="silero_tts",
                language="en", speaker="v3_en", trust_repo=True,
            )
        finally:
            for k in list(sys.modules):
                if k == "src" or k.startswith("src."):
                    del sys.modules[k]
            sys.modules.update(ours)
            sys.path.extend(removed)
        _CACHE["silero"] = model
    model = _CACHE["silero"]
    samples, sr = model.apply_tts(text=text, speaker="en_56", sample_rate=24000), 24000
    return _wav_bytes_from_float(samples.numpy(), sr), "silero/v3_en/en_56"


def _synth_kokoro(text: str):
    if "kokoro" not in _CACHE:
        from kokoro_onnx import Kokoro
        _CACHE["kokoro"] = Kokoro(
            str(ROOT / "models" / "kokoro" / "kokoro-v1.0.int8.onnx"),
            str(ROOT / "models" / "kokoro" / "voices-v1.0.bin"),
        )
    kokoro = _CACHE["kokoro"]
    samples, sr = kokoro.create(text, voice="af_heart", speed=1.0, lang="en-us")
    return _wav_bytes_from_float(samples, sr), "kokoro-82m/af_heart"


def _synth_mms(text: str):
    if "mms" not in _CACHE:
        import torch
        from transformers import VitsModel, AutoTokenizer
        model = VitsModel.from_pretrained("facebook/mms-tts-eng")
        tok = AutoTokenizer.from_pretrained("facebook/mms-tts-eng")
        _CACHE["mms"] = (model, tok)
    model, tok = _CACHE["mms"]
    import torch
    inputs = tok(text, return_tensors="pt")
    with torch.no_grad():
        out = model(**inputs).waveform
    sr = model.config.sampling_rate
    return _wav_bytes_from_float(out.squeeze().numpy(), sr), "facebook/mms-tts-eng"


def _synth_espeak(text: str):
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        subprocess.run(
            ["espeak-ng", "-v", "en-us", "-w", tmp.name, text],
            check=True, capture_output=True,
        )
        data = Path(tmp.name).read_bytes()
    return data, "espeak-ng/en-us"


_SYNTH = {
    "piper": _synth_piper,
    "gtts": _synth_gtts,
    "silero": _synth_silero,
    "kokoro": _synth_kokoro,
    "mms": _synth_mms,
    "espeak": _synth_espeak,
}


def synthesize(provider: str, text: str) -> dict:
    """Returns {data: bytes, mime: str, model_detail: str}."""
    if provider not in _SYNTH:
        raise ValueError(f"Unknown/unready provider: {provider}")
    result = _SYNTH[provider](text)
    if len(result) == 3:
        data, model_detail, mime = result
    else:
        data, model_detail = result
        mime = "audio/wav"
    return {"data": data, "mime": mime, "model_detail": model_detail}
