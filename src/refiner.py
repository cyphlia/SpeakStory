"""Uses a local LLM served by Ollama to turn a raw Whisper transcript into
grammatically correct, context-aware text.

Ollama must be running locally (`ollama serve`, or the desktop app) with the
configured model already pulled (`ollama pull llama3.1`).
"""
from __future__ import annotations

from typing import List

import requests

SYSTEM_PROMPT = """\
You are a professional speech-to-text transcript editor.

Your sole job is to turn a raw, noisy speech-to-text transcript into polished,
publication-ready text.  Follow these rules exactly:

1. Fix ALL grammar, punctuation, and capitalisation errors.
2. Remove filler words and false starts (um, uh, like, "I mean", "you know",
   repeated/stuttered words) UNLESS removing them would change the speaker's
   intended meaning.
3. Use the conversation context provided to correct words the speech
   recogniser likely misheard — homophones, names mentioned earlier,
   domain-specific jargon.
4. Where appropriate, break the text into natural sentences and paragraphs.
5. Preserve the speaker's original meaning, tone, and intent exactly.
   DO NOT add information that was not said.  DO NOT answer questions the
   speaker asked — only clean up their own words.
6. Output ONLY the cleaned-up text.  No preamble, no quotation marks,
   no explanations, no markdown formatting, no commentary.\
"""


class Refiner:
    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "llama3.1",
        temperature: float = 0.2,
    ):
        self.host = host.rstrip("/")
        self.model = model
        self.temperature = temperature

    # ── Connectivity ────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Return True if Ollama is running and reachable."""
        try:
            resp = requests.get(f"{self.host}/api/tags", timeout=3)
            return resp.status_code == 200
        except (requests.ConnectionError, requests.Timeout, OSError):
            return False

    # ── Prompt construction ─────────────────────────────────────────────────

    def _build_messages(self, raw_text: str, context_turns: List[str]) -> list[dict]:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if context_turns:
            context_block = "\n".join(f"- {turn}" for turn in context_turns)
            messages.append(
                {
                    "role": "user",
                    "content": (
                        "Here is the recent conversation context (already cleaned), "
                        "most recent last:\n"
                        f"{context_block}\n\n"
                        "Use it only to resolve ambiguous words in the new transcript below."
                    ),
                }
            )

        messages.append(
            {
                "role": "user",
                "content": f"Raw transcript to clean up:\n{raw_text}",
            }
        )
        return messages

    # ── Refine ──────────────────────────────────────────────────────────────

    def refine(self, raw_text: str, context_turns: List[str] | None = None) -> str:
        """Send raw transcript to Ollama for cleanup.  Returns the cleaned
        text, or the original ``raw_text`` on any error (graceful fallback)."""
        if not raw_text.strip():
            return ""

        messages = self._build_messages(raw_text, context_turns or [])

        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": self.temperature},
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "").strip()
            return content or raw_text

        except (requests.ConnectionError, requests.Timeout) as exc:
            print(f"[refiner] Ollama connection error: {exc}")
            return raw_text
        except requests.HTTPError as exc:
            print(f"[refiner] Ollama HTTP error: {exc}")
            return raw_text
        except Exception as exc:
            print(f"[refiner] Unexpected error: {exc}")
            return raw_text
