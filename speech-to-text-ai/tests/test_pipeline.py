"""Lightweight tests that don't require a microphone, Whisper weights, or a
running Ollama server. Run with: pytest tests/
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import load_config
from src.refiner import Refiner


def test_load_config_defaults(tmp_path):
    # Non-existent path -> should fall back to defaults without raising
    config = load_config(tmp_path / "does_not_exist.yaml")
    assert config["whisper"]["model_size"] == "small"
    assert config["audio"]["sample_rate"] == 16000
    assert config["context"]["max_turns"] == 6


def test_refiner_builds_messages_with_context():
    refiner = Refiner()
    messages = refiner._build_messages(
        "so um i think the meeting is tomorrow",
        ["We discussed the Q3 roadmap.", "John will send the slides."],
    )
    roles = [m["role"] for m in messages]
    assert roles[0] == "system"
    assert any("Q3 roadmap" in m["content"] for m in messages)
    assert "so um i think" in messages[-1]["content"]


@patch("src.refiner.requests.post")
def test_refiner_refine_parses_response(mock_post):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "message": {"content": "I think the meeting is tomorrow."}
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    refiner = Refiner()
    result = refiner.refine("so um i think the meeting is tomorrow", [])
    assert result == "I think the meeting is tomorrow."
    mock_post.assert_called_once()


def test_refiner_refine_empty_input_short_circuits():
    refiner = Refiner()
    assert refiner.refine("   ", []) == ""
