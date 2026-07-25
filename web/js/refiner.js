/**
 * SYS - Speak Your Story — Text Refiner
 *
 * Two modes:
 *   1. Built-in offline regex refiner (same rules as the Python version)
 *   2. Hugging Face Inference API (free serverless LLMs)
 */

const FILLER_PATTERNS = [
    /\b(um+s?|uh+s?|er+m?|ah+s?|hmm+s?|mhm+s?)\b/gi,
    /\b(you know|i mean|sort of|kind of|basically|actually)\b/gi,
];

const I_CONTRACTIONS = {
    "i": "I", "i'm": "I'm", "i've": "I've", "i'd": "I'd", "i'll": "I'll",
    "dont": "don't", "cant": "can't", "wont": "won't",
    "couldnt": "couldn't", "shouldnt": "shouldn't", "wouldnt": "wouldn't",
    "isnt": "isn't", "arent": "aren't", "wasnt": "wasn't", "werent": "weren't",
    "hasnt": "hasn't", "havent": "haven't", "hadnt": "hadn't", "doesnt": "doesn't",
};

const SYSTEM_PROMPT = `You are a professional speech-to-text transcript editor.

Your sole job is to turn a raw, noisy speech-to-text transcript into polished,
publication-ready text. Follow these rules exactly:

1. Fix ALL grammar, punctuation, and capitalisation errors.
2. Remove filler words and false starts (um, uh, like, "I mean", "you know",
   repeated/stuttered words) UNLESS removing them would change the speaker's
   intended meaning.
3. Use the conversation context to correct words the speech recogniser likely
   misheard — homophones, names, domain-specific jargon.
4. Where appropriate, break the text into natural sentences and paragraphs.
5. Preserve the speaker's original meaning, tone, and intent exactly.
   DO NOT add information that was not said.
6. Output ONLY the cleaned-up text. No preamble, no quotation marks,
   no explanations, no markdown formatting, no commentary.`;

const DEFAULT_HF_MODEL = 'Qwen/Qwen2.5-7B-Instruct';

class Refiner {
    constructor() {
        this.mode = 'builtin';  // 'builtin' or 'huggingface'
        this.hfModel = DEFAULT_HF_MODEL;
        this.hfToken = localStorage.getItem('sys_hf_token') || '';
    }

    setMode(mode) {
        this.mode = mode;
    }

    setHfToken(token) {
        this.hfToken = token;
        localStorage.setItem('sys_hf_token', token);
    }

    async refine(rawText) {
        if (!rawText || !rawText.trim()) return '';

        if (this.mode === 'huggingface') {
            return this._huggingfaceRefine(rawText);
        }
        return this._builtinRefine(rawText);
    }

    // ── Built-in Offline Refiner ──────────────────────────────────────────

    _builtinRefine(text) {
        let cleaned = text;

        // 1. Remove filler words
        for (const pattern of FILLER_PATTERNS) {
            cleaned = cleaned.replace(pattern, '');
        }

        // 2. Remove duplicate adjacent stutter words
        cleaned = cleaned.replace(/\b(\w+)\s+\1\b/gi, '$1');

        // 3. Clean up punctuation spacing
        cleaned = cleaned.replace(/\s*,\s*,+/g, ',');
        cleaned = cleaned.replace(/\s+([,.?!])/g, '$1');
        cleaned = cleaned.replace(/\s+/g, ' ').trim();

        if (!cleaned) return text;

        // 4. Fix contractions
        const words = cleaned.split(' ');
        const fixedWords = words.map(word => {
            const lower = word.toLowerCase().replace(/[,.?!]$/, '');
            const punct = word.match(/[,.?!]$/) ? word.slice(-1) : '';
            if (I_CONTRACTIONS[lower]) {
                return I_CONTRACTIONS[lower] + punct;
            }
            return word;
        });
        cleaned = fixedWords.join(' ');

        // 5. Capitalize sentences
        const sentences = cleaned.split(/(?<=[.!?])\s+/);
        const caps = sentences.map(s => s ? s[0].toUpperCase() + s.slice(1) : s);
        let result = caps.join(' ');

        // Ensure trailing period
        if (result && !/[.!?]$/.test(result)) result += '.';

        return result;
    }

    // ── Hugging Face Inference API ────────────────────────────────────────

    async _huggingfaceRefine(rawText) {
        try {
            const prompt = `<|im_start|>system\n${SYSTEM_PROMPT}<|im_end|>\n<|im_start|>user\nRaw transcript to clean up:\n${rawText}<|im_end|>\n<|im_start|>assistant\n`;

            const headers = { 'Content-Type': 'application/json' };
            if (this.hfToken) {
                headers['Authorization'] = `Bearer ${this.hfToken}`;
            }

            const resp = await fetch(`https://api-inference.huggingface.co/models/${this.hfModel}`, {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    inputs: prompt,
                    parameters: {
                        temperature: 0.2,
                        max_new_tokens: 512,
                        return_full_text: false,
                    },
                }),
            });

            if (resp.ok) {
                const data = await resp.json();
                if (Array.isArray(data) && data.length > 0) {
                    let generated = data[0].generated_text || '';
                    generated = generated.replace(/<\|im_end\|>[\s\S]*/, '').trim();
                    if (generated) return generated;
                }
            }
        } catch (err) {
            console.warn('[Refiner] HF API failed, falling back to builtin:', err);
        }
        return this._builtinRefine(rawText);
    }
}
