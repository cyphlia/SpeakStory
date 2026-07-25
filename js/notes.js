/**
 * SYS - Speak Your Story — Notes Manager (localStorage persistence)
 *
 * Note model and CRUD operations. JSON format is compatible with the
 * desktop Python app so notes can be exported/imported between them.
 */

const TAG_COLOURS = [
    '#C4956A', '#6AAF6A', '#C46A6A', '#6A9FC4', '#D4A54A',
    '#9A7ACC', '#6AC4B8', '#C47AA0', '#8AB46A', '#C49A4A',
];

function tagColour(text) {
    let hash = 0;
    for (let i = 0; i < text.length; i++) {
        hash = ((hash << 5) - hash + text.charCodeAt(i)) | 0;
    }
    return TAG_COLOURS[Math.abs(hash) % TAG_COLOURS.length];
}

function uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
        const r = (Math.random() * 16) | 0;
        return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
    });
}

function isoNow() {
    return new Date().toISOString();
}

function relativeTime(isoStr) {
    try {
        const dt = new Date(isoStr);
        const secs = (Date.now() - dt.getTime()) / 1000;
        if (secs < 0 || secs < 60) return 'Just now';
        if (secs < 3600) {
            const m = Math.floor(secs / 60);
            return m > 1 ? `${m} min ago` : '1 min ago';
        }
        if (secs < 86400) {
            const h = Math.floor(secs / 3600);
            return h > 1 ? `${h}h ago` : '1h ago';
        }
        if (secs < 604800) {
            const d = Math.floor(secs / 86400);
            return d > 1 ? `${d}d ago` : 'Yesterday';
        }
        return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return '';
    }
}

class Note {
    constructor(data = {}) {
        this.id = data.id || uuid();
        this.title = data.title || 'Untitled Note';
        this.content = data.content || '';
        this.tags = data.tags || [];
        this.created_at = data.created_at || isoNow();
        this.modified_at = data.modified_at || isoNow();
        this.is_pinned = data.is_pinned || false;
    }

    toJSON() {
        return {
            id: this.id,
            title: this.title,
            content: this.content,
            tags: this.tags,
            created_at: this.created_at,
            modified_at: this.modified_at,
            is_pinned: this.is_pinned,
        };
    }
}

class NotesManager {
    constructor() {
        this.notes = {};
        this._loadAll();
    }

    _loadAll() {
        try {
            const raw = localStorage.getItem('sys_notes');
            if (raw) {
                const arr = JSON.parse(raw);
                arr.forEach(data => {
                    const note = new Note(data);
                    this.notes[note.id] = note;
                });
            }
        } catch (e) {
            console.warn('[NotesManager] Failed to load notes:', e);
        }
    }

    _persist() {
        const arr = Object.values(this.notes).map(n => n.toJSON());
        localStorage.setItem('sys_notes', JSON.stringify(arr));
    }

    createNote(title = 'Untitled Note') {
        const note = new Note({ title });
        this.notes[note.id] = note;
        this._persist();
        return note;
    }

    saveNote(note) {
        note.modified_at = isoNow();
        this.notes[note.id] = note;
        this._persist();
    }

    deleteNote(noteId) {
        delete this.notes[noteId];
        this._persist();
    }

    getNote(noteId) {
        return this.notes[noteId] || null;
    }

    getAllNotes() {
        return Object.values(this.notes);
    }

    searchNotes(query) {
        if (!query.trim()) return this.getAllNotes();
        const q = query.toLowerCase();
        return this.getAllNotes().filter(n =>
            n.title.toLowerCase().includes(q) ||
            n.content.toLowerCase().includes(q) ||
            n.tags.some(t => t.toLowerCase().includes(q))
        );
    }

    sortNotes(notes, criteria = 'modified', ascending = false) {
        const keyFns = {
            modified: n => n.modified_at,
            created:  n => n.created_at,
            title:    n => n.title.toLowerCase(),
        };
        const keyFn = keyFns[criteria] || keyFns.modified;
        const pinned   = notes.filter(n => n.is_pinned).sort((a, b) => {
            const va = keyFn(a), vb = keyFn(b);
            return ascending ? (va < vb ? -1 : 1) : (va > vb ? -1 : 1);
        });
        const unpinned = notes.filter(n => !n.is_pinned).sort((a, b) => {
            const va = keyFn(a), vb = keyFn(b);
            return ascending ? (va < vb ? -1 : 1) : (va > vb ? -1 : 1);
        });
        return [...pinned, ...unpinned];
    }

    exportAllAsJSON() {
        return JSON.stringify(Object.values(this.notes).map(n => n.toJSON()), null, 2);
    }

    importFromJSON(jsonStr) {
        try {
            const arr = JSON.parse(jsonStr);
            let count = 0;
            arr.forEach(data => {
                const note = new Note(data);
                this.notes[note.id] = note;
                count++;
            });
            this._persist();
            return count;
        } catch (e) {
            console.error('[NotesManager] Import failed:', e);
            return 0;
        }
    }
}
