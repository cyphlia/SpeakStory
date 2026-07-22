"""Reusable styled widgets for the SpeakStory UI.

NoteCard   — sidebar preview card for a single note
TagChip    — removable tag pill
AudioLevel — canvas-based real-time audio-level bar
StatusDot  — tiny circle indicating connection health
"""
from __future__ import annotations

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
        on_click: Optional[Callable[[str], None]] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        on_pin_toggle: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        bg = T.ACCENT_SUBTLE if is_selected else T.BG_MEDIUM
        super().__init__(
            master,
            fg_color=bg,
            corner_radius=T.CORNER_RADIUS_SM,
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

        # Row 0 — title + pin
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=0, column=0, sticky="ew", padx=T.PAD_SM, pady=(T.PAD_SM, 0))
        top_row.grid_columnconfigure(0, weight=1)

        title_text = title if len(title) <= 28 else title[:26] + "…"
        self.title_label = ctk.CTkLabel(
            top_row, text=title_text,
            font=T.FONT_BODY_BOLD, text_color=T.TEXT_PRIMARY,
            anchor="w",
        )
        self.title_label.grid(row=0, column=0, sticky="w")

        if is_pinned:
            pin_lbl = ctk.CTkLabel(top_row, text="📌", font=T.FONT_TINY)
            pin_lbl.grid(row=0, column=1, sticky="e", padx=(4, 0))

        # Row 1 — preview
        preview_text = preview if len(preview) <= 42 else preview[:40] + "…"
        self.preview_label = ctk.CTkLabel(
            self, text=preview_text or " ",
            font=T.FONT_SMALL, text_color=T.TEXT_MUTED,
            anchor="w",
        )
        self.preview_label.grid(row=1, column=0, sticky="ew",
                                padx=T.PAD_SM, pady=(2, 0))

        # Row 2 — time
        self.time_label = ctk.CTkLabel(
            self, text=time_label,
            font=T.FONT_TINY, text_color=T.TEXT_MUTED,
            anchor="w",
        )
        self.time_label.grid(row=2, column=0, sticky="ew",
                             padx=T.PAD_SM, pady=(2, T.PAD_SM))

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
            self.configure(fg_color=T.BG_LIGHT)

    def _on_leave(self, event=None):
        if not self._is_selected:
            self.configure(fg_color=T.BG_MEDIUM)

    def _show_menu(self, event):
        self._menu.tk_popup(event.x_root, event.y_root)

    def _toggle_pin(self):
        if self._on_pin_toggle:
            self._on_pin_toggle(self.note_id)

    def _delete(self):
        if self._on_delete:
            self._on_delete(self.note_id)


# ═══════════════════════════════════════════════════════════════════════════
#  TagChip — removable tag pill
# ═══════════════════════════════════════════════════════════════════════════

class TagChip(ctk.CTkFrame):
    """Small rounded pill showing a tag name with optional ✕ button."""

    def __init__(
        self,
        master,
        text: str,
        on_remove: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(
            master, fg_color=T.ACCENT_DARK, corner_radius=12, height=26,
            **kwargs,
        )
        self.tag_text = text
        self.pack_propagate(False)

        lbl = ctk.CTkLabel(
            self, text=text, font=(T.FONT_FAMILY, 11),
            text_color=T.TEXT_PRIMARY,
        )
        lbl.pack(side="left", padx=(10, 2 if on_remove else 10), pady=2)

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
#  AudioLevelBar — canvas-based VU meter
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

        # Background track
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

    def reset(self) -> None:
        self._level = 0.0
        self._target_level = 0.0
        self._draw()


# ═══════════════════════════════════════════════════════════════════════════
#  StatusDot — tiny connection-health circle
# ═══════════════════════════════════════════════════════════════════════════

class StatusDot(tk.Canvas):
    """Tiny coloured dot — green = connected, red = offline, grey = unknown."""

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
        self._draw()

    def set_status(self, status: str) -> None:
        self._status = status
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        colour = self.COLOURS.get(self._status, T.TEXT_MUTED)
        pad = 1
        self.create_oval(pad, pad, self._size - pad, self._size - pad,
                         fill=colour, outline="")
