/**
 * Global shortcut registration.
 *
 *   Cmd/Ctrl+Shift+N — toggle the main window from anywhere on the desktop.
 *
 * Registration is idempotent and failure-tolerant: if the accelerator is
 * already taken (another app grabbed it first), we log and move on rather
 * than preventing the app from starting.
 */
'use strict';

const { globalShortcut } = require('electron');

const ACCELERATOR = 'CommandOrControl+Shift+N';

function registerHotkeys({ toggle }) {
  try {
    const ok = globalShortcut.register(ACCELERATOR, () => {
      try { toggle(); } catch (e) { /* never let hotkey crash */ }
    });
    if (!ok) {
      // eslint-disable-next-line no-console
      console.warn(`[NexusAgent] Could not register ${ACCELERATOR} — already in use`);
    }
  } catch (e) {
    console.warn('[NexusAgent] hotkey register failed:', e);
  }
}

function unregisterHotkeys() {
  try { globalShortcut.unregisterAll(); } catch {}
}

module.exports = { registerHotkeys, unregisterHotkeys };
