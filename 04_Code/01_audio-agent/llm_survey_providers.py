"""Direct Ollama HTTP wrappers for the LLM-only test harness (test3).

Kept separate from src/llm.py (production, which pins one CONFIG.ollama_model)
so the test harness can hit any locally pulled model on demand.
"""
from __future__ import annotations

import requests

from src.config import CONFIG
from src.llm import resolve_system_prompt

MODELS = {
    "qwen2.5:0.5b": "Qwen2.5 0.5B",
    "qwen2.5:1.5b": "Qwen2.5 1.5B",
    "qwen2.5:3b": "Qwen2.5 3B",
    "qwen2.5:7b": "Qwen2.5 7B (baseline hiện tại)",
    "qwen3:4b": "Qwen3 4B",
    "qwen3:8b": "Qwen3 8B",
    "llama3.2:1b": "Llama 3.2 1B",
    "llama3.2:3b": "Llama 3.2 3B",
    "llama3.1:8b": "Llama 3.1 8B",
}


def ask(model: str, text: str, system_instruction: str | None = None) -> dict:
    """Returns {answer, eval_count, eval_tps, load_s, total_s}."""
    messages = [
        {"role": "system", "content": resolve_system_prompt(system_instruction)},
        {"role": "user", "content": text},
    ]
    resp = requests.post(
        f"{CONFIG.ollama_host}/api/chat",
        json={"model": model, "messages": messages, "stream": False},
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()
    answer = data["message"]["content"].strip()

    eval_count = data.get("eval_count")
    eval_duration_ns = data.get("eval_duration")
    load_duration_ns = data.get("load_duration", 0)
    total_duration_ns = data.get("total_duration", 0)

    eval_tps = (eval_count / (eval_duration_ns / 1e9)) if eval_count and eval_duration_ns else None
    return {
        "answer": answer,
        "eval_count": eval_count,
        "eval_tps": eval_tps,
        "load_s": load_duration_ns / 1e9,
        "total_s": total_duration_ns / 1e9,
    }
