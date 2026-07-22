"""Ties audio capture, transcription, and refinement together, and keeps a
rolling window of prior refined turns to use as context for future ones.

Adds ``process_utterance_threaded()`` for GUI integration — runs the full
pipeline on the calling thread while firing status/level/result callbacks
that the UI can schedule onto the main thread.
"""
from __future__ import annotations

import threading
from collections import deque
from typing import Callable, Optional

from .audio_capture import AudioCapture
from .refiner import Refiner
from .transcriber import Transcriber


class Pipeline:
    def __init__(self, config: dict):
        audio_cfg  = config["audio"]
        whisper_cfg = config["whisper"]
        ollama_cfg  = config["ollama"]
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

    # ── Connectivity helpers ────────────────────────────────────────────────

    def check_ollama_status(self) -> bool:
        """Check whether the Ollama server is running and reachable."""
        return self.refiner.is_available()

    # ── Original CLI helpers (kept for backward compatibility) ──────────────

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

    # ── GUI-friendly async method ──────────────────────────────────────────

    def process_utterance_threaded(
        self,
        on_status: Callable[[str], None],
        on_level:  Optional[Callable[[float], None]] = None,
        on_result: Optional[Callable[[dict], None]] = None,
        on_error:  Optional[Callable[[str], None]] = None,
        stop_event: Optional[threading.Event] = None,
    ) -> None:
        """Run the full capture → transcribe → refine pipeline.

        **Call this from a background thread** — it blocks until the
        utterance is fully processed.  The callbacks will be invoked on the
        *same* background thread; the UI layer is responsible for scheduling
        them onto the main thread via ``root.after()``.
        """
        try:
            on_status("listening")

            audio_int16 = self.capture.record_utterance(
                level_callback=on_level,
                stop_event=stop_event,
            )

            if audio_int16 is None:
                on_status("idle")
                return

            # ── Transcribe ──────────────────────────────────────────────
            on_status("transcribing")
            audio_f32 = AudioCapture.to_float32(audio_int16)
            raw_text = self.transcriber.transcribe_array(
                audio_f32, self.sample_rate
            )

            if not raw_text.strip():
                on_status("idle")
                return

            # ── Refine (graceful fallback) ──────────────────────────────
            on_status("refining")
            try:
                refined_text = self.refiner.refine(raw_text, list(self.context))
            except Exception:
                refined_text = raw_text   # show raw text if Ollama fails

            self.context.append(refined_text)

            if on_result:
                on_result({"raw": raw_text, "refined": refined_text})

            on_status("idle")

        except Exception as exc:
            if on_error:
                on_error(str(exc))
            on_status("error")

    # ── Internal ────────────────────────────────────────────────────────────

    def _transcribe_and_refine_array(self, audio_int16) -> dict:
        audio_f32 = AudioCapture.to_float32(audio_int16)
        raw_text = self.transcriber.transcribe_array(audio_f32, self.sample_rate)
        refined_text = self.refiner.refine(raw_text, list(self.context))
        self.context.append(refined_text)
        return {"raw": raw_text, "refined": refined_text}
