#!/usr/bin/env python3
"""Realtime voice-chat server.

The browser streams raw PCM16 (16 kHz mono) over a WebSocket. The server detects
turns with VAD, runs STT -> LLM -> TTS, and streams the spoken reply back.
Supports barge-in: if the user speaks while the bot is talking, the current reply
is cancelled.

    python server.py            # then open http://localhost:8000
"""
from __future__ import annotations

import asyncio
import base64
import csv
import tempfile
import time
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.config import CONFIG
from src.llm import get_llm
from src.stt import get_stt
from src.tts import get_tts
from src.vad import TurnDetector
import tts_survey_providers
import llm_survey_providers

# Serve the Health Dashboard (04_web-app) as the main UI
WEB_DIR = Path(__file__).resolve().parent.parent / "04_web-app"

app = FastAPI(title="Health Dashboard + Voice Agent")

SUPPORTED_LANGS = {"en"}

# Per-turn response-time log — one CSV row per completed STT->LLM->TTS turn, so a
# live mic test session can be pulled straight into a spreadsheet afterward.
RESPONSE_LOG = Path(__file__).resolve().parent / "logs" / "response_times.csv"
RESPONSE_LOG_FIELDS = [
    "timestamp", "question", "answer",
    "stt_s", "llm_s", "tts_s", "total_s",
    "stt_model", "llm_model", "tts_provider",
]


def _log_turn(
    question: str, answer: str, stt_s: float, llm_s: float, tts_s: float | None,
    stt_model: str = None,
) -> None:
    RESPONSE_LOG.parent.mkdir(parents=True, exist_ok=True)
    is_new = not RESPONSE_LOG.exists()
    total_s = stt_s + llm_s + (tts_s or 0.0)
    with open(RESPONSE_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=RESPONSE_LOG_FIELDS)
        if is_new:
            w.writeheader()
        w.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "question": question, "answer": answer,
            "stt_s": round(stt_s, 3), "llm_s": round(llm_s, 3),
            "tts_s": round(tts_s, 3) if tts_s is not None else "",
            "total_s": round(total_s, 3),
            "stt_model": f"whisper-{stt_model or CONFIG.whisper_model}",
            "llm_model": CONFIG.ollama_model if CONFIG.llm_provider == "ollama" else CONFIG.gemini_model,
            "tts_provider": CONFIG.tts_provider,
        })
    print(
        f"   ⏱️  STT={stt_s:.2f}s  LLM={llm_s:.2f}s  "
        f"TTS={f'{tts_s:.2f}s' if tts_s is not None else 'n/a'}  TOTAL={total_s:.2f}s",
        flush=True,
    )


# --- Test 2: TTS-only survey (no STT/LLM) — manual, listen-then-log workflow ---
TTS_TEST_LOG = Path(__file__).resolve().parent / "logs" / "tts_test_times.csv"
TTS_TEST_LOG_FIELDS = [
    "timestamp", "provider", "model_detail", "text", "word_count",
    "synth_s", "audio_duration_s", "rtf", "rating", "notes",
]


def _log_tts_test(
    provider: str, model_detail: str, text: str, synth_s: float,
    audio_duration_s: float, rating: str = "", notes: str = "",
) -> None:
    TTS_TEST_LOG.parent.mkdir(parents=True, exist_ok=True)
    is_new = not TTS_TEST_LOG.exists()
    rtf = synth_s / audio_duration_s if audio_duration_s > 0 else ""
    with open(TTS_TEST_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=TTS_TEST_LOG_FIELDS)
        if is_new:
            w.writeheader()
        w.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "provider": provider, "model_detail": model_detail, "text": text,
            "word_count": len(text.split()),
            "synth_s": round(synth_s, 3),
            "audio_duration_s": round(audio_duration_s, 3),
            "rtf": round(rtf, 3) if rtf != "" else "",
            "rating": rating, "notes": notes,
        })
    print(f"   📝 TTS test logged: {provider} | RTF={rtf if rtf=='' else f'{rtf:.3f}'} | rating={rating!r}", flush=True)


class TTSTestRequest(BaseModel):
    provider: str
    text: str


class TTSTestLogRequest(BaseModel):
    provider: str
    model_detail: str
    text: str
    synth_s: float
    audio_duration_s: float
    rating: str = ""
    notes: str = ""


def _wav_duration_seconds(wav_bytes: bytes) -> float:
    import io
    import wave
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        return wf.getnframes() / wf.getframerate()


@app.get("/test2")
def test2_ui() -> FileResponse:
    return FileResponse(TEST_UI_DIR / "test2.html", headers={"Cache-Control": "no-cache"})


@app.get("/api/tts_providers")
def tts_providers() -> dict:
    return {"providers": tts_survey_providers.PROVIDERS}


@app.post("/api/tts_test")
async def tts_test(req: TTSTestRequest) -> dict:
    t0 = time.perf_counter()
    result = await asyncio.to_thread(tts_survey_providers.synthesize, req.provider, req.text)
    synth_s = time.perf_counter() - t0
    audio_duration_s = _wav_duration_seconds(result["data"]) if result["mime"] == "audio/wav" else None
    return {
        "data": base64.b64encode(result["data"]).decode(),
        "mime": result["mime"],
        "model_detail": result["model_detail"],
        "synth_s": round(synth_s, 3),
        "audio_duration_s": round(audio_duration_s, 3) if audio_duration_s is not None else None,
    }


@app.post("/api/tts_test/log")
def tts_test_log(req: TTSTestLogRequest) -> dict:
    _log_tts_test(
        req.provider, req.model_detail, req.text, req.synth_s,
        req.audio_duration_s, req.rating, req.notes,
    )
    return {"ok": True}


# --- Test 3: LLM-only survey (no STT/TTS) — manual, read-then-log workflow ---
LLM_TEST_LOG = Path(__file__).resolve().parent / "logs" / "llm_test_times.csv"
LLM_TEST_LOG_FIELDS = [
    "timestamp", "model", "question", "answer",
    "gen_s", "eval_count", "eval_tps", "rating", "notes",
]


def _log_llm_test(
    model: str, question: str, answer: str, gen_s: float,
    eval_count: int | None, eval_tps: float | None,
    rating: str = "", notes: str = "",
) -> None:
    LLM_TEST_LOG.parent.mkdir(parents=True, exist_ok=True)
    is_new = not LLM_TEST_LOG.exists()
    with open(LLM_TEST_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LLM_TEST_LOG_FIELDS)
        if is_new:
            w.writeheader()
        w.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "model": model, "question": question, "answer": answer,
            "gen_s": round(gen_s, 3),
            "eval_count": eval_count if eval_count is not None else "",
            "eval_tps": round(eval_tps, 2) if eval_tps is not None else "",
            "rating": rating, "notes": notes,
        })
    print(f"   📝 LLM test logged: {model} | gen_s={gen_s:.2f}s | rating={rating!r}", flush=True)


class LLMTestRequest(BaseModel):
    model: str
    text: str


class LLMTestLogRequest(BaseModel):
    model: str
    text: str
    answer: str
    gen_s: float
    eval_count: int | None = None
    eval_tps: float | None = None
    rating: str = ""
    notes: str = ""


@app.get("/test3")
def test3_ui() -> FileResponse:
    return FileResponse(TEST_UI_DIR / "test3.html", headers={"Cache-Control": "no-cache"})


@app.get("/api/llm_models")
def llm_models() -> dict:
    return {"models": llm_survey_providers.MODELS}


@app.post("/api/llm_test")
async def llm_test(req: LLMTestRequest) -> dict:
    t0 = time.perf_counter()
    result = await asyncio.to_thread(llm_survey_providers.ask, req.model, req.text)
    gen_s = time.perf_counter() - t0
    return {
        "answer": result["answer"],
        "gen_s": round(gen_s, 3),
        "eval_count": result["eval_count"],
        "eval_tps": round(result["eval_tps"], 2) if result["eval_tps"] is not None else None,
        "load_s": round(result["load_s"], 3),
    }


@app.post("/api/llm_test/log")
def llm_test_log(req: LLMTestLogRequest) -> dict:
    _log_llm_test(
        req.model, req.text, req.answer, req.gen_s,
        req.eval_count, req.eval_tps, req.rating, req.notes,
    )
    return {"ok": True}


@app.on_event("startup")
def _startup() -> None:
    print(
        f"⚙️  MODE={CONFIG.mode} | STT={CONFIG.stt_provider} | "
        f"LLM={CONFIG.llm_provider} | TTS={CONFIG.tts_provider} | LANG={CONFIG.language}"
    )
    print("⏳  Loading models...", flush=True)
    # Warm the STT cache so the first turn isn't slow.
    if CONFIG.mode != "realtime":
        get_stt(CONFIG.language)
    print("✅  Server ready.")


def _friendly_error(exc: Exception, language: str = "en") -> str:
    msg = str(exc)
    quota = "429" in msg or "RESOURCE_EXHAUSTED" in msg
    return ("Sorry, the service is rate-limited right now, please try again shortly."
            if quota else "Sorry, something went wrong. Please try again.")


def _synth(text: str, tts) -> dict:
    """Synthesize speech, return base64 audio + mime."""
    with tempfile.TemporaryDirectory() as tmp:
        out = tts.speak_to_file(text, Path(tmp) / "reply.wav")
        data = out.read_bytes()
        mime = "audio/mpeg" if out.suffix == ".mp3" else "audio/wav"
    return {"data": base64.b64encode(data).decode(), "mime": mime}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html", headers={"Cache-Control": "no-cache"})


# Standalone response-time test harness, decoupled from the health dashboard UI.
TEST_UI_DIR = Path(__file__).resolve().parent / "test_ui"


@app.get("/test")
def test_ui() -> FileResponse:
    return FileResponse(TEST_UI_DIR / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/api/config")
def config() -> dict:
    return {
        "mode": CONFIG.mode,
        "language": CONFIG.language,
        "languages": sorted(SUPPORTED_LANGS),
        "stt": CONFIG.stt_provider,
        "stt_model": CONFIG.whisper_model if CONFIG.stt_provider == "faster_whisper" else None,
        "llm": CONFIG.llm_provider,
        "llm_model": CONFIG.ollama_model if CONFIG.llm_provider == "ollama" else CONFIG.gemini_model,
        "tts": CONFIG.tts_provider,
    }


class Session:
    """One realtime conversation over a WebSocket."""

    def __init__(
        self, ws: WebSocket, system_instruction: str = None, language: str = None,
        stt_model: str = None,
    ) -> None:
        self.ws = ws
        self.system_instruction = system_instruction
        self.language = language if language in SUPPORTED_LANGS else CONFIG.language
        self.stt_model_override = stt_model
        self.stt_model_name = stt_model or CONFIG.whisper_model
        self.task: asyncio.Task | None = None

    async def setup(self) -> None:
        """Build STT/LLM/TTS off the event loop — swapping to an uncached Whisper
        size (e.g. large-v3) can take several seconds and must not block other
        connections."""
        if CONFIG.mode == "realtime":
            return
        self.stt = await asyncio.to_thread(get_stt, self.language, self.stt_model_override)
        self.stt_model_name = getattr(self.stt, "model_name", self.stt_model_name)
        self.tts = await asyncio.to_thread(get_tts, self.language)
        self.llm = get_llm(self.system_instruction, self.language)  # fresh chat history per connection
        self.vad = TurnDetector()

    async def send(self, **msg) -> None:
        await self.ws.send_json(msg)

    async def run(self) -> None:
        await self.send(type="ready", stt_model=self.stt_model_name)
        await self.send(type="state", value="listening")
        if CONFIG.mode == "realtime":
            await self._run_realtime()
        else:
            while True:
                event = await self.ws.receive()
                if event["type"] == "websocket.disconnect":
                    break
                if (data := event.get("bytes")) is not None:
                    await self._on_audio(data)
                elif (text := event.get("text")) is not None:
                    await self._on_control(text)

    async def _run_realtime(self) -> None:
        from google import genai
        from google.genai import types

        if not CONFIG.gemini_api_key:
            await self.send(type="error", text="GEMINI_API_KEY is not set in .env.local")
            return

        client = genai.Client(
            api_key=CONFIG.gemini_api_key,
            http_options={'api_version': 'v1alpha'}
        )
        
        # Determine live model name. If config's model is not supporting Live API, use gemini-2.5-flash-native-audio-latest
        live_model = CONFIG.gemini_model
        if "1.5" in live_model or "2.0-flash-exp" in live_model or "2.5-flash" == live_model:
            live_model = "gemini-2.5-flash-native-audio-latest"
            
        # Determine preset voice name based on language
        voice_name = "Zephyr" # 'Puck', 'Charon', 'Kore', 'Fenrir', 'Zephyr'
        if CONFIG.language == "vi":
            voice_name = "Zephyr"
        else:
            voice_name = "Aoede" # Aoede / Zephyr
            
        from src.llm import resolve_system_prompt
        system_instruction = resolve_system_prompt(self.system_instruction, self.language)
        
        live_config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=system_instruction)]
            ),
            thinking_config=types.ThinkingConfig(
                thinking_budget=0
            ),
            input_audio_transcription=types.AudioTranscriptionConfig(),
            output_audio_transcription=types.AudioTranscriptionConfig()
        )
        
        print(f"🔗 Kết nối Gemini Live API: model={live_model}, voice={voice_name}", flush=True)
        
        try:
            async with client.aio.live.connect(model=live_model, config=live_config) as session:
                print("✅ Connected to Gemini Live API.", flush=True)
                
                async def read_from_client():
                    try:
                        while True:
                            event = await self.ws.receive()
                            if event["type"] == "websocket.disconnect":
                                break
                            
                            # Client streams audio as raw binary PCM 16kHz
                            if (pcm_data := event.get("bytes")) is not None:
                                await session.send_realtime_input(
                                    audio=types.Blob(
                                        data=pcm_data,
                                        mime_type="audio/pcm;rate=16000"
                                    )
                                )
                            elif (text_data := event.get("text")) is not None:
                                if text_data == "reset":
                                    pass
                                else:
                                    await session.send_realtime_input(text=text_data)
                    except WebSocketDisconnect:
                        print("Client disconnected (WebSocketDisconnect).", flush=True)
                    except Exception as e:
                        print(f"Error reading from client: {e}", flush=True)
                        
                async def read_from_gemini():
                    try:
                        async for response in session.receive():
                            server_content = response.server_content
                            if server_content is not None:
                                # 1. Model turn audio & text chunks
                                model_turn = server_content.model_turn
                                if model_turn is not None:
                                    for part in model_turn.parts:
                                        if part.inline_data is not None:
                                            audio_b64 = base64.b64encode(part.inline_data.data).decode('utf-8')
                                            await self.send(
                                                type="audio_chunk",
                                                data=audio_b64,
                                                mime=part.inline_data.mime_type
                                            )
                                        if part.text is not None:
                                            await self.send(
                                                type="bot_chunk",
                                                text=part.text
                                            )
                                            
                                # 2. User input transcription
                                input_trans = server_content.input_transcription
                                if input_trans is not None and input_trans.text:
                                    await self.send(
                                        type="user_chunk",
                                        text=input_trans.text
                                    )
                                    
                                # 3. Model output transcription
                                output_trans = server_content.output_transcription
                                if output_trans is not None and output_trans.text:
                                    await self.send(
                                        type="bot_chunk",
                                        text=output_trans.text
                                    )
                                    
                                # 4. Interruption flag
                                if server_content.interrupted:
                                    await self.send(
                                        type="interrupt"
                                    )
                                    
                                # 5. Turn complete flag (reset state to listening)
                                if server_content.turn_complete:
                                    await self.send(
                                        type="state",
                                        value="listening"
                                    )
                    except Exception as e:
                        print(f"Error reading from Gemini: {e}", flush=True)
                        
                # Wait for both tasks
                await asyncio.gather(read_from_client(), read_from_gemini())
                
        except Exception as err:
            import traceback
            traceback.print_exc()
            await self.send(type="error", text=f"Gemini Live error: {err}")

    async def _on_audio(self, pcm: bytes) -> None:
        # No barge-in: a reply in flight (STT/LLM/TTS) always runs to
        # completion. New speech detected while one is active is dropped —
        # the user just waits for the current turn to finish.
        for ev in self.vad.process(pcm):
            if isinstance(ev, tuple) and ev[0] == "utterance":
                if self.task and not self.task.done():
                    continue
                audio = ev[1]
                self.task = asyncio.create_task(self._handle(audio))

    async def _on_control(self, text: str) -> None:
        if text == "reset":
            self.llm = get_llm(self.system_instruction, self.language)
            await self.send(type="state", value="listening")

    async def _handle(self, audio) -> None:
        try:
            import numpy as np
            print(f"🎧 utterance {len(audio)/16000:.2f}s peak={np.abs(audio).max():.3f}", flush=True)
            await self.send(type="state", value="thinking")

            t0 = time.perf_counter()
            user_text = (await asyncio.to_thread(self.stt.transcribe, audio)).strip()
            stt_s = time.perf_counter() - t0
            print(f"   📝 STT ({stt_s:.2f}s): {user_text!r}", flush=True)
            if not user_text:
                await self.send(type="state", value="listening")
                return
            await self.send(type="user", text=user_text)

            t0 = time.perf_counter()
            try:
                bot_text = (await asyncio.to_thread(self.llm.reply, user_text)).strip()
            except Exception as exc:
                import traceback
                traceback.print_exc()
                bot_text = _friendly_error(exc, self.language)
            llm_s = time.perf_counter() - t0
            await self.send(type="bot", text=bot_text)

            await self.send(type="state", value="speaking")
            tts_s = None
            if bot_text.strip(" .!?,"):
                try:
                    t0 = time.perf_counter()
                    audio_msg = await asyncio.to_thread(_synth, bot_text, self.tts)
                    tts_s = time.perf_counter() - t0
                    print(
                        f"   🔊 TTS ({tts_s:.2f}s): mime={audio_msg['mime']} "
                        f"b64_len={len(audio_msg['data'])} head={audio_msg['data'][:16]!r}",
                        flush=True,
                    )
                    await self.send(type="audio", **audio_msg)
                except Exception:
                    import traceback
                    traceback.print_exc()
            _log_turn(user_text, bot_text, stt_s, llm_s, tts_s, stt_model=self.stt_model_name)
            await self.send(
                type="timing",
                stt_s=round(stt_s, 3), llm_s=round(llm_s, 3),
                tts_s=round(tts_s, 3) if tts_s is not None else None,
                total_s=round(stt_s + llm_s + (tts_s or 0.0), 3),
            )
        except asyncio.CancelledError:
            pass  # barge-in cancelled this reply
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            try:
                await self.send(type="state", value="listening")
            except Exception:
                pass


@app.websocket("/ws")
async def ws_endpoint(
    ws: WebSocket, system_instruction: str = None, lang: str = None, stt_model: str = None,
) -> None:
    await ws.accept()
    session = Session(ws, system_instruction=system_instruction, language=lang, stt_model=stt_model)
    try:
        await session.send(type="state", value="loading")
        await session.setup()
        await session.run()
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        import traceback
        traceback.print_exc()
        try:
            await session.send(type="error", text=f"Failed to load model: {exc}")
        except Exception:
            pass
    finally:
        if session.task and not session.task.done():
            session.task.cancel()


# Mount static files (CSS, JS, data/) from the dashboard directory.
# This must come AFTER all explicit routes so /ws, /api/config, / are matched first.
app.mount("/", StaticFiles(directory=str(WEB_DIR)), name="static")


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
