# SpeakStory

**AI-powered voice notes — speak, and your words become clean, polished text.**

SpeakStory is a desktop notes app that lets you capture ideas by speaking. It
listens to your microphone, transcribes with a local Whisper model, and
refines the transcript through a local LLM (via [Ollama](https://ollama.com))
into grammatically correct, publication-ready text — all offline, nothing
leaves your machine.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)

---

## Features

| Feature | Description |
|---------|-------------|
| 🎤 **Voice-to-text** | Click the mic, speak naturally — text appears in your note |
| 🤖 **AI refinement** | Ollama LLM fixes grammar, removes filler words, adds punctuation |
| 📝 **Rich notes** | Create, edit, tag, pin, search, and sort notes |
| 🔍 **Full-text search** | Instantly filter notes by title, content, or tags |
| 📌 **Pin & sort** | Pin important notes; sort by date, title, or creation time |
| 🏷️ **Tags** | Organise notes with removable tag chips |
| 💾 **Auto-save** | Changes save automatically 1 second after you stop typing |
| 🎨 **Matte brown theme** | Premium dark UI with warm brown tones |
| 🔒 **Fully offline** | No cloud APIs, no accounts — everything runs locally |
| 📦 **Portable .exe** | Build a standalone `SpeakStory.exe` with PyInstaller |

---

## How It Works

```
microphone → VAD (voice activity detection) → Whisper (local) → raw transcript
                                                                       |
                                                                       ▼
                                        rolling conversation context → Ollama LLM
                                                                       |
                                                                       ▼
                                                        clean, grammatical text
                                                                       |
                                                                       ▼
                                                          appended to your note
```

1. **`src/audio_capture.py`** — records from your mic using WebRTC VAD to
   detect when you start and stop talking, with real-time audio level
   feedback for the UI.
2. **`src/transcriber.py`** — runs audio through
   [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) for a raw
   transcript.
3. **`src/refiner.py`** — sends the raw transcript plus recent conversation
   context to a local Ollama model that fixes grammar, removes fillers
   ("um", "uh", false starts), adds punctuation, and resolves misheard words.
4. **`src/pipeline.py`** — wires capture → transcription → refinement
   together with threaded callbacks for the GUI.
5. **`src/notes_manager.py`** — manages note CRUD, search, sort, and
   persistent JSON storage in `~/.speakstory/notes/`.
6. **`src/ui/`** — CustomTkinter-based desktop interface with sidebar,
   note editor, speech bar, and matte brown theme.

---

## Setup

### 1. System Dependencies

- **Python 3.10+**
- [**ffmpeg**](https://ffmpeg.org/) (required by Whisper)
- [**Ollama**](https://ollama.com/download) installed and running

```bash
# Windows (via winget)
winget install FFmpeg
winget install Ollama

# macOS
brew install ffmpeg
brew install ollama

# Ubuntu / Debian
sudo apt install ffmpeg
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull a Local LLM

```bash
ollama pull llama3.1
# smaller / faster alternative:
# ollama pull phi3
```

Make sure Ollama is running (`ollama serve` or the desktop app).

### 3. Python Environment

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

The Whisper model weights (~500 MB for `small`) download automatically on first
launch and are cached locally.

### 4. Configure

Edit `config.yaml` to choose model sizes and tune VAD sensitivity:

```yaml
whisper:
  model_size: small       # tiny, base, small, medium, large-v3
  device: cpu              # cpu or cuda
  compute_type: int8       # int8 (CPU) or float16 (GPU)

ollama:
  host: http://localhost:11434
  model: llama3.1

audio:
  sample_rate: 16000
  vad_aggressiveness: 2    # 0 (permissive) – 3 (aggressive)
  max_silence_ms: 800      # silence before an utterance ends
  max_utterance_s: 30

context:
  max_turns: 6             # how many prior turns to keep for context
```

Bigger Whisper models are more accurate but slower. Start with `small` on CPU;
move to `medium` / `large-v3` with `device: cuda` if you have a GPU.

---

## Usage

### Desktop App (recommended)

```bash
python app.py
```

This launches the SpeakStory window:

- **Left sidebar** — search, sort, note list, "＋ New Note" button
- **Centre editor** — title, tags, content area with word count
- **Bottom speech bar** — 🎤 mic button, status indicator, audio level, AI status

**Keyboard shortcuts:**
| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New note |
| `Ctrl+F` | Focus search |
| Right-click note | Pin / Delete |

### CLI Mode

The original CLI still works for headless / scripting use:

```bash
# Continuous listening
python main.py

# Single utterance
python main.py --once

# Transcribe an audio file
python main.py --file path/to/audio.wav
```

### Build Standalone .exe

```bash
python build.py
# → dist/SpeakStory/SpeakStory.exe
```

---

## Project Layout

```
SpeakStory/
├── app.py                  # Desktop GUI entry point
├── main.py                 # CLI entry point
├── build.py                # PyInstaller build script
├── config.yaml             # Model & audio configuration
├── requirements.txt
├── src/
│   ├── audio_capture.py    # Mic recording + VAD + level callback
│   ├── transcriber.py      # faster-whisper wrapper
│   ├── refiner.py          # Ollama LLM grammar cleanup
│   ├── pipeline.py         # Orchestration + threaded processing
│   ├── config.py           # Config loading
│   ├── notes_manager.py    # Note CRUD, search, sort, JSON storage
│   └── ui/
│       ├── theme.py        # Matte brown design tokens
│       ├── components.py   # NoteCard, TagChip, AudioLevelBar, StatusDot
│       ├── sidebar.py      # Left panel: search, sort, note list
│       ├── note_editor.py  # Centre panel: title, tags, editor
│       ├── speech_bar.py   # Bottom bar: mic, status, level, AI dot
│       └── main_window.py  # Top-level window + controller
└── tests/
    └── test_pipeline.py
```

---

## Data Storage

Notes are stored as individual JSON files in:

```
~/.speakstory/notes/<uuid>.json
```

Each file contains:
```json
{
  "id": "uuid",
  "title": "Meeting Notes",
  "content": "Full note text...",
  "tags": ["work", "meeting"],
  "created_at": "2026-07-22T07:00:00",
  "modified_at": "2026-07-22T07:05:00",
  "is_pinned": false
}
```

---

## Roadmap

- [ ] Streaming transcription (partial results while still speaking)
- [ ] Export notes to Markdown / PDF
- [ ] Speaker diarization for multi-person conversations
- [ ] Wake-word activation
- [ ] Note categories / folders
- [ ] Dark / light theme toggle

---

## License

MIT — see `LICENSE`.
