"""Left sidebar — app title, search, sort, quick-filter tabs, scrollable note list, + new note.

Communicates with the MainWindow through callbacks passed at init time.
"""
from __future__ import annotations

from typing import Callable, List, Optional

import customtkinter as ctk

from ..notes_manager import Note, relative_time
from . import theme as T
from .components import NoteCard


class Sidebar(ctk.CTkFrame):
    """Fixed-width left panel listing all notes with search, sort & quick-filter."""

    def __init__(
        self,
        master,
        on_note_select: Callable[[str], None],
        on_new_note: Callable[[], None],
        on_delete_note: Callable[[str], None],
        on_pin_toggle: Callable[[str], None],
        on_search: Callable[[str], None],
        on_sort_change: Callable[[str], None],
        on_filter_change: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(
            master,
            width=T.SIDEBAR_WIDTH,
            fg_color=T.BG_DARK,
            corner_radius=0,
            **kwargs,
        )
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)

        self._on_note_select = on_note_select
        self._on_new_note = on_new_note
        self._on_delete_note = on_delete_note
        self._on_pin_toggle = on_pin_toggle
        self._on_search = on_search
        self._on_sort_change = on_sort_change
        self._on_filter_change = on_filter_change
        self._selected_id: Optional[str] = None
        self._active_filter = "all"
        self._total_count = 0
        self._pinned_count = 0

        self._search_timer = None

        row = 0

        # ── App title ──────────────────────────────────────────────────
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=row, column=0, sticky="ew",
                         padx=T.PAD_LG, pady=(T.PAD_XL, T.PAD_SM))
        title_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_frame, text="📖  SYS",
            font=T.FONT_SUBTITLE,
            text_color=T.ACCENT,
            anchor="w",
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            title_frame, text="Speak Your Story",
            font=T.FONT_SMALL,
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", pady=(0, 0))

        row += 1

        # ── Search ─────────────────────────────────────────────────────
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self,
            placeholder_text="🔍  Search notes…",
            textvariable=self.search_var,
            fg_color=T.SURFACE_ELEVATED,
            border_color=T.BORDER,
            text_color=T.TEXT_PRIMARY,
            placeholder_text_color=T.TEXT_MUTED,
            font=T.FONT_SMALL,
            height=36,
            corner_radius=T.CORNER_RADIUS,
        )
        self.search_entry.grid(row=row, column=0, sticky="ew",
                               padx=T.PAD_LG, pady=(0, T.PAD_SM))
        self.search_var.trace_add("write", self._on_search_typed)
        row += 1

        # ── Quick-filter tabs ──────────────────────────────────────────
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.grid(row=row, column=0, sticky="ew",
                          padx=T.PAD_LG, pady=(0, T.PAD_SM))

        self._filter_buttons: dict[str, ctk.CTkButton] = {}
        for filter_key, label in [("all", "All"), ("pinned", "📌 Pinned"), ("recent", "🕐 Recent")]:
            btn = ctk.CTkButton(
                filter_frame,
                text=label,
                width=0,
                height=28,
                font=T.FONT_TINY,
                fg_color=T.ACCENT_SUBTLE if filter_key == "all" else "transparent",
                hover_color=T.BG_LIGHT,
                text_color=T.ACCENT if filter_key == "all" else T.TEXT_SECONDARY,
                corner_radius=T.CORNER_RADIUS_SM,
                command=lambda k=filter_key: self._set_filter(k),
            )
            btn.pack(side="left", padx=(0, T.PAD_XS), expand=True, fill="x")
            self._filter_buttons[filter_key] = btn

        row += 1

        # ── Sort dropdown + note count ─────────────────────────────────
        sort_row = ctk.CTkFrame(self, fg_color="transparent")
        sort_row.grid(row=row, column=0, sticky="ew",
                      padx=T.PAD_LG, pady=(0, T.PAD_SM))
        sort_row.grid_columnconfigure(0, weight=1)

        self.sort_var = ctk.StringVar(value="Recently Modified")
        sort_menu = ctk.CTkOptionMenu(
            sort_row,
            variable=self.sort_var,
            values=[
                "Recently Modified",
                "Recently Created",
                "Title (A → Z)",
                "Title (Z → A)",
                "Oldest First",
            ],
            fg_color=T.SURFACE_ELEVATED,
            button_color=T.BG_LIGHT,
            button_hover_color=T.BG_LIGHTER,
            dropdown_fg_color=T.BG_MEDIUM,
            dropdown_hover_color=T.BG_LIGHT,
            dropdown_text_color=T.TEXT_PRIMARY,
            text_color=T.TEXT_SECONDARY,
            font=T.FONT_TINY,
            dropdown_font=T.FONT_SMALL,
            height=28,
            corner_radius=T.CORNER_RADIUS_SM,
            command=self._sort_changed,
        )
        sort_menu.grid(row=0, column=0, sticky="ew")

        self.count_badge = ctk.CTkLabel(
            sort_row, text="0",
            font=T.FONT_MICRO,
            fg_color=T.ACCENT_SUBTLE,
            text_color=T.ACCENT,
            corner_radius=8,
            width=28, height=18,
        )
        self.count_badge.grid(row=0, column=1, sticky="e", padx=(T.PAD_SM, 0))

        row += 1

        # ── Separator ─────────────────────────────────────────────────
        sep = ctk.CTkFrame(self, height=1, fg_color=T.BORDER)
        sep.grid(row=row, column=0, sticky="ew", padx=T.PAD_MD)
        row += 1

        # ── Scrollable note list ───────────────────────────────────────
        self.grid_rowconfigure(row, weight=1)
        self.note_list = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=T.BG_LIGHT,
            scrollbar_button_hover_color=T.BG_LIGHTER,
        )
        self.note_list.grid(row=row, column=0, sticky="nsew",
                            padx=T.PAD_SM, pady=T.PAD_SM)
        self.note_list.grid_columnconfigure(0, weight=1)
        row += 1

        # ── "New note" button ──────────────────────────────────────────
        new_btn = ctk.CTkButton(
            self,
            text="＋  New Note",
            command=self._on_new_note,
            height=42,
            **T.BTN_PRIMARY,
        )
        new_btn.grid(row=row, column=0, sticky="ew",
                     padx=T.PAD_LG, pady=(T.PAD_SM, T.PAD_LG))

    # ── Public API ─────────────────────────────────────────────────────

    def refresh(self, notes: List[Note], selected_id: Optional[str] = None):
        """Rebuild the note card list."""
        self._selected_id = selected_id
        self._total_count = len(notes)
        self._pinned_count = sum(1 for n in notes if n.is_pinned)

        # Apply quick-filter
        if self._active_filter == "pinned":
            display_notes = [n for n in notes if n.is_pinned]
        elif self._active_filter == "recent":
            display_notes = notes[:10]  # top 10 most recent
        else:
            display_notes = notes

        # Update count badge
        self.count_badge.configure(text=str(len(display_notes)))

        # Clear existing cards
        for child in self.note_list.winfo_children():
            child.destroy()

        if not display_notes:
            empty_msg = "No pinned notes." if self._active_filter == "pinned" else (
                "No notes yet.\nClick '＋ New Note' to begin."
            )
            ctk.CTkLabel(
                self.note_list,
                text=empty_msg,
                font=T.FONT_SMALL,
                text_color=T.TEXT_MUTED,
                justify="center",
            ).grid(row=0, column=0, pady=T.PAD_XL)
            return

        for idx, note in enumerate(display_notes):
            first_line = (note.content.split("\n")[0].strip()
                          if note.content.strip() else "")
            card = NoteCard(
                self.note_list,
                note_id=note.id,
                title=note.title,
                preview=first_line,
                time_label=relative_time(note.modified_at),
                is_pinned=note.is_pinned,
                is_selected=(note.id == selected_id),
                tags=note.tags,
                char_count=len(note.content),
                on_click=self._on_note_select,
                on_delete=self._on_delete_note,
                on_pin_toggle=self._on_pin_toggle,
            )
            card.grid(row=idx, column=0, sticky="ew", pady=(0, T.PAD_XS))

    def set_selected(self, note_id: Optional[str]):
        self._selected_id = note_id

    # ── Internal ───────────────────────────────────────────────────────

    def _set_filter(self, filter_key: str) -> None:
        self._active_filter = filter_key
        # Update button styles
        for key, btn in self._filter_buttons.items():
            if key == filter_key:
                btn.configure(fg_color=T.ACCENT_SUBTLE, text_color=T.ACCENT)
            else:
                btn.configure(fg_color="transparent", text_color=T.TEXT_SECONDARY)
        # Trigger a refresh via the filter change callback or search
        if self._on_filter_change:
            self._on_filter_change(filter_key)
        else:
            # Trigger refresh via search (empty query = show all)
            self._on_search(self.search_var.get())

    def _on_search_typed(self, *_args):
        """Debounced search — fires after 300 ms of inactivity."""
        if self._search_timer is not None:
            self.after_cancel(self._search_timer)
        self._search_timer = self.after(
            300, lambda: self._on_search(self.search_var.get())
        )

    def _sort_changed(self, value: str):
        self._on_sort_change(value)
