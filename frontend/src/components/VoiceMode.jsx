/**
 * VoiceMode — fullscreen hands-free voice conversation with the agent.
 *
 * Flow (one turn):
 *   idle       → user just opened the modal, mic permission not yet granted
 *   listening  → mic is live, VAD watches volume, MediaRecorder running
 *                during detected speech window
 *   thinking   → audio uploaded to /api/voice/transcribe → agent answers
 *   speaking   → TTS reads a short version of the answer aloud
 *   → back to listening for the next question
 *
 *   error      → transient problem; shows message + retry. Never strands
 *                the user in a silent state.
 *
 * Privacy & security:
 *   - Audio is uploaded to our own authenticated endpoint only.
 *   - No cloud STT or TTS services are used — Whisper runs on the server,
 *     speechSynthesis uses the OS voice engine in the browser.
 *   - Every AudioContext / MediaStream / MediaRecorder / fetch is cleaned
 *     up on unmount or ESC via a single `cleanup()` function so we never
 *     leak the mic light after the modal closes.
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { X, Mic, MicOff, Loader2, AlertTriangle, Volume2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { agentChat } from '../services/agent';
import { transcribeBlob, speakText, cancelSpeech, pickVoice } from '../services/voice';

// VAD (voice activity detection) thresholds — tuned on quiet room + laptop mic
const RMS_SPEECH    = 0.022;   // above this, treat as speech
const SPEECH_MS     = 220;     // sustained speech to start capture
const SILENCE_MS    = 850;     // sustained silence to end capture
const MAX_CAPTURE_MS = 15000;  // safety cap per utterance
const MIN_CAPTURE_MS =   400;  // ignore sub-400ms blips (keyboard thumps)

const STATE_LABEL = {
  idle:      'Tap to start',
  listening: 'Listening…',
  thinking:  'Thinking…',
  speaking:  'Speaking…',
  error:     'Something went wrong',
};


export default function VoiceMode({ open, onClose, onTranscript, onAgentReply, convId, setConvId }) {
  const [state, setState]               = useState('idle');
  const [volume, setVolume]             = useState(0);      // 0..1 smoothed RMS for orb pulse
  const [transcript, setTranscript]     = useState('');     // last user utterance
  const [answer, setAnswer]             = useState('');     // last agent answer (full markdown)
  const [errorMsg, setErrorMsg]         = useState('');

  // Refs for all mutable audio / network / RAF resources. We never render
  // from these — they're for cleanup and the main loop only.
  const streamRef       = useRef(null);
  const audioCtxRef     = useRef(null);
  const analyserRef     = useRef(null);
  const recorderRef     = useRef(null);
  const rafRef          = useRef(null);
  const abortRef        = useRef(null);
  const mountedRef      = useRef(true);
  const stateRef        = useRef(state);         // always-current state for closures
  useEffect(() => { stateRef.current = state; }, [state]);

  // ── Cleanup: idempotent, always safe ──────────────────────────────────────
  const cleanup = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;

    if (recorderRef.current && recorderRef.current.state !== 'inactive') {
      try { recorderRef.current.stop(); } catch {}
    }
    recorderRef.current = null;

    if (streamRef.current) {
      for (const track of streamRef.current.getTracks()) track.stop();
      streamRef.current = null;
    }
    if (audioCtxRef.current && audioCtxRef.current.state !== 'closed') {
      try { audioCtxRef.current.close(); } catch {}
    }
    audioCtxRef.current = null;
    analyserRef.current = null;

    if (abortRef.current) { try { abortRef.current.abort(); } catch {} }
    abortRef.current = null;

    cancelSpeech();
    setVolume(0);
  }, []);

  // ── ESC to exit ───────────────────────────────────────────────────────────
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  // ── Unmount cleanup ───────────────────────────────────────────────────────
  useEffect(() => {
    mountedRef.current = true;
    return () => { mountedRef.current = false; cleanup(); };
  }, [cleanup]);

  // ── Reset when the modal is closed from outside ───────────────────────────
  useEffect(() => {
    if (!open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      cleanup();
      setState('idle');
      setTranscript('');
      setAnswer('');
      setErrorMsg('');
    }
  }, [open, cleanup]);

  // Preload a TTS voice so the first speak isn't silent while voices load
  useEffect(() => { if (open) pickVoice().catch(() => {}); }, [open]);

  const safeSet = useCallback((setter) => (v) => {
    if (mountedRef.current) setter(v);
  }, []);

  // ── Handle one recorded utterance end-to-end ──────────────────────────────
  // Declared BEFORE startListening so the MediaRecorder.onstop closure picks
  // up the real function, not a `undefined` temporal-dead-zone capture.
  const handleUtterance = useCallback(async (blob) => {
    if (!mountedRef.current) return;
    setState('thinking');

    const abort = new AbortController();
    abortRef.current = abort;

    try {
      // 1. Transcribe
      const text = await transcribeBlob(blob, abort.signal);
      if (!mountedRef.current) return;
      if (!text) {
        // Whisper returned nothing — go straight back to listening instead of
        // showing a scary error. Users frequently just paused.
        setState('listening');
        return;
      }
      setTranscript(text);

      // Hook back into parent chat so the voice turn is persisted alongside
      // regular typed messages.
      onTranscript?.(text);

      // 2. Ask the agent (always agent mode so tool use works)
      const res = await agentChat(text, convId);
      if (!mountedRef.current) return;
      if (!convId && res.conversation_id && setConvId) setConvId(res.conversation_id);

      const full = res?.message?.content || '';
      setAnswer(full);
      // Surface the full turn back to the parent chat log
      onAgentReply?.(res?.message);

      // 3. Speak the short version
      setState('speaking');
      await speakText(full, {
        onEnd: () => {
          if (!mountedRef.current) return;
          // Auto-loop back to listening for the next question
          setState('listening');
        },
      });
    } catch (e) {
      if (!mountedRef.current) return;
      if (e.name === 'AbortError') return;  // user exited
      setErrorMsg(e.message || 'Voice turn failed');
      setState('error');
    } finally {
      abortRef.current = null;
    }
  }, [convId, setConvId, onTranscript, onAgentReply]);

  // ── Start listening (runs once per turn) ──────────────────────────────────
  const startListening = useCallback(async () => {
    setErrorMsg('');
    try {
      // Acquire mic with modern constraints — echo cancel + noise suppression
      // make VAD far more reliable.
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl:  true,
        },
      });
      streamRef.current = stream;

      // Web Audio graph for volume metering
      const AC = window.AudioContext || window.webkitAudioContext;
      const ctx = new AC();
      audioCtxRef.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 1024;
      analyser.smoothingTimeConstant = 0.6;
      source.connect(analyser);
      analyserRef.current = analyser;

      // MediaRecorder — gathers the audio during detected speech
      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'audio/webm';
      const recorder = new MediaRecorder(stream, { mimeType });
      recorderRef.current = recorder;

      const chunks = [];
      let recordingStartedAt = 0;
      recorder.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data); };
      recorder.onstop = async () => {
        const duration = performance.now() - recordingStartedAt;
        const blob = new Blob(chunks, { type: mimeType });
        chunks.length = 0;
        if (duration < MIN_CAPTURE_MS || blob.size < 500) {
          // Too short — keep listening instead of bothering Whisper.
          if (stateRef.current === 'listening') return;
        }
        await handleUtterance(blob);
      };

      setState('listening');

      // VAD main loop with RAF
      const timeBuf = new Uint8Array(analyser.fftSize);
      let speechStart = 0;
      let silenceStart = 0;
      let capturing = false;

      const tick = () => {
        if (stateRef.current !== 'listening') {
          // Stop the loop when we transition out of listening
          rafRef.current = null;
          return;
        }
        analyser.getByteTimeDomainData(timeBuf);
        // RMS over the window, scaled to 0..1
        let sum = 0;
        for (let i = 0; i < timeBuf.length; i++) {
          const v = (timeBuf[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / timeBuf.length);
        // Exponentially smoothed for the orb animation
        setVolume((prev) => prev * 0.75 + rms * 0.25);

        const now = performance.now();
        if (rms >= RMS_SPEECH) {
          silenceStart = 0;
          if (!speechStart) speechStart = now;
          if (!capturing && now - speechStart >= SPEECH_MS) {
            capturing = true;
            recordingStartedAt = now;
            try { recorder.start(100); } catch {}
          }
          if (capturing && now - recordingStartedAt >= MAX_CAPTURE_MS) {
            // Hard cap to protect Whisper + network
            capturing = false; speechStart = 0;
            try { recorder.stop(); } catch {}
          }
        } else {
          speechStart = 0;
          if (capturing) {
            if (!silenceStart) silenceStart = now;
            if (now - silenceStart >= SILENCE_MS) {
              capturing = false; silenceStart = 0;
              try { recorder.stop(); } catch {}
            }
          }
        }
        rafRef.current = requestAnimationFrame(tick);
      };
      rafRef.current = requestAnimationFrame(tick);
    } catch (e) {
      if (e.name === 'NotAllowedError') {
        safeSet(setErrorMsg)('Microphone access was blocked. Enable it for this site in your browser settings and try again.');
      } else if (e.name === 'NotFoundError') {
        safeSet(setErrorMsg)('No microphone found on this device.');
      } else {
        safeSet(setErrorMsg)(e.message || 'Could not open the microphone.');
      }
      safeSet(setState)('error');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [safeSet]);

  // Kick off listening when the user confirms they want voice mode
  const handleStart = () => { if (state === 'idle' || state === 'error') startListening(); };

  if (!open) return null;

  const isActive = state === 'listening' || state === 'speaking';
  // Orb scale: 1.0 baseline, bumps up with volume while listening, gentle
  // pulse while speaking (visual only — actual TTS handled in speakText).
  const orbScale = state === 'listening'
    ? 1 + Math.min(0.45, volume * 5)
    : state === 'speaking' ? 1.15 : 1;
  const orbOpacity = state === 'listening'
    ? 0.55 + Math.min(0.4, volume * 6)
    : isActive ? 0.95 : 0.6;

  return (
    <div
      role="dialog" aria-modal="true" aria-label="Voice conversation"
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'color-mix(in srgb, var(--color-bg) 94%, black)',
        backdropFilter: 'blur(8px)',
        display: 'flex', flexDirection: 'column',
        animation: 'fade-in var(--dur-base) var(--ease-out)',
      }}
    >
      {/* Top bar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '14px 24px', borderBottom: '1px solid var(--color-border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Volume2 size={16} color="var(--color-accent)" />
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>Voice chat</span>
          <span style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
            · nothing leaves your machine
          </span>
        </div>
        <button
          onClick={onClose}
          title="Exit voice mode (Esc)"
          className="btn-ghost"
        >
          <X size={14} /> Exit
        </button>
      </div>

      {/* Main area — orb + captions */}
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: 24, gap: 28, minHeight: 0,
      }}>
        {/* Orb */}
        <div style={{ position: 'relative', width: 240, height: 240 }}>
          {/* Outer glow halo */}
          <div style={{
            position: 'absolute', inset: -60, borderRadius: '50%',
            background: `radial-gradient(circle, color-mix(in srgb, var(--color-accent) ${Math.round(orbOpacity * 40)}%, transparent), transparent 70%)`,
            transition: 'background 120ms linear',
          }} />
          {/* Main orb */}
          <div
            onClick={handleStart}
            style={{
              position: 'absolute', inset: 0, borderRadius: '50%',
              background: 'radial-gradient(circle at 30% 30%, color-mix(in srgb, var(--color-accent) 65%, white), var(--color-accent) 55%, color-mix(in srgb, var(--color-accent) 55%, black))',
              transform: `scale(${orbScale})`,
              transition: 'transform 90ms cubic-bezier(0.3, 0.8, 0.4, 1), opacity 200ms',
              opacity: orbOpacity,
              boxShadow: `0 0 80px color-mix(in srgb, var(--color-accent) ${Math.round(orbOpacity * 45)}%, transparent)`,
              cursor: state === 'idle' || state === 'error' ? 'pointer' : 'default',
              animation: state === 'speaking' ? 'voice-orb-breathe 1.4s ease-in-out infinite' : 'none',
            }}
          />
          {/* Centre icon shows state at a glance */}
          <div style={{
            position: 'absolute', inset: 0, display: 'flex',
            alignItems: 'center', justifyContent: 'center',
            pointerEvents: 'none', color: 'white',
            textShadow: '0 2px 8px rgba(0,0,0,0.4)',
          }}>
            {state === 'listening' && <Mic size={42} />}
            {state === 'thinking'  && <Loader2 size={42} style={{ animation: 'spin 1.2s linear infinite' }} />}
            {state === 'speaking'  && <Volume2 size={42} />}
            {state === 'error'     && <AlertTriangle size={42} />}
            {state === 'idle'      && <MicOff size={42} />}
          </div>
        </div>

        {/* State label */}
        <div style={{
          fontSize: 15, fontWeight: 600, letterSpacing: 0.3,
          color: state === 'error' ? 'var(--color-err)' : 'var(--color-text)',
        }}>
          {STATE_LABEL[state]}
        </div>

        {/* Live transcript + last answer (captions) */}
        <div style={{
          width: '100%', maxWidth: 680,
          display: 'flex', flexDirection: 'column', gap: 10,
          overflow: 'auto', flexShrink: 1, minHeight: 0,
        }}>
          {transcript && (
            <div style={{
              padding: '10px 14px', borderRadius: 'var(--r-md)',
              background: 'var(--color-accent-soft)',
              border: '1px solid color-mix(in srgb, var(--color-accent) 22%, transparent)',
              fontSize: 13, color: 'var(--color-text)',
            }}>
              <div style={{ fontSize: 10, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 4 }}>You said</div>
              {transcript}
            </div>
          )}
          {answer && (
            <div style={{
              padding: '10px 14px', borderRadius: 'var(--r-md)',
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
              fontSize: 13, color: 'var(--color-text)',
              lineHeight: 1.55,
            }}>
              <div style={{ fontSize: 10, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.6, marginBottom: 4 }}>Agent</div>
              <div className="chat-markdown"><ReactMarkdown>{answer}</ReactMarkdown></div>
            </div>
          )}
          {errorMsg && (
            <div style={{
              padding: '10px 14px', borderRadius: 'var(--r-md)',
              background: 'color-mix(in srgb, var(--color-err) 10%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-err) 28%, transparent)',
              fontSize: 13, color: 'var(--color-err)',
            }}>
              {errorMsg}
            </div>
          )}
        </div>
      </div>

      {/* Footer — hints + start/retry */}
      <div style={{
        padding: '14px 24px', borderTop: '1px solid var(--color-border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
      }}>
        <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
          {state === 'idle' && 'Click the orb to begin. Pause when you finish a question — I\'ll answer.'}
          {state === 'listening' && 'Speak naturally. I\'ll start answering when you pause.'}
          {state === 'speaking'  && 'Press Exit or Esc to interrupt.'}
          {state === 'thinking'  && 'Working on it…'}
          {state === 'error'     && 'Click to try again.'}
        </div>
        {(state === 'idle' || state === 'error') && (
          <button className="btn-primary" onClick={handleStart}>
            <Mic size={12} /> Start
          </button>
        )}
      </div>
    </div>
  );
}
