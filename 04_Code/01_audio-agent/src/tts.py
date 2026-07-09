"""Text-to-speech providers: Piper (local/offline) and gTTS (online, no key)."""
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

    def __init__(self) -> None:
        from piper import PiperVoice

        voice = PIPER_VOICES.get(CONFIG.language, PIPER_VOICES["en"])
        onnx = CONFIG.models_dir / "piper" / f"{voice}.onnx"
        if not onnx.exists():
            raise RuntimeError(
                f"Chưa có Piper voice tại {onnx}. Chạy: python download_models.py"
            )
        self.voice = PiperVoice.load(str(onnx))

    def speak_to_file(self, text: str, out_path: Path) -> Path:
        import wave

        # piper-tts >=1.3 writes a complete wav (header + frames) for us.
        with wave.open(str(out_path), "wb") as wf:
            self.voice.synthesize_wav(text, wf)
        return out_path


class GTTSTTS(BaseTTS):
    """Online TTS via Google Translate voices — no API key required."""

    def __init__(self) -> None:
        from gtts import gTTS  # noqa: F401

        self.lang = CONFIG.language if CONFIG.language in {"vi", "en"} else "en"

    def speak_to_file(self, text: str, out_path: Path) -> Path:
        from gtts import gTTS

        mp3 = out_path.with_suffix(".mp3")
        gTTS(text=text, lang=self.lang).save(str(mp3))
        return mp3


def get_tts() -> BaseTTS | None:
    provider = CONFIG.tts_provider
    if provider == "piper":
        return PiperTTS()
    if provider == "gtts":
        return GTTSTTS()
    if provider == "gemini_live":
        return None
    raise ValueError(f"TTS provider không hợp lệ: {provider}")
