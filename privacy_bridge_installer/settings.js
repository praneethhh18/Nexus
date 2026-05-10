/**
 * Tiny JSON-on-disk settings store.
 *
 * Lives in Electron's per-user "userData" directory, which on each OS is:
 *   - Win:   %APPDATA%\NexusAgent Privacy Bridge\settings.json
 *   - Mac:   ~/Library/Application Support/NexusAgent Privacy Bridge/settings.json
 *   - Linux: ~/.config/NexusAgent Privacy Bridge/settings.json
 *
 * Why not electron-store? One file, ~30 lines, zero dependencies — keeps
 * the installer small and the dependency surface tiny.
 *
 * Schema:
 *   {
 *     token:     "pb_xxx",                          // from Settings → Privacy Mode
 *     base:      "https://app.nexusagent.in",       // SaaS base URL
 *     model:     "llama3.1:8b",                     // preferred model
 *     autostart: true,                              // launch at login
 *   }
 */
'use strict';

const { app } = require('electron');
const fs = require('node:fs');
const path = require('node:path');

const DEFAULTS = {
  token: '',
  base: 'https://app.nexusagent.in',
  model: 'llama3.1:8b',
  autostart: true,
};

function settingsPath() {
  return path.join(app.getPath('userData'), 'settings.json');
}

function load() {
  try {
    const raw = fs.readFileSync(settingsPath(), 'utf8');
    return { ...DEFAULTS, ...JSON.parse(raw) };
  } catch {
    return { ...DEFAULTS };
  }
}

function save(patch) {
  const merged = { ...load(), ...patch };
  const file = settingsPath();
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify(merged, null, 2), 'utf8');
  return merged;
}

module.exports = { load, save, settingsPath };
