# SYS - Speak Your Story

**AI-powered voice notes — speak, and your words become clean, polished text.**

SYS - Speak Your Story is a modern desktop notes application that lets you capture ideas effortlessly by speaking. It listens to your microphone, transcribes with a local Whisper model, and refines the transcript through a local LLM (via [Ollama](https://ollama.com)) into grammatically correct, publication-ready text — **all 100% offline with zero cloud latency or privacy concerns**.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

---

## Key Features

| Feature | Description |
|---------|-------------|
| 🖥️ **Instant Launch** | Double-click `SpeakStory.exe` to run directly in Windows without terminal commands |
| 🎤 **Voice Activity Detection** | Auto-detects speech boundaries (WebRTC VAD) with real-time VU meter feedback |
| 🤖 **AI Grammar Cleanup** | Ollama LLM eliminates filler words ("um", "uh"), stutters, and fixes punctuation |
| 📝 **Rich Note Management** | Create, edit, tag, pin, search, and sort notes in a custom matte brown UI |
| 🔍 **Full-Text Search** | Instantly search across titles, note bodies, and tag chips |
| 📌 **Pin & Multi-Sort** | Keep key notes pinned; sort by modification date, creation date, or title |
| 🏷️ **Tagging System** | Organize notes with interactive, removable tag pills |
| 💾 **Debounced Auto-Save** | Saves changes automatically 1 second after typing stops |
| 🔒 **100% Offline & Private** | Zero data sent to the cloud; everything executes locally on your hardware |

---

## How It Works

```
Microphone → WebRTC VAD → Local Whisper ASR → Raw Transcript
                                                    │
                                                    ▼
                        Rolling Context Buffer → Ollama LLM
                                                    │
                                                    ▼
                                     Grammatically Clean Text
                                                    │
                                                    ▼
                                      Appended to Note Editor
```

1. **`src/audio_capture.py`**: Captures 16kHz PCM audio via `sounddevice`, using WebRTC VAD (30ms frames) to detect utterance start/stop automatically with 800ms trailing silence.
2. **`src/transcriber.py`**: Runs audio through `faster-whisper` (CTranslate2 INT8 engine) for rapid ASR.
3. **`src/refiner.py`**: Passes the raw transcript and a 6-turn rolling conversation context to a local Ollama LLM (`llama3.1` or `phi3`) to fix grammar, remove filler words, and disambiguate homophones.
4. **`src/notes_manager.py`**: Manages note CRUD operations, atomic JSON file writes, search, and multi-criteria sorting.
5. **`src/ui/`**: Responsive CustomTkinter GUI adhering to a warm matte brown color palette (`src/ui/theme.py`).

---

## Quick Start

### 1. Launch directly (No Terminal Required)
Double-click **`SpeakStory.exe`** in the root project folder!

### 2. Run via Python Command (Optional)
```powershell
python app.py
```

### 3. Prerequisites for AI Refinement
- Install [**Ollama**](https://ollama.com) and pull a local model:
  ```bash
  ollama pull llama3.1
  ```
- Make sure Ollama is running (`ollama serve` or desktop app). *Note: If Ollama is offline, SYS - Speak Your Story gracefully falls back to raw Whisper transcripts.*

---

## Project Layout

```
SYS - Speak Your Story/
├── SpeakStory.exe          # Native Windows executable launcher
├── app.py                  # Desktop GUI entry point
├── main.py                 # CLI entry point
├── build.py                # PyInstaller & executable builder
├── config.yaml             # Whisper & Ollama settings
├── requirements.txt        # Python package dependencies
├── docs/                   # Documentation & guides
│   └── SYS-speak-your-story-guide.docx
├── src/
│   ├── audio_capture.py    # Mic recording + VAD + audio level stream
│   ├── transcriber.py      # faster-whisper INT8 ASR engine
│   ├── refiner.py          # Ollama LLM contextual refiner
│   ├── pipeline.py         # Threaded recognition pipeline
│   ├── config.py           # Configuration parser
│   ├── notes_manager.py    # JSON note CRUD, search & sort
│   └── ui/
│       ├── theme.py        # Matte brown theme palette & tokens
│       ├── components.py   # NoteCard, TagChip, AudioLevelBar, StatusDot
│       ├── sidebar.py      # Left panel: search, sort, note list
│       ├── note_editor.py  # Centre panel: title, tags, content editor
│       ├── speech_bar.py   # Bottom bar: mic, status, level, AI dot
│       └── main_window.py  # Main window controller
└── tests/
    └── test_pipeline.py
```

---

## Data Storage

Notes are saved as human-readable JSON files under:
`~/.speakstory/notes/<uuid>.json`

```json
{
  "id": "7b2a6f10-3e28-4e80-b219-5d4681729b10",
  "title": "Project Brainstorming",
  "content": "Discussed the architecture for offline speech recognition...",
  "tags": ["work", "ai"],
  "created_at": "2026-07-22T07:00:00",
  "modified_at": "2026-07-22T07:05:00",
  "is_pinned": true
}
```

---

## License

MIT — see `LICENSE`.
