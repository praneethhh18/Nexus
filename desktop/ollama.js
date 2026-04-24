/**
 * Ollama detection + model management.
 *
 * Talks to the local Ollama daemon over its HTTP API (default :11434). All
 * helpers are best-effort: they never throw, always resolve to a plain
 * object the renderer can render directly.
 *
 * probeOllama()        → { online, version?, models?, installHintUrl }
 * listModels()         → { ok, models[] }
 * pullModel(name)      → { ok, stream }        (streamed progress events)
 * deleteModel(name)    → { ok }
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
  // The Ollama pull endpoint streams progress; for the MVP we just fire it
  // and return — the UI can poll listModels() until the new name appears.
  const r = await _request('POST', '/api/pull', {
    body: { name, stream: false },
    timeout: 5 * 60 * 1000,  // 5 min for a cold pull
  });
  return { ok: r.ok, error: r.error, body: r.body };
}


async function deleteModel(name) {
  const r = await _request('DELETE', '/api/delete', {
    body: { name },
    timeout: 10_000,
  });
  return { ok: r.ok, error: r.error };
}


module.exports = { probeOllama, listModels, pullModel, deleteModel, INSTALL_HINT };
