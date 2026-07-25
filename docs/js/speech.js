/**
 * SYS - Speak Your Story — Web Speech API Wrapper
 *
 * Uses the browser's built-in Web Speech API (webkitSpeechRecognition /
 * SpeechRecognition) for real-time speech-to-text. Falls back to a helpful
 * error message if the browser doesn't support it.
 *
 * Also provides audio level visualization via Web Audio API.
 */

class SpeechEngine {
    constructor() {
        this.recognition = null;
        this.audioContext = null;
        this.analyser = null;
        this.mediaStream = null;
        this.isListening = false;
        this.isSupported = !!(window.SpeechRecognition || window.webkitSpeechRecognition);

        this._onResult = null;
        this._onStatus = null;
        this._onLevel = null;
        this._onError = null;

        this._interimTranscript = '';
        this._finalTranscript = '';

        if (this.isSupported) {
            this._initRecognition();
        }
    }

    /** Set callback: (transcript: string) => void */
    onResult(fn) { this._onResult = fn; return this; }

    /** Set callback: (status: string) => void — 'idle' | 'listening' | 'transcribing' | 'error' */
    onStatus(fn) { this._onStatus = fn; return this; }

    /** Set callback: (level: number 0–1) => void */
    onLevel(fn) { this._onLevel = fn; return this; }

    /** Set callback: (errorMsg: string) => void */
    onError(fn) { this._onError = fn; return this; }

    _initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();
        this.recognition.continuous = true;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;

        this.recognition.onstart = () => {
            this.isListening = true;
            this._emitStatus('listening');
        };

        this.recognition.onresult = (event) => {
            this._interimTranscript = '';
            this._finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i];
                if (result.isFinal) {
                    this._finalTranscript += result[0].transcript;
                } else {
                    this._interimTranscript += result[0].transcript;
                }
            }

            // If we have a final transcript, emit it
            if (this._finalTranscript.trim()) {
                if (this._onResult) {
                    this._onResult(this._finalTranscript.trim());
                }
            }
        };

        this.recognition.onerror = (event) => {
            console.warn('[Speech] Error:', event.error);
            if (event.error === 'not-allowed') {
                this._emitError('Microphone access denied. Please allow microphone permissions.');
            } else if (event.error === 'no-speech') {
                // Not a critical error, just no speech detected
                return;
            } else {
                this._emitError(`Speech error: ${event.error}`);
            }
            this.stop();
        };

        this.recognition.onend = () => {
            this.isListening = false;
            this._emitStatus('idle');
            this._stopAudioAnalysis();
        };
    }

    async start() {
        if (!this.isSupported) {
            this._emitError('Speech recognition is not supported in this browser. Try Chrome or Edge.');
            return;
        }

        if (this.isListening) {
            this.stop();
            return;
        }

        try {
            // Start audio analysis for level meter
            await this._startAudioAnalysis();

            this._emitStatus('listening');
            this.recognition.start();
        } catch (err) {
            console.error('[Speech] Start failed:', err);
            this._emitError('Failed to start speech recognition.');
        }
    }

    stop() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
        this.isListening = false;
        this._emitStatus('idle');
        this._stopAudioAnalysis();
    }

    toggle() {
        if (this.isListening) {
            this.stop();
        } else {
            this.start();
        }
    }

    // ── Audio Level Analysis ──────────────────────────────────────────────

    async _startAudioAnalysis() {
        try {
            this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            source.connect(this.analyser);
            this._analyseLevel();
        } catch (err) {
            console.warn('[Speech] Audio analysis unavailable:', err);
        }
    }

    _analyseLevel() {
        if (!this.analyser || !this.isListening) return;

        const data = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(data);

        // Calculate RMS level normalised to 0–1
        let sum = 0;
        for (let i = 0; i < data.length; i++) sum += data[i] * data[i];
        const rms = Math.sqrt(sum / data.length) / 255;
        const level = Math.min(1, rms * 2.5); // amplify for better visual response

        if (this._onLevel) this._onLevel(level);

        requestAnimationFrame(() => this._analyseLevel());
    }

    _stopAudioAnalysis() {
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(t => t.stop());
            this.mediaStream = null;
        }
        if (this.audioContext) {
            this.audioContext.close().catch(() => {});
            this.audioContext = null;
            this.analyser = null;
        }
        if (this._onLevel) this._onLevel(0);
    }

    // ── Event helpers ─────────────────────────────────────────────────────

    _emitStatus(status) {
        if (this._onStatus) this._onStatus(status);
    }

    _emitError(msg) {
        this._emitStatus('error');
        if (this._onError) this._onError(msg);
    }
}
