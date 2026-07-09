#!/usr/bin/env python3
"""Entry point for the voice agent.

Usage:
    python run.py            # hands-free voice chat (mic + speaker)
    python run.py --text     # type-to-chat (no microphone, still speaks replies)
"""
from __future__ import annotations

import argparse

from src.agent import VoiceAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="Medical Signal Voice Agent")
    parser.add_argument(
        "--text", action="store_true", help="Type instead of speaking (test mode)"
    )
    args = parser.parse_args()

    agent = VoiceAgent()
    if args.text:
        agent.run_text()
    else:
        agent.run_voice()


if __name__ == "__main__":
    main()
