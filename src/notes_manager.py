"""Persistent notes storage — JSON files in ~/.speakstory/notes/.

Each note is a JSON file named after its UUID.  NotesManager handles CRUD,
full-text search, and sorting.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional


STORAGE_DIR = Path.home() / ".speakstory" / "notes"


@dataclass
class Note:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "Untitled Note"
    content: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_pinned: bool = False


def relative_time(dt_str: str) -> str:
    """Return a human-friendly relative time string, e.g. '2 min ago'."""
    try:
        dt = datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return ""
    diff = datetime.now() - dt
    secs = diff.total_seconds()
    if secs < 0:
        return "Just now"
    if secs < 60:
        return "Just now"
    if secs < 3600:
        m = int(secs / 60)
        return f"{m} min ago" if m > 1 else "1 min ago"
    if secs < 86400:
        h = int(secs / 3600)
        return f"{h}h ago" if h > 1 else "1h ago"
    if secs < 604800:
        d = int(secs / 86400)
        return f"{d}d ago" if d > 1 else "Yesterday"
    return dt.strftime("%b %d, %Y")


class NotesManager:
    """Manages notes on disk as individual JSON files."""

    def __init__(self, storage_dir: Path = STORAGE_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.notes: dict[str, Note] = {}
        self.load_all()

    # ── CRUD ────────────────────────────────────────────────────────────────

    def load_all(self) -> None:
        """Load every *.json note from disk."""
        self.notes = {}
        for path in self.storage_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                note = Note(**{k: v for k, v in data.items()
                               if k in Note.__dataclass_fields__})
                self.notes[note.id] = note
            except Exception:
                pass  # skip corrupt files

    def create_note(self, title: str = "Untitled Note") -> Note:
        note = Note(title=title)
        self.save_note(note)
        return note

    def save_note(self, note: Note) -> None:
        note.modified_at = datetime.now().isoformat()
        self.notes[note.id] = note
        path = self.storage_dir / f"{note.id}.json"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(asdict(note), fh, indent=2, ensure_ascii=False)

    def delete_note(self, note_id: str) -> None:
        path = self.storage_dir / f"{note_id}.json"
        if path.exists():
            path.unlink()
        self.notes.pop(note_id, None)

    def get_note(self, note_id: str) -> Optional[Note]:
        return self.notes.get(note_id)

    def get_all_notes(self) -> List[Note]:
        return list(self.notes.values())

    # ── Search ──────────────────────────────────────────────────────────────

    def search_notes(self, query: str) -> List[Note]:
        """Case-insensitive substring search across title, content, tags."""
        if not query.strip():
            return self.get_all_notes()
        q = query.lower()
        return [
            n for n in self.notes.values()
            if q in n.title.lower()
            or q in n.content.lower()
            or any(q in t.lower() for t in n.tags)
        ]

    # ── Sort ────────────────────────────────────────────────────────────────

    @staticmethod
    def sort_notes(
        notes: List[Note],
        criteria: str = "modified",
        ascending: bool = False,
    ) -> List[Note]:
        """Sort notes — pinned notes always stay on top."""
        key_map = {
            "modified": lambda n: n.modified_at,
            "created":  lambda n: n.created_at,
            "title":    lambda n: n.title.lower(),
        }
        key_fn = key_map.get(criteria, key_map["modified"])
        pinned   = sorted([n for n in notes if n.is_pinned],
                          key=key_fn, reverse=not ascending)
        unpinned = sorted([n for n in notes if not n.is_pinned],
                          key=key_fn, reverse=not ascending)
        return pinned + unpinned
