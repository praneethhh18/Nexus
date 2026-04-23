/**
 * Voice service — pure helpers for the Voice Mode feature.
 *
 * Responsibilities (and non-responsibilities):
 *   ✓ Transcribe an audio blob via the authenticated backend endpoint.
 *   ✓ Pick a good TTS voice from the browser (prefers local-only voices).
 *   ✓ Speak text using the browser's native speechSynthesis API.
 *   ✓ Sanitise LLM markdown output before it becomes speech.
 *   ✗ No UI state — components own that.
 *   ✗ No mic capture — that lives in the VoiceMode component so it can
 *     bind cleanup to React lifecycle and avoid orphaned streams.
 *
 * Privacy / security notes:
 *   - Audio is sent only to our own /api/voice/transcribe endpoint.
 *   - No third-party speech APIs are called; TTS uses the user's OS voice.
 *   - transcribeBlob attaches the user's auth bearer + business-id headers
 *     exactly like every other service client; audio uploads are rejected
 *     server-side without valid auth.
 */
import { getToken, getBusinessId } from './auth';


// ── Transcription ──────────────────────────────────────────────────────────
/**
 * POST an audio blob to /api/voice/transcribe and return the transcript.
 *
 * @param {Blob} blob      WebM/ogg/wav audio captured by MediaRecorder.
 * @param {AbortSignal} signal  Abort the request if the user exits voice mode.
 * @returns {Promise<string>}   The transcribed text (may be empty).
 */
export async function transcribeBlob(blob, signal) {
  if (!blob || blob.size === 0) return '';

  const headers = {};
  const t = getToken();
  if (t) headers['Authorization'] = `Bearer ${t}`;
  const b = getBusinessId();
  if (b) headers['X-Business-Id'] = b;

  const form = new FormData();
  form.append('file', blob, 'voice.webm');

  const res = await fetch('/api/voice/transcribe', {
    method: 'POST',
    body: form,
    headers,
    signal,
  });
  if (!res.ok) {
    let detail = '';
    try { detail = (await res.json()).detail || ''; } catch {}
    throw new Error(detail || `Transcription failed (${res.status})`);
  }
  const data = await res.json();
  return (data.text || '').trim();
}


// ── Markdown stripping for speech ──────────────────────────────────────────
/**
 * Convert Markdown-flavoured LLM output into plain speech-safe text.
 *
 * Rules (applied in order):
 *   - Drop code fences entirely (saying a SQL block aloud is useless).
 *   - Strip bold/italic/inline-code/strikethrough markers.
 *   - Collapse links "[text](url)" → "text".
 *   - Drop heading markers, list bullets, blockquote markers.
 *   - Collapse repeated whitespace.
 */
export function stripMarkdownForSpeech(text) {
  if (!text) return '';
  let t = text;
  t = t.replace(/```[\s\S]*?```/g, ' ');          // fenced code blocks
  t = t.replace(/`([^`]+)`/g, '$1');              // inline code
  t = t.replace(/\*\*([^*]+)\*\*/g, '$1');        // bold
  t = t.replace(/__([^_]+)__/g, '$1');            // bold alt
  t = t.replace(/(^|[^*])\*([^*\n]+)\*/g, '$1$2'); // italic
  t = t.replace(/(^|[^_])_([^_\n]+)_/g, '$1$2');   // italic alt
  t = t.replace(/~~([^~]+)~~/g, '$1');            // strikethrough
  t = t.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');  // [text](url) → text
  t = t.replace(/^\s{0,3}#{1,6}\s+/gm, '');       // headings
  t = t.replace(/^\s{0,3}>\s?/gm, '');            // blockquotes
  t = t.replace(/^\s{0,3}[-*+]\s+/gm, '');        // bullet markers
  t = t.replace(/^\s{0,3}\d+\.\s+/gm, '');        // ordered list markers
  t = t.replace(/\s+/g, ' ').trim();
  return t;
}


/**
 * Trim spoken text so it stays conversational. The UI still shows the full
 * markdown response; only the speech layer gets truncated.
 */
export function truncateForSpeech(text, maxSentences = 3, maxChars = 420) {
  if (!text) return '';
  // Sentence-ish split that keeps the punctuation.
  const parts = text.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [text];
  let out = parts.slice(0, maxSentences).join(' ').trim();
  if (out.length > maxChars) out = out.slice(0, maxChars).replace(/\s+\S*$/, '') + '…';
  return out;
}


// ── Voice picking ──────────────────────────────────────────────────────────
let _voicesReady = null;

/**
 * speechSynthesis.getVoices() is populated asynchronously in most browsers.
 * Resolve once voices are available, or after a short timeout.
 */
function _waitForVoices(timeoutMs = 1500) {
  if (_voicesReady) return _voicesReady;
  _voicesReady = new Promise((resolve) => {
    if (typeof window === 'undefined' || !window.speechSynthesis) {
      resolve([]); return;
    }
    const initial = window.speechSynthesis.getVoices();
    if (initial && initial.length) { resolve(initial); return; }
    const handler = () => {
      window.speechSynthesis.removeEventListener('voiceschanged', handler);
      resolve(window.speechSynthesis.getVoices());
    };
    window.speechSynthesis.addEventListener('voiceschanged', handler);
    setTimeout(() => {
      window.speechSynthesis.removeEventListener('voiceschanged', handler);
      resolve(window.speechSynthesis.getVoices());
    }, timeoutMs);
  });
  return _voicesReady;
}


/**
 * Pick the best available voice:
 *   1. localService = true (offline, matches the "nothing leaves the machine" posture)
 *   2. en-* locale
 *   3. Prefer known-clear names (Zira on Windows, Samantha on Mac)
 *   4. Anything else that matches en-*
 */
export async function pickVoice() {
  const voices = await _waitForVoices();
  if (!voices.length) return null;

  const localEn = voices.filter(v => v.localService && /^en[-_]/i.test(v.lang));
  const en = voices.filter(v => /^en[-_]/i.test(v.lang));
  const pool = localEn.length ? localEn : (en.length ? en : voices);

  const preferred = ['Zira', 'Samantha', 'Karen', 'Aria', 'Jenny'];
  for (const name of preferred) {
    const hit = pool.find(v => v.name.toLowerCase().includes(name.toLowerCase()));
    if (hit) return hit;
  }
  // Fall back to the first female-sounding voice we can spot by name hint
  const female = pool.find(v => /female|woman|zira|samantha|karen|aria|jenny|eva/i.test(v.name));
  return female || pool[0];
}


// ── Speaking ───────────────────────────────────────────────────────────────
/**
 * Speak a string. Resolves when the utterance finishes, rejects if cancelled.
 * The returned `cancel` on the options object lets callers abort mid-speech.
 *
 * Browsers queue utterances by default; we cancel any in-flight speech first
 * so a new question from the user doesn't get drowned out by the previous
 * answer.
 */
export async function speakText(text, { onStart, onEnd, voice } = {}) {
  if (typeof window === 'undefined' || !window.speechSynthesis) {
    throw new Error('speechSynthesis unavailable in this browser');
  }
  const clean = stripMarkdownForSpeech(text);
  const spoken = truncateForSpeech(clean);
  if (!spoken) return;

  window.speechSynthesis.cancel();  // flush any previous queue

  const utter = new SpeechSynthesisUtterance(spoken);
  const chosen = voice || await pickVoice();
  if (chosen) utter.voice = chosen;
  utter.rate = 1.0;
  utter.pitch = 1.0;
  utter.volume = 1.0;

  return new Promise((resolve, reject) => {
    utter.onstart = () => { onStart?.(); };
    utter.onend   = () => { onEnd?.(); resolve(); };
    utter.onerror = (e) => {
      if (e.error === 'canceled' || e.error === 'interrupted') {
        reject(new DOMException('Speech cancelled', 'AbortError'));
      } else {
        reject(new Error(e.error || 'TTS failed'));
      }
    };
    window.speechSynthesis.speak(utter);
  });
}


/** Hard-stop any ongoing or queued speech. Safe to call anytime. */
export function cancelSpeech() {
  if (typeof window !== 'undefined' && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
}


/** Quick feature detection for the UI to decide whether to show the button. */
export function voiceSupported() {
  return !!(typeof navigator !== 'undefined'
    && navigator.mediaDevices
    && navigator.mediaDevices.getUserMedia
    && typeof window !== 'undefined'
    && window.speechSynthesis
    && window.MediaRecorder);
}
