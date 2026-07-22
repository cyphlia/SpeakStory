"""Microphone capture with WebRTC VAD-based automatic start/stop.

Records audio from the default input device and returns just the "speech"
portion of a single utterance: recording begins once voiced frames are
detected and ends after a configurable amount of trailing silence.

GUI additions over the original:
  - ``level_callback``  — reports RMS audio level for waveform visualization
  - ``stop_event``      — threading.Event to cancel recording externally
"""
from __future__ import annotations

import collections
import math
import queue
import struct
import sys
import threading
import time
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
import webrtcvad


class AudioCapture:
    def __init__(
        self,
        sample_rate: int = 16000,
        vad_aggressiveness: int = 2,
        frame_duration_ms: int = 30,
        max_silence_ms: int = 800,
        max_utterance_s: int = 30,
        min_utterance_ms: int = 300,
    ):
        if frame_duration_ms not in (10, 20, 30):
            raise ValueError("frame_duration_ms must be 10, 20, or 30 (webrtcvad requirement)")

        self.sample_rate = sample_rate
        self.frame_duration_ms = frame_duration_ms
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)  # samples per frame
        self.vad = webrtcvad.Vad(vad_aggressiveness)

        self.max_silence_frames = max(1, int(max_silence_ms / frame_duration_ms))
        self.max_utterance_frames = int(max_utterance_s * 1000 / frame_duration_ms)
        self.min_utterance_frames = max(1, int(min_utterance_ms / frame_duration_ms))

    def _frame_is_speech(self, frame_bytes: bytes) -> bool:
        return self.vad.is_speech(frame_bytes, self.sample_rate)

    @staticmethod
    def _rms_level(frame_bytes: bytes) -> float:
        """Calculate normalised RMS audio level from raw int16 bytes (0.0–1.0)."""
        count = len(frame_bytes) // 2
        if count == 0:
            return 0.0
        shorts = struct.unpack(f"<{count}h", frame_bytes)
        sum_sq = sum(s * s for s in shorts)
        rms = math.sqrt(sum_sq / count)
        # int16 max is 32768; typical voiced speech RMS ~1000-5000
        return min(1.0, rms / 8000.0)

    def record_utterance(
        self,
        timeout_s: Optional[float] = None,
        level_callback: Optional[Callable[[float], None]] = None,
        stop_event: Optional[threading.Event] = None,
    ) -> Optional[np.ndarray]:
        """Block until the user starts speaking, then record until they stop
        (trailing silence), ``stop_event`` is set, or ``max_utterance_s`` is
        hit.  Returns int16 mono numpy array of just the speech, or *None* if
        nothing was captured before timeout_s elapses.
        """
        audio_q: "queue.Queue[bytes]" = queue.Queue()

        def callback(indata, frames, time_info, status):
            if status:
                print(f"[audio_capture] stream status: {status}", file=sys.stderr)
            audio_q.put(bytes(indata))

        voiced_frames: list[bytes] = []
        ring_buffer: collections.deque = collections.deque(maxlen=self.max_silence_frames)
        triggered = False
        num_frames_total = 0
        start_time = time.monotonic()

        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=self.frame_size,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            while True:
                # ── External cancellation ───────────────────────────────
                if stop_event is not None and stop_event.is_set():
                    break

                # ── Pre-speech timeout ──────────────────────────────────
                if timeout_s is not None and not triggered:
                    if time.monotonic() - start_time > timeout_s:
                        return None

                try:
                    frame = audio_q.get(timeout=0.1)
                except queue.Empty:
                    # Send zero level while idle so the UI bar stays alive
                    if level_callback is not None:
                        level_callback(0.0)
                    continue

                if len(frame) < self.frame_size * 2:  # 2 bytes per int16 sample
                    continue

                # Report audio level for UI waveform
                if level_callback is not None:
                    level_callback(self._rms_level(frame))

                is_speech = self._frame_is_speech(frame)

                if not triggered:
                    ring_buffer.append((frame, is_speech))
                    if is_speech:
                        triggered = True
                        voiced_frames.extend(f for f, _ in ring_buffer)
                        ring_buffer.clear()
                else:
                    voiced_frames.append(frame)
                    ring_buffer.append((frame, is_speech))
                    num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                    num_frames_total += 1

                    silence_exceeded = (
                        len(ring_buffer) == ring_buffer.maxlen
                        and num_unvoiced == ring_buffer.maxlen
                    )
                    too_long = num_frames_total >= self.max_utterance_frames

                    if silence_exceeded or too_long:
                        break

        if len(voiced_frames) < self.min_utterance_frames:
            return None

        raw = b"".join(voiced_frames)
        audio = np.frombuffer(raw, dtype=np.int16)
        return audio

    @staticmethod
    def to_float32(audio_int16: np.ndarray) -> np.ndarray:
        """faster-whisper expects float32 samples in [-1, 1]."""
        return audio_int16.astype(np.float32) / 32768.0
