# speech-to-text-ai

Fully offline speech recognition pipeline. It listens to your microphone,
transcribes what you say with a local Whisper model, then passes the raw
transcript to a local LLM (via [Ollama](https://ollama.com)) that cleans it
up into a grammatically accurate, context-aware block of text.

Nothing leaves your machine — no cloud APIs, no API keys.

## How it works

```
microphone --> VAD (voice activity detection) --> Whisper (local) --> raw transcript
                                                                          |
                                                                          v
                                        rolling conversation context --> Ollama LLM
                                                                          |
                                                                          v
                                                          clean, grammatical text
```

1. **`src/audio_capture.py`** — records from your mic and uses WebRTC VAD to
   automatically detect when you start/stop talking (so you don't have to
   press a button for every sentence).
2. **`src/transcriber.py`** — runs the audio through
   [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) to get a raw
   transcript.
3. **`src/refiner.py`** — sends the raw transcript, plus the last few turns
   of conversation, to a local model running in Ollama. The model fixes
   grammar, removes filler words ("um", "uh", false starts), adds
   punctuation, and uses prior context to disambiguate words that Whisper
   may have gotten wrong.
4. **`src/pipeline.py`** — wires the above together and keeps a rolling
   context buffer across utterances.
5. **`main.py`** — CLI entry point.

## Setup

### 1. System dependencies

- Python 3.10+
- [`ffmpeg`](https://ffmpeg.org/) (required by Whisper)
- [Ollama](https://ollama.com/download) installed and running

```bash
# macOS
brew install ffmpeg
brew install ollama

# Ubuntu/Debian
sudo apt install ffmpeg
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull a local LLM for the refinement step

```bash
ollama pull llama3.1
# smaller/faster alternative:
# ollama pull phi3
```

Make sure Ollama is running (it usually starts automatically, or run
`ollama serve` in a terminal).

### 3. Python environment

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

`faster-whisper` will download the Whisper model weights the first time you
run it (cached locally afterward).

### 4. Configure

Edit `config.yaml` to pick model sizes and tune VAD sensitivity:

```yaml
whisper:
  model_size: small       # tiny, base, small, medium, large-v3
  device: cpu              # cpu or cuda
  compute_type: int8        # int8 (fast on CPU) or float16 (GPU)

ollama:
  host: http://localhost:11434
  model: llama3.1

audio:
  sample_rate: 16000
  vad_aggressiveness: 2     # 0 (permissive) - 3 (aggressive)
  max_silence_ms: 800       # silence before an utterance is considered done
  max_utterance_s: 30

context:
  max_turns: 6              # how many prior turns to keep for context
```

Bigger Whisper models are more accurate but slower. Start with `small` on
CPU; move to `medium`/`large-v3` with `device: cuda` if you have a GPU.

## Usage

Continuous mode (default) — keeps listening, transcribing, and refining
until you press `Ctrl+C`:

```bash
python main.py
```

Single-shot mode — records one utterance and exits:

```bash
python main.py --once
```

Transcribe an existing audio file instead of the mic (still runs the LLM
refinement step, but skips capture):

```bash
python main.py --file path/to/audio.wav
```

Each run prints both the raw Whisper transcript and the refined text, e.g.:

```
[raw]      so um i think the uh meeting is like tomorrow at three right
[refined]  I think the meeting is tomorrow at 3 PM, right?
```

## Project layout

```
speech-to-text-ai/
├── main.py
├── config.yaml
├── requirements.txt
├── src/
│   ├── audio_capture.py   # mic recording + VAD
│   ├── transcriber.py     # faster-whisper wrapper
│   ├── refiner.py         # Ollama-based grammar/context cleanup
│   ├── pipeline.py        # orchestration + rolling context
│   └── config.py          # config loading
└── tests/
    └── test_pipeline.py
```

## Roadmap / ideas for extending this

- Streaming transcription (partial results while still speaking)
- Speaker diarization for multi-person conversations
- Wake-word activation instead of continuous VAD listening
- Export refined transcripts to Markdown/notes automatically
- Swap Ollama for any other local inference server (llama.cpp server, LM Studio)

## License

MIT — see `LICENSE`.
