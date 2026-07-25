"""Bottom speech bar — microphone toggle, engine mode selector, status label,
audio level bar, waveform visualization, and recording timer.

Allows changing refinement engine mode on the fly
(Built-in 0MB RAM / Hugging Face Free AI / Cloud API / Ollama).
"""
from __future__ import annotations

import time
from typing import Callable, Optional

import customtkinter as ctk

from . import theme as T
from .components import AudioLevelBar, StatusDot, WaveformBar


class SpeechBar(ctk.CTkFrame):
    """Fixed-height bar at the bottom of the editor area for speech-to-text."""

    STATUS_LABELS = {
        "idle":         "Ready — click 🎤 to speak",
        "loading":      "Loading speech engine…",
        "listening":    "🔴  Listening… speak now",
        "transcribing": "✍️  Transcribing audio…",
        "refining":     "✨  Refining transcript…",
        "error":        "⚠️  Error — try again",
    }

    MODE_LABELS = {
        "builtin":     "⚡ Built-in (0MB RAM)",
        "huggingface": "🤗 Hugging Face Free AI",
        "api":         "🌐 Other Cloud API",
        "ollama":      "🦙 Local Ollama",
    }

    def __init__(
        self,
        master,
        on_record_toggle: Callable[[], None],
        on_mode_change: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=T.SURFACE_ELEVATED,
            corner_radius=0,
            height=T.SPEECH_BAR_HEIGHT,
            **kwargs,
        )
        self.pack_propagate(False)
        self._on_record_toggle = on_record_toggle
        self._on_mode_change = on_mode_change
        self._is_recording = False
        self._record_start_time = 0.0
        self._timer_running = False

        # ── Inner container (centred vertically) ───────────────────────
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="x", expand=True, padx=T.PAD_XL, pady=T.PAD_SM)

        # ── Mic button ─────────────────────────────────────────────────
        mic_frame = ctk.CTkFrame(inner, fg_color="transparent")
        mic_frame.pack(side="left", padx=(0, T.PAD_LG))

        self.mic_btn = ctk.CTkButton(
            mic_frame,
            text="🎤",
            width=54, height=54,
            font=T.FONT_ICON_LG,
            fg_color=T.ACCENT,
            hover_color=T.ACCENT_HOVER,
            text_color=T.BG_DARKEST,
            corner_radius=27,
            command=self._toggle,
        )
        self.mic_btn.pack()

        # Recording timer below mic button
        self.timer_label = ctk.CTkLabel(
            mic_frame, text="",
            font=T.FONT_MONO, text_color=T.DANGER,
        )
        self.timer_label.pack(pady=(2, 0))

        # ── Middle section (status + level bar + waveform) ─────────────
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

        self.waveform = WaveformBar(mid, width=300, height=24)
        self.waveform.pack(fill="x", pady=(T.PAD_XS, 0))

        # ── Right section (Mode selector + Engine dot) ─────────────────
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right", padx=(T.PAD_LG, 0))

        # Mode Selector Dropdown
        self.mode_var = ctk.StringVar(value="⚡ Built-in (0MB RAM)")
        self.mode_dropdown = ctk.CTkOptionMenu(
            right,
            variable=self.mode_var,
            values=[
                "⚡ Built-in (0MB RAM)",
                "🤗 Hugging Face Free AI",
                "🌐 Other Cloud API",
                "🦙 Local Ollama",
            ],
            fg_color=T.BG_MEDIUM,
            button_color=T.BG_LIGHT,
            button_hover_color=T.BG_LIGHTER,
            dropdown_fg_color=T.BG_MEDIUM,
            dropdown_hover_color=T.BG_LIGHT,
            dropdown_text_color=T.TEXT_PRIMARY,
            text_color=T.TEXT_PRIMARY,
            font=T.FONT_TINY,
            dropdown_font=T.FONT_SMALL,
            height=28,
            width=180,
            corner_radius=T.CORNER_RADIUS_SM,
            command=self._on_dropdown_selected,
        )
        self.mode_dropdown.pack(side="left", padx=(0, T.PAD_SM))

        # Engine status
        status_frame = ctk.CTkFrame(right, fg_color="transparent")
        status_frame.pack(side="left")

        self.ai_dot = StatusDot(status_frame, size=10)
        self.ai_dot.pack(side="left", padx=(0, T.PAD_XS))
        self.ai_dot.set_status("connected")

        self.ai_label = ctk.CTkLabel(
            status_frame, text="Ready",
            font=T.FONT_TINY, text_color=T.SUCCESS,
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
            if is_rec:
                self._record_start_time = time.time()
                self._timer_running = True
                self._update_timer()
                self.waveform.start()
            else:
                self._timer_running = False
                self.timer_label.configure(text="")
                self.waveform.stop()

        if status != "listening":
            self.level_bar.reset()

    def set_audio_level(self, level: float) -> None:
        self.level_bar.set_level(level)
        self.waveform.set_amplitude(level)

    def set_engine_status(self, ready: bool, mode_name: str = "builtin") -> None:
        if mode_name == "builtin":
            self.ai_dot.set_status("connected")
            self.ai_label.configure(text="0MB RAM Engine", text_color=T.SUCCESS)
        elif mode_name == "huggingface":
            self.ai_dot.set_status("connected")
            self.ai_label.configure(text="HF Free AI", text_color=T.SUCCESS)
        elif mode_name == "api":
            status = "connected" if ready else "offline"
            self.ai_dot.set_status(status)
            self.ai_label.configure(
                text="API Key Set" if ready else "API Key Needed",
                text_color=T.SUCCESS if ready else T.WARNING,
            )
        else:
            status = "connected" if ready else "offline"
            self.ai_dot.set_status(status)
            self.ai_label.configure(
                text="Ollama Online" if ready else "Ollama Offline",
                text_color=T.SUCCESS if ready else T.DANGER,
            )

    # ── Internal ───────────────────────────────────────────────────────

    def _update_timer(self) -> None:
        if not self._timer_running:
            return
        elapsed = time.time() - self._record_start_time
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        self.timer_label.configure(text=f"🔴 {mins:02d}:{secs:02d}")
        self.after(500, self._update_timer)

    def _on_dropdown_selected(self, choice: str) -> None:
        mode_key = "builtin"
        if "Hugging Face" in choice:
            mode_key = "huggingface"
        elif "Cloud API" in choice:
            mode_key = "api"
        elif "Ollama" in choice:
            mode_key = "ollama"

        if self._on_mode_change:
            self._on_mode_change(mode_key)

    def _toggle(self) -> None:
        self._on_record_toggle()
