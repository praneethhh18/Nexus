/**
 * Ollama detection + model management.
 *
 * Talks to the local Ollama daemon over its HTTP API (default :11434). All
 * helpers are best-effort: they never throw, always resolve to a plain
 * object the renderer can render directly.
 *
 *   probeOllama()             → { online, version?, models?, installHintUrl }
 *   listModels()              → { ok, models[] }
 *   pullModel(name)           → { ok, error?, body? }    (one-shot, no progress)
 *   pullModelStream(name, cb) → { ok, error? }           (streams progress to cb)
 *   deleteModel(name)         → { ok }
 *
 * Streaming pull contract — `cb` is called repeatedly with one of:
 *   { kind: 'status',   status: 'pulling manifest', ... }
 *   { kind: 'progress', completed: 12345, total: 67890, percent: 18, status: 'downloading' }
 *   { kind: 'done',     ok: true }
 *   { kind: 'error',    message: '...' }
 */
'use strict';

const http = require('node:http');

const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://127.0.0.1:11434';
const INSTALL_HINT = 'https://ollama.com/download';


function _request(method, path, { body, timeout = 5000 } = {}) {
  return new Promise((resolve) => {
    const url = new URL(path, OLLAMA_HOST);
    const payload = body ? JSON.stringify(body) : null;
    const req = http.request({
      hostname: url.hostname,
      port: url.port || 80,
      path: url.pathname + (url.search || ''),
      method,
      headers: Object.assign(
        { Accept: 'application/json' },
        payload ? { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) } : {},
      ),
      timeout,
    }, (res) => {
      let data = '';
      res.on('data', (c) => (data += c));
      res.on('end', () => {
        try {
          resolve({ ok: res.statusCode < 400, status: res.statusCode, body: data ? JSON.parse(data) : {} });
        } catch {
          resolve({ ok: false, status: res.statusCode, body: data });
        }
      });
    });
    req.on('timeout', () => { req.destroy(); resolve({ ok: false, error: 'timeout' }); });
    req.on('error', (e) => resolve({ ok: false, error: String(e.message || e) }));
    if (payload) req.write(payload);
    req.end();
  });
}


async function probeOllama() {
  const tags = await _request('GET', '/api/tags', { timeout: 1500 });
  if (tags.ok) {
    const models = (tags.body.models || []).map((m) => m.name);
    return {
      online: true,
      host: OLLAMA_HOST,
      models,
      installHintUrl: null,
    };
  }
  return {
    online: false,
    host: OLLAMA_HOST,
    error: tags.error || `HTTP ${tags.status}`,
    installHintUrl: INSTALL_HINT,
  };
}


async function listModels() {
  const r = await _request('GET', '/api/tags');
  if (!r.ok) return { ok: false, error: r.error || `HTTP ${r.status}`, models: [] };
  return {
    ok: true,
    models: (r.body.models || []).map((m) => ({
      name: m.name,
      size_bytes: m.size || 0,
      modified: m.modified_at || '',
      family: (m.details && m.details.family) || '',
    })),
  };
}


async function pullModel(name) {
  const r = await _request('POST', '/api/pull', {
    body: { name, stream: false },
    timeout: 30 * 60 * 1000,
  });
  return { ok: r.ok, error: r.error, body: r.body };
}


/**
 * Stream a model pull. Calls `onEvent` with progress objects until done.
 * Resolves once the stream closes.
 */
function pullModelStream(name, onEvent) {
  return new Promise((resolve) => {
    const url = new URL('/api/pull', OLLAMA_HOST);
    const payload = JSON.stringify({ name, stream: true });

    let buf = '';
    let lastTotal = 0;
    let lastCompleted = 0;

    const safeEmit = (e) => { try { onEvent(e); } catch {} };

    const req = http.request({
      hostname: url.hostname,
      port: url.port || 80,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload),
      },
      // No timeout — the request can take several minutes for a 4GB model.
      timeout: 0,
    }, (res) => {
      if (res.statusCode >= 400) {
        let body = '';
        res.on('data', (c) => (body += c));
        res.on('end', () => {
          safeEmit({ kind: 'error', message: `HTTP ${res.statusCode}: ${body.slice(0, 200)}` });
          resolve({ ok: false, error: `HTTP ${res.statusCode}` });
        });
        return;
      }

      res.on('data', (chunk) => {
        buf += chunk.toString('utf8');
        let idx;
        while ((idx = buf.indexOf('\n')) !== -1) {
          const line = buf.slice(0, idx).trim();
          buf = buf.slice(idx + 1);
          if (!line) continue;
          let evt;
          try { evt = JSON.parse(line); } catch { continue; }

          if (evt.error) {
            safeEmit({ kind: 'error', message: String(evt.error) });
            continue;
          }

          if (typeof evt.completed === 'number' && typeof evt.total === 'number' && evt.total > 0) {
            lastCompleted = evt.completed;
            lastTotal = evt.total;
            safeEmit({
              kind: 'progress',
              status: evt.status || 'downloading',
              completed: evt.completed,
              total: evt.total,
              percent: Math.min(100, Math.round((evt.completed / evt.total) * 100)),
            });
          } else if (evt.status) {
            safeEmit({ kind: 'status', status: evt.status });
          }

          if (evt.status === 'success') {
            safeEmit({ kind: 'done', ok: true });
          }
        }
      });

      res.on('end', () => {
        // If we ended without a 'success' event, treat it as done if we
        // saw a complete byte count.
        if (lastTotal > 0 && lastCompleted >= lastTotal) {
          safeEmit({ kind: 'done', ok: true });
        }
        resolve({ ok: true });
      });
    });

    req.on('error', (e) => {
      safeEmit({ kind: 'error', message: String(e.message || e) });
      resolve({ ok: false, error: String(e.message || e) });
    });

    req.write(payload);
    req.end();
  });
}


async function deleteModel(name) {
  const r = await _request('DELETE', '/api/delete', {
    body: { name },
    timeout: 10_000,
  });
  return { ok: r.ok, error: r.error };
}


module.exports = { probeOllama, listModels, pullModel, pullModelStream, deleteModel, INSTALL_HINT };
