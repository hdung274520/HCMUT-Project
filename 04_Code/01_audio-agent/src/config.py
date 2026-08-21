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


def detect_device_profile() -> tuple[str, str, str, int, int]:
    """Detects system hardware and returns (profile_name, default_whisper_model,
    default_ollama_model, whisper_beam_size, whisper_cpu_threads)."""
    import platform

    arch = platform.machine().lower()
    is_arm = "arm" in arch or "aarch" in arch

    total_ram_gb = 8.0
    try:
        pages = os.sysconf('SC_PHYS_PAGES')
        page_size = os.sysconf('SC_PAGE_SIZE')
        total_ram_gb = (pages * page_size) / (1024 ** 3)
    except Exception:
        pass

    cpu_count = os.cpu_count() or 4

    if is_arm or total_ram_gb < 6.0:
        # Pi 4 is CPU/RAM constrained: 'tiny' is the only size that keeps STT
        # near real-time. Greedy decoding + leave 1 core free for audio I/O/OS.
        return "Raspberry Pi 4 (Target Edge)", "tiny", "qwen2.5:0.5b", 1, max(1, cpu_count - 1)
    else:
        # Winners from the /test /test2 /test3 survey harnesses (see
        # logs/{stt,llm,tts}_test_times.csv and README's Benchmark section):
        # distil-medium.en matches vanilla 'medium' on accuracy but is ~26%
        # faster, and qwen2.5:0.5b ties the best LLM rating while being by far
        # the fastest (~1.3s vs 6-15s+ for 7B/8B models).
        return "Development PC (i5/16GB)", "Systran/faster-distil-whisper-medium.en", "qwen2.5:0.5b", 3, cpu_count


# Auto-detect hardware specs
PROFILE_NAME, DETECTED_WHISPER_MODEL, DETECTED_OLLAMA_MODEL, DETECTED_BEAM_SIZE, DETECTED_CPU_THREADS = (
    detect_device_profile()
)


def resolve_whisper_model(language: str = "en") -> str:
    """English-only STT model: explicit WHISPER_MODEL override, else the
    hardware-detected faster-whisper size ('medium' on PC, 'tiny' on Pi).
    (The `language` arg is kept for call-site compatibility.)
    """
    override = os.getenv("WHISPER_MODEL", "").strip()
    return override or DETECTED_WHISPER_MODEL


def _env_or(env_key: str, default: str) -> str:
    """Explicit env value if non-blank, otherwise `default` (blank counts as unset,
    since .env.example pre-populates every key, blank or not)."""
    explicit = os.getenv(env_key, "").strip()
    return explicit if explicit else default


def _pick(env_key: str, mode_key: str) -> str:
    """Use the explicit override if set, otherwise the MODE default."""
    explicit = os.getenv(env_key, "").strip()
    if explicit:
        return explicit
    mode = os.getenv("MODE", "local").strip().lower()
    return _MODE_DEFAULTS.get(mode, _MODE_DEFAULTS["local"])[mode_key]


@dataclass
class Config:
    mode: str = os.getenv("MODE", "local").strip().lower()
    language: str = os.getenv("LANGUAGE", "en").strip().lower()

    stt_provider: str = _pick("STT_PROVIDER", "stt")
    tts_provider: str = _pick("TTS_PROVIDER", "tts")
    llm_provider: str = _pick("LLM_PROVIDER", "llm")

    # Gemini
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

    # faster-whisper (English STT)
    whisper_model: str = resolve_whisper_model()
    whisper_beam_size: int = int(_env_or("WHISPER_BEAM_SIZE", str(DETECTED_BEAM_SIZE)))
    whisper_cpu_threads: int = int(_env_or("WHISPER_CPU_THREADS", str(DETECTED_CPU_THREADS)))

    # Ollama
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434").strip()
    ollama_model: str = _env_or("OLLAMA_MODEL", DETECTED_OLLAMA_MODEL)

    # Silero TTS voice (see src/tts.py SileroTTS — 118 voices: en_0..en_117, or "random")
    silero_speaker: str = _env_or("SILERO_SPEAKER", "en_56")

    # Microphone / VAD
    silence_threshold: float = float(os.getenv("SILENCE_THRESHOLD", "0.012"))
    silence_duration: float = float(os.getenv("SILENCE_DURATION", "0.9"))
    max_record_seconds: float = float(os.getenv("MAX_RECORD_SECONDS", "20"))

    sample_rate: int = 16000  # 16 kHz mono — what whisper/vosk expect

    # Where downloaded models live (Piper voices, etc.)
    models_dir: Path = ROOT / "models"


CONFIG = Config()

# Print diagnostics once
print(f"🖥️  Detected hardware profile: {PROFILE_NAME}")
print(f"📦 Offline config (LANG={CONFIG.language}): STT=whisper-{CONFIG.whisper_model} | Ollama LLM={CONFIG.ollama_model}")
