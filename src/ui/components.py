"""Reusable styled widgets for the SpeakStory UI.

NoteCard     — sidebar preview card for a single note
TagChip      — removable tag pill with auto-colour
AudioLevelBar — canvas-based real-time audio-level bar with gradient
StatusDot    — tiny circle indicating connection health with pulse animation
WaveformBar  — simple sine-wave visualization for recording state
"""
from __future__ import annotations

import math
import tkinter as tk
from typing import Callable, Optional

import customtkinter as ctk

from . import theme as T


# ═══════════════════════════════════════════════════════════════════════════
#  NoteCard — sidebar item
# ═══════════════════════════════════════════════════════════════════════════

class NoteCard(ctk.CTkFrame):
    """A clickable card that represents a single note in the sidebar list."""

    def __init__(
        self,
        master,
        note_id: str,
        title: str,
        preview: str,
        time_label: str,
        is_pinned: bool = False,
        is_selected: bool = False,
        tags: list[str] | None = None,
        char_count: int = 0,
        on_click: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        on_pin_toggle: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        bg = T.ACCENT_SUBTLE if is_selected else T.BG_MEDIUM
        border_col = T.BORDER_FOCUS if is_selected else T.BORDER
        super().__init__(
            master,
            fg_color=bg,
            corner_radius=T.CORNER_RADIUS,
            border_width=1,
            border_color=border_col,
            cursor="hand2",
            **kwargs,
        )
        self.note_id = note_id
        self._on_click = on_click
        self._on_delete = on_delete
        self._on_pin_toggle = on_pin_toggle
        self._is_selected = is_selected

        # ── Layout ──────────────────────────────────────────────────────
        self.grid_columnconfigure(0, weight=1)

        # Row 0 — title + pin indicator
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=T.PAD_MD, pady=(T.PAD_SM, 0))
        top_row.grid_columnconfigure(0, weight=1)

        title_text = title if len(title) <= 30 else title[:28] + "…"
        self.title_label = ctk.CTkLabel(
            top_row, text=title_text,
            font=T.FONT_BODY_BOLD,
            text_color=T.TEXT_BRIGHT if is_selected else T.TEXT_PRIMARY,
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        if is_pinned:
            pin_lbl = ctk.CTkLabel(top_row, text="📌", font=T.FONT_TINY)
            pin_lbl.grid(row=0, column=1, sticky="e", padx=(4, 0))

        # Row 1 — preview
        preview_text = preview if len(preview) <= 50 else preview[:48] + "…"
        self.preview_label = ctk.CTkLabel(
            self, text=preview_text or "Empty note",
            font=T.FONT_SMALL,
            text_color=T.TEXT_MUTED if not preview_text else T.TEXT_SECONDARY,
            anchor="w",
        )
        self.preview_label.grid(row=1, column=0, sticky="ew",
                                padx=T.PAD_MD, pady=(2, 0))

        # Row 2 — bottom: time + tag dots + char count
        bottom_row = ctk.CTkFrame(self, fg_color="transparent")
        bottom_row.grid(row=2, column=0, sticky="ew",
                        padx=T.PAD_MD, pady=(4, T.PAD_SM))
        bottom_row.grid_columnconfigure(1, weight=1)

        self.time_label = ctk.CTkLabel(
            bottom_row, text=time_label,
            font=T.FONT_MICRO, text_color=T.TEXT_MUTED,
            anchor="w",
        )
        self.time_label.grid(row=0, column=0, sticky="w")

        # Tag colour dots
        if tags:
            dots_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
            dots_frame.grid(row=0, column=1, sticky="w", padx=(T.PAD_SM, 0))
            for tag in tags[:4]:  # show up to 4 tag dots
                dot = tk.Canvas(
                    dots_frame, width=8, height=8,
                    bg=bg, highlightthickness=0, bd=0,
                )
                dot.create_oval(1, 1, 7, 7, fill=T.tag_colour(tag), outline="")
                dot.pack(side="left", padx=(0, 2))

        # Character count
        if char_count > 0:
            count_text = f"{char_count:,}c" if char_count < 10000 else f"{char_count // 1000}k"
            ctk.CTkLabel(
                bottom_row, text=count_text,
                font=T.FONT_MICRO, text_color=T.TEXT_MUTED,
                anchor="e",
            ).grid(row=0, column=2, sticky="e")

        # ── Events ─────────────────────────────────────────────────────
        self.bind("<Button-1>", self._clicked)
        for child in self.winfo_children():
            child.bind("<Button-1>", self._clicked)
            for grandchild in child.winfo_children():
                grandchild.bind("<Button-1>", self._clicked)

        # Hover
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # Right-click context menu
        self._menu = tk.Menu(self, tearoff=0,
                             bg=T.BG_LIGHT, fg=T.TEXT_PRIMARY,
                             activebackground=T.ACCENT,
                             activeforeground=T.BG_DARKEST,
                             relief="flat", bd=0)
        pin_text = "Unpin" if is_pinned else "Pin to top"
        self._menu.add_command(label=pin_text, command=self._toggle_pin)
        self._menu.add_separator()
        self._menu.add_command(label="Delete", command=self._delete)
        self.bind("<Button-3>", self._show_menu)
        for child in self.winfo_children():
            child.bind("<Button-3>", self._show_menu)

    # ── Callbacks ──────────────────────────────────────────────────────

    def _clicked(self, event=None):
        if self._on_click:
            self._on_click(self.note_id)

    def _on_enter(self, event=None):
        if not self._is_selected:
            self.configure(fg_color=T.BG_LIGHT, border_color=T.BORDER_LIGHT)

    def _on_leave(self, event=None):
        if not self._is_selected:
            self.configure(fg_color=T.BG_MEDIUM, border_color=T.BORDER)

    def _show_menu(self, event):
        self._menu.tk_popup(event.x_root, event.y_root)

    def _toggle_pin(self):
        if self._on_pin_toggle:
            self._on_pin_toggle(self.note_id)

    def _delete(self):
        if self._on_delete:
            self._on_delete(self.note_id)


# ═══════════════════════════════════════════════════════════════════════════
#  TagChip — removable tag pill with auto-colour
# ═══════════════════════════════════════════════════════════════════════════

class TagChip(ctk.CTkFrame):
    """Small rounded pill showing a tag name with optional ✕ button.
    Colour is automatically determined from the tag text hash."""

    def __init__(
        self,
        master,
        text: str,
        on_remove: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        colour = T.tag_colour(text)
        # Create a subtle bg from the tag colour
        super().__init__(
            master, fg_color=T.ACCENT_SUBTLE, corner_radius=12, height=26,
            border_width=1, border_color=colour,
            **kwargs,
        )
        self.tag_text = text
        self.pack_propagate(False)

        lbl = ctk.CTkLabel(
            self, text=f"● {text}", font=(T.FONT_FAMILY, 11),
            text_color=colour,
        )
        lbl.pack(side="left", padx=(8, 2 if on_remove else 8), pady=2)

        if on_remove:
            btn = ctk.CTkButton(
                self, text="✕", width=18, height=18,
                font=(T.FONT_FAMILY, 10), corner_radius=9,
                fg_color="transparent", hover_color=T.DANGER,
                text_color=T.TEXT_SECONDARY,
                command=lambda: on_remove(text),
            )
            btn.pack(side="left", padx=(0, 4), pady=2)


# ═══════════════════════════════════════════════════════════════════════════
#  AudioLevelBar — canvas-based VU meter with gradient
# ═══════════════════════════════════════════════════════════════════════════

class AudioLevelBar(tk.Canvas):
    """Horizontal bar that fills proportionally to the current audio level."""

    def __init__(self, master, width: int = 200, height: int = 10, **kwargs):
        super().__init__(
            master, width=width, height=height,
            bg=T.BG_DARK, highlightthickness=0, bd=0,
            **kwargs,
        )
        self._level = 0.0
        self._target_level = 0.0
        self._animating = False
        self.bind("<Configure>", lambda e: self._draw())

    def set_level(self, level: float) -> None:
        self._target_level = max(0.0, min(1.0, level))
        if not self._animating:
            self._animating = True
            self._animate()

    def _animate(self) -> None:
        # Smooth interpolation toward target
        diff = self._target_level - self._level
        self._level += diff * 0.35
        if abs(diff) < 0.005:
            self._level = self._target_level
        self._draw()
        if self._level != self._target_level:
            self.after(30, self._animate)
        else:
            self._animating = False

    def _draw(self) -> None:
        self.delete("all")
        w = self.winfo_width() or 200
        h = self.winfo_height() or 10

        # Background track with rounded appearance
        r = h // 2
        self.create_rectangle(0, 0, w, h, fill=T.BG_MEDIUM, outline="")

        if self._level > 0.01:
            bar_w = max(2, int(w * self._level))
            # Colour ramps with level
            if self._level < 0.55:
                colour = T.ACCENT
            elif self._level < 0.80:
                colour = T.SUCCESS
            else:
                colour = T.DANGER
            self.create_rectangle(0, 0, bar_w, h, fill=colour, outline="")

            # Segment markers (subtle tick marks every 10%)
            for pct in range(1, 10):
                x = int(w * pct / 10)
                if x < bar_w:
                    self.create_line(x, 0, x, h, fill=T.BG_DARK, width=1)

    def reset(self) -> None:
        self._level = 0.0
        self._target_level = 0.0
        self._draw()


# ═══════════════════════════════════════════════════════════════════════════
#  StatusDot — tiny connection-health circle with pulse animation
# ═══════════════════════════════════════════════════════════════════════════

class StatusDot(tk.Canvas):
    """Tiny coloured dot — green = connected, red = offline, grey = unknown.
    Pulses when status is 'loading'."""

    COLOURS = {
        "connected": T.SUCCESS,
        "offline":   T.DANGER,
        "unknown":   T.TEXT_MUTED,
        "loading":   T.WARNING,
    }

    def __init__(self, master, size: int = 10, **kwargs):
        super().__init__(
            master, width=size, height=size,
            bg=T.BG_DARK, highlightthickness=0, bd=0,
            **kwargs,
        )
        self._size = size
        self._status = "unknown"
        self._pulse_phase = 0.0
        self._pulse_running = False
        self._draw()

    def set_status(self, status: str) -> None:
        self._status = status
        if status == "loading" and not self._pulse_running:
            self._pulse_running = True
            self._pulse()
        elif status != "loading":
            self._pulse_running = False
        self._draw()

    def _pulse(self) -> None:
        if not self._pulse_running:
            return
        self._pulse_phase += 0.15
        self._draw()
        self.after(50, self._pulse)

    def _draw(self) -> None:
        self.delete("all")
        colour = self.COLOURS.get(self._status, T.TEXT_MUTED)
        pad = 1

        if self._status == "loading":
            # Pulsing effect — vary the size
            scale = 0.7 + 0.3 * abs(math.sin(self._pulse_phase))
            r = (self._size - 2) * scale / 2
            cx, cy = self._size / 2, self._size / 2
            self.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                fill=colour, outline="",
            )
        else:
            self.create_oval(
                pad, pad, self._size - pad, self._size - pad,
                fill=colour, outline="",
            )


# ═══════════════════════════════════════════════════════════════════════════
#  WaveformBar — simple animated sine-wave for recording state
# ═══════════════════════════════════════════════════════════════════════════

class WaveformBar(tk.Canvas):
    """Animated sine-wave visualization shown during recording."""

    def __init__(self, master, width: int = 120, height: int = 30, **kwargs):
        super().__init__(
            master, width=width, height=height,
            bg=T.BG_DARK, highlightthickness=0, bd=0,
            **kwargs,
        )
        self._phase = 0.0
        self._amplitude = 0.5
        self._running = False
        self._draw()

    def start(self) -> None:
        if not self._running:
            self._running = True
            self._animate()

    def stop(self) -> None:
        self._running = False
        self._amplitude = 0.0
        self._draw()

    def set_amplitude(self, amp: float) -> None:
        self._amplitude = max(0.0, min(1.0, amp))

    def _animate(self) -> None:
        if not self._running:
            return
        self._phase += 0.12
        self._draw()
        self.after(40, self._animate)

    def _draw(self) -> None:
        self.delete("all")
        w = self.winfo_width() or 120
        h = self.winfo_height() or 30
        mid_y = h / 2
        num_bars = 20
        bar_width = max(2, w // (num_bars * 2))

        for i in range(num_bars):
            x = int(w * i / num_bars) + bar_width
            # Each bar has a phase-shifted sine wave height
            wave_val = math.sin(self._phase + i * 0.4) * self._amplitude
            bar_h = max(2, int(abs(wave_val) * mid_y * 0.8))

            colour = T.ACCENT if abs(wave_val) < 0.5 else T.ACCENT_GLOW
            self.create_rectangle(
                x, mid_y - bar_h, x + bar_width, mid_y + bar_h,
                fill=colour, outline="",
            )
