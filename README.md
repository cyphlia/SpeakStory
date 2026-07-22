# SYS - Speak Your Story

**AI-powered voice notes — speak, and your words become clean, polished text.**

SYS - Speak Your Story is a modern desktop notes application that lets you capture ideas effortlessly by speaking. It listens to your microphone, transcribes with a local Whisper model, and refines the transcript through your choice of **0MB RAM Built-in Offline Engine**, **Hugging Face Free AI API**, **Cloud API (Gemini/Groq)**, or **Local Ollama** — **all fully self-contained in a standalone executable with zero heavy LLM downloads required!**

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

---

## Key Features

| Feature | Description |
|---------|-------------|
| ⚡ **0MB RAM Built-In Engine** | Instant offline grammar/filler cleanup without downloading Ollama or heavy 4GB+ LLMs! |
| 🤗 **Hugging Face Free AI** | Free serverless LLM refinement (Qwen 2.5 / Mistral 7B / Llama 3.2) via Hugging Face API |
| 🖥️ **Instant Windows Launch** | Double-click `SpeakStory.exe` to run directly in Windows without terminal commands |
| 🎤 **Voice Activity Detection** | Auto-detects speech boundaries (WebRTC VAD) with real-time VU meter feedback |
| 🤖 **Multi-Engine Refinement** | Switch dynamically between ⚡ Built-in (0MB RAM), 🤗 Hugging Face AI, 🌐 Cloud API, or 🦙 Local Ollama |
| 📝 **Action Toolbar** | Copy note to clipboard (`📋 Copy`), export to Desktop (`📥 Export`), Pin (`📌`), Delete (`🗑️`) |
| 🔍 **Full-Text Search** | Instantly search across titles, note bodies, and tag chips |
| 📌 **Pin & Multi-Sort** | Keep key notes pinned; sort by modification date, creation date, or title |
| 🏷️ **Tagging System** | Organize notes with interactive, removable tag pills |
| 💾 **Debounced Auto-Save** | Saves changes automatically 1 second after typing stops |

---

## How It Works

```
Microphone → WebRTC VAD → Local Whisper ASR → Raw Transcript
                                                    │
                                                    ▼
         ┌──────────────────────────────────────────┴──────────────────────────────────────────┐
         │                                          │                                          │
         ▼                                          ▼                                          ▼
⚡ Built-in Fast Engine                   🤗 Hugging Face Free AI                       🌐 Cloud API / 🦙 Ollama
(0MB RAM, Instant Rule-Based)             (Qwen 2.5 / Mistral 7B)                     (Deep Context Cleanup)
         │                                          │                                          │
         └──────────────────────────────────────────┼──────────────────────────────────────────┘
                                                    │
                                                    ▼
                                      Appended to Note Editor
```

1. **`src/audio_capture.py`**: Captures 16kHz PCM audio via `sounddevice`, using WebRTC VAD (30ms frames) to detect utterance start/stop automatically with 800ms trailing silence.
2. **`src/transcriber.py`**: Runs audio through `faster-whisper` (CTranslate2 INT8 engine) for rapid ASR.
3. **`src/refiner.py`**:
   - **`builtin` (Default)**: Ultra-fast offline NLP engine that cleans disfluencies ("um", "uh", "you know"), stutters, fixes capitalization & punctuation with **0 MB extra RAM** and **zero setup**!
   - **`huggingface`**: Free Hugging Face Inference API for open-source LLMs (Qwen 2.5 / Mistral 7B) with zero local RAM.
   - **`api`**: Free Cloud API (Gemini / Groq / OpenAI) for cloud refinement.
   - **`ollama`**: Optional local Ollama LLM server.
4. **`src/notes_manager.py`**: Manages note CRUD operations, atomic JSON file writes, search, and multi-criteria sorting.
5. **`src/ui/`**: Responsive CustomTkinter GUI adhering to a warm matte brown color palette (`src/ui/theme.py`).

---

## Quick Start

### 1. Launch directly (No Setup Required)
Double-click **`SpeakStory.exe`** in the root project folder!
*(No Ollama or LLM downloads needed! Runs out-of-the-box using the built-in fast engine or Hugging Face API.)*

### 2. Run via Python Command (Optional)
```powershell
python app.py
```

---

## Project Layout

```
SYS - Speak Your Story/
├── SpeakStory.exe          # Native Windows executable launcher
├── app.py                  # Desktop GUI entry point
├── main.py                 # CLI entry point
├── build.py                # PyInstaller & executable builder
├── config.yaml             # Whisper & Engine settings
├── requirements.txt        # Python package dependencies
├── docs/                   # Documentation & guides
│   └── SYS-speak-your-story-guide.docx
├── src/
│   ├── audio_capture.py    # Mic recording + VAD + audio level stream
│   ├── transcriber.py      # faster-whisper INT8 ASR engine
│   ├── refiner.py          # Built-in 0MB RAM refiner + Hugging Face + API + Ollama
│   ├── pipeline.py         # Threaded recognition pipeline
│   ├── config.py           # Configuration parser
│   ├── notes_manager.py    # JSON note CRUD, search & sort
│   └── ui/
│       ├── theme.py        # Matte brown theme palette & tokens
│       ├── components.py   # NoteCard, TagChip, AudioLevelBar, StatusDot
│       ├── sidebar.py      # Left panel: search, sort, note list
│       ├── note_editor.py  # Centre panel: action toolbar, title, tags, editor
│       ├── speech_bar.py   # Bottom bar: mic, status, level, engine selector dropdown
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
