"""Wrapper around faster-whisper for local, offline transcription."""
from __future__ import annotations

from typing import Optional

import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        language: Optional[str] = None,
    ):
        self.language = language
        print(f"[transcriber] loading Whisper model '{model_size}' ({device}/{compute_type})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print("[transcriber] model ready.")

    def transcribe_array(self, audio_float32: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe a float32 mono numpy array in [-1, 1]."""
        segments, info = self.model.transcribe(
            audio_float32,
            language=self.language,
            vad_filter=False,  # we already did VAD during capture
            beam_size=5,
        )
        text = " ".join(segment.text.strip() for segment in segments)
        return text.strip()

    def transcribe_file(self, path: str) -> str:
        segments, info = self.model.transcribe(
            path,
            language=self.language,
            vad_filter=True,
            beam_size=5,
        )
        text = " ".join(segment.text.strip() for segment in segments)
        return text.strip()
