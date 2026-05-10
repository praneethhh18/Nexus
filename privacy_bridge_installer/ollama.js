/**
 * Ollama detection + lightweight model management.
 *
 * We don't bundle Ollama (it's 200MB+ and changes often). Instead we:
 *   1. Probe http://127.0.0.1:11434/api/tags to see if it's running
 *   2. If not, the main process opens https://ollama.com/download in browser
 *   3. Once detected, we can trigger `ollama pull <model>` for the user
 *
 * The customer's laptop owns the model files — we only orchestrate.
 */
'use strict';

const http = require('node:http');
const { spawn } = require('node:child_process');

const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://127.0.0.1:11434';


function probeOllama() {
  return new Promise((resolve) => {
    const req = http.request(OLLAMA_HOST + '/api/tags', { timeout: 3000 }, (res) => {
      if (res.statusCode !== 200) {
        return resolve({ online: false, error: `HTTP ${res.statusCode}`, models: [] });
      }
      let buf = '';
      res.on('data', (c) => (buf += c));
      res.on('end', () => {
        try {
          const data = JSON.parse(buf);
          resolve({
            online: true,
            models: (data.models || []).map((m) => m.name),
          });
        } catch {
          resolve({ online: false, error: 'malformed response', models: [] });
        }
      });
    });
    req.on('timeout', () => { req.destroy(); resolve({ online: false, error: 'timeout', models: [] }); });
    req.on('error', (e) => resolve({ online: false, error: String(e.message || e), models: [] }));
    req.end();
  });
}


/**
 * Pull a model via the local `ollama` CLI. Streams progress lines back
 * via the onProgress callback. Resolves when complete or rejects on error.
 *
 * Note: we shell out to `ollama` rather than calling /api/pull directly
 * because the CLI handles resume + integrity checks for us.
 */
function pullModelOnce(modelName, onProgress = () => {}) {
  return new Promise((resolve, reject) => {
    const child = spawn('ollama', ['pull', modelName], {
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stderrTail = '';

    child.stdout.on('data', (chunk) => {
      const text = chunk.toString('utf8');
      text.split(/\r?\n/).filter(Boolean).forEach((line) => onProgress(line));
    });
    child.stderr.on('data', (chunk) => {
      const text = chunk.toString('utf8');
      stderrTail = (stderrTail + text).slice(-500);
      text.split(/\r?\n/).filter(Boolean).forEach((line) => onProgress(line));
    });
    child.on('error', (err) => {
      if (err.code === 'ENOENT') {
        return reject(new Error('Ollama CLI not found on PATH. Install from ollama.com.'));
      }
      reject(err);
    });
    child.on('exit', (code) => {
      if (code === 0) return resolve({ ok: true, model: modelName });
      reject(new Error(`ollama pull exited (code ${code}): ${stderrTail.trim().slice(-200)}`));
    });
  });
}


module.exports = { probeOllama, pullModelOnce };
