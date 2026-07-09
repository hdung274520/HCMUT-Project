"""Central configuration loaded from .env.local (falls back to .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

# Load .env.local first, then .env.example as a fallback for any missing keys.
load_dotenv(ROOT / ".env.local")
load_dotenv(ROOT / ".env.example")

# Default component choice per MODE.
_MODE_DEFAULTS = {
    "api": {"stt": "gemini", "tts": "gtts", "llm": "gemini"},
    "local": {"stt": "faster_whisper", "tts": "piper", "llm": "ollama"},
    "realtime": {"stt": "gemini_live", "tts": "gemini_live", "llm": "gemini_live"},
}


def _pick(env_key: str, mode_key: str) -> str:
    """Use the explicit override if set, otherwise the MODE default."""
    explicit = os.getenv(env_key, "").strip()
    if explicit:
        return explicit
    mode = os.getenv("MODE", "api").strip().lower()
    return _MODE_DEFAULTS.get(mode, _MODE_DEFAULTS["api"])[mode_key]


@dataclass
class Config:
    mode: str = os.getenv("MODE", "api").strip().lower()
    language: str = os.getenv("LANGUAGE", "vi").strip().lower()

    stt_provider: str = _pick("STT_PROVIDER", "stt")
    tts_provider: str = _pick("TTS_PROVIDER", "tts")
    llm_provider: str = _pick("LLM_PROVIDER", "llm")

    # Gemini
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    # faster-whisper
    whisper_model: str = os.getenv("WHISPER_MODEL", "base").strip()

    # Ollama
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:3b").strip()

    # Microphone / VAD
    silence_threshold: float = float(os.getenv("SILENCE_THRESHOLD", "0.012"))
    silence_duration: float = float(os.getenv("SILENCE_DURATION", "0.9"))
    max_record_seconds: float = float(os.getenv("MAX_RECORD_SECONDS", "20"))

    sample_rate: int = 16000  # 16 kHz mono — what whisper/vosk expect

    # Where downloaded models live (Piper voices, etc.)
    models_dir: Path = ROOT / "models"


CONFIG = Config()
