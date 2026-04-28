/**
 * NexusAgent desktop — main process entry point.
 *
 * Packages the React frontend as a native app with:
 *   - First-run setup wizard (Ollama detect → model pull → backend probe)
 *   - Single-instance lock (second launch focuses the running window)
 *   - System tray with menu actions
 *   - Global hotkey (Cmd/Ctrl+Shift+N) to focus/toggle the window
 *   - Native notifications via IPC from the renderer
 *   - Hardened webPreferences (no node integration, context-isolated preload)
 *
 * Renderer URL:
 *   - DEV:  process.env.NEXUS_DEV_URL (default http://localhost:5173)
 *   - PROD: file://<app>/frontend/dist/index.html bundled next to this file
 *
 * Boot order:
 *   1. app.whenReady
 *   2. setup.registerIpc()
 *   3. if setup-complete marker is missing → openSetupWindow(); else
 *      directly createWindow().
 *   4. tray + hotkey come up regardless.
 */
'use strict';

const { app, BrowserWindow, Tray, Menu, globalShortcut, ipcMain,
        Notification, shell, nativeImage } = require('electron');
const path = require('node:path');

const { buildTrayMenu } = require('./tray');
const { registerHotkeys, unregisterHotkeys } = require('./hotkey');
const { probeOllama } = require('./ollama');
const setup = require('./setup');

const isDev = !!process.env.NEXUS_DEV_URL || !app.isPackaged;
const DEV_URL = process.env.NEXUS_DEV_URL || 'http://localhost:5173';
const BACKEND_URL = process.env.NEXUS_BACKEND_URL || 'http://localhost:8000';

let mainWindow = null;
let tray = null;

// ── Single-instance lock ────────────────────────────────────────────────────
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      if (!mainWindow.isVisible()) mainWindow.show();
      mainWindow.focus();
    }
  });
}


function createWindow() {
  if (mainWindow) {
    mainWindow.show();
    mainWindow.focus();
    return;
  }
  mainWindow = new BrowserWindow({
    width: 1380,
    height: 860,
    minWidth: 960,
    minHeight: 600,
    backgroundColor: '#0a0b0f',
    show: false,
    title: 'NexusAgent',
    icon: path.join(__dirname, 'assets', 'icon.png'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      // Let the renderer reach the local backend + local assets only.
      webSecurity: true,
    },
  });

  const target = isDev
    ? DEV_URL
    : `file://${path.join(__dirname, '..', 'frontend', 'dist', 'index.html')}`;
  mainWindow.loadURL(target).catch((e) => {
    console.error('[NexusAgent] Failed to load renderer:', e);
  });

  mainWindow.once('ready-to-show', () => mainWindow.show());

  // Open external links in the default browser, never in an in-app webview.
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (!url.startsWith('http://localhost') && !url.startsWith('file://')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'deny' };
  });

  // Minimize-to-tray on close (keeps agents running in the background).
  mainWindow.on('close', (e) => {
    if (!app.isQuittingForReal) {
      e.preventDefault();
      mainWindow.hide();
    }
  });

  mainWindow.on('closed', () => { mainWindow = null; });
}


function toggleWindow() {
  if (!mainWindow) return createWindow();
  if (mainWindow.isVisible() && mainWindow.isFocused()) {
    mainWindow.hide();
  } else {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.show();
    mainWindow.focus();
  }
}


function setupTray() {
  const iconPath = path.join(__dirname, 'assets', 'tray.png');
  let image;
  try {
    image = nativeImage.createFromPath(iconPath);
  } catch {
    image = nativeImage.createEmpty();
  }
  tray = new Tray(image);
  tray.setToolTip('NexusAgent — private AI business OS');
  const refresh = async () => {
    const baseMenu = await buildTrayMenu({
      toggle: toggleWindow,
      quit: () => {
        app.isQuittingForReal = true;
        app.quit();
      },
      backendUrl: BACKEND_URL,
    });
    // Append a "Re-run setup wizard" item.
    const menu = baseMenu.slice();
    menu.splice(menu.length - 1, 0, {
      label: 'Re-run setup wizard…',
      click: () => {
        setup.resetSetup();
        setup.openSetupWindow({ onDone: () => createWindow() });
      },
    });
    tray.setContextMenu(Menu.buildFromTemplate(menu));
  };
  refresh();
  // Refresh the menu every 30s so "X pending approvals" stays live.
  setInterval(refresh, 30_000);
  tray.on('click', () => toggleWindow());
}


// ── IPC bridge ──────────────────────────────────────────────────────────────
ipcMain.handle('nexus:notify', (_evt, { title, body, urgent }) => {
  try {
    const n = new Notification({
      title: title || 'NexusAgent',
      body: body || '',
      urgency: urgent ? 'critical' : 'normal',
    });
    n.on('click', () => toggleWindow());
    n.show();
    return { ok: true };
  } catch (e) {
    return { ok: false, error: String(e) };
  }
});

ipcMain.handle('nexus:ollama/probe', async () => {
  return probeOllama();
});

ipcMain.handle('nexus:open-external', (_evt, url) => {
  if (typeof url === 'string' && /^https?:\/\//i.test(url)) {
    shell.openExternal(url);
    return { ok: true };
  }
  return { ok: false, error: 'Invalid URL' };
});


// ── App lifecycle ───────────────────────────────────────────────────────────
app.whenReady().then(() => {
  setup.registerIpc();

  if (setup.isSetupComplete()) {
    createWindow();
  } else {
    setup.openSetupWindow({ onDone: () => createWindow() });
  }

  setupTray();
  registerHotkeys({
    toggle: toggleWindow,
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      if (setup.isSetupComplete()) createWindow();
      else setup.openSetupWindow({ onDone: () => createWindow() });
    }
  });
});

app.on('will-quit', () => {
  unregisterHotkeys();
});

app.on('window-all-closed', () => {
  // Keep the tray alive on macOS/Win so background agents stay active.
  if (process.platform === 'darwin') return;
  // On Windows/Linux we also keep running in the tray unless user quit explicitly.
  if (!app.isQuittingForReal) return;
  app.quit();
});
