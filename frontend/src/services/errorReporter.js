/**
 * Client-side error reporter — provider-agnostic hook.
 *
 * Wires into three sources:
 *   1. React ErrorBoundary (renders fall back → reports the caught error)
 *   2. window.onerror / window.onunhandledrejection (uncaught async errors)
 *   3. fetchWithRetry failures (via explicit reportError calls)
 *
 * Behaviour is controlled by `VITE_ERROR_REPORTER_ENDPOINT` and
 * `VITE_ERROR_REPORTER_DSN`:
 *
 *   - If an endpoint URL is configured: POST each report there.
 *   - If a Sentry-compatible DSN is configured AND window.Sentry is loaded:
 *     forward to window.Sentry.captureException. We never ship the Sentry
 *     SDK ourselves — the integrator loads it via a script tag if they
 *     want full Sentry features.
 *   - Otherwise: store in an in-memory ring buffer + call
 *     window.nexusReportError so the ErrorBoundary's docs contract keeps
 *     working for self-hosted installs that don't wire anything up.
 *
 * Every report is tagged with user_id + business_id when available, build
 * version, current URL, and a truncated user-agent — enough to diagnose
 * without shipping PII.
 */
import { getUser, getBusinessId } from './auth';

// Ring buffer so a crashed install can show the last N errors in Settings.
const _buffer = [];
const _MAX_BUFFER = 50;

const ENDPOINT = import.meta.env?.VITE_ERROR_REPORTER_ENDPOINT || '';
const DSN      = import.meta.env?.VITE_ERROR_REPORTER_DSN      || '';
const RELEASE  = import.meta.env?.VITE_APP_VERSION             || 'dev';

// Console spam guard — don't hammer the network during a render loop that
// triggers the same error 60 times per second.
let _lastSignature = '';
let _lastSentAt = 0;
const _RATE_LIMIT_MS = 2000;


/**
 * Canonicalise whatever the caller hands us into a serialisable shape.
 */
function _normalise(error, context = {}) {
  const user = (() => { try { return getUser(); } catch { return null; } })();
  const businessId = (() => { try { return getBusinessId(); } catch { return null; } })();

  const report = {
    message:   String(error?.message || error || 'Unknown error'),
    stack:     error?.stack || null,
    name:      error?.name   || null,
    url:       typeof window !== 'undefined' ? window.location.href : null,
    userAgent: typeof navigator !== 'undefined' ? (navigator.userAgent || '').slice(0, 300) : null,
    release:   RELEASE,
    timestamp: new Date().toISOString(),
    user_id:   user?.id || null,
    business_id: businessId || null,
    context,
  };
  return report;
}


function _signature(report) {
  // Ignore line numbers so repeated identical errors still collapse.
  return `${report.name}::${report.message}`.slice(0, 200);
}


export function reportError(error, context = {}) {
  try {
    const report = _normalise(error, context);
    _buffer.push(report);
    if (_buffer.length > _MAX_BUFFER) _buffer.shift();

    const sig = _signature(report);
    const now = Date.now();
    if (sig === _lastSignature && (now - _lastSentAt) < _RATE_LIMIT_MS) {
      return report;       // swallow duplicates during a storm
    }
    _lastSignature = sig;
    _lastSentAt = now;

    // 1. Sentry bridge — only if the integrator loaded their own Sentry SDK.
    if (DSN && typeof window !== 'undefined' && window.Sentry?.captureException) {
      try { window.Sentry.captureException(error, { extra: context }); } catch { /* ignore */ }
    }

    // 2. Custom endpoint.
    if (ENDPOINT) {
      try {
        fetch(ENDPOINT, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(report),
          keepalive: true,     // let it fly even if the user is navigating away
        }).catch(() => { /* offline? nothing to do */ });
      } catch { /* ignore */ }
    }

    // 3. Compatibility hook — older code might read window.nexusReportError.
    if (typeof window !== 'undefined') {
      try { window.nexusReportError?.(report); } catch { /* ignore */ }
    }

    return report;
  } catch {
    // Reporter must never throw; if we error here we'll make things worse.
    return null;
  }
}


/**
 * Hook window-level listeners. Call once during app boot.
 */
export function initGlobalErrorHandlers() {
  if (typeof window === 'undefined' || window._nexusErrorHandlersReady) return;
  window._nexusErrorHandlersReady = true;

  window.addEventListener('error', (ev) => {
    reportError(ev.error || ev.message, { source: 'window.error' });
  });

  window.addEventListener('unhandledrejection', (ev) => {
    const err = ev?.reason instanceof Error ? ev.reason : new Error(String(ev?.reason || 'Unhandled promise rejection'));
    reportError(err, { source: 'unhandledrejection' });
  });
}


export function getRecentErrors() {
  return _buffer.slice();
}


export function clearRecentErrors() {
  _buffer.length = 0;
}
