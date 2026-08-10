"""LLM providers: Google Gemini (API) and Ollama (local)."""
from __future__ import annotations

from .config import CONFIG

SYSTEM_PROMPT_EN = (
    "You are a spoken health assistant for a medical-signal monitoring project "
    "(sleep EEG, heart rate, blood pressure). Answer briefly and naturally in English, "
    "at most 2-3 sentences since the reply will be read aloud. No markdown, emoji or lists."
)


def _time_context() -> str:
    import datetime
    now = datetime.datetime.now().astimezone()
    local_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    tz_offset = now.strftime("%z")
    formatted_tz = f"UTC{tz_offset[:3]}:{tz_offset[3:]}" if tz_offset else "local timezone"
    return f"\nCurrent system time: {local_time_str} (Timezone: {formatted_tz}). Reference this time when user asks about recent vitals or timing."


def _system_prompt() -> str:
    return SYSTEM_PROMPT_EN + _time_context()


def resolve_system_prompt(custom: str | None = None, language: str | None = None) -> str:
    """Custom prompt (e.g. a browser-built one carrying live vitals data) wins
    if given; otherwise fall back to the generic English one. Both get the
    current time appended. (`language` kept for call-site compatibility.)"""
    if custom:
        return custom + _time_context()
    return _system_prompt()


class BaseLLM:
    def reply(self, user_text: str) -> str:
        raise NotImplementedError


class GeminiLLM(BaseLLM):
    def __init__(self, system_instruction: str | None = None, language: str | None = None) -> None:
        from google import genai
        from google.genai import types

        if not CONFIG.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in .env.local")
        # Keep a reference so the underlying httpx client isn't closed on GC.
        self.client = genai.Client(api_key=CONFIG.gemini_api_key)
        self.chat = self.client.chats.create(
            model=CONFIG.gemini_model,
            config=types.GenerateContentConfig(
                system_instruction=resolve_system_prompt(system_instruction, language)
            ),
        )

    def reply(self, user_text: str) -> str:
        resp = self.chat.send_message(user_text)
        return (resp.text or "").strip()


class OllamaLLM(BaseLLM):
    """Local model over Ollama's HTTP API. Keeps short conversation history."""

    def __init__(self, system_instruction: str | None = None, language: str | None = None) -> None:
        import requests  # noqa: F401

        self.history = [{"role": "system", "content": resolve_system_prompt(system_instruction, language)}]

    def reply(self, user_text: str) -> str:
        import requests

        self.history.append({"role": "user", "content": user_text})
        resp = requests.post(
            f"{CONFIG.ollama_host}/api/chat",
            json={"model": CONFIG.ollama_model, "messages": self.history, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        text = resp.json()["message"]["content"].strip()
        self.history.append({"role": "assistant", "content": text})
        return text


def get_llm(system_instruction: str | None = None, language: str | None = None) -> BaseLLM | None:
    provider = CONFIG.llm_provider
    if provider == "gemini":
        return GeminiLLM(system_instruction, language)
    if provider == "ollama":
        return OllamaLLM(system_instruction, language)
    if provider == "gemini_live":
        return None
    raise ValueError(f"Invalid LLM provider: {provider}")
