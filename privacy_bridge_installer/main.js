/**
 * Privacy Bridge — main process.
 *
 * UX promise: customer double-clicks the installer, the app installs itself,
 * lives quietly in the system tray, and "just works" forever after.
 *
 * Boot order:
 *   1. Single-instance lock (second launch focuses tray, doesn't spawn twice)
 *   2. Hide from dock (Mac LSUIElement) / no main window by default
 *   3. Read settings.json — if no token saved, open setup window (one-shot)
 *   4. Start cloudflared subprocess → grab tunnel URL
 *   5. POST URL to NexusAgent's /api/privacy-bridge/register
 *   6. Re-register every 5 min so health stays fresh
 *   7. Tray icon shows real-time status (green / yellow / red)
 *   8. Auto-start on login enabled by default (configurable from tray menu)
 *
 * Customer never sees a terminal, never types a command, never installs Node.
 * Ollama install is the only manual step (we open the download page in
 * their browser if Ollama isn't detected on first run).
 */
'use strict';

const { app, BrowserWindow, Tray, Menu, ipcMain, shell,
        Notification, nativeImage } = require('electron');
const path = require('node:path');

const tunnel    = require('./tunnel');
const ollama    = require('./ollama');
const settings  = require('./settings');
const trayMod   = require('./tray');

const isDev = !!process.env.BRIDGE_DEV;
let setupWindow = null;
let tray = null;

// Live status. Tray icon + menu re-render whenever this changes.
const state = {
  status: 'starting',           // starting | needs-setup | tunnel-up | registered | bridge-down
  tunnelUrl: null,
  ollamaOk: false,
  ollamaModels: [],
  lastError: null,
  lastRegisteredAt: null,
};


// ── Single-instance lock ──────────────────────────────────────────────────
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (setupWindow) {
      if (setupWindow.isMinimized()) setupWindow.restore();
      setupWindow.show();
      setupWindow.focus();
    }
  });
}


// ── Hide from Dock on Mac so we're truly background-only ──────────────────
if (process.platform === 'darwin' && app.dock) {
  app.dock.hide();
}


// ── Setup window (only opens when no token saved) ─────────────────────────
function openSetupWindow() {
  if (setupWindow) {
    setupWindow.show();
    setupWindow.focus();
    return;
  }
  setupWindow = new BrowserWindow({
    width: 540, height: 640,
    resizable: false,
    title: 'NexusAgent Privacy Bridge — Setup',
    autoHideMenuBar: true,
    show: false,
    backgroundColor: '#0F172A',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  setupWindow.once('ready-to-show', () => setupWindow.show());
  setupWindow.on('closed', () => { setupWindow = null; });
  setupWindow.loadFile(path.join(__dirname, 'setup.html'));
}


// ── Periodic re-registration with the SaaS ────────────────────────────────
let reregisterTimer = null;

async function registerNow() {
  const cfg = settings.load();
  if (!cfg.token || !cfg.base) {
    state.status = 'needs-setup';
    refreshTray();
    return;
  }
  if (!state.tunnelUrl) {
    state.status = 'starting';
    refreshTray();
    return;
  }
  try {
    const url = cfg.base.replace(/\/$/, '') + '/api/privacy-bridge/register';
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: cfg.token,
        endpoint_url: state.tunnelUrl,
        ollama_models: state.ollamaModels,
      }),
    });
    if (!res.ok) {
      const text = await res.text();
      state.status = 'bridge-down';
      state.lastError = `register HTTP ${res.status}: ${text.slice(0, 120)}`;
      refreshTray();
      return;
    }
    const data = await res.json();
    state.status = data.status === 'healthy' ? 'registered' : 'bridge-down';
    state.lastError = data.ping_error || null;
    state.lastRegisteredAt = new Date().toISOString();
    refreshTray();
  } catch (e) {
    state.status = 'bridge-down';
    state.lastError = String(e.message || e);
    refreshTray();
  }
}


function startReregisterLoop() {
  if (reregisterTimer) return;
  reregisterTimer = setInterval(registerNow, 5 * 60 * 1000);
}


// ── Bridge lifecycle ──────────────────────────────────────────────────────
async function startBridge() {
  // 1. Verify Ollama is up
  const probe = await ollama.probeOllama();
  state.ollamaOk = probe.online;
  state.ollamaModels = probe.models || [];
  if (!probe.online) {
    state.status = 'needs-setup';
    state.lastError = 'Ollama is not running. Install from ollama.com';
    refreshTray();
    // Open the download page automatically in the browser — friendly nudge
    if (process.platform !== 'linux') {
      shell.openExternal('https://ollama.com/download');
    }
    notify('Ollama not detected', 'Install Ollama from ollama.com to enable Privacy Mode.');
    return;
  }

  // 2. Start the tunnel
  try {
    state.status = 'starting';
    refreshTray();
    const url = await tunnel.start({
      localUrl: 'http://127.0.0.1:11434',
      onUrl: async (newUrl) => {
        state.tunnelUrl = newUrl;
        state.status = 'tunnel-up';
        refreshTray();
        await registerNow();
      },
      onExit: (code) => {
        state.tunnelUrl = null;
        state.status = 'bridge-down';
        state.lastError = `cloudflared exited (code ${code})`;
        refreshTray();
        notify('Privacy Bridge tunnel disconnected',
               'Will retry automatically. Check NexusAgent settings if this persists.');
        // Auto-restart tunnel after 10 sec
        setTimeout(startBridge, 10_000);
      },
    });
  } catch (e) {
    state.status = 'bridge-down';
    state.lastError = String(e.message || e);
    refreshTray();
    notify('Cloudflared not installed',
           'NexusAgent Privacy Bridge needs Cloudflare Tunnel. Click the tray icon for help.');
    if (process.platform !== 'linux') {
      shell.openExternal('https://github.com/cloudflare/cloudflared/releases');
    }
  }
}


function stopBridge() {
  tunnel.stop();
  if (reregisterTimer) {
    clearInterval(reregisterTimer);
    reregisterTimer = null;
  }
  state.tunnelUrl = null;
  state.status = 'starting';
  refreshTray();
}


// ── Tray refresh helper ────────────────────────────────────────────────────
function refreshTray() {
  if (!tray) return;
  tray.setToolTip(trayMod.tooltipFor(state));
  tray.setImage(trayMod.iconFor(state));
  tray.setContextMenu(trayMod.menuFor(state, {
    openSetup: openSetupWindow,
    restart:   () => { stopBridge(); startBridge(); },
    quit:      () => { stopBridge(); app.quit(); },
    openDashboard: () => {
      const cfg = settings.load();
      if (cfg.base) shell.openExternal(cfg.base + '/settings/privacy-mode');
    },
    revoke: async () => {
      stopBridge();
      settings.save({ token: '', base: '' });
      notify('Privacy Bridge stopped',
             'Sensitive prompts will fall back to cloud-with-redaction.');
      openSetupWindow();
    },
  }));
}


function notify(title, body) {
  if (Notification.isSupported()) {
    new Notification({ title, body, silent: true }).show();
  }
}


// ── Auto-start at login (configurable from tray) ──────────────────────────
function ensureAutoStart() {
  const cfg = settings.load();
  if (cfg.autostart === false) return;
  if (process.platform === 'win32' || process.platform === 'darwin') {
    app.setLoginItemSettings({ openAtLogin: true, openAsHidden: true });
  }
  // Linux: user has to set up systemd/Desktop Entry themselves; we don't
  // touch their session config from an Electron app.
}


// ── IPC from setup window ─────────────────────────────────────────────────
ipcMain.handle('settings:save', (_evt, payload) => {
  settings.save(payload);
  return { ok: true };
});
ipcMain.handle('settings:load', () => settings.load());
ipcMain.handle('bridge:restart', () => {
  stopBridge();
  startBridge();
  return { ok: true };
});
ipcMain.handle('ollama:probe', () => ollama.probeOllama());
ipcMain.handle('ollama:pull', async (_evt, modelName) => {
  return ollama.pullModelOnce(modelName);
});


// ── App lifecycle ─────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  ensureAutoStart();

  tray = new Tray(trayMod.iconFor(state));
  refreshTray();

  startReregisterLoop();

  const cfg = settings.load();
  if (!cfg.token || !cfg.base) {
    state.status = 'needs-setup';
    refreshTray();
    openSetupWindow();
  } else {
    await startBridge();
  }
});

// Don't quit when all windows close — we're a tray-only app
app.on('window-all-closed', (e) => {
  e.preventDefault();
});

app.on('before-quit', () => {
  stopBridge();
});
