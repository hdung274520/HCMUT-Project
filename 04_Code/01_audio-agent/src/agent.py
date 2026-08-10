"""Orchestrates the voice loop: mic -> STT -> LLM -> TTS -> speaker."""
from __future__ import annotations

from pathlib import Path

from .audio import play_wav, record_until_silence
from .config import CONFIG
from .llm import get_llm
from .stt import get_stt
from .tts import get_tts

OUT_WAV = Path(__file__).resolve().parent.parent / ".reply.wav"


class VoiceAgent:
    def __init__(self) -> None:
        print(
            f"⚙️  MODE={CONFIG.mode} | STT={CONFIG.stt_provider} | "
            f"LLM={CONFIG.llm_provider} | TTS={CONFIG.tts_provider} | LANG={CONFIG.language}"
        )
        print("⏳  Loading models...", flush=True)
        self.stt = get_stt()
        self.llm = get_llm()
        self.tts = get_tts()
        print("✅  Ready!\n")

    def _say(self, text: str) -> None:
        audio_file = self.tts.speak_to_file(text, OUT_WAV)
        play_wav(audio_file)

    def handle_text(self, user_text: str) -> str:
        """Run one LLM+TTS turn from already-transcribed text. Returns the reply."""
        reply = self.llm.reply(user_text)
        print(f"🤖  Bot: {reply}")
        self._say(reply)
        return reply

    def run_voice(self) -> None:
        """Main hands-free loop. Ctrl+C to quit."""
        self._say("Hi, I'm listening.")
        try:
            while True:
                audio = record_until_silence()
                if audio is None:
                    continue
                user_text = self.stt.transcribe(audio)
                if not user_text:
                    continue
                print(f"🧑  You: {user_text}")
                if user_text.lower().strip(" .!?") in {"goodbye", "exit", "quit"}:
                    self._say("Goodbye!")
                    break
                self.handle_text(user_text)
        except KeyboardInterrupt:
            print("\n👋  Done.")

    def run_text(self) -> None:
        """Type-to-chat fallback (LLM + TTS, no microphone). Useful for testing."""
        print("Type a message (type 'exit' to quit):")
        try:
            while True:
                user_text = input("🧑  You: ").strip()
                if not user_text:
                    continue
                if user_text.lower() in {"exit", "quit"}:
                    break
                self.handle_text(user_text)
        except (KeyboardInterrupt, EOFError):
            print("\n👋  Done.")
