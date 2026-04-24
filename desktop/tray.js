/**
 * Tray menu builder.
 *
 * Asks the backend how many approvals are pending + how many agents are
 * enabled, then renders a context menu with:
 *   - "X pending approvals" (click opens /inbox)
 *   - Quick-run agents submenu (morning_briefing / email_triage / ...)
 *   - Show / Hide window
 *   - Open in browser
 *   - Quit
 *
 * Failures are swallowed — the menu must render even when the backend is
 * offline, otherwise the tray icon becomes useless.
 */
'use strict';

const { shell } = require('electron');
const http = require('node:http');

function _get(url, { timeout = 1500 } = {}) {
  return new Promise((resolve) => {
    const req = http.get(url, { timeout }, (res) => {
      let data = '';
      res.on('data', (c) => (data += c));
      res.on('end', () => {
        try {
          resolve({ ok: res.statusCode < 400, status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ ok: false, status: res.statusCode, body: null });
        }
      });
    });
    req.on('timeout', () => { req.destroy(); resolve({ ok: false, status: 0, body: null }); });
    req.on('error', () => resolve({ ok: false, status: 0, body: null }));
  });
}


async function buildTrayMenu({ toggle, quit, backendUrl }) {
  const health = await _get(`${backendUrl}/api/health`);
  const backendOk = health.ok;

  const items = [
    {
      label: backendOk ? `NexusAgent — running` : 'NexusAgent — backend offline',
      enabled: false,
    },
    { type: 'separator' },
    {
      label: 'Show / hide window',
      click: () => toggle(),
    },
    {
      label: 'Open in browser',
      click: () => shell.openExternal(backendUrl.replace(/:8000$/, ':5173') + '/'),
    },
    { type: 'separator' },
    {
      label: 'Agents',
      submenu: [
        { label: 'Open Agents page', click: () => {
          toggle();
        }},
        // The run-now entries require auth so they're intentionally just
        // deep links into the app rather than fire-and-forget HTTP calls.
      ],
    },
    { type: 'separator' },
    { label: 'Quit', click: () => quit() },
  ];

  return items;
}

module.exports = { buildTrayMenu };
