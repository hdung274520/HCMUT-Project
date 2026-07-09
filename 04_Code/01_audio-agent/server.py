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
import tempfile
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.config import CONFIG
from src.llm import get_llm
from src.stt import get_stt
from src.tts import get_tts
from src.vad import TurnDetector

# Serve the Health Dashboard (04_web-app) as the main UI
WEB_DIR = Path(__file__).resolve().parent.parent / "04_web-app"

app = FastAPI(title="Health Dashboard + Voice Agent")

# Heavy, stateless models are loaded once and shared across connections.
STT = None
TTS = None


@app.on_event("startup")
def _startup() -> None:
    global STT, TTS
    print(
        f"⚙️  MODE={CONFIG.mode} | STT={CONFIG.stt_provider} | "
        f"LLM={CONFIG.llm_provider} | TTS={CONFIG.tts_provider} | LANG={CONFIG.language}"
    )
    print("⏳  Đang nạp mô hình...", flush=True)
    STT = get_stt()
    TTS = get_tts()
    print("✅  Server realtime sẵn sàng.")


def _friendly_error(exc: Exception) -> str:
    msg = str(exc)
    quota = "429" in msg or "RESOURCE_EXHAUSTED" in msg
    if CONFIG.language == "vi":
        return ("Xin lỗi, hệ thống đang quá tải (hết lượt gọi miễn phí), bạn thử lại sau ít phút nhé."
                if quota else "Xin lỗi, có lỗi khi xử lý. Bạn thử lại giúp tôi nhé.")
    return ("Sorry, the service is rate-limited right now, please try again shortly."
            if quota else "Sorry, something went wrong. Please try again.")


def _synth(text: str) -> dict:
    """Synthesize speech, return base64 audio + mime."""
    with tempfile.TemporaryDirectory() as tmp:
        out = TTS.speak_to_file(text, Path(tmp) / "reply.wav")
        data = out.read_bytes()
        mime = "audio/mpeg" if out.suffix == ".mp3" else "audio/wav"
    return {"audio": base64.b64encode(data).decode(), "mime": mime}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html", headers={"Cache-Control": "no-cache"})


@app.get("/api/config")
def config() -> dict:
    return {
        "mode": CONFIG.mode,
        "language": CONFIG.language,
        "stt": CONFIG.stt_provider,
        "llm": CONFIG.llm_provider,
        "tts": CONFIG.tts_provider,
    }


class Session:
    """One realtime conversation over a WebSocket."""

    def __init__(self, ws: WebSocket, system_instruction: str = None) -> None:
        self.ws = ws
        self.system_instruction = system_instruction
        if CONFIG.mode != "realtime":
            self.llm = get_llm()          # fresh chat history per connection
            self.vad = TurnDetector()
        self.task: asyncio.Task | None = None

    async def send(self, **msg) -> None:
        await self.ws.send_json(msg)

    async def run(self) -> None:
        await self.send(type="ready")
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
            await self.send(type="error", text="GEMINI_API_KEY chưa được đặt trong .env.local")
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
            
        if self.system_instruction:
            import datetime
            now = datetime.datetime.now().astimezone()
            local_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
            tz_offset = now.strftime("%z")
            formatted_tz = f"UTC{tz_offset[:3]}:{tz_offset[3:]}" if tz_offset else "local timezone"
            if CONFIG.language == "vi":
                time_context = f"\nThời gian hiện tại của hệ thống: {local_time_str} (Múi giờ: {formatted_tz}). Hãy tham chiếu thời gian này khi người dùng hỏi về thời điểm hoặc các chỉ số sinh hiệu gần đây."
            else:
                time_context = f"\nCurrent system time: {local_time_str} (Timezone: {formatted_tz}). Reference this time when user asks about recent vitals or timing."
            system_instruction = self.system_instruction + time_context
        else:
            from src.llm import _system_prompt
            system_instruction = _system_prompt()
        
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
                print("✅ Kết nối thành công Gemini Live API.", flush=True)
                
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
                        print(f"Lỗi đọc từ Client: {e}", flush=True)
                        
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
                        print(f"Lỗi đọc từ Gemini: {e}", flush=True)
                        
                # Wait for both tasks
                await asyncio.gather(read_from_client(), read_from_gemini())
                
        except Exception as err:
            import traceback
            traceback.print_exc()
            await self.send(type="error", text=f"Gemini Live error: {err}")

    async def _on_audio(self, pcm: bytes) -> None:
        for ev in self.vad.process(pcm):
            if ev == "speech_start":
                # Barge-in: user interrupts the bot mid-reply.
                if self.task and not self.task.done():
                    self.task.cancel()
                    await self.send(type="interrupt")
                await self.send(type="state", value="listening")
            elif isinstance(ev, tuple) and ev[0] == "utterance":
                audio = ev[1]
                if self.task and not self.task.done():
                    self.task.cancel()
                self.task = asyncio.create_task(self._handle(audio))

    async def _on_control(self, text: str) -> None:
        if text == "reset":
            self.llm = get_llm()
            await self.send(type="state", value="listening")

    async def _handle(self, audio) -> None:
        try:
            import numpy as np
            print(f"🎧 utterance {len(audio)/16000:.2f}s đỉnh={np.abs(audio).max():.3f}", flush=True)
            await self.send(type="state", value="thinking")
            user_text = (await asyncio.to_thread(STT.transcribe, audio)).strip()
            print(f"   📝 STT: {user_text!r}", flush=True)
            if not user_text:
                await self.send(type="state", value="listening")
                return
            await self.send(type="user", text=user_text)

            try:
                bot_text = (await asyncio.to_thread(self.llm.reply, user_text)).strip()
            except Exception as exc:
                import traceback
                traceback.print_exc()
                bot_text = _friendly_error(exc)
            await self.send(type="bot", text=bot_text)

            await self.send(type="state", value="speaking")
            try:
                audio_msg = await asyncio.to_thread(_synth, bot_text)
                await self.send(type="audio", **audio_msg)
            except Exception:
                import traceback
                traceback.print_exc()
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
async def ws_endpoint(ws: WebSocket, system_instruction: str = None) -> None:
    await ws.accept()
    session = Session(ws, system_instruction=system_instruction)
    try:
        await session.run()
    except WebSocketDisconnect:
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
