#!/usr/bin/env python3
"""CLI entry point for the offline SYS - Speak Your Story pipeline.

Usage:
    python main.py                # continuous listening loop
    python main.py --once         # record and process a single utterance
    python main.py --file a.wav   # transcribe+refine an existing audio file
"""
from __future__ import annotations

import argparse
import sys

from src.config import load_config
from src.pipeline import Pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Process a single utterance and exit")
    parser.add_argument("--file", type=str, default=None, help="Path to an audio file to transcribe instead of using the mic")
    parser.add_argument("--config", type=str, default=None, help="Path to a config.yaml (defaults to ./config.yaml)")
    return parser.parse_args()


def print_result(result: dict) -> None:
    print(f"[raw]      {result['raw']}")
    print(f"[refined]  {result['refined']}")
    print("-" * 60)


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    pipeline = Pipeline(config)

    if args.file:
        result = pipeline.process_file(args.file)
        print_result(result)
        return 0

    if args.once:
        result = pipeline.process_utterance()
        if result is None:
            print("No speech detected.")
            return 1
        print_result(result)
        return 0

    print("Listening continuously. Press Ctrl+C to stop.\n")
    try:
        while True:
            result = pipeline.process_utterance()
            if result is not None:
                print_result(result)
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
