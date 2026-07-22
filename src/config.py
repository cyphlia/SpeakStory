"""Small helper for loading config.yaml with sane defaults."""
from __future__ import annotations

import pathlib
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = pathlib.Path(__file__).resolve().parent.parent / "config.yaml"


def load_config(path: str | pathlib.Path | None = None) -> dict[str, Any]:
    """Load the YAML config file, falling back to built-in defaults for any
    keys that are missing so the app still runs with a partial config."""
    config_path = pathlib.Path(path) if path else DEFAULT_CONFIG_PATH

    defaults: dict[str, Any] = {
        "whisper": {
            "model_size": "small",
            "device": "cpu",
            "compute_type": "int8",
            "language": None,
        },
        "refiner": {
            "mode": "builtin",
            "api_key": "",
        },
        "ollama": {
            "host": "http://localhost:11434",
            "model": "llama3.1",
            "temperature": 0.2,
        },
        "audio": {
            "sample_rate": 16000,
            "vad_aggressiveness": 2,
            "frame_duration_ms": 30,
            "max_silence_ms": 800,
            "max_utterance_s": 30,
            "min_utterance_ms": 300,
        },
        "context": {
            "max_turns": 6,
        },
    }

    if not config_path.exists():
        return defaults

    with open(config_path, "r", encoding="utf-8") as f:
        loaded = yaml.safe_load(f) or {}

    merged = defaults
    for section, values in loaded.items():
        if isinstance(values, dict) and section in merged:
            merged[section] = {**merged[section], **values}
        else:
            merged[section] = values

    return merged
