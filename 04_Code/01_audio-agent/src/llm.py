"""LLM providers: Google Gemini (API) and Ollama (local)."""
from __future__ import annotations

from .config import CONFIG

SYSTEM_PROMPT_VI = (
    "Bạn là trợ lý sức khỏe bằng giọng nói cho dự án theo dõi tín hiệu y sinh "
    "(EEG giấc ngủ, nhịp tim, huyết áp). Trả lời ngắn gọn, tự nhiên, bằng tiếng Việt, "
    "tối đa 2-3 câu vì câu trả lời sẽ được đọc to. Không dùng markdown, emoji hay liệt kê."
)
SYSTEM_PROMPT_EN = (
    "You are a spoken health assistant for a medical-signal monitoring project "
    "(sleep EEG, heart rate, blood pressure). Answer briefly and naturally in English, "
    "at most 2-3 sentences since the reply will be read aloud. No markdown, emoji or lists."
)


def _system_prompt() -> str:
    import datetime
    now = datetime.datetime.now().astimezone()
    local_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    tz_offset = now.strftime("%z")
    formatted_tz = f"UTC{tz_offset[:3]}:{tz_offset[3:]}" if tz_offset else "local timezone"
    
    if CONFIG.language == "vi":
        time_context = f"\nThời gian hiện tại của hệ thống: {local_time_str} (Múi giờ: {formatted_tz}). Hãy tham chiếu thời gian này khi người dùng hỏi về thời điểm hoặc các chỉ số sinh hiệu gần đây."
    else:
        time_context = f"\nCurrent system time: {local_time_str} (Timezone: {formatted_tz}). Reference this time when user asks about recent vitals or timing."
        
    base_prompt = SYSTEM_PROMPT_VI if CONFIG.language == "vi" else SYSTEM_PROMPT_EN
    return base_prompt + time_context


class BaseLLM:
    def reply(self, user_text: str) -> str:
        raise NotImplementedError


class GeminiLLM(BaseLLM):
    def __init__(self) -> None:
        from google import genai
        from google.genai import types

        if not CONFIG.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY chưa được đặt trong .env.local")
        # Keep a reference so the underlying httpx client isn't closed on GC.
        self.client = genai.Client(api_key=CONFIG.gemini_api_key)
        self.chat = self.client.chats.create(
            model=CONFIG.gemini_model,
            config=types.GenerateContentConfig(system_instruction=_system_prompt()),
        )

    def reply(self, user_text: str) -> str:
        resp = self.chat.send_message(user_text)
        return (resp.text or "").strip()


class OllamaLLM(BaseLLM):
    """Local model over Ollama's HTTP API. Keeps short conversation history."""

    def __init__(self) -> None:
        import requests  # noqa: F401

        self.history = [{"role": "system", "content": _system_prompt()}]

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


def get_llm() -> BaseLLM | None:
    provider = CONFIG.llm_provider
    if provider == "gemini":
        return GeminiLLM()
    if provider == "ollama":
        return OllamaLLM()
    if provider == "gemini_live":
        return None
    raise ValueError(f"LLM provider không hợp lệ: {provider}")
