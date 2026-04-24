/**
 * fetchWithRetry — drop-in replacement for `fetch` that retries transient
 * network failures with exponential backoff.
 *
 * Retries on:
 *   - Network errors (TypeError from fetch)
 *   - HTTP 502 / 503 / 504
 *   - HTTP 429 (honors Retry-After header)
 *
 * Does NOT retry on:
 *   - 4xx other than 429 (user error — retrying is pointless)
 *   - AbortSignal-triggered aborts (user cancelled)
 *
 * Defaults: 3 attempts total, 300ms base with ×2 backoff + jitter.
 */
const DEFAULT_MAX_RETRIES = 3;
const DEFAULT_BASE_MS = 300;
const RETRYABLE_STATUSES = new Set([502, 503, 504]);


export async function fetchWithRetry(url, options = {}, retryOpts = {}) {
  const {
    maxRetries = DEFAULT_MAX_RETRIES,
    baseMs = DEFAULT_BASE_MS,
  } = retryOpts;

  let lastErr;
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const res = await fetch(url, options);
      if (res.ok) return res;

      if (res.status === 429) {
        const retryAfter = Number(res.headers.get('Retry-After')) || 2;
        // Cap at 15s so one angry server doesn't hang the UI forever.
        await _sleep(Math.min(retryAfter * 1000, 15_000));
        lastErr = new Error(`HTTP 429 — rate limited`);
        continue;
      }
      if (RETRYABLE_STATUSES.has(res.status)) {
        lastErr = new Error(`HTTP ${res.status}`);
        await _sleep(_backoff(attempt, baseMs));
        continue;
      }
      // Non-retryable — return the response so the caller handles it.
      return res;
    } catch (err) {
      if (err.name === 'AbortError') throw err;
      lastErr = err;
      await _sleep(_backoff(attempt, baseMs));
    }
  }
  throw lastErr || new Error('fetchWithRetry: exhausted attempts');
}


function _backoff(attempt, baseMs) {
  const exp = baseMs * Math.pow(2, attempt);
  const jitter = Math.random() * baseMs;
  return exp + jitter;
}

function _sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}
