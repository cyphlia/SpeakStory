"""Main application window — orchestrates sidebar, editor, and speech bar.

This is the controller that wires together data (NotesManager), AI (Pipeline),
and the three UI panels.  The speech pipeline is loaded lazily in a background
thread so the window appears instantly.
"""
from __future__ import annotations

import threading
import tkinter as tk
from typing import Optional

import customtkinter as ctk

from ..config import load_config
from ..notes_manager import Note, NotesManager
from ..pipeline import Pipeline
from . import theme as T
from .note_editor import NoteEditor
from .sidebar import Sidebar
from .speech_bar import SpeechBar


class MainWindow(ctk.CTk):
    """Top-level SYS - Speak Your Story application window."""

    def __init__(self):
        super().__init__()

        # ── Window chrome ──────────────────────────────────────────────
        self.title("SYS - Speak Your Story")
        self.geometry(f"{T.WINDOW_DEFAULT_W}x{T.WINDOW_DEFAULT_H}")
        self.minsize(T.WINDOW_MIN_WIDTH, T.WINDOW_MIN_HEIGHT)
        self.configure(fg_color=T.BG_DARKEST)

        # ── State ──────────────────────────────────────────────────────
        self.notes_mgr = NotesManager()
        self.pipeline: Optional[Pipeline] = None
        self._current_note_id: Optional[str] = None
        self._stop_event = threading.Event()
        self._recording_thread: Optional[threading.Thread] = None
        self._sort_criteria = "modified"
        self._sort_ascending = False
        self._search_query = ""

        # ── Grid layout: sidebar | right panel ─────────────────────────
        self.grid_columnconfigure(0, weight=0)   # sidebar
        self.grid_columnconfigure(1, weight=1)   # right
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar ───────────────────────────────────────────────────
        self.sidebar = Sidebar(
            self,
            on_note_select=self._select_note,
            on_new_note=self._new_note,
            on_delete_note=self._delete_note,
            on_pin_toggle=self._pin_toggle,
            on_search=self._on_search,
            on_sort_change=self._on_sort_change,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # ── Right container (editor + speech bar) ─────────────────────
        right = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(0, weight=1)
        right.grid_rowconfigure(1, weight=0)
        right.grid_columnconfigure(0, weight=1)

        self.editor = NoteEditor(right, on_save=self._save_current_note)
        self.editor.grid(row=0, column=0, sticky="nsew")

        self.speech_bar = SpeechBar(right, on_record_toggle=self._toggle_recording)
        self.speech_bar.grid(row=1, column=0, sticky="sew")

        # ── Keyboard shortcuts ─────────────────────────────────────────
        self.bind("<Control-n>", lambda e: self._new_note())
        self.bind("<Control-f>", lambda e: self.sidebar.search_entry.focus())

        # ── Initial data load ──────────────────────────────────────────
        self._refresh_sidebar()

        # ── Lazy-load speech pipeline in the background ────────────────
        threading.Thread(target=self._load_pipeline, daemon=True).start()

        # ── Periodically check Ollama status ───────────────────────────
        self._check_ai_status()

    # ═══════════════════════════════════════════════════════════════════
    #  Note operations
    # ═══════════════════════════════════════════════════════════════════

    def _new_note(self) -> None:
        note = self.notes_mgr.create_note()
        self._current_note_id = note.id
        self._refresh_sidebar()
        self.editor.load_note(note)
        self.editor.title_entry.focus()

    def _select_note(self, note_id: str) -> None:
        # Save current note first
        self._save_current_note_quietly()

        self._current_note_id = note_id
        note = self.notes_mgr.get_note(note_id)
        if note:
            self.editor.load_note(note)
        self._refresh_sidebar()

    def _delete_note(self, note_id: str) -> None:
        self.notes_mgr.delete_note(note_id)
        if self._current_note_id == note_id:
            self._current_note_id = None
            self.editor.clear()
        self._refresh_sidebar()

    def _pin_toggle(self, note_id: str) -> None:
        note = self.notes_mgr.get_note(note_id)
        if note:
            note.is_pinned = not note.is_pinned
            self.notes_mgr.save_note(note)
            self._refresh_sidebar()

    def _save_current_note(self) -> None:
        """Save the note currently in the editor (called by auto-save)."""
        if not self._current_note_id:
            return
        note = self.notes_mgr.get_note(self._current_note_id)
        if not note:
            return

        note.title = self.editor.get_title() or "Untitled Note"
        note.content = self.editor.get_content()
        note.tags = self.editor.get_tags()
        self.notes_mgr.save_note(note)
        self.editor.show_save_status()
        self._refresh_sidebar()

    def _save_current_note_quietly(self) -> None:
        """Save without visual feedback (used when switching notes)."""
        if not self._current_note_id:
            return
        note = self.notes_mgr.get_note(self._current_note_id)
        if not note:
            return
        note.title = self.editor.get_title() or "Untitled Note"
        note.content = self.editor.get_content()
        note.tags = self.editor.get_tags()
        self.notes_mgr.save_note(note)

    # ═══════════════════════════════════════════════════════════════════
    #  Search & sort
    # ═══════════════════════════════════════════════════════════════════

    def _on_search(self, query: str) -> None:
        self._search_query = query
        self._refresh_sidebar()

    def _on_sort_change(self, value: str) -> None:
        sort_map = {
            "Recently Modified": ("modified", False),
            "Recently Created":  ("created",  False),
            "Title (A → Z)":     ("title",    True),
            "Title (Z → A)":     ("title",    False),
            "Oldest First":      ("created",  True),
        }
        self._sort_criteria, self._sort_ascending = sort_map.get(
            value, ("modified", False)
        )
        self._refresh_sidebar()

    def _refresh_sidebar(self) -> None:
        if self._search_query.strip():
            notes = self.notes_mgr.search_notes(self._search_query)
        else:
            notes = self.notes_mgr.get_all_notes()

        notes = NotesManager.sort_notes(
            notes, self._sort_criteria, self._sort_ascending
        )
        self.sidebar.refresh(notes, self._current_note_id)

    # ═══════════════════════════════════════════════════════════════════
    #  Speech-to-text
    # ═══════════════════════════════════════════════════════════════════

    def _load_pipeline(self) -> None:
        """Background thread: load Whisper model + pipeline."""
        try:
            config = load_config()
            self.pipeline = Pipeline(config)
            self.after(0, self.speech_bar.set_ready)
        except Exception as exc:
            self.after(0, lambda: self.speech_bar.set_status("error"))
            print(f"[main_window] Pipeline load error: {exc}")

    def _toggle_recording(self) -> None:
        if self._recording_thread and self._recording_thread.is_alive():
            # Stop current recording
            self._stop_event.set()
            return

        if not self.pipeline:
            return

        # Auto-create a note if none is selected
        if not self._current_note_id:
            self._new_note()

        self._stop_event.clear()
        self._recording_thread = threading.Thread(
            target=self._run_recording, daemon=True
        )
        self._recording_thread.start()

    def _run_recording(self) -> None:
        """Runs on a background thread — processes one utterance."""
        def ui_status(s: str):
            self.after(0, lambda: self.speech_bar.set_status(s))

        def ui_level(lv: float):
            self.after(0, lambda: self.speech_bar.set_audio_level(lv))

        def ui_result(r: dict):
            self.after(0, lambda: self._on_speech_result(r))

        def ui_error(e: str):
            self.after(0, lambda: self._on_speech_error(e))

        self.pipeline.process_utterance_threaded(
            on_status=ui_status,
            on_level=ui_level,
            on_result=ui_result,
            on_error=ui_error,
            stop_event=self._stop_event,
        )

    def _on_speech_result(self, result: dict) -> None:
        """Called on the main thread when speech is successfully processed."""
        refined = result.get("refined", result.get("raw", ""))
        if refined:
            self.editor.insert_text(refined)

    def _on_speech_error(self, error: str) -> None:
        print(f"[speech] Error: {error}")
        self.speech_bar.set_status("error")
        # Auto-recover to idle after 3 seconds
        self.after(3000, lambda: self.speech_bar.set_status("idle"))

    def _check_ai_status(self) -> None:
        """Periodically check Ollama connectivity (every 15 s)."""
        def check():
            if self.pipeline:
                connected = self.pipeline.check_ollama_status()
                self.after(0, lambda: self.speech_bar.set_ai_status(connected))

        threading.Thread(target=check, daemon=True).start()
        self.after(15_000, self._check_ai_status)
