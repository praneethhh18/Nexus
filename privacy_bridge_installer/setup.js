/**
 * Setup window renderer.
 *
 * Talks to the main process via the `window.bridge` API set up by preload.js.
 * No `require`, no Node — this runs in a sandboxed renderer.
 *
 * Flow:
 *   1. On load: pre-fill saved settings, probe Ollama
 *   2. As user fills in token + base, validate (enable Save button)
 *   3. On save: persist settings, ask main to restart the bridge, close window
 *      after a short success delay
 *   4. Re-probe Ollama every 4 sec while window is open (catches "user just
 *      installed it" without making them refresh)
 */
'use strict';

const $ = (id) => document.getElementById(id);

function setBadge(el, kind) {
  el.classList.remove('ok', 'warn', 'bad');
  if (kind) el.classList.add(kind);
}

function setPill(el, text, kind) {
  el.textContent = text;
  el.classList.remove('ok', 'warn', 'bad');
  if (kind) el.classList.add(kind);
}

function tokenLooksValid(t)  { return /^pb_[A-Za-z0-9_-]{20,}$/.test((t || '').trim()); }
function baseLooksValid(b)   { try { const u = new URL((b || '').trim()); return u.protocol === 'https:' || u.protocol === 'http:'; } catch { return false; } }

let lastOllamaOnline = false;

function refreshSaveButton() {
  const ok = tokenLooksValid($('token').value) && baseLooksValid($('base').value);
  $('save').disabled = !ok;
}

async function refreshOllama() {
  const probe = await window.bridge.ollamaProbe();
  lastOllamaOnline = !!probe.online;
  if (probe.online) {
    setBadge($('b-ollama'), 'ok');
    setPill($('ollama-status'), `running · ${probe.models.length} model(s)`, 'ok');
    if (probe.models.length) {
      $('ollama-models-row').style.display = '';
      $('ollama-models').textContent = probe.models.slice(0, 3).join(', ') +
        (probe.models.length > 3 ? '…' : '');
    } else {
      $('ollama-models-row').style.display = '';
      setPill($('ollama-models'), 'none — pull llama3.1:8b', 'warn');
    }
  } else {
    setBadge($('b-ollama'), 'bad');
    setPill($('ollama-status'), 'not detected', 'bad');
    $('ollama-models-row').style.display = 'none';
  }
}

async function init() {
  const cfg = await window.bridge.settingsLoad();
  $('base').value  = cfg.base  || 'https://app.nexusagent.in';
  $('token').value = cfg.token || '';
  refreshSaveButton();

  await refreshOllama();
  setInterval(refreshOllama, 4000);

  $('token').addEventListener('input', refreshSaveButton);
  $('base').addEventListener('input', refreshSaveButton);

  $('get-token-link').addEventListener('click', (e) => {
    e.preventDefault();
    const base = ($('base').value || 'https://app.nexusagent.in').replace(/\/$/, '');
    // Use anchor target=_blank fallback by setting href so Electron's default
    // shell.openExternal handler picks it up — but safer: use bridge IPC if added.
    window.open(base + '/settings/privacy-mode', '_blank');
  });

  $('ollama-download').addEventListener('click', () => {
    // anchor href handles it
  });

  $('save').addEventListener('click', async () => {
    $('save').disabled = true;
    const payload = {
      base:  $('base').value.trim().replace(/\/$/, ''),
      token: $('token').value.trim(),
    };
    await window.bridge.settingsSave(payload);
    $('status-line').textContent = 'Saved. Starting bridge…';
    try {
      await window.bridge.bridgeRestart();
      $('status-line').textContent = lastOllamaOnline
        ? '✓ Connected. You can close this window — the bridge runs in your tray.'
        : '✓ Saved. Install Ollama from ollama.com to finish setup.';
    } catch (e) {
      $('status-line').textContent = 'Saved, but bridge had an issue: ' + (e.message || e);
    }
    setTimeout(() => window.close(), 2400);
  });
}

window.addEventListener('DOMContentLoaded', init);
