# SYS - Speak Your Story

**AI-powered voice notes — speak, and your words become clean, polished text.**

SYS - Speak Your Story is a multi-platform voice-enabled notes application. It captures your thoughts via speech, transcribes with high accuracy, and refines the transcript through your choice of **⚡ 0MB RAM Built-in Offline Engine**, **🤗 Hugging Face Free AI API**, **🌐 Cloud API (Gemini/Groq/OpenAI)**, or **🦙 Local Ollama**.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Web PWA](https://img.shields.io/badge/Web-PWA-brightgreen)
![Android](https://img.shields.io/badge/Platform-Windows%20%7C%20Web%20%7C%20Android-brown)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🌐 Multi-Platform Availability

| Platform | Access / Install | Engine Support |
|----------|------------------|----------------|
| 🖥️ **Windows Desktop** | Double-click `SpeakStory.exe` or run `python app.py` | Local Whisper ASR + Built-in / HF / Cloud / Ollama |
| 📱 **Android Mobile** | Install via APK (`mobile/android`) or add PWA to Home Screen | Web Speech API + Built-in / HF AI |
| 🌍 **Web App (PWA)** | [Live Demo: cyphlia.github.io/SpeakStory/](https://cyphlia.github.io/SpeakStory/) | Browser Web Speech + Built-in / HF AI |

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| ⚡ **0MB RAM Built-In Engine** | Instant offline grammar/filler cleanup without downloading Ollama or heavy 4GB+ LLMs! |
| 🤗 **Hugging Face Free AI** | Free serverless LLM refinement (Qwen 2.5 / Mistral 7B / Llama 3.2) via Hugging Face API |
| ✨ **AI Action Tools** | Single-click **"✨ Summarize"** (1-2 sentence summary) and **"📝 Improve Writing"** (grammar/style polish) |
| 📱 **Android & PWA Ready** | Responsive mobile interface, offline service worker caching, and installable manifest |
| 🖥️ **Instant Windows Launch** | Double-click `SpeakStory.exe` to run directly on Windows without terminal commands |
| 🎤 **Voice Activity Detection** | Auto-detects speech boundaries (WebRTC VAD / Web Speech) with real-time VU meter & waveform |
| ⏱️ **Live Recording Timer** | Displays real-time elapsed recording timer (`🔴 MM:SS`) during active voice input |
| 🏷️ **Auto-Colored Tags** | Deterministic hash-colored tag pills for visual organization |
| 📁 **Quick-Filter Tabs** | Instant filtering between **All Notes**, **📌 Pinned**, and **🕐 Recent** |
| 📝 **Action Toolbar** | Copy to clipboard (`📋 Copy`), export as Markdown (`📥 Export`), Pin (`📌`), Delete (`🗑️`) |
| 🔍 **Full-Text Search** | Instantly search across titles, note bodies, and tag chips |
| 💾 **Debounced Auto-Save** | Saves changes automatically 1 second after typing stops |

---

## 🏗️ Architecture

```
                                Microphone Input
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
       Desktop (Python/C#)                             Web / Mobile (JS)
  [sounddevice + WebRTC VAD]                     [Web Speech + Web Audio]
                │                                             │
                ▼                                             ▼
       faster-whisper (INT8)                          Browser ASR Engine
                │                                             │
                └──────────────────────┬──────────────────────┘
                                       │
                                       ▼
         ┌─────────────────────────────┴─────────────────────────────┐
         │                                                           │
         ▼                                                           ▼
⚡ Built-in Fast Engine                                     🤗 Hugging Face Free AI
(0MB RAM, Instant Rule-Based Cleanup)                       (Serverless Open LLMs)
         │                                                           │
         └─────────────────────────────┬─────────────────────────────┘
                                       │
                                       ▼
                       Appended to Note Editor & Persisted
                     (Desktop: JSON | Web/Mobile: localStorage)
```

---

## 🚀 Quick Start

### 1. Web App (Any Device)
Open the live PWA directly in your browser:  
👉 **[https://cyphlia.github.io/SpeakStory/](https://cyphlia.github.io/SpeakStory/)**

### 2. Windows Desktop Executable
Double-click **`SpeakStory.exe`** in the root project directory.  
*(Or launch via Python command: `python app.py`)*

### 3. Android Mobile Build
```bash
cd mobile
npm install
npx cap sync android
# Build debug APK with Android Studio or Gradle:
cd android && .\gradlew assembleDebug
```

---

## 📁 Project Layout

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
├── web/                    # Progressive Web App (PWA)
│   ├── index.html          # Web app SPA layout
│   ├── css/style.css       # Matte brown responsive design system
│   ├── js/
│   │   ├── notes.js        # Note CRUD & localStorage persistence
│   │   ├── refiner.js      # Built-in + Hugging Face text refiner
│   │   ├── speech.js       # Web Speech API & VU meter
│   │   └── app.js          # Controller & event wiring
│   ├── manifest.json       # PWA manifest
│   ├── sw.js               # Service Worker for offline caching
│   └── icons/              # PWA app icons (192x192, 512x512)
├── mobile/                 # Capacitor Android app wrapper
│   ├── capacitor.config.json # Capacitor mobile configuration
│   └── android/            # Android Studio project & manifest
├── src/
│   ├── audio_capture.py    # Mic recording + VAD + audio level stream
│   ├── transcriber.py      # faster-whisper INT8 ASR engine
│   ├── refiner.py          # Built-in 0MB RAM refiner + Hugging Face + API + Ollama
│   ├── pipeline.py         # Threaded recognition pipeline
│   ├── notes_manager.py    # JSON note CRUD, search & sort
│   └── ui/
│       ├── theme.py        # Matte brown theme palette & tokens
│       ├── components.py   # NoteCard, TagChip, AudioLevelBar, StatusDot, WaveformBar
│       ├── sidebar.py      # Left panel: search, quick-filters, sort, note list
│       ├── note_editor.py  # Centre panel: AI action toolbar, title, tags, editor
│       ├── speech_bar.py   # Bottom bar: mic, timer, status, level, waveform, engine selector
│       └── main_window.py  # Main window controller
└── tests/
    └── test_pipeline.py
```

---

## 💾 Data Storage

- **Desktop**: JSON files stored under `~/.speakstory/notes/<uuid>.json`
- **Web / Mobile**: Stored in `localStorage` (`sys_notes`) in identical JSON schema for seamless import/export compatibility.

```json
{
  "id": "7b2a6f10-3e28-4e80-b219-5d4681729b10",
  "title": "Project Brainstorming",
  "content": "Discussed the multi-platform architecture for voice notes...",
  "tags": ["work", "ai"],
  "created_at": "2026-07-26T02:00:00",
  "modified_at": "2026-07-26T02:05:00",
  "is_pinned": true
}
```

---

## 📄 License

MIT — see `LICENSE`.
