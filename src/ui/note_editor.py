"""Centre-panel note editor — title, tags bar, content text area, footer.

Includes an empty-state overlay when no note is loaded.
"""
from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from ..notes_manager import Note
from . import theme as T
from .components import TagChip


class NoteEditor(ctk.CTkFrame):
    """Editable view for the currently selected note."""

    def __init__(
        self,
        master,
        on_save: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, fg_color=T.BG_DARKEST, corner_radius=0, **kwargs)
        self._on_save = on_save
        self._current_note: Optional[Note] = None
        self._save_timer = None
        self._ignore_changes = False   # suppress saves while loading a note

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)  # content area expands

        # ── Row 0 — Title entry ─────────────────────────────────────────
        self.title_var = ctk.StringVar()
        self.title_entry = ctk.CTkEntry(
            self,
            textvariable=self.title_var,
            placeholder_text="Note title…",
            font=T.FONT_TITLE,
            fg_color="transparent",
            border_width=0,
            text_color=T.TEXT_PRIMARY,
            placeholder_text_color=T.TEXT_MUTED,
            height=52,
        )
        self.title_entry.grid(row=0, column=0, sticky="ew",
                              padx=T.PAD_XL, pady=(T.PAD_XL, 0))
        self.title_var.trace_add("write", self._on_content_changed)

        # ── Row 1 — Tags bar ──────────────────────────────────────────
        self.tags_frame = ctk.CTkFrame(self, fg_color="transparent", height=36)
        self.tags_frame.grid(row=1, column=0, sticky="ew",
                             padx=T.PAD_XL, pady=(T.PAD_SM, T.PAD_SM))

        self.tag_entry_var = ctk.StringVar()
        self.tag_entry = ctk.CTkEntry(
            self.tags_frame,
            textvariable=self.tag_entry_var,
            placeholder_text="+ add tag…",
            font=(T.FONT_FAMILY, 11),
            width=100, height=26,
            fg_color=T.BG_MEDIUM,
            border_color=T.BORDER,
            text_color=T.TEXT_PRIMARY,
            placeholder_text_color=T.TEXT_MUTED,
            corner_radius=12,
        )
        self.tag_entry.bind("<Return>", self._add_tag)

        # ── Row 2 — Content textbox ───────────────────────────────────
        self.content_box = ctk.CTkTextbox(
            self,
            font=T.FONT_BODY,
            fg_color=T.BG_DARKEST,
            text_color=T.TEXT_PRIMARY,
            scrollbar_button_color=T.BG_LIGHT,
            scrollbar_button_hover_color=T.BG_LIGHTER,
            border_width=0,
            corner_radius=0,
            wrap="word",
        )
        self.content_box.grid(row=2, column=0, sticky="nsew",
                              padx=T.PAD_XL, pady=0)
        self.content_box.bind("<<Modified>>", self._on_text_modified)

        # ── Row 3 — Footer ────────────────────────────────────────────
        self.footer = ctk.CTkFrame(self, fg_color=T.BG_DARK, height=30,
                                   corner_radius=0)
        self.footer.grid(row=3, column=0, sticky="ew")
        self.footer.grid_columnconfigure(0, weight=1)

        self.word_count_label = ctk.CTkLabel(
            self.footer, text="",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED,
            anchor="w",
        )
        self.word_count_label.grid(row=0, column=0, sticky="w",
                                   padx=T.PAD_LG, pady=T.PAD_XS)

        self.save_status_label = ctk.CTkLabel(
            self.footer, text="",
            font=T.FONT_TINY, text_color=T.TEXT_MUTED,
            anchor="e",
        )
        self.save_status_label.grid(row=0, column=1, sticky="e",
                                    padx=T.PAD_LG, pady=T.PAD_XS)

        # ── Empty state overlay ────────────────────────────────────────
        self.empty_overlay = ctk.CTkFrame(self, fg_color=T.BG_DARKEST,
                                          corner_radius=0)
        self.empty_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        inner = ctk.CTkFrame(self.empty_overlay, fg_color="transparent")
        inner.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(inner, text="📖", font=(T.FONT_FAMILY, 52)).pack()
        ctk.CTkLabel(
            inner, text="SpeakStory",
            font=(T.FONT_FAMILY, 28, "bold"), text_color=T.ACCENT,
        ).pack(pady=(T.PAD_SM, T.PAD_XS))
        ctk.CTkLabel(
            inner, text="Your AI-powered voice notes",
            font=T.FONT_BODY, text_color=T.TEXT_SECONDARY,
        ).pack()
        ctk.CTkLabel(
            inner,
            text="Select a note from the sidebar\nor create a new one to get started.",
            font=T.FONT_SMALL, text_color=T.TEXT_MUTED,
            justify="center",
        ).pack(pady=(T.PAD_LG, 0))

    # ── Public API ─────────────────────────────────────────────────────

    def load_note(self, note: Note) -> None:
        """Populate the editor with a note's data."""
        self._ignore_changes = True
        self._current_note = note

        self.title_var.set(note.title)

        self.content_box.delete("1.0", "end")
        self.content_box.insert("1.0", note.content)
        self.content_box.edit_modified(False)

        self._rebuild_tags()
        self._update_word_count()
        self.save_status_label.configure(text="")
        self.empty_overlay.place_forget()
        self._ignore_changes = False

    def clear(self) -> None:
        """Reset to empty state."""
        self._ignore_changes = True
        self._current_note = None
        self.title_var.set("")
        self.content_box.delete("1.0", "end")
        self._rebuild_tags()
        self.word_count_label.configure(text="")
        self.save_status_label.configure(text="")
        self.empty_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._ignore_changes = False

    def get_title(self) -> str:
        return self.title_var.get().strip()

    def get_content(self) -> str:
        return self.content_box.get("1.0", "end-1c")

    def get_tags(self) -> list[str]:
        if self._current_note:
            return list(self._current_note.tags)
        return []

    def insert_text(self, text: str) -> None:
        """Insert text at the current cursor position (for speech-to-text).
        Adds a space before the text if the cursor isn't at the beginning
        of a line."""
        if not self._current_note:
            return

        cursor_pos = self.content_box.index("insert")
        # Add leading space if not at start of line and content exists
        current_line = self.content_box.get(
            f"{cursor_pos} linestart", cursor_pos
        )
        if current_line.strip():
            text = " " + text

        self.content_box.insert("insert", text)
        self.content_box.see("insert")
        self._schedule_save()

    def show_save_status(self, text: str = "Saved ✓") -> None:
        self.save_status_label.configure(text=text, text_color=T.SUCCESS)
        self.after(2000, lambda: self.save_status_label.configure(
            text="", text_color=T.TEXT_MUTED
        ))

    # ── Internal ───────────────────────────────────────────────────────

    def _rebuild_tags(self) -> None:
        """Recreate tag chips from the current note's tags list."""
        for child in self.tags_frame.winfo_children():
            if child is not self.tag_entry:
                child.destroy()

        if self._current_note:
            for tag in self._current_note.tags:
                chip = TagChip(self.tags_frame, text=tag,
                               on_remove=self._remove_tag)
                chip.pack(side="left", padx=(0, T.PAD_XS))

        self.tag_entry.pack(side="left", padx=(T.PAD_XS, 0))

    def _add_tag(self, event=None) -> None:
        tag = self.tag_entry_var.get().strip()
        if not tag or not self._current_note:
            return
        if tag not in self._current_note.tags:
            self._current_note.tags.append(tag)
            self._rebuild_tags()
            self._schedule_save()
        self.tag_entry_var.set("")

    def _remove_tag(self, tag: str) -> None:
        if not self._current_note:
            return
        if tag in self._current_note.tags:
            self._current_note.tags.remove(tag)
            self._rebuild_tags()
            self._schedule_save()

    def _on_content_changed(self, *_args) -> None:
        if self._ignore_changes:
            return
        self._schedule_save()

    def _on_text_modified(self, event=None) -> None:
        if self.content_box.edit_modified():
            self.content_box.edit_modified(False)
            if not self._ignore_changes:
                self._schedule_save()
                self._update_word_count()

    def _schedule_save(self) -> None:
        """Debounced auto-save — fires 1 s after the last change."""
        if self._save_timer is not None:
            self.after_cancel(self._save_timer)
        self._save_timer = self.after(1000, self._do_save)

    def _do_save(self) -> None:
        self._save_timer = None
        if self._current_note and self._on_save:
            self._on_save()

    def _update_word_count(self) -> None:
        text = self.get_content()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_label.configure(
            text=f"{words:,} words  ·  {chars:,} characters"
        )
