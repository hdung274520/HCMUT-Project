"""Text-to-speech providers: Silero (local/offline, natural), Piper (local/offline,
fast) and gTTS (online, no key)."""
from __future__ import annotations

from pathlib import Path

from .config import CONFIG

# Default Piper voices downloaded by download_models.py
PIPER_VOICES = {
    "vi": "vi_VN-vais1000-medium",
    "en": "en_US-amy-medium",
}


class BaseTTS:
    def speak_to_file(self, text: str, out_path: Path) -> Path:
        raise NotImplementedError


class PiperTTS(BaseTTS):
    """Offline ONNX TTS — very fast on CPU, the project's edge default."""

    def __init__(self, language: str | None = None) -> None:
        from piper import PiperVoice

        lang = language or CONFIG.language
        voice = PIPER_VOICES.get(lang, PIPER_VOICES["en"])
        onnx = CONFIG.models_dir / "piper" / f"{voice}.onnx"
        if not onnx.exists():
            raise RuntimeError(
                f"Missing Piper voice at {onnx}. Run: python download_models.py"
            )
        self.voice = PiperVoice.load(str(onnx))

    def speak_to_file(self, text: str, out_path: Path) -> Path:
        import wave

        # piper-tts >=1.3 writes a complete wav (header + frames) for us.
        with wave.open(str(out_path), "wb") as wf:
            self.voice.synthesize_wav(text, wf)
        return out_path


# Silero's torch.hub model is heavy to load (~1s even from cache); share one
# instance across all sessions instead of reloading per WebSocket connection.
_SILERO_MODEL = None


def _load_silero_model():
    """torch.hub's silero-models repo has its own `src/silero.py`, which collides
    with this project's own `src` package: both are importable under the name
    `src`. Clearing sys.modules alone isn't enough to fix this — our `src` has an
    `__init__.py` (a *regular* package) while the hub repo's `src/` doesn't (an
    implicit *namespace* package), and Python's import system lets a regular
    package win over a namespace package for the same name **regardless of
    sys.path order**. So even with the hub repo dir prepended to sys.path,
    `from src.silero import ...` inside its hubconf.py still finds *our* `src`
    first and fails with `ModuleNotFoundError: No module named 'src.silero'`.
    Fix: also drop the sys.path entry that resolves `src` to our project root
    for the duration of the load, then restore everything afterward.
    """
    import os
    import sys
    import torch

    project_root = str(Path(__file__).resolve().parent.parent)
    removed_paths = [p for p in sys.path if os.path.abspath(p or ".") == project_root]
    for p in removed_paths:
        sys.path.remove(p)

    ours = {k: v for k, v in sys.modules.items() if k == "src" or k.startswith("src.")}
    for k in ours:
        del sys.modules[k]
    try:
        model, _ = torch.hub.load(
            repo_or_dir="snakers4/silero-models",
            model="silero_tts",
            language="en",
            speaker="v3_en",
            trust_repo=True,
        )
    finally:
        for k in list(sys.modules):
            if k == "src" or k.startswith("src."):
                del sys.modules[k]
        sys.modules.update(ours)
        sys.path.extend(removed_paths)
    return model


class SileroTTS(BaseTTS):
    """Offline neural TTS (Silero v3_en) — natural multi-speaker voice, CPU-fast."""

    SAMPLE_RATE = 24000

    def __init__(self, language: str | None = None) -> None:
        import torch

        global _SILERO_MODEL
        if _SILERO_MODEL is None:
            torch.set_num_threads(CONFIG.whisper_cpu_threads or 4)
            _SILERO_MODEL = _load_silero_model()
        self.model = _SILERO_MODEL
        self.speaker = CONFIG.silero_speaker

    def speak_to_file(self, text: str, out_path: Path) -> Path:
        wav = out_path.with_suffix(".wav")
        self.model.save_wav(
            text=text,
            speaker=self.speaker,
            sample_rate=self.SAMPLE_RATE,
            audio_path=str(wav),
        )
        return wav


class GTTSTTS(BaseTTS):
    """Online TTS via Google Translate voices — no API key required."""

    def __init__(self, language: str | None = None) -> None:
        from gtts import gTTS  # noqa: F401

        lang = language or CONFIG.language
        self.lang = lang if lang in {"vi", "en"} else "en"

    def speak_to_file(self, text: str, out_path: Path) -> Path:
        from gtts import gTTS

        mp3 = out_path.with_suffix(".mp3")
        gTTS(text=text, lang=self.lang).save(str(mp3))
        return mp3


def get_tts(language: str | None = None) -> BaseTTS | None:
    provider = CONFIG.tts_provider
    if provider == "silero":
        return SileroTTS(language)
    if provider == "piper":
        return PiperTTS(language)
    if provider == "gtts":
        return GTTSTTS(language)
    if provider == "gemini_live":
        return None
    raise ValueError(f"Invalid TTS provider: {provider}")
