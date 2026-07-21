"""Ties audio capture, transcription, and refinement together, and keeps a
rolling window of prior refined turns to use as context for future ones.
"""
from __future__ import annotations

from collections import deque
from typing import Optional

from .audio_capture import AudioCapture
from .refiner import Refiner
from .transcriber import Transcriber


class Pipeline:
    def __init__(self, config: dict):
        audio_cfg = config["audio"]
        whisper_cfg = config["whisper"]
        ollama_cfg = config["ollama"]
        context_cfg = config["context"]

        self.sample_rate = audio_cfg["sample_rate"]

        self.capture = AudioCapture(
            sample_rate=self.sample_rate,
            vad_aggressiveness=audio_cfg["vad_aggressiveness"],
            frame_duration_ms=audio_cfg["frame_duration_ms"],
            max_silence_ms=audio_cfg["max_silence_ms"],
            max_utterance_s=audio_cfg["max_utterance_s"],
            min_utterance_ms=audio_cfg["min_utterance_ms"],
        )
        self.transcriber = Transcriber(
            model_size=whisper_cfg["model_size"],
            device=whisper_cfg["device"],
            compute_type=whisper_cfg["compute_type"],
            language=whisper_cfg["language"],
        )
        self.refiner = Refiner(
            host=ollama_cfg["host"],
            model=ollama_cfg["model"],
            temperature=ollama_cfg["temperature"],
        )

        self.context: deque[str] = deque(maxlen=context_cfg["max_turns"])

    def process_utterance(self) -> Optional[dict]:
        """Record one utterance from the mic and run it through the full
        pipeline. Returns a dict with 'raw' and 'refined' text, or None if
        no speech was captured."""
        audio_int16 = self.capture.record_utterance()
        if audio_int16 is None:
            return None
        return self._transcribe_and_refine_array(audio_int16)

    def process_file(self, path: str) -> dict:
        raw_text = self.transcriber.transcribe_file(path)
        refined_text = self.refiner.refine(raw_text, list(self.context))
        self.context.append(refined_text)
        return {"raw": raw_text, "refined": refined_text}

    def _transcribe_and_refine_array(self, audio_int16) -> dict:
        audio_f32 = AudioCapture.to_float32(audio_int16)
        raw_text = self.transcriber.transcribe_array(audio_f32, self.sample_rate)
        refined_text = self.refiner.refine(raw_text, list(self.context))
        self.context.append(refined_text)
        return {"raw": raw_text, "refined": refined_text}
