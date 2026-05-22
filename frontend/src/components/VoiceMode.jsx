/**
 * VoiceMode, fullscreen hands-free voice conversation with the agent.
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
 *   - No cloud STT or TTS services are used, Whisper runs on the server,
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

// VAD (voice activity detection) thresholds, tuned on quiet room + laptop mic
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
  // from these, they're for cleanup and the main loop only.
  const streamRef       = useRef(null);
  const audioCtxRef     = useRef(null);
  const analyserRef     = useRef(null);
  const recorderRef     = useRef(null);
  const rafRef          = useRef(null);
  const abortRef        = useRef(null);
  const mountedRef      = useRef(true);
  const stateRef        = useRef(state);         // always-current state for closures
  const stopSessionRef  = useRef(false);          // set true to break the conversation loop
  const mimeTypeRef     = useRef('audio/webm;codecs=opus');
  useEffect(() => { stateRef.current = state; }, [state]);

  // ── Cleanup: idempotent, always safe ──────────────────────────────────────
  const cleanup = useCallback(() => {
    // Signal the conversation loop to exit on the next iteration.
    stopSessionRef.current = true;
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

  // The conversation loop runs as long as the modal is open: capture →
  // transcribe → agent → speak → capture next. Each turn creates a
  // fresh MediaRecorder (the previous design left the recorder stopped
  // after turn 1 and never restarted it, that's why the 2nd turn
  // wasn't listening). The persistent resources (stream, audioCtx,
  // analyser) stay alive across turns; only the recorder + RAF loop
  // are per-turn.

  // Capture ONE utterance from the existing audio graph.
  // Resolves with the blob (or null if nothing meaningful was captured).
  const captureOneTurn = useCallback(() => new Promise((resolve) => {
    if (!streamRef.current || !analyserRef.current) { resolve(null); return; }
    const mimeType = mimeTypeRef.current;
    const recorder = new MediaRecorder(streamRef.current, { mimeType });
    recorderRef.current = recorder;
    const chunks = [];
    const startedAt = performance.now();
    recorder.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data); };
    recorder.onstop = () => {
      const duration = performance.now() - startedAt;
      const blob = new Blob(chunks, { type: mimeType });
      resolve((duration < MIN_CAPTURE_MS || blob.size < 500) ? null : blob);
    };
    try { recorder.start(250); } catch { resolve(null); return; }

    // VAD loop, orb animation + silence-after-speech auto-stop.
    const analyser = analyserRef.current;
    const timeBuf = new Uint8Array(analyser.fftSize);
    let everSpoke = false;
    let silenceStart = 0;
    const tick = () => {
      if (!mountedRef.current || stopSessionRef.current) {
        try { recorder.stop(); } catch {}
        return;
      }
      analyser.getByteTimeDomainData(timeBuf);
      let sum = 0;
      for (let i = 0; i < timeBuf.length; i++) {
        const v = (timeBuf[i] - 128) / 128;
        sum += v * v;
      }
      const rms = Math.sqrt(sum / timeBuf.length);
      setVolume((prev) => prev * 0.75 + rms * 0.25);
      const now = performance.now();
      if (now - startedAt >= MAX_CAPTURE_MS) {
        try { recorder.stop(); } catch {}
        return;
      }
      if (rms >= RMS_SPEECH) {
        everSpoke = true;
        silenceStart = 0;
      } else if (everSpoke) {
        if (!silenceStart) silenceStart = now;
        if (now - silenceStart >= SILENCE_MS) {
          try { recorder.stop(); } catch {}
          return;
        }
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
  }), []);

  // Process one utterance end-to-end. Returns when the agent has spoken
  // its reply, so the outer loop can immediately start a new turn.
  const handleUtterance = useCallback(async (blob) => {
    if (!mountedRef.current) return;
    setState('thinking');
    const abort = new AbortController();
    abortRef.current = abort;
    try {
      const text = await transcribeBlob(blob, abort.signal);
      if (!mountedRef.current) return;
      if (!text) return;  // Whisper returned empty, loop to listen again
      setTranscript(text);
      onTranscript?.(text);

      const res = await agentChat(text, convId);
      if (!mountedRef.current) return;
      if (!convId && res.conversation_id && setConvId) setConvId(res.conversation_id);
      const full = res?.message?.content || '';
      setAnswer(full);
      onAgentReply?.(res?.message);

      setState('speaking');
      await speakText(full);
    } catch (e) {
      if (e.name === 'AbortError') return;
      setErrorMsg(e.message || 'Voice turn failed');
      setState('error');
      stopSessionRef.current = true;
    } finally {
      abortRef.current = null;
    }
  }, [convId, setConvId, onTranscript, onAgentReply]);

  // Top-level entry: acquire mic ONCE, then loop capture → handle until
  // the user exits or an error stops the session.
  const startListening = useCallback(async () => {
    setErrorMsg('');
    stopSessionRef.current = false;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      streamRef.current = stream;

      const AC = window.AudioContext || window.webkitAudioContext;
      const ctx = new AC();
      audioCtxRef.current = ctx;
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 1024;
      analyser.smoothingTimeConstant = 0.6;
      source.connect(analyser);
      analyserRef.current = analyser;

      let mimeType = 'audio/webm;codecs=opus';
      if (!MediaRecorder.isTypeSupported(mimeType)) mimeType = 'audio/webm';
      mimeTypeRef.current = mimeType;

      // ── Conversation loop ─────────────────────────────────────────────
      while (mountedRef.current && !stopSessionRef.current) {
        setState('listening');
        const blob = await captureOneTurn();
        if (!mountedRef.current || stopSessionRef.current) break;
        if (!blob) continue;        // nothing meaningful captured, loop
        await handleUtterance(blob); // transcribe → agent → speak
      }
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
  }, [safeSet, captureOneTurn, handleUtterance]);

  // Kick off listening when the user confirms they want voice mode
  const handleStart = () => { if (state === 'idle' || state === 'error') startListening(); };

  if (!open) return null;

  const isActive = state === 'listening' || state === 'speaking';
  // Orb scale: 1.0 baseline, bumps up with volume while listening, gentle
  // pulse while speaking (visual only, actual TTS handled in speakText).
  const orbScale = state === 'listening'
    ? 1 + Math.min(0.45, volume * 5)
    : state === 'speaking' ? 1.15 : 1;
  const orbOpacity = state === 'listening'
    ? 0.55 + Math.min(0.4, volume * 6)
    : isActive ? 0.95 : 0.6;

  return (
    <div
      role="dialog" aria-modal="true" aria-label="Voice conversation"
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 1000,
        background: 'rgba(0,0,0,0.78)',
        backdropFilter: 'blur(8px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
        animation: 'fade-in var(--dur-base) var(--ease-out)',
      }}
    >
    <div
      onClick={(e) => e.stopPropagation()}
      style={{
        width: '100%', maxWidth: 460, maxHeight: '85vh',
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border-strong)',
        borderRadius: 16,
        boxShadow: '0 24px 80px rgba(0,0,0,0.55)',
        display: 'flex', flexDirection: 'column', overflow: 'hidden',
        /* Opaque, no see-through to chat behind. */
        opacity: 1,
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

      {/* Main area, orb + captions */}
      <div style={{
        flex: 1, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        padding: 20, gap: 18, minHeight: 0, overflow: 'auto',
      }}>
        {/* Orb */}
        <div style={{ position: 'relative', width: 140, height: 140, flexShrink: 0 }}>
          {/* Outer glow halo */}
          <div style={{
            position: 'absolute', inset: -60, borderRadius: '50%',
            background: `radial-gradient(circle, color-mix(in srgb, var(--color-accent) ${Math.round(orbOpacity * 40)}%, transparent), transparent 70%)`,
            transition: 'background 120ms linear',
          }} />
          {/* Main orb */}
          <div
            onClick={state === 'idle' || state === 'error' ? handleStart : undefined}
            title={state === 'listening' ? 'Listening… pause when you finish' : ''}
            style={{
              position: 'absolute', inset: 0, borderRadius: '50%',
              background: 'radial-gradient(circle at 30% 30%, color-mix(in srgb, var(--color-accent) 65%, white), var(--color-accent) 55%, color-mix(in srgb, var(--color-accent) 55%, black))',
              transform: `scale(${orbScale})`,
              transition: 'transform 90ms cubic-bezier(0.3, 0.8, 0.4, 1), opacity 200ms',
              opacity: orbOpacity,
              boxShadow: `0 0 80px color-mix(in srgb, var(--color-accent) ${Math.round(orbOpacity * 45)}%, transparent)`,
              cursor: (state === 'idle' || state === 'error') ? 'pointer' : 'default',
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
            {state === 'listening' && <Mic size={28} />}
            {state === 'thinking'  && <Loader2 size={28} style={{ animation: 'spin 1.2s linear infinite' }} />}
            {state === 'speaking'  && <Volume2 size={28} />}
            {state === 'error'     && <AlertTriangle size={28} />}
            {state === 'idle'      && <MicOff size={28} />}
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

      {/* Footer, hints + start/retry */}
      <div style={{
        padding: '14px 24px', borderTop: '1px solid var(--color-border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
      }}>
        <div style={{ fontSize: 11, color: 'var(--color-text-dim)', flex: 1 }}>
          {state === 'idle' && 'Click the orb to begin.'}
          {state === 'listening' && 'Speak naturally, I\'ll reply when you pause.'}
          {state === 'speaking'  && 'Press Exit or Esc to interrupt.'}
          {state === 'thinking'  && 'Working on it…'}
          {state === 'error'     && 'Click the orb to try again.'}
        </div>
        {(state === 'idle' || state === 'error') && (
          <button className="btn-primary" onClick={handleStart}>
            <Mic size={12} /> Start
          </button>
        )}
      </div>
    </div>
    </div>
  );
}
