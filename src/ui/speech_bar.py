"""Bottom speech bar — microphone toggle, status label, audio level, AI dot.

The bar communicates upward through callbacks; the MainWindow is responsible
for threading and scheduling.
"""
from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from . import theme as T
from .components import AudioLevelBar, StatusDot


class SpeechBar(ctk.CTkFrame):
    """Fixed-height bar at the bottom of the editor area for speech-to-text."""

    STATUS_LABELS = {
        "idle":         "Ready — click 🎤 to speak",
        "loading":      "Loading AI model…",
        "listening":    "🔴  Listening… speak now",
        "transcribing": "✍️  Transcribing audio…",
        "refining":     "🤖  Refining with AI…",
        "error":        "⚠️  Error — try again",
    }

    def __init__(
        self,
        master,
        on_record_toggle: Callable[[], None],
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=T.BG_DARK,
            corner_radius=0,
            height=T.SPEECH_BAR_HEIGHT,
            **kwargs,
        )
        self.pack_propagate(False)
        self._on_record_toggle = on_record_toggle
        self._is_recording = False

        # ── Inner container (centred vertically) ───────────────────────
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", expand=True, padx=T.PAD_LG, pady=T.PAD_SM)

        # ── Mic button ─────────────────────────────────────────────────
        self.mic_btn = ctk.CTkButton(
            inner,
            text="🎤",
            width=50, height=50,
            font=T.FONT_ICON_LG,
            fg_color=T.ACCENT,
            hover_color=T.ACCENT_HOVER,
            text_color=T.BG_DARKEST,
            corner_radius=25,
            command=self._toggle,
        )
        self.mic_btn.pack(side="left", padx=(0, T.PAD_LG))

        # ── Middle section (status + level bar) ────────────────────────
        mid = ctk.CTkFrame(inner, fg_color="transparent")
        mid.pack(side="left", fill="x", expand=True)

        self.status_label = ctk.CTkLabel(
            mid,
            text=self.STATUS_LABELS["loading"],
            font=T.FONT_SMALL,
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        )
        self.status_label.pack(anchor="w")

        self.level_bar = AudioLevelBar(mid, width=300, height=8)
        self.level_bar.pack(fill="x", pady=(T.PAD_XS, 0))

        # ── Right section (AI status) ──────────────────────────────────
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right", padx=(T.PAD_LG, 0))

        self.ai_dot = StatusDot(right, size=10)
        self.ai_dot.pack(side="left", padx=(0, T.PAD_XS))

        self.ai_label = ctk.CTkLabel(
            right, text="AI",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED,
        )
        self.ai_label.pack(side="left")

        # Start disabled until pipeline is loaded
        self.mic_btn.configure(state="disabled")

    # ── Public API ─────────────────────────────────────────────────────

    def set_ready(self) -> None:
        """Enable the mic button once the pipeline is loaded."""
        self.mic_btn.configure(state="normal")
        self.set_status("idle")

    def set_status(self, status: str) -> None:
        label = self.STATUS_LABELS.get(status, status)
        colour = T.DANGER if status == "error" else T.TEXT_SECONDARY
        if status == "listening":
            colour = T.SUCCESS
        self.status_label.configure(text=label, text_color=colour)

        is_rec = status == "listening"
        if is_rec != self._is_recording:
            self._is_recording = is_rec
            self.mic_btn.configure(
                fg_color=T.DANGER if is_rec else T.ACCENT,
                hover_color="#D47A7A" if is_rec else T.ACCENT_HOVER,
                text="⏹" if is_rec else "🎤",
            )

        # Reset level bar when not listening
        if status != "listening":
            self.level_bar.reset()

    def set_audio_level(self, level: float) -> None:
        self.level_bar.set_level(level)

    def set_ai_status(self, connected: bool) -> None:
        status = "connected" if connected else "offline"
        self.ai_dot.set_status(status)
        self.ai_label.configure(
            text="AI Online" if connected else "AI Offline",
            text_color=T.SUCCESS if connected else T.DANGER,
        )

    # ── Internal ───────────────────────────────────────────────────────

    def _toggle(self) -> None:
        self._on_record_toggle()
