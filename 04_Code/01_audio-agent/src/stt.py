"""Speech-to-text providers: faster-whisper (local) and Gemini (API)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import CONFIG


class BaseSTT:
    def transcribe(self, audio: np.ndarray) -> str:  # noqa: D401
        raise NotImplementedError


class FasterWhisperSTT(BaseSTT):
    """Offline, multilingual STT running int8 on CPU."""

    def __init__(self) -> None:
        from faster_whisper import WhisperModel

        # int8 keeps RAM/CPU low — ideal for a GPU-less i5 laptop.
        self.model = WhisperModel(CONFIG.whisper_model, device="cpu", compute_type="int8")
        self.lang = CONFIG.language if CONFIG.language in {"vi", "en"} else None

    def transcribe(self, audio: np.ndarray) -> str:
        segments, _ = self.model.transcribe(
            audio.astype(np.float32),
            language=self.lang,
            beam_size=1,            # greedy = faster on CPU
            vad_filter=True,
        )
        return " ".join(seg.text for seg in segments).strip()


class GeminiSTT(BaseSTT):
    """Transcribe audio with the Gemini multimodal API (one key for STT + LLM)."""

    def __init__(self) -> None:
        from google import genai

        if not CONFIG.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY chưa được đặt trong .env.local")
        self.client = genai.Client(api_key=CONFIG.gemini_api_key)

    def transcribe(self, audio: np.ndarray) -> str:
        from .audio import save_wav
        import uuid
        import google.genai.types as types

        tmp_name = f".stt_tmp_{uuid.uuid4().hex}.wav"
        tmp = Path(CONFIG.models_dir).parent / tmp_name
        try:
            save_wav(audio, tmp)
            with open(tmp, "rb") as f:
                audio_bytes = f.read()
            
            lang = "tiếng Việt" if CONFIG.language == "vi" else "English"
            prompt = (
                f"Transcribe this audio to plain {lang} text only. "
                "Return just the transcription with no extra words."
            )
            resp = self.client.models.generate_content(
                model=CONFIG.gemini_model,
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type="audio/wav"
                    )
                ]
            )
            return (resp.text or "").strip()
        finally:
            if tmp.exists():
                tmp.unlink()


def get_stt() -> BaseSTT | None:
    provider = CONFIG.stt_provider
    if provider == "faster_whisper":
        return FasterWhisperSTT()
    if provider == "gemini":
        return GeminiSTT()
    if provider == "gemini_live":
        return None
    raise ValueError(f"STT provider không hợp lệ: {provider}")
