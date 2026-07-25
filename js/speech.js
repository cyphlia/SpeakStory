/**
 * SYS - Speak Your Story — Web Speech API Wrapper
 *
 * Uses the browser's built-in Web Speech API (webkitSpeechRecognition /
 * SpeechRecognition) for real-time speech-to-text.
 *
 * Features robust error recovery, auto-retry on Chrome 'network' errors,
 * non-continuous segmenting for network stability, and Web Audio API level metering.
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
        this._retryCount = 0;
        this._maxRetries = 3;
        this._restartTimer = null;

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

        // Using false prevents long-connection timeouts in Chrome's Web Speech engine
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.lang = 'en-US';
        this.recognition.maxAlternatives = 1;

        this.recognition.onstart = () => {
            this.isListening = true;
            this._retryCount = 0; // Reset retries on clean start
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

            if (this._finalTranscript.trim()) {
                if (this._onResult) {
                    this._onResult(this._finalTranscript.trim());
                }
            }
        };

        this.recognition.onerror = (event) => {
            console.warn('[Speech] Error event:', event.error);

            if (event.error === 'not-allowed') {
                this.isListening = false;
                this._emitError('Microphone access denied. Please check browser permissions.');
                this._stopAudioAnalysis();
                return;
            }

            if (event.error === 'no-speech') {
                // Ignore silent intervals; loop will restart on end
                return;
            }

            if (event.error === 'network') {
                console.warn(`[Speech] Network glitch detected (attempt ${this._retryCount + 1}/${this._maxRetries}). Auto-reconnecting…`);
                if (this.isListening && this._retryCount < this._maxRetries) {
                    this._retryCount++;
                    // Schedule quiet auto-restart
                    clearTimeout(this._restartTimer);
                    this._restartTimer = setTimeout(() => {
                        if (this.isListening) {
                            try { this.recognition.start(); } catch (e) { /* ignore busy */ }
                        }
                    }, 500);
                    return;
                } else {
                    this._emitError('Speech network error. Google Speech service timed out. Retrying or type your notes.');
                }
            } else {
                this._emitError(`Speech error: ${event.error}`);
            }

            this.stop();
        };

        this.recognition.onend = () => {
            // If user did not explicitly stop recording, automatically restart loop
            if (this.isListening) {
                clearTimeout(this._restartTimer);
                this._restartTimer = setTimeout(() => {
                    if (this.isListening) {
                        try {
                            this.recognition.start();
                        } catch (e) {
                            // Already started or busy
                        }
                    }
                }, 200);
            } else {
                this._emitStatus('idle');
                this._stopAudioAnalysis();
            }
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

        this.isListening = true;
        this._retryCount = 0;

        try {
            await this._startAudioAnalysis();
            this._emitStatus('listening');
            this.recognition.start();
        } catch (err) {
            console.error('[Speech] Start failed:', err);
            // If recognition is already running, try stopping first
            try {
                this.recognition.stop();
                setTimeout(() => {
                    if (this.isListening) this.recognition.start();
                }, 300);
            } catch (e) {
                this._emitError('Failed to start microphone speech input.');
            }
        }
    }

    stop() {
        this.isListening = false;
        clearTimeout(this._restartTimer);
        if (this.recognition) {
            try { this.recognition.stop(); } catch (e) {}
        }
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
            if (this.mediaStream) return;
            this.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const source = this.audioContext.createMediaStreamSource(this.mediaStream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            source.connect(this.analyser);
            this._analyseLevel();
        } catch (err) {
            console.warn('[Speech] Audio level analysis unavailable:', err);
        }
    }

    _analyseLevel() {
        if (!this.analyser || !this.isListening) return;

        const data = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(data);

        let sum = 0;
        for (let i = 0; i < data.length; i++) sum += data[i] * data[i];
        const rms = Math.sqrt(sum / data.length) / 255;
        const level = Math.min(1, rms * 2.5);

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
