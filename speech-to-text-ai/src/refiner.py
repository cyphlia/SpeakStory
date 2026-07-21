"""Uses a local LLM served by Ollama to turn a raw Whisper transcript into
grammatically correct, context-aware text.

Ollama must be running locally (`ollama serve`, or the desktop app) with the
configured model already pulled (`ollama pull llama3.1`).
"""
from __future__ import annotations

from typing import List

import requests

SYSTEM_PROMPT = """You clean up raw speech-to-text transcripts.

Rules:
- Fix grammar, punctuation, and capitalization.
- Remove filler words and false starts (um, uh, "I mean", repeated words) \
unless removing them would change the speaker's meaning.
- Use the conversation context to correct words the speech recognizer likely \
misheard (e.g. homophones, names mentioned earlier, domain-specific terms).
- Preserve the speaker's original meaning, tone, and intent. Do not add \
information that wasn't said and do not answer questions the speaker asked \
- just clean up their own words.
- Output ONLY the cleaned-up text. No preamble, no quotation marks, no \
explanations."""


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

    def refine(self, raw_text: str, context_turns: List[str] | None = None) -> str:
        if not raw_text.strip():
            return ""

        messages = self._build_messages(raw_text, context_turns or [])

        response = requests.post(
            f"{self.host}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": self.temperature},
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        content = data.get("message", {}).get("content", "").strip()
        return content or raw_text
