"""Streaming voice-activity detection for realtime turn-taking.

Feed raw PCM16 (16 kHz mono) bytes as they arrive from the browser. The
detector buffers fixed 20 ms frames, runs WebRTC VAD on each, and emits events:

    "speech_start"  -> user just began talking (use for barge-in)
    ("utterance", np.ndarray) -> a full user turn ended (speech then silence)

Keeps a little pre-roll so the first phoneme isn't clipped.
"""
from __future__ import annotations

import collections

import numpy as np
import webrtcvad

SAMPLE_RATE = 16000
FRAME_MS = 20
FRAME_BYTES = int(SAMPLE_RATE * FRAME_MS / 1000) * 2  # 20 ms of int16 = 640 bytes


class TurnDetector:
    def __init__(
        self,
        aggressiveness: int = 2,
        start_frames: int = 5,      # ~100 ms of speech to confirm a turn started
        end_silence_ms: int = 700,  # silence after speech that ends the turn
        preroll_ms: int = 200,      # audio kept before detected speech
    ) -> None:
        self.vad = webrtcvad.Vad(aggressiveness)
        self.start_frames = start_frames
        self.end_frames = int(end_silence_ms / FRAME_MS)
        self.preroll = collections.deque(maxlen=int(preroll_ms / FRAME_MS))
        self._buf = bytearray()
        self._reset()

    def _reset(self) -> None:
        self.triggered = False
        self.voiced: list[bytes] = []
        self.silence_run = 0
        self.speech_run = 0

    def process(self, pcm: bytes) -> list:
        """Feed raw bytes; return a list of events produced by completed frames."""
        events: list = []
        self._buf.extend(pcm)
        while len(self._buf) >= FRAME_BYTES:
            frame = bytes(self._buf[:FRAME_BYTES])
            del self._buf[:FRAME_BYTES]
            events.extend(self._frame(frame))
        return events

    def _frame(self, frame: bytes) -> list:
        events: list = []
        is_speech = self.vad.is_speech(frame, SAMPLE_RATE)

        if not self.triggered:
            self.preroll.append(frame)
            self.speech_run = self.speech_run + 1 if is_speech else 0
            if self.speech_run >= self.start_frames:
                self.triggered = True
                self.voiced = list(self.preroll)  # include pre-roll
                self.preroll.clear()
                self.silence_run = 0
                events.append("speech_start")
        else:
            self.voiced.append(frame)
            self.silence_run = 0 if is_speech else self.silence_run + 1
            if self.silence_run >= self.end_frames:
                pcm = b"".join(self.voiced)
                audio = np.frombuffer(pcm, dtype=np.int16).astype(np.float32) / 32768.0
                self._reset()
                events.append(("utterance", audio))
        return events
