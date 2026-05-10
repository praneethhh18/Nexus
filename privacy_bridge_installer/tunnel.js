/**
 * Cloudflare Tunnel subprocess management.
 *
 * Uses cloudflared's "quick tunnel" mode (`cloudflared tunnel --url <local>`)
 * which:
 *   - Doesn't need a Cloudflare account or auth
 *   - Returns an https://*.trycloudflare.com URL
 *   - Is FREE forever
 *   - Tunnel persists for the lifetime of the cloudflared process
 *
 * We look for the cloudflared binary in this order:
 *   1. Bundled inside the app under resources/bin/<os>/<arch>/cloudflared
 *      (electron-builder ships it via extraResources — see package.json)
 *   2. ./bin/cloudflared (dev mode)
 *   3. PATH (fallback to user-installed cloudflared)
 *
 * If none found, throw — main.js opens the download page in their browser.
 */
'use strict';

const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

let proc = null;


function bundledBinaryPath() {
  // electron-builder copies extraResources to process.resourcesPath/bin/
  const ext = process.platform === 'win32' ? '.exe' : '';
  const candidates = [
    process.resourcesPath ? path.join(process.resourcesPath, 'bin', 'cloudflared' + ext) : null,
    path.join(__dirname, 'bin', 'cloudflared' + ext),
  ].filter(Boolean);
  for (const p of candidates) {
    try { fs.accessSync(p, fs.constants.X_OK); return p; } catch { /* not found */ }
  }
  return null;
}


function resolveCloudflared() {
  // Prefer bundled. Fall through to PATH (`cloudflared` command).
  return bundledBinaryPath() || 'cloudflared';
}


function start({ localUrl, onUrl, onExit }) {
  return new Promise((resolve, reject) => {
    if (proc) {
      try { proc.kill(); } catch { /* already dead */ }
      proc = null;
    }
    const bin = resolveCloudflared();
    const args = ['tunnel', '--url', localUrl, '--no-autoupdate'];

    let child;
    try {
      child = spawn(bin, args, { stdio: ['ignore', 'pipe', 'pipe'] });
    } catch (e) {
      return reject(new Error(`cloudflared not found: ${e.message}`));
    }

    proc = child;
    let urlEmitted = false;
    let stderrBuf = '';

    const handleLine = (line) => {
      // Quick-tunnel URL appears on stderr, e.g.
      //   2025-XX-XX INF |  https://xxx.trycloudflare.com  |
      const m = line.match(/(https:\/\/[a-z0-9-]+\.trycloudflare\.com)/);
      if (m && !urlEmitted) {
        urlEmitted = true;
        onUrl(m[1]);
        resolve(m[1]);
      }
    };

    child.stderr.on('data', (chunk) => {
      stderrBuf += chunk.toString('utf8');
      let i;
      while ((i = stderrBuf.indexOf('\n')) !== -1) {
        handleLine(stderrBuf.slice(0, i));
        stderrBuf = stderrBuf.slice(i + 1);
      }
    });

    child.on('exit', (code) => {
      proc = null;
      if (!urlEmitted) {
        reject(new Error(`cloudflared exited (code ${code}) before tunnel was up`));
      }
      try { onExit(code); } catch { /* fall through */ }
    });

    child.on('error', (err) => {
      proc = null;
      // Most common: ENOENT — cloudflared binary missing from PATH AND not bundled
      if (err.code === 'ENOENT') {
        reject(new Error('cloudflared not installed and not bundled with this build'));
      } else {
        reject(err);
      }
    });

    // Safety: if we don't see a URL within 30 sec, give up
    setTimeout(() => {
      if (!urlEmitted) {
        try { child.kill(); } catch { /* dead already */ }
        reject(new Error('cloudflared did not emit a tunnel URL within 30s'));
      }
    }, 30_000);
  });
}


function stop() {
  if (proc) {
    try { proc.kill(); } catch { /* already dead */ }
    proc = null;
  }
}


function isRunning() {
  return proc !== null;
}


module.exports = { start, stop, isRunning };
