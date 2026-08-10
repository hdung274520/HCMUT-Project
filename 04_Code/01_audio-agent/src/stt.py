"""Speech-to-text providers: faster-whisper (local) and Gemini (API)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import CONFIG


class BaseSTT:
    def transcribe(self, audio: np.ndarray) -> str:  # noqa: D401
        raise NotImplementedError


class FasterWhisperSTT(BaseSTT):
    """Offline English STT running int8 on CPU."""

    def __init__(self, language: str | None = None, model: str | None = None) -> None:
        from faster_whisper import WhisperModel
        from .config import resolve_whisper_model

        self.lang = "en"
        self.model_name = model or resolve_whisper_model()

        # int8 keeps RAM/CPU low — ideal for a GPU-less i5 laptop / Raspberry Pi 4.
        self.model = WhisperModel(
            self.model_name,
            device="cpu",
            compute_type="int8",
            cpu_threads=CONFIG.whisper_cpu_threads,
        )

    # Segment-quality gates that drop hallucinated / low-confidence output
    # (faster-whisper applies these internally for temperature fallback; we also
    # use them to discard whole segments that would otherwise be returned).
    NO_SPEECH_MAX = 0.6      # p(this was actually silence/noise, not speech)
    LOGPROB_MIN = -1.0       # average token log-probability (confidence)
    COMPRESSION_RATIO_MAX = 2.4  # gzip ratio — very repetitive text compresses hard

    def transcribe(self, audio: np.ndarray) -> str:
        try:
            segments, info = self.model.transcribe(
                audio.astype(np.float32),
                language=self.lang,
                beam_size=CONFIG.whisper_beam_size,
                # Whisper's own VAD trims leading/trailing silence & noise the
                # caller's VAD let through (server's WebRTC VAD is coarse, and
                # the CLI's energy-threshold VAD is coarser still).
                vad_filter=True,
                # Don't let a hallucinated segment poison the next one — the
                # classic cause of runaway repetition loops on short/noisy audio.
                condition_on_previous_text=False,
            )

            kept = []
            for seg in segments:
                if (
                    seg.no_speech_prob > self.NO_SPEECH_MAX
                    or seg.avg_logprob < self.LOGPROB_MIN
                    or seg.compression_ratio > self.COMPRESSION_RATIO_MAX
                ):
                    print(
                        f"   [STT Filter] Dropped low-quality segment "
                        f"(no_speech={seg.no_speech_prob:.2f} logprob={seg.avg_logprob:.2f} "
                        f"compression={seg.compression_ratio:.2f}): '{seg.text.strip()}'",
                        flush=True,
                    )
                    continue
                kept.append(seg.text)
            text = " ".join(kept).strip()
            print(f"   [STT Debug] lang={info.language} (p={info.language_probability:.2f}) | result='{text}'", flush=True)
            return text
        except Exception as e:
            print(f"   [STT Error] Speech recognition failed: {e}", flush=True)
            return ""


class GeminiSTT(BaseSTT):
    """Transcribe audio with the Gemini multimodal API (one key for STT + LLM)."""

    def __init__(self) -> None:
        from google import genai

        if not CONFIG.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in .env.local")
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


# faster-whisper models are heavy to load, so keep one instance cached — reused
# instantly on repeat requests for the same (language, model). A different model
# (e.g. switching the Whisper size to compare in the test harness) evicts the old
# one first so several GB-sized models don't pile up in RAM at once.
_WHISPER_CACHE: dict[str, "FasterWhisperSTT"] = {}


def get_stt(language: str | None = None, model: str | None = None) -> BaseSTT | None:
    provider = CONFIG.stt_provider
    lang = language or CONFIG.language
    if provider == "faster_whisper":
        key = f"{lang}:{model or CONFIG.whisper_model}"
        if key not in _WHISPER_CACHE:
            _WHISPER_CACHE.clear()
            _WHISPER_CACHE[key] = FasterWhisperSTT(lang, model=model)
        return _WHISPER_CACHE[key]
    if provider == "gemini":
        return GeminiSTT()
    if provider == "gemini_live":
        return None
    raise ValueError(f"Invalid STT provider: {provider}")
