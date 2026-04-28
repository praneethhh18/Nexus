/**
 * First-run setup wizard — opens before the main app window.
 *
 * Walks the user through:
 *   1. Welcome
 *   2. Ollama running? If not, link to install + auto-detect on poll.
 *   3. Required model present? If not, pull with live progress.
 *   4. Backend reachable? If not, show command + auto-detect on poll.
 *   5. Done — closes itself; main process opens the main window.
 *
 * The wizard state is persisted in `userData/.setup-complete` so subsequent
 * launches skip directly to the main window. The user can re-run it from
 * the tray menu if anything breaks.
 */
'use strict';

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const http = require('node:http');

const { probeOllama, pullModelStream } = require('./ollama');

const REQUIRED_MODEL = process.env.NEXUS_REQUIRED_MODEL || 'llama3.1:8b-instruct-q4_K_M';
const REQUIRED_EMBED = process.env.NEXUS_REQUIRED_EMBED || 'nomic-embed-text:latest';
const BACKEND_URL    = process.env.NEXUS_BACKEND_URL    || 'http://localhost:8000';

let setupWindow = null;
let onComplete = null;

const stateFile = () => path.join(app.getPath('userData'), '.setup-complete');

function isSetupComplete() {
  try { return fs.existsSync(stateFile()); } catch { return false; }
}

function markSetupComplete() {
  try {
    fs.mkdirSync(path.dirname(stateFile()), { recursive: true });
    fs.writeFileSync(stateFile(), JSON.stringify({ at: new Date().toISOString() }));
  } catch (e) {
    // not fatal — worst case, wizard runs again next launch
    console.warn('[NexusAgent] could not persist setup-complete marker:', e);
  }
}

function resetSetup() {
  try { fs.unlinkSync(stateFile()); } catch {}
}


function _getJson(url, timeoutMs = 1500) {
  return new Promise((resolve) => {
    try {
      const u = new URL(url);
      const req = http.get({
        hostname: u.hostname, port: u.port, path: u.pathname + u.search,
        timeout: timeoutMs,
      }, (res) => {
        let data = '';
        res.on('data', (c) => (data += c));
        res.on('end', () => {
          try { resolve({ ok: res.statusCode < 400, body: JSON.parse(data) }); }
          catch { resolve({ ok: res.statusCode < 400, body: null }); }
        });
      });
      req.on('timeout', () => { req.destroy(); resolve({ ok: false }); });
      req.on('error', () => resolve({ ok: false }));
    } catch {
      resolve({ ok: false });
    }
  });
}


function probeBackend() {
  return _getJson(`${BACKEND_URL}/api/health`, 1500);
}


function openSetupWindow({ onDone }) {
  onComplete = onDone;
  if (setupWindow) {
    setupWindow.show();
    setupWindow.focus();
    return setupWindow;
  }

  setupWindow = new BrowserWindow({
    width: 720,
    height: 620,
    resizable: false,
    minimizable: true,
    maximizable: false,
    fullscreenable: false,
    title: 'NexusAgent — Setup',
    backgroundColor: '#0a0b10',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  setupWindow.removeMenu();
  setupWindow.loadFile(path.join(__dirname, 'setup.html'));
  setupWindow.once('ready-to-show', () => setupWindow.show());

  setupWindow.on('closed', () => {
    setupWindow = null;
  });

  return setupWindow;
}


function registerIpc() {
  // Idempotent — main can call wireSetup() once safely.
  ipcMain.handle('nexus:setup/probe', async () => {
    const ollama = await probeOllama();
    const backend = await probeBackend();
    const haveModel = ollama.online && (ollama.models || []).some((m) =>
      m === REQUIRED_MODEL || m.startsWith(REQUIRED_MODEL.split(':')[0] + ':'));
    const haveEmbed = ollama.online && (ollama.models || []).some((m) =>
      m === REQUIRED_EMBED || m.startsWith(REQUIRED_EMBED.split(':')[0] + ':'));
    return {
      ollama: {
        online: ollama.online,
        host: ollama.host,
        installHintUrl: ollama.installHintUrl,
        models: ollama.models || [],
      },
      model: { required: REQUIRED_MODEL, present: haveModel },
      embed: { required: REQUIRED_EMBED, present: haveEmbed },
      backend: { online: backend.ok, url: BACKEND_URL },
    };
  });

  ipcMain.handle('nexus:setup/pull-model', async (event, modelName) => {
    const target = modelName || REQUIRED_MODEL;
    const sender = event.sender;
    await pullModelStream(target, (evt) => {
      try {
        if (!sender.isDestroyed()) sender.send('nexus:setup/pull-progress', { model: target, ...evt });
      } catch {}
    });
    return { ok: true, model: target };
  });

  ipcMain.handle('nexus:setup/done', async () => {
    markSetupComplete();
    try {
      if (typeof onComplete === 'function') onComplete();
    } catch (e) {
      console.warn('[NexusAgent] onComplete handler failed:', e);
    }
    if (setupWindow) {
      setupWindow.close();
    }
    return { ok: true };
  });

  ipcMain.handle('nexus:setup/reset', async () => {
    resetSetup();
    return { ok: true };
  });
}


module.exports = {
  openSetupWindow,
  registerIpc,
  isSetupComplete,
  resetSetup,
  REQUIRED_MODEL,
  REQUIRED_EMBED,
  BACKEND_URL,
};
