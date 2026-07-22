"""SYS - Speak Your Story Refiner Engine.

Supports 4 operational modes:
  1. "builtin" (Default) — Ultra-fast, 100% offline rule-based NLP refiner.
     Takes 0 MB extra RAM, requires NO Ollama installation, runs instantly in <1ms!
  2. "huggingface" — Free Hugging Face Inference API (Qwen 2.5 / Mistral 7B / Llama 3.2).
     Zero local RAM usage, completely free!
  3. "api" — Cloud AI API (Gemini / Groq / OpenAI) with zero local memory cost.
  4. "ollama" — Optional local Ollama LLM server.
"""
from __future__ import annotations

import re
from typing import List, Optional

import requests

SYSTEM_PROMPT = """\
You are a professional speech-to-text transcript editor.

Your sole job is to turn a raw, noisy speech-to-text transcript into polished,
publication-ready text. Follow these rules exactly:

1. Fix ALL grammar, punctuation, and capitalisation errors.
2. Remove filler words and false starts (um, uh, like, "I mean", "you know",
   repeated/stuttered words) UNLESS removing them would change the speaker's
   intended meaning.
3. Use the conversation context provided to correct words the speech
   recogniser likely misheard — homophones, names mentioned earlier,
   domain-specific jargon.
4. Where appropriate, break the text into natural sentences and paragraphs.
5. Preserve the speaker's original meaning, tone, and intent exactly.
   DO NOT add information that was not said. DO NOT answer questions the
   speaker asked — only clean up their own words.
6. Output ONLY the cleaned-up text. No preamble, no quotation marks,
   no explanations, no markdown formatting, no commentary.\
"""

# Common filler words and hesitations pattern
FILLER_WORDS = [
    r"\b(um+s?|uh+s?|er+m?|ah+s?|hmm+s?|mhm+s?)\b",
    r"\b(you know|i mean|sort of|kind of|basically|actually)\b",
]

# Common standalone contractions / capitalization fixes
I_CONTRACTIONS = {
    "i": "I",
    "i'm": "I'm",
    "i've": "I've",
    "i'd": "I'd",
    "i'll": "I'll",
    "dont": "don't",
    "cant": "can't",
    "wont": "won't",
    "couldnt": "couldn't",
    "shouldnt": "shouldn't",
    "wouldnt": "wouldn't",
    "isnt": "isn't",
    "arent": "aren't",
    "wasnt": "wasn't",
    "werent": "weren't",
    "hasnt": "hasn't",
    "havent": "haven't",
    "hadnt": "hadn't",
    "doesnt": "doesn't",
}

DEFAULT_HF_MODEL = "Qwen/Qwen2.5-7B-Instruct"


class Refiner:
    def __init__(
        self,
        mode: str = "builtin",  # "builtin", "huggingface", "api", "ollama"
        host: str = "http://localhost:11434",
        model: str = "llama3.1",
        hf_model: str = DEFAULT_HF_MODEL,
        temperature: float = 0.2,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
    ):
        self.mode = mode.lower()
        self.host = host.rstrip("/")
        self.model = model
        self.hf_model = hf_model
        self.temperature = temperature
        self.api_key = api_key
        self.api_url = api_url or "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

    def set_mode(self, mode: str, api_key: Optional[str] = None) -> None:
        self.mode = mode.lower()
        if api_key is not None:
            self.api_key = api_key

    # ── Connectivity ────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Return True if the configured engine mode is ready."""
        if self.mode in ("builtin", "huggingface"):
            return True
        if self.mode == "api":
            return bool(self.api_key and self.api_key.strip())
        if self.mode == "ollama":
            try:
                resp = requests.get(f"{self.host}/api/tags", timeout=3)
                return resp.status_code == 200
            except Exception:
                return False
        return True

    # ── Main Refine Entry Point ─────────────────────────────────────────────

    def refine(self, raw_text: str, context_turns: List[str] | None = None) -> str:
        """Refine raw transcript based on current mode."""
        if not raw_text or not raw_text.strip():
            return ""

        text = raw_text.strip()

        if self.mode == "huggingface":
            return self._huggingface_refine(text, context_turns)
        elif self.mode == "api" and self.api_key:
            return self._api_refine(text, context_turns)
        elif self.mode == "ollama":
            return self._ollama_refine(text, context_turns)
        else:
            return self._builtin_refine(text)

    # ── 1. Built-in Offline Fast Refiner (0 MB RAM, Instant) ────────────────

    def _builtin_refine(self, text: str) -> str:
        """Lightweight heuristic NLP rules to clean speech disfluencies."""
        # 1. Remove filler words (case-insensitive)
        cleaned = text
        for pattern in FILLER_WORDS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

        # 2. Remove duplicate adjacent stutter words (e.g. "the the", "I I")
        cleaned = re.sub(r"\b(\w+)\s+\1\b", r"\1", cleaned, flags=re.IGNORECASE)

        # 3. Clean up multiple spaces, commas, and punctuation spacing
        cleaned = re.sub(r"\s*,\s*,+", ",", cleaned)
        cleaned = re.sub(r"\s+([,.?!])", r"\1", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        if not cleaned:
            return text

        # 4. Fix word-level capitalization & contractions
        words = cleaned.split()
        fixed_words = []
        for word in words:
            lower_word = word.lower()
            if lower_word in I_CONTRACTIONS:
                # Preserve trailing punctuation if present
                punct = ""
                if not word[-1].isalnum():
                    punct = word[-1]
                    lower_word = lower_word[:-1]
                replacement = I_CONTRACTIONS.get(lower_word, word)
                fixed_words.append(replacement + punct)
            else:
                fixed_words.append(word)

        cleaned = " ".join(fixed_words)

        # 5. Fix sentence-level capitalization and terminal punctuation
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        capitalized_sentences = []
        for s in sentences:
            if s:
                s = s[0].upper() + s[1:]
                capitalized_sentences.append(s)

        result = " ".join(capitalized_sentences)

        # Ensure trailing period if sentence doesn't end with punctuation
        if result and result[-1] not in ".!?":
            result += "."

        return result

    # ── 2. Free Hugging Face Inference API ─────────────────────────────────

    def _huggingface_refine(self, raw_text: str, context_turns: List[str] | None = None) -> str:
        """Call free Hugging Face Inference API (e.g. Qwen 2.5 / Mistral 7B) with zero local RAM usage."""
        try:
            prompt = f"<|im_start|>system\n{SYSTEM_PROMPT}<|im_end|>\n"
            if context_turns:
                context_block = "\n".join(f"- {turn}" for turn in context_turns)
                prompt += f"<|im_start|>user\nContext:\n{context_block}\n\nRaw transcript to clean:\n{raw_text}<|im_end|>\n<|im_start|>assistant\n"
            else:
                prompt += f"<|im_start|>user\nRaw transcript to clean up:\n{raw_text}<|im_end|>\n<|im_start|>assistant\n"

            headers = {}
            if self.api_key and self.api_key.strip():
                headers["Authorization"] = f"Bearer {self.api_key.strip()}"

            url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": self.temperature,
                    "max_new_tokens": 512,
                    "return_full_text": False,
                },
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    generated_text = data[0].get("generated_text", "").strip()
                    if generated_text:
                        # Clean up assistant tags if present
                        cleaned_out = re.sub(r"<\|im_end\|>.*", "", generated_text, flags=re.DOTALL).strip()
                        return cleaned_out or generated_text
        except Exception as exc:
            print(f"[refiner] Hugging Face API call failed: {exc}, falling back to builtin")

        return self._builtin_refine(raw_text)

    # ── 3. Other Cloud API Refiner (Gemini / Groq / OpenAI) ─────────────────

    def _api_refine(self, raw_text: str, context_turns: List[str] | None = None) -> str:
        """Call free cloud API (e.g. Gemini API) with zero local RAM usage."""
        try:
            prompt = f"{SYSTEM_PROMPT}\n\nRaw transcript to clean up:\n{raw_text}"
            if context_turns:
                context_block = "\n".join(f"- {turn}" for turn in context_turns)
                prompt = f"{SYSTEM_PROMPT}\n\nContext:\n{context_block}\n\nRaw transcript:\n{raw_text}"

            url = f"{self.api_url}?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": self.temperature, "maxOutputTokens": 1024},
            }
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    out = parts[0].get("text", "").strip()
                    if out:
                        return out
        except Exception as exc:
            print(f"[refiner] Cloud API call failed: {exc}, falling back to builtin")

        return self._builtin_refine(raw_text)

    # ── 4. Ollama Refiner (Optional Local Server) ───────────────────────────

    def _ollama_refine(self, raw_text: str, context_turns: List[str] | None = None) -> str:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if context_turns:
            context_block = "\n".join(f"- {turn}" for turn in context_turns)
            messages.append(
                {
                    "role": "user",
                    "content": f"Context:\n{context_block}\n\nRaw transcript to clean:\n{raw_text}",
                }
            )
        else:
            messages.append({"role": "user", "content": f"Raw transcript to clean up:\n{raw_text}"})

        try:
            response = requests.post(
                f"{self.host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": self.temperature},
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("message", {}).get("content", "").strip()
            return content or self._builtin_refine(raw_text)
        except Exception as exc:
            print(f"[refiner] Ollama error: {exc}, falling back to builtin")
            return self._builtin_refine(raw_text)
