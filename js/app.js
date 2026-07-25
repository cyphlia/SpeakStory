/**
 * SYS - Speak Your Story — Main Application Controller
 *
 * Orchestrates the UI, notes manager, speech engine, and text refiner.
 * Pure vanilla JS — no frameworks, no build step.
 */

(() => {
    'use strict';

    // ── Instances ─────────────────────────────────────────────────────────
    const notesMgr = new NotesManager();
    const refiner = new Refiner();
    const speech = new SpeechEngine();

    // ── State ─────────────────────────────────────────────────────────────
    let currentNoteId = null;
    let activeFilter = 'all';
    let sortCriteria = 'modified';
    let sortAscending = false;
    let saveTimer = null;
    let recordStartTime = 0;
    let timerInterval = null;

    // ── DOM References ────────────────────────────────────────────────────
    const $ = id => document.getElementById(id);

    const sidebar        = $('sidebar');
    const sidebarOpenBtn = $('sidebarOpenBtn');
    const sidebarCloseBtn = $('sidebarCloseBtn');
    const searchInput    = $('searchInput');
    const filterTabs     = $('filterTabs');
    const sortSelect     = $('sortSelect');
    const noteCountBadge = $('noteCountBadge');
    const noteList       = $('noteList');
    const newNoteBtn     = $('newNoteBtn');
    const emptyNewNoteBtn = $('emptyNewNoteBtn');

    const toolbar       = $('toolbar');
    const modePill      = $('modePill');
    const summarizeBtn  = $('summarizeBtn');
    const improveBtn    = $('improveBtn');
    const copyBtn       = $('copyBtn');
    const exportBtn     = $('exportBtn');
    const pinBtn        = $('pinBtn');
    const deleteBtn     = $('deleteBtn');

    const editorArea    = $('editorArea');
    const emptyState    = $('emptyState');
    const titleInput    = $('titleInput');
    const tagsContainer = $('tagsContainer');
    const tagInput      = $('tagInput');
    const contentArea   = $('contentArea');

    const micBtn        = $('micBtn');
    const timerLabel    = $('timerLabel');
    const statusLabel   = $('statusLabel');
    const levelBarFill  = $('levelBarFill');
    const waveformCanvas = $('waveformCanvas');
    const engineSelect  = $('engineSelect');
    const engineDot     = $('engineDot');
    const engineLabel   = $('engineLabel');

    const settingsModal = $('settingsModal');
    const settingsCloseBtn = $('settingsCloseBtn');
    const hfTokenInput  = $('hfTokenInput');
    const settingsSaveBtn = $('settingsSaveBtn');

    // ── Waveform Animation ────────────────────────────────────────────────
    let wavePhase = 0;
    let waveAmplitude = 0;
    let waveRunning = false;

    function startWaveform() {
        waveRunning = true;
        animateWaveform();
    }

    function stopWaveform() {
        waveRunning = false;
        const ctx = waveformCanvas.getContext('2d');
        ctx.clearRect(0, 0, waveformCanvas.width, waveformCanvas.height);
    }

    function animateWaveform() {
        if (!waveRunning) return;
        wavePhase += 0.12;
        const ctx = waveformCanvas.getContext('2d');
        const w = waveformCanvas.width = waveformCanvas.clientWidth;
        const h = waveformCanvas.height;
        const midY = h / 2;
        ctx.clearRect(0, 0, w, h);

        const numBars = 25;
        const barW = Math.max(2, w / (numBars * 2));
        for (let i = 0; i < numBars; i++) {
            const x = (w * i / numBars) + barW;
            const val = Math.sin(wavePhase + i * 0.4) * waveAmplitude;
            const barH = Math.max(1, Math.abs(val) * midY * 0.8);
            ctx.fillStyle = Math.abs(val) < 0.5 ? '#C4956A' : '#E8C49A';
            ctx.fillRect(x, midY - barH, barW, barH * 2);
        }
        requestAnimationFrame(animateWaveform);
    }

    // ── Toast Notifications ───────────────────────────────────────────────
    function showToast(message, type = 'success') {
        const existing = document.querySelector('.toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    // ── Sidebar ───────────────────────────────────────────────────────────
    function toggleSidebar(open) {
        if (open) sidebar.classList.add('open');
        else sidebar.classList.remove('open');
    }

    function refreshSidebar() {
        let notes = searchInput.value.trim()
            ? notesMgr.searchNotes(searchInput.value)
            : notesMgr.getAllNotes();

        notes = notesMgr.sortNotes(notes, sortCriteria, sortAscending);

        // Apply filter
        if (activeFilter === 'pinned') {
            notes = notes.filter(n => n.is_pinned);
        } else if (activeFilter === 'recent') {
            notes = notes.slice(0, 10);
        }

        noteCountBadge.textContent = notes.length;
        noteList.innerHTML = '';

        if (notes.length === 0) {
            noteList.innerHTML = `<div class="note-list-empty">
                ${activeFilter === 'pinned' ? 'No pinned notes.' : "No notes yet.<br>Click '＋ New Note' to begin."}
            </div>`;
            return;
        }

        notes.forEach(note => {
            const card = document.createElement('div');
            card.className = `note-card${note.id === currentNoteId ? ' active' : ''}`;
            card.dataset.id = note.id;

            const preview = note.content.split('\n')[0].trim().slice(0, 50) || 'Empty note';
            const charCount = note.content.length;
            const charLabel = charCount < 10000 ? `${charCount.toLocaleString()}c` : `${Math.floor(charCount / 1000)}k`;

            let tagDotsHTML = '';
            if (note.tags.length) {
                tagDotsHTML = '<div class="tag-dots">' +
                    note.tags.slice(0, 4).map(t =>
                        `<span class="tag-dot" style="background:${tagColour(t)}"></span>`
                    ).join('') + '</div>';
            }

            card.innerHTML = `
                <div class="note-card-title">
                    ${note.title.length > 30 ? note.title.slice(0, 28) + '…' : note.title}
                    ${note.is_pinned ? '<span class="pin-icon">📌</span>' : ''}
                </div>
                <div class="note-card-preview">${preview}</div>
                <div class="note-card-footer">
                    <span>${relativeTime(note.modified_at)}</span>
                    ${tagDotsHTML}
                    <span class="note-card-chars">${charLabel}</span>
                </div>
            `;

            card.addEventListener('click', () => selectNote(note.id));
            noteList.appendChild(card);
        });
    }

    // ── Note CRUD ─────────────────────────────────────────────────────────
    function newNote() {
        const note = notesMgr.createNote();
        currentNoteId = note.id;
        loadNote(note);
        refreshSidebar();
        titleInput.focus();
        toggleSidebar(false);
    }

    function selectNote(noteId) {
        saveCurrentNoteQuietly();
        currentNoteId = noteId;
        const note = notesMgr.getNote(noteId);
        if (note) loadNote(note);
        refreshSidebar();
        toggleSidebar(false);
    }

    function loadNote(note) {
        emptyState.classList.add('hidden');
        editorArea.style.display = 'flex';

        titleInput.value = note.title === 'Untitled Note' ? '' : note.title;
        contentArea.value = note.content;
        pinBtn.textContent = note.is_pinned ? '📌 Pinned' : '📌 Pin';
        rebuildTags(note.tags);
        updateStats();
    }

    function clearEditor() {
        currentNoteId = null;
        titleInput.value = '';
        contentArea.value = '';
        tagsContainer.innerHTML = '';
        editorArea.style.display = 'none';
        emptyState.classList.remove('hidden');
    }

    function saveCurrentNote() {
        if (!currentNoteId) return;
        const note = notesMgr.getNote(currentNoteId);
        if (!note) return;
        note.title = titleInput.value.trim() || 'Untitled Note';
        note.content = contentArea.value;
        notesMgr.saveNote(note);
        refreshSidebar();
        showToast('Saved ✓');
    }

    function saveCurrentNoteQuietly() {
        if (!currentNoteId) return;
        const note = notesMgr.getNote(currentNoteId);
        if (!note) return;
        note.title = titleInput.value.trim() || 'Untitled Note';
        note.content = contentArea.value;
        notesMgr.saveNote(note);
    }

    function scheduleSave() {
        if (saveTimer) clearTimeout(saveTimer);
        saveTimer = setTimeout(() => {
            saveCurrentNoteQuietly();
            refreshSidebar();
        }, 1000);
    }

    function deleteCurrentNote() {
        if (!currentNoteId) return;
        if (!confirm('Delete this note?')) return;
        notesMgr.deleteNote(currentNoteId);
        clearEditor();
        refreshSidebar();
        showToast('Note deleted');
    }

    function togglePin() {
        if (!currentNoteId) return;
        const note = notesMgr.getNote(currentNoteId);
        if (!note) return;
        note.is_pinned = !note.is_pinned;
        notesMgr.saveNote(note);
        pinBtn.textContent = note.is_pinned ? '📌 Pinned' : '📌 Pin';
        refreshSidebar();
    }

    // ── Tags ──────────────────────────────────────────────────────────────
    function rebuildTags(tags) {
        tagsContainer.innerHTML = '';
        tags.forEach(tag => {
            const chip = document.createElement('span');
            chip.className = 'tag-chip';
            const colour = tagColour(tag);
            chip.style.borderColor = colour;
            chip.innerHTML = `
                <span class="tag-dot-inline" style="background:${colour}"></span>
                ${tag}
                <button class="tag-remove" data-tag="${tag}">✕</button>
            `;
            chip.querySelector('.tag-remove').addEventListener('click', (e) => {
                e.stopPropagation();
                removeTag(tag);
            });
            tagsContainer.appendChild(chip);
        });
    }

    function addTag(tagText) {
        if (!tagText || !currentNoteId) return;
        const note = notesMgr.getNote(currentNoteId);
        if (!note || note.tags.includes(tagText)) return;
        note.tags.push(tagText);
        notesMgr.saveNote(note);
        rebuildTags(note.tags);
    }

    function removeTag(tagText) {
        if (!currentNoteId) return;
        const note = notesMgr.getNote(currentNoteId);
        if (!note) return;
        note.tags = note.tags.filter(t => t !== tagText);
        notesMgr.saveNote(note);
        rebuildTags(note.tags);
    }

    // ── Stats ─────────────────────────────────────────────────────────────
    function updateStats() {
        // Could add a footer bar — for now stats are implicit in the cards
    }

    // ── Clipboard & Export ────────────────────────────────────────────────
    function copyToClipboard() {
        const content = contentArea.value;
        if (!content) return;
        navigator.clipboard.writeText(content).then(() => {
            showToast('Copied to clipboard ✓');
        }).catch(() => {
            showToast('Copy failed', 'error');
        });
    }

    function exportNote() {
        if (!currentNoteId) return;
        const note = notesMgr.getNote(currentNoteId);
        if (!note) return;

        let md = `# ${note.title}\n\n`;
        if (note.tags.length) md += `Tags: ${note.tags.join(', ')}\n\n`;
        md += note.content;

        const blob = new Blob([md], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${note.title.replace(/[^a-zA-Z0-9 _-]/g, '')}.md`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Exported as Markdown ✓');
    }

    // ── AI Actions ────────────────────────────────────────────────────────
    async function summarizeNote() {
        const content = contentArea.value.trim();
        if (!content) return;
        showToast('✨ Summarizing…');
        try {
            const summary = await refiner.refine(`Summarize the following text in 1-2 concise sentences:\n\n${content}`);
            if (summary) {
                contentArea.value += `\n\n--- Summary ---\n${summary}`;
                scheduleSave();
                showToast('Summary added ✓');
            }
        } catch {
            showToast('Summarize failed', 'error');
        }
    }

    async function improveWriting() {
        const content = contentArea.value.trim();
        if (!content) return;
        showToast('📝 Improving…');
        try {
            const improved = await refiner.refine(content);
            if (improved) {
                contentArea.value = improved;
                scheduleSave();
                showToast('Writing improved ✓');
            }
        } catch {
            showToast('Improve failed', 'error');
        }
    }

    // ── Speech-to-Text ────────────────────────────────────────────────────
    speech
        .onResult(async (transcript) => {
            // Refine the transcript
            statusLabel.textContent = '✨ Refining…';
            const refined = await refiner.refine(transcript);
            const text = refined || transcript;

            if (currentNoteId) {
                const cursor = contentArea.selectionStart;
                const before = contentArea.value.slice(0, cursor);
                const after = contentArea.value.slice(cursor);
                const sep = before.trim() && !before.endsWith(' ') && !before.endsWith('\n') ? ' ' : '';
                contentArea.value = before + sep + text + after;
                contentArea.selectionStart = contentArea.selectionEnd = cursor + sep.length + text.length;
                scheduleSave();
            }
        })
        .onStatus((status) => {
            const labels = {
                idle: 'Ready — click 🎤 to speak',
                listening: '🔴 Listening… speak now',
                error: '⚠️ Error — try again',
            };
            statusLabel.textContent = labels[status] || status;
            statusLabel.className = `status-label ${status}`;

            if (status === 'listening') {
                micBtn.classList.add('recording');
                micBtn.querySelector('.mic-icon').textContent = '⏹';
                recordStartTime = Date.now();
                timerInterval = setInterval(updateRecordingTimer, 500);
                startWaveform();
            } else {
                micBtn.classList.remove('recording');
                micBtn.querySelector('.mic-icon').textContent = '🎤';
                timerLabel.textContent = '';
                if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
                stopWaveform();
            }
        })
        .onLevel((level) => {
            const pct = Math.round(level * 100);
            levelBarFill.style.width = `${pct}%`;
            levelBarFill.className = 'level-bar-fill' +
                (level > 0.8 ? ' peak' : level > 0.55 ? ' high' : '');
            waveAmplitude = level;
        })
        .onError((msg) => {
            showToast(msg, 'error');
        });

    function updateRecordingTimer() {
        const elapsed = (Date.now() - recordStartTime) / 1000;
        const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
        const secs = String(Math.floor(elapsed % 60)).padStart(2, '0');
        timerLabel.textContent = `🔴 ${mins}:${secs}`;
    }

    // ── Engine Mode ───────────────────────────────────────────────────────
    function setEngineMode(mode) {
        refiner.setMode(mode);
        const labels = {
            builtin: '⚡ Built-in Engine',
            huggingface: '🤗 HF Free AI',
            api: '🌐 Cloud API',
        };
        modePill.textContent = labels[mode] || mode;
        engineDot.className = 'status-dot connected';
        engineLabel.textContent = mode === 'builtin' ? '0MB RAM' : mode === 'huggingface' ? 'HF Free' : 'API';
    }

    // ── Settings Modal ────────────────────────────────────────────────────
    function openSettings() { settingsModal.classList.add('visible'); }
    function closeSettings() { settingsModal.classList.remove('visible'); }

    // ── Event Wiring ──────────────────────────────────────────────────────

    // Sidebar
    sidebarOpenBtn.addEventListener('click', () => toggleSidebar(true));
    sidebarCloseBtn.addEventListener('click', () => toggleSidebar(false));
    newNoteBtn.addEventListener('click', newNote);
    emptyNewNoteBtn.addEventListener('click', newNote);

    // Search (debounced)
    let searchTimer = null;
    searchInput.addEventListener('input', () => {
        if (searchTimer) clearTimeout(searchTimer);
        searchTimer = setTimeout(refreshSidebar, 300);
    });

    // Filter tabs
    filterTabs.addEventListener('click', (e) => {
        const btn = e.target.closest('.filter-tab');
        if (!btn) return;
        filterTabs.querySelectorAll('.filter-tab').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeFilter = btn.dataset.filter;
        refreshSidebar();
    });

    // Sort
    sortSelect.addEventListener('change', () => {
        const map = {
            modified: ['modified', false],
            created: ['created', false],
            'title-az': ['title', true],
            'title-za': ['title', false],
            oldest: ['created', true],
        };
        const [c, a] = map[sortSelect.value] || ['modified', false];
        sortCriteria = c;
        sortAscending = a;
        refreshSidebar();
    });

    // Toolbar actions
    summarizeBtn.addEventListener('click', summarizeNote);
    improveBtn.addEventListener('click', improveWriting);
    copyBtn.addEventListener('click', copyToClipboard);
    exportBtn.addEventListener('click', exportNote);
    pinBtn.addEventListener('click', togglePin);
    deleteBtn.addEventListener('click', deleteCurrentNote);

    // Editor auto-save
    titleInput.addEventListener('input', scheduleSave);
    contentArea.addEventListener('input', () => { scheduleSave(); updateStats(); });

    // Tags
    tagInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTag(tagInput.value.trim());
            tagInput.value = '';
        }
    });

    // Mic
    micBtn.addEventListener('click', () => {
        if (!currentNoteId) newNote();
        speech.toggle();
    });

    // Engine select
    engineSelect.addEventListener('change', () => setEngineMode(engineSelect.value));

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'n') { e.preventDefault(); newNote(); }
        if (e.ctrlKey && e.key === 'f') { e.preventDefault(); searchInput.focus(); }
        if (e.ctrlKey && e.key === 's') { e.preventDefault(); saveCurrentNote(); }
    });

    // Settings
    settingsCloseBtn.addEventListener('click', closeSettings);
    settingsSaveBtn.addEventListener('click', () => {
        refiner.setHfToken(hfTokenInput.value.trim());
        closeSettings();
        showToast('Settings saved ✓');
    });
    settingsModal.addEventListener('click', (e) => {
        if (e.target === settingsModal) closeSettings();
    });

    // ── PWA Install ───────────────────────────────────────────────────────
    let deferredPrompt = null;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
    });

    // ── Service Worker Registration ───────────────────────────────────────
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('sw.js').catch(() => {});
    }

    // ── Init ──────────────────────────────────────────────────────────────
    function init() {
        // Enable mic
        micBtn.disabled = false;
        statusLabel.textContent = speech.isSupported
            ? 'Ready — click 🎤 to speak'
            : '⚠️ Speech not supported in this browser';

        // Load HF token
        hfTokenInput.value = refiner.hfToken;

        // Initial sidebar render
        refreshSidebar();

        // Show empty state if no note selected
        if (!currentNoteId) {
            editorArea.style.display = 'none';
            emptyState.classList.remove('hidden');
        }
    }

    init();
})();
