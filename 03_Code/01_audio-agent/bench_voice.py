#!/usr/bin/env python3
"""Benchmark voice pipeline on EC2/local (STT -> LLM -> TTS).

Synthesizes 10 standard test questions using Piper TTS to simulate speech audio,
then feeds them into Faster-Whisper STT, Ollama LLM, and Piper TTS, recording
latency (STT, LLM, TTS, total) and STT accuracy.

Usage:
    python bench_voice.py
    python bench_voice.py --whisper-model Systran/faster-distil-whisper-small.en
    python bench_voice.py --beam-size 3
    python bench_voice.py --stt-only
"""
from __future__ import annotations

import argparse
import io
import os
import statistics
import tempfile
import time
import wave
from pathlib import Path

import numpy as np
import soundfile as sf

from src.config import CONFIG
from src.llm import get_llm
from src.stt import FasterWhisperSTT
from src.tts import get_tts

# 10 standard questions reflecting health vitals and queries from Week 46/47
BENCH_QUESTIONS = [
    "What is my heart rate?",
    "What is my blood pressure?",
    "What is my blood oxygen?",
    "What is my SpO2?",
    "Give me a summary of my health.",
    "How did I sleep last night?",
    "What is my sleep score?",
    "How about my heart rate?",
    "What is my current heart rate?",
    "Can you check my vitals?",
]

# Standard System Instruction (Prompt B with explicit facts from latest vitals)
SYSTEM_INSTRUCTION = (
    "You are an extremely friendly, warm health assistant that answers briefly (at most 2-3 sentences). "
    "You answer questions about the user's vital signs and health. "
    "Always reply in English. No markdown, emoji or lists, since the reply will be read aloud. "
    "Answer only from these facts. Never make up a number.\n\n"
    "Current heart rate: 74 bpm (magene_h303, 28 Oct 22:26 Vietnam time).\n"
    "Current SpO2: 99% (yuwell_yx110, 28 Oct 22:26 Vietnam time).\n"
    "Blood pressure: not measured.\n"
    "Sleep: not measured.\n"
    "User profile: 25 years old, male, 175 cm, 70 kg, BMI = 22.86, BMR = 1680 kcal.\n"
)


def resample_to_16k(audio: np.ndarray, orig_sr: int) -> np.ndarray:
    """Resample mono float32 audio to 16000 Hz if needed."""
    if orig_sr == 16000:
        return audio
    # Simple linear interpolation for resampling mono audio
    target_len = int(len(audio) * 16000 / orig_sr)
    indices = np.linspace(0, len(audio) - 1, target_len)
    return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)


def synth_question_audio(tts, text: str, tmp_dir: Path) -> np.ndarray:
    """Synthesize text to WAV via Piper and load as 16kHz float32 mono ndarray."""
    wav_path = tmp_dir / "q.wav"
    tts.speak_to_file(text, wav_path)
    data, sr = sf.read(str(wav_path), dtype="float32")
    if data.ndim > 1:
        data = data[:, 0]
    return resample_to_16k(data, sr)


def run_bench(
    whisper_model: str,
    beam_size: int,
    stt_only: bool = False,
    llm_model: str | None = None,
) -> None:
    print(f"\n{'='*70}")
    print(f"🎤 Voice Pipeline Benchmark")
    print(f"STT Model : {whisper_model}")
    print(f"Beam Size : {beam_size}")
    print(f"LLM Model : {'(disabled)' if stt_only else (llm_model or CONFIG.ollama_model)}")
    print(f"TTS Model : {CONFIG.tts_provider}")
    print(f"{'='*70}\n")

    # Set environment variables for STT config
    os.environ["WHISPER_BEAM_SIZE"] = str(beam_size)
    CONFIG.whisper_beam_size = beam_size

    print("⏳ Loading STT model...")
    stt = FasterWhisperSTT(language="en", model=whisper_model)

    print("⏳ Loading TTS model...")
    tts = get_tts("en")

    llm = None
    if not stt_only:
        print("⏳ Loading LLM...")
        llm = get_llm(system_instruction=SYSTEM_INSTRUCTION, language="en")
        # Warmup LLM to ensure it's loaded in RAM
        try:
            llm.reply("hello")
        except Exception as e:
            print(f"⚠️  LLM warmup error: {e}")

    print("\n🚀 Starting benchmark on 10 questions...\n")

    results = []
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        for idx, q in enumerate(BENCH_QUESTIONS, 1):
            print(f"[{idx:02d}/10] Testing: {q!r}")

            # 1. Synthesize question speech audio
            audio_16k = synth_question_audio(tts, q, tmp_dir)

            # 2. STT
            t0 = time.perf_counter()
            recognized = stt.transcribe(audio_16k).strip()
            stt_s = time.perf_counter() - t0

            # Check match (normalize lower and strip punctuation)
            norm_q = q.lower().strip(" .?!,")
            norm_rec = recognized.lower().strip(" .?!,")
            is_match = (norm_q == norm_rec) or (
                "spo2" in norm_q and "spo2" in norm_rec
            )

            # 3. LLM
            llm_s = 0.0
            reply = ""
            if llm:
                t0 = time.perf_counter()
                try:
                    reply = llm.reply(recognized if recognized else q).strip()
                except Exception as exc:
                    reply = f"Error: {exc}"
                llm_s = time.perf_counter() - t0

            # 4. TTS on reply
            tts_s = 0.0
            if reply and not stt_only:
                reply_wav = tmp_dir / "reply.wav"
                t0 = time.perf_counter()
                try:
                    tts.speak_to_file(reply, reply_wav)
                except Exception:
                    pass
                tts_s = time.perf_counter() - t0

            total_s = stt_s + llm_s + tts_s

            results.append({
                "id": idx,
                "question": q,
                "recognized": recognized,
                "match": is_match,
                "stt_s": stt_s,
                "llm_s": llm_s,
                "tts_s": tts_s,
                "total_s": total_s,
                "reply": reply,
            })

            status_icon = "✅" if is_match else "❌"
            print(
                f"   STT ({stt_s:.2f}s) {status_icon}: {recognized!r}\n"
                f"   LLM ({llm_s:.2f}s)   : {reply[:60] + '...' if len(reply) > 60 else reply}\n"
                f"   TTS ({tts_s:.2f}s) | Total: {total_s:.2f}s\n"
            )

    # Summary Table
    print("\n" + "=" * 90)
    print(f"{'#':<3} | {'Original Question':<32} | {'Recognized (STT)':<32} | {'STT':<6} | {'Total':<6} | Match")
    print("-" * 90)
    for r in results:
        rec_disp = (r["recognized"][:29] + "...") if len(r["recognized"]) > 32 else r["recognized"]
        q_disp = (r["question"][:29] + "...") if len(r["question"]) > 32 else r["question"]
        m_str = "✅ Yes" if r["match"] else "❌ No"
        print(f"{r['id']:<3} | {q_disp:<32} | {rec_disp:<32} | {r['stt_s']:5.2f}s | {r['total_s']:5.2f}s | {m_str}")

    stt_times = [r["stt_s"] for r in results]
    llm_times = [r["llm_s"] for r in results]
    tts_times = [r["tts_s"] for r in results]
    total_times = [r["total_s"] for r in results]
    correct_count = sum(1 for r in results if r["match"])

    print("=" * 90)
    print("\n📊 THỐNG KÊ:")
    print(f"  * STT Đúng: {correct_count}/{len(results)} câu ({correct_count/len(results)*100:.0f}%)")
    print(f"  * STT Thời gian  : Trung bình = {statistics.mean(stt_times):.2f}s | Trung vị = {statistics.median(stt_times):.2f}s")
    if not stt_only:
        print(f"  * LLM Thời gian  : Trung bình = {statistics.mean(llm_times):.2f}s | Trung vị = {statistics.median(llm_times):.2f}s")
        print(f"  * TTS Thời gian  : Trung bình = {statistics.mean(tts_times):.2f}s | Trung vị = {statistics.median(tts_times):.2f}s")
        print(f"  * TỔNG Thời gian : Trung bình = {statistics.mean(total_times):.2f}s | Trung vị = {statistics.median(total_times):.2f}s")
    print("=" * 90 + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Voice pipeline benchmark")
    ap.add_argument(
        "--whisper-model",
        type=str,
        default=os.getenv("WHISPER_MODEL", "Systran/faster-distil-whisper-medium.en"),
        help="Whisper model name or path",
    )
    ap.add_argument(
        "--beam-size",
        type=int,
        default=int(os.getenv("WHISPER_BEAM_SIZE", "1")),
        help="Beam size for STT (default: 1)",
    )
    ap.add_argument(
        "--stt-only",
        action="store_true",
        help="Benchmark STT only without calling LLM and TTS",
    )
    ap.add_argument(
        "--llm-model",
        type=str,
        default=None,
        help="Ollama model override",
    )
    args = ap.parse_args()

    run_bench(
        whisper_model=args.whisper_model,
        beam_size=args.beam_size,
        stt_only=args.stt_only,
        llm_model=args.llm_model,
    )


if __name__ == "__main__":
    main()
