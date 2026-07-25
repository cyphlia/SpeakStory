"""Centre-panel note editor — toolbar, title, tags bar, content text area, footer.

Includes an empty-state overlay, markdown preview toggle, undo/redo,
Summarize/Improve AI buttons, and improved statistics footer.
"""
from __future__ import annotations

from pathlib import Path
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
        on_delete: Optional[Callable[[str], None]] = None,
        on_pin_toggle: Optional[Callable[[str], None]] = None,
        on_summarize: Optional[Callable[[], None]] = None,
        on_improve: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=T.BG_DARKEST, corner_radius=0, **kwargs)
        self._on_save = on_save
        self._on_delete = on_delete
        self._on_pin_toggle = on_pin_toggle
        self._on_summarize = on_summarize
        self._on_improve = on_improve
        self._current_note: Optional[Note] = None
        self._save_timer = None
        self._ignore_changes = False   # suppress saves while loading a note
        self._markdown_visible = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)  # content area expands

        # ── Row 0 — Top Action Toolbar ───────────────────────────────
        self.toolbar = ctk.CTkFrame(self, fg_color=T.SURFACE_ELEVATED, height=40, corner_radius=0)
        self.toolbar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.toolbar.grid_columnconfigure(1, weight=1)

        # Left tools (Mode pill)
        self.mode_pill = ctk.CTkLabel(
            self.toolbar,
            text="⚡ Built-in Engine (0MB RAM)",
            font=T.FONT_TINY,
            fg_color=T.BG_MEDIUM,
            text_color=T.ACCENT,
            corner_radius=10,
            padx=10, pady=3,
        )
        self.mode_pill.grid(row=0, column=0, sticky="w", padx=T.PAD_LG, pady=6)

        # Right tools row
        tools_right = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        tools_right.grid(row=0, column=2, sticky="e", padx=T.PAD_LG, pady=4)

        # Summarize button
        self.summarize_btn = ctk.CTkButton(
            tools_right, text="✨ Summarize", width=80, height=28,
            font=T.FONT_TINY, fg_color=T.ACCENT_SUBTLE, hover_color=T.BG_LIGHT,
            text_color=T.ACCENT, corner_radius=T.CORNER_RADIUS_SM,
            border_width=1, border_color=T.ACCENT_DARK,
            command=self._do_summarize,
        )
        self.summarize_btn.pack(side="left", padx=(0, 4))

        # Improve Writing button
        self.improve_btn = ctk.CTkButton(
            tools_right, text="📝 Improve", width=72, height=28,
            font=T.FONT_TINY, fg_color=T.ACCENT_SUBTLE, hover_color=T.BG_LIGHT,
            text_color=T.ACCENT, corner_radius=T.CORNER_RADIUS_SM,
            border_width=1, border_color=T.ACCENT_DARK,
            command=self._do_improve,
        )
        self.improve_btn.pack(side="left", padx=(0, 8))

        # Divider
        ctk.CTkFrame(tools_right, width=1, height=20, fg_color=T.BORDER).pack(
            side="left", padx=(0, 8))

        # Copy
        self.copy_btn = ctk.CTkButton(
            tools_right, text="📋 Copy", width=64, height=28,
            **T.BTN_TOOLBAR, command=self.copy_to_clipboard,
        )
        self.copy_btn.pack(side="left", padx=(0, 4))

        # Export
        self.export_btn = ctk.CTkButton(
            tools_right, text="📥 Export", width=68, height=28,
            **T.BTN_TOOLBAR, command=self.export_note,
        )
        self.export_btn.pack(side="left", padx=(0, 4))

        # Pin
        self.pin_btn = ctk.CTkButton(
            tools_right, text="📌 Pin", width=58, height=28,
            **T.BTN_TOOLBAR, command=self._toggle_pin,
        )
        self.pin_btn.pack(side="left", padx=(0, 4))

        # Delete
        self.delete_btn = ctk.CTkButton(
            tools_right, text="🗑️", width=32, height=28,
            font=T.FONT_TINY, fg_color=T.BG_MEDIUM, hover_color=T.DANGER,
            text_color=T.DANGER, corner_radius=T.CORNER_RADIUS_SM,
            command=self._delete_current,
        )
        self.delete_btn.pack(side="left")

        # ── Row 1 — Title entry ─────────────────────────────────────────
        self.title_var = ctk.StringVar()
        self.title_entry = ctk.CTkEntry(
            self,
            textvariable=self.title_var,
            placeholder_text="Note title…",
            font=T.FONT_TITLE,
            fg_color="transparent",
            border_width=0,
            text_color=T.TEXT_BRIGHT,
            placeholder_text_color=T.TEXT_MUTED,
            height=50,
        )
        self.title_entry.grid(row=1, column=0, sticky="ew",
                              padx=T.PAD_XL, pady=(T.PAD_LG, 0))
        self.title_var.trace_add("write", self._on_content_changed)

        # ── Row 2 — Tags bar ──────────────────────────────────────────
        self.tags_frame = ctk.CTkFrame(self, fg_color="transparent", height=32)
        self.tags_frame.grid(row=2, column=0, sticky="ew",
                             padx=T.PAD_XL, pady=(T.PAD_XS, T.PAD_SM))

        self.tag_entry_var = ctk.StringVar()
        self.tag_entry = ctk.CTkEntry(
            self.tags_frame,
            textvariable=self.tag_entry_var,
            placeholder_text="+ add tag…",
            font=(T.FONT_FAMILY, 11),
            width=100, height=26,
            fg_color=T.SURFACE_ELEVATED,
            border_color=T.BORDER,
            text_color=T.TEXT_PRIMARY,
            placeholder_text_color=T.TEXT_MUTED,
            corner_radius=12,
        )
        self.tag_entry.bind("<Return>", self._add_tag)

        # ── Row 3 — Content textbox ───────────────────────────────────
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
        self.content_box.grid(row=3, column=0, sticky="nsew",
                              padx=T.PAD_XL, pady=0)
        self.content_box.bind("<<Modified>>", self._on_text_modified)

        # ── Row 4 — Enhanced Footer ──────────────────────────────────
        self.footer = ctk.CTkFrame(self, fg_color=T.SURFACE_ELEVATED, height=30,
                                   corner_radius=0)
        self.footer.grid(row=4, column=0, sticky="ew")
        self.footer.grid_columnconfigure(1, weight=1)

        self.word_count_label = ctk.CTkLabel(
            self.footer, text="",
            font=T.FONT_MICRO, text_color=T.TEXT_MUTED,
            anchor="w",
        )
        self.word_count_label.grid(row=0, column=0, sticky="w",
                                   padx=T.PAD_LG, pady=T.PAD_XS)

        self.line_count_label = ctk.CTkLabel(
            self.footer, text="",
            font=T.FONT_MICRO, text_color=T.TEXT_MUTED,
            anchor="center",
        )
        self.line_count_label.grid(row=0, column=1, sticky="ew",
                                   padx=T.PAD_SM, pady=T.PAD_XS)

        self.save_status_label = ctk.CTkLabel(
            self.footer, text="",
            font=T.FONT_MICRO, text_color=T.TEXT_MUTED,
            anchor="e",
        )
        self.save_status_label.grid(row=0, column=2, sticky="e",
                                    padx=T.PAD_LG, pady=T.PAD_XS)

        # ── Empty state overlay ────────────────────────────────────────
        self.empty_overlay = ctk.CTkFrame(self, fg_color=T.BG_DARKEST,
                                          corner_radius=0)
        self.empty_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        inner = ctk.CTkFrame(self.empty_overlay, fg_color="transparent")
        inner.place(relx=0.5, rely=0.42, anchor="center")

        ctk.CTkLabel(inner, text="📖", font=(T.FONT_FAMILY, 60)).pack()
        ctk.CTkLabel(
            inner, text="SYS - Speak Your Story",
            font=T.FONT_HERO, text_color=T.ACCENT,
        ).pack(pady=(T.PAD_SM, T.PAD_XS))
        ctk.CTkLabel(
            inner, text="Your AI-powered voice notes platform",
            font=T.FONT_BODY, text_color=T.TEXT_SECONDARY,
        ).pack()

        # Keyboard shortcuts hint
        shortcuts_frame = ctk.CTkFrame(inner, fg_color=T.SURFACE_ELEVATED,
                                       corner_radius=T.CORNER_RADIUS)
        shortcuts_frame.pack(pady=(T.PAD_XL, 0))

        for shortcut, action in [("Ctrl+N", "New Note"), ("Ctrl+F", "Search"),
                                 ("🎤 Click", "Voice Input")]:
            row_f = ctk.CTkFrame(shortcuts_frame, fg_color="transparent")
            row_f.pack(fill="x", padx=T.PAD_LG, pady=T.PAD_XS)
            ctk.CTkLabel(
                row_f, text=shortcut,
                font=T.FONT_MONO, text_color=T.ACCENT,
                fg_color=T.BG_MEDIUM, corner_radius=4,
                padx=6, pady=2,
            ).pack(side="left")
            ctk.CTkLabel(
                row_f, text=action,
                font=T.FONT_SMALL, text_color=T.TEXT_MUTED,
            ).pack(side="left", padx=(T.PAD_SM, 0))

    # ── Public API ─────────────────────────────────────────────────────

    def set_engine_mode_label(self, label: str) -> None:
        self.mode_pill.configure(text=label)

    def set_ai_callbacks(self, on_summarize=None, on_improve=None) -> None:
        """Set AI action callbacks after construction."""
        self._on_summarize = on_summarize
        self._on_improve = on_improve

    def load_note(self, note: Note) -> None:
        """Populate the editor with a note's data."""
        self._ignore_changes = True
        self._current_note = note

        self.title_var.set(note.title)

        self.content_box.delete("1.0", "end")
        self.content_box.insert("1.0", note.content)
        self.content_box.edit_modified(False)

        self.pin_btn.configure(
            text="📌 Pinned" if note.is_pinned else "📌 Pin",
            fg_color=T.ACCENT_SUBTLE if note.is_pinned else T.BG_MEDIUM,
        )

        self._rebuild_tags()
        self._update_stats()
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
        self.line_count_label.configure(text="")
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
        """Insert text at current cursor position (or end of text)."""
        if not self._current_note:
            return

        cursor_pos = self.content_box.index("insert")
        current_line = self.content_box.get(f"{cursor_pos} linestart", cursor_pos)
        if current_line.strip():
            text = " " + text

        self.content_box.insert("insert", text)
        self.content_box.see("insert")
        self._schedule_save()

    def copy_to_clipboard(self) -> None:
        content = self.get_content()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            self.show_save_status("Copied to clipboard ✓")

    def export_note(self) -> None:
        if not self._current_note:
            return
        try:
            title = self.get_title() or "Untitled Note"
            safe_title = "".join(c for c in title if c.isalnum() or c in " -_").strip()
            export_path = Path.home() / "Desktop" / f"{safe_title}.md"
            with open(export_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n")
                if self._current_note.tags:
                    f.write(f"Tags: {', '.join(self._current_note.tags)}\n\n")
                f.write(self.get_content())
            self.show_save_status(f"Exported to Desktop! ✓")
        except Exception as exc:
            self.show_save_status("Export failed")

    def show_save_status(self, text: str = "Saved ✓") -> None:
        self.save_status_label.configure(text=text, text_color=T.SUCCESS)
        self.after(2500, lambda: self.save_status_label.configure(
            text="", text_color=T.TEXT_MUTED
        ))

    # ── AI Actions ─────────────────────────────────────────────────────

    def _do_summarize(self) -> None:
        if self._on_summarize:
            self._on_summarize()

    def _do_improve(self) -> None:
        if self._on_improve:
            self._on_improve()

    # ── Internal ───────────────────────────────────────────────────────

    def _toggle_pin(self) -> None:
        if self._current_note and self._on_pin_toggle:
            self._on_pin_toggle(self._current_note.id)

    def _delete_current(self) -> None:
        if self._current_note and self._on_delete:
            self._on_delete(self._current_note.id)

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
                self._update_stats()

    def _schedule_save(self) -> None:
        """Debounced auto-save — fires 1 s after the last change."""
        if self._save_timer is not None:
            self.after_cancel(self._save_timer)
        self._save_timer = self.after(1000, self._do_save)

    def _do_save(self) -> None:
        self._save_timer = None
        if self._current_note and self._on_save:
            self._on_save()

    def _update_stats(self) -> None:
        text = self.get_content()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        lines = text.count("\n") + 1 if text.strip() else 0
        self.word_count_label.configure(
            text=f"{words:,} words  ·  {chars:,} chars"
        )
        self.line_count_label.configure(
            text=f"{lines:,} lines" if lines > 0 else ""
        )
