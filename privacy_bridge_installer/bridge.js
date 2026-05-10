#!/usr/bin/env node
/**
 * NexusAgent Privacy Bridge
 * ─────────────────────────────────────────────────────────────────────────
 * Runs on the customer's laptop. Three jobs:
 *   1. Verify Ollama is running locally + has a usable model
 *   2. Start a Cloudflare Tunnel to expose localhost:11434 publicly (HTTPS)
 *   3. Register that tunnel URL with NexusAgent's SaaS backend so sensitive
 *      AI prompts route to THIS laptop instead of cloud LLM
 *
 * Customer flow:
 *   1. Install Ollama from ollama.com (one-time)
 *   2. ollama pull llama3.1:8b           (one-time, ~5 GB download)
 *   3. Install cloudflared (instructions below)
 *   4. Get a registration token from app.nexusagent.in → Settings → Privacy Mode
 *   5. Run:  node bridge.js --token pb_xxx --base https://app.nexusagent.in
 *   6. Leave this terminal open. Sensitive prompts now use YOUR laptop.
 *
 * On first run, prints a setup checklist if anything is missing.
 *
 * Why a CLI script (not an Electron app):
 *   The polished tray-icon Electron version is on the roadmap. This CLI
 *   ships the moment the backend is ready and gives developer-friendly
 *   customers an immediate way to test the privacy story end-to-end.
 *
 * Dependencies (zero npm installs needed):
 *   - Node.js 18+ (built-in fetch + child_process)
 *   - Ollama running on localhost:11434
 *   - cloudflared on PATH  (Cloudflare Tunnel CLI — free, no account needed
 *     for "quick tunnels")
 */
'use strict';

const { spawn } = require('node:child_process');
const http = require('node:http');

const OLLAMA_HOST = process.env.OLLAMA_HOST || 'http://127.0.0.1:11434';
const POLL_INTERVAL_MS = 5 * 60 * 1000;  // re-register URL every 5 min in case it changes


// ── tiny CLI parser ───────────────────────────────────────────────────────
function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--token')         out.token = argv[++i];
    else if (a === '--base')     out.base  = argv[++i];
    else if (a === '--model')    out.model = argv[++i];
    else if (a === '--help' || a === '-h') out.help = true;
  }
  return out;
}


function printUsage() {
  console.log(`
NexusAgent Privacy Bridge

Usage:
  node bridge.js --token <pb_xxx> --base <https://app.nexusagent.in> [--model llama3.1:8b]

Required:
  --token   Registration token from app.nexusagent.in → Settings → Privacy Mode
  --base    Your NexusAgent server URL (production: https://app.nexusagent.in)

Optional:
  --model   Ollama model to verify is installed (default: llama3.1:8b)

Setup checklist (one-time):
  1. Install Ollama:               https://ollama.com/download
  2. Pull a model:                 ollama pull llama3.1:8b
  3. Install Cloudflare Tunnel:    https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
  4. Get a token from app.nexusagent.in → Settings → Privacy Mode

Then keep this terminal open while you want privacy mode active.
`);
}


// ── Ollama health check ───────────────────────────────────────────────────
function probeOllama() {
  return new Promise((resolve) => {
    const req = http.request(OLLAMA_HOST + '/api/tags', { timeout: 3000 }, (res) => {
      if (res.statusCode !== 200) {
        resolve({ ok: false, error: `HTTP ${res.statusCode}` });
        return;
      }
      let buf = '';
      res.on('data', (c) => (buf += c));
      res.on('end', () => {
        try {
          const data = JSON.parse(buf);
          resolve({
            ok: true,
            models: (data.models || []).map((m) => m.name),
          });
        } catch (e) {
          resolve({ ok: false, error: 'malformed response from Ollama' });
        }
      });
    });
    req.on('timeout', () => { req.destroy(); resolve({ ok: false, error: 'timeout — is `ollama serve` running?' }); });
    req.on('error', (e) => resolve({ ok: false, error: String(e.message || e) }));
    req.end();
  });
}


// ── Cloudflare Tunnel (quick mode, no account required) ───────────────────
function startCloudflareTunnel(localUrl, onUrl, onExit) {
  console.log(`[bridge] starting Cloudflare Tunnel → ${localUrl}`);
  // `cloudflared tunnel --url <local>` prints the assigned trycloudflare.com
  // URL on stderr, then keeps the tunnel running. Quick tunnels are HTTPS
  // and don't need a Cloudflare account.
  const proc = spawn('cloudflared', ['tunnel', '--url', localUrl, '--no-autoupdate'], {
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  let urlEmitted = false;
  const handleLine = (line) => {
    // Cloudflare prints lines like:
    //   2025-XX-XX INF |  https://random-name.trycloudflare.com  |
    const match = line.match(/(https:\/\/[a-z0-9-]+\.trycloudflare\.com)/);
    if (match && !urlEmitted) {
      urlEmitted = true;
      onUrl(match[1]);
    }
  };

  let stderrBuf = '';
  proc.stderr.on('data', (chunk) => {
    stderrBuf += chunk.toString('utf8');
    let idx;
    while ((idx = stderrBuf.indexOf('\n')) !== -1) {
      handleLine(stderrBuf.slice(0, idx));
      stderrBuf = stderrBuf.slice(idx + 1);
    }
  });

  proc.on('exit', (code) => {
    console.log(`[bridge] cloudflared exited (code ${code})`);
    onExit(code);
  });

  proc.on('error', (err) => {
    if (err.code === 'ENOENT') {
      console.error('\n[bridge] ERROR: `cloudflared` is not installed or not on PATH.');
      console.error('Install it from:');
      console.error('  https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/');
      process.exit(2);
    }
    console.error('[bridge] cloudflared error:', err);
    process.exit(2);
  });

  return proc;
}


// ── Register the tunnel URL with the SaaS backend ─────────────────────────
async function registerWithSaaS(base, token, tunnelUrl, ollamaProbe) {
  const url = base.replace(/\/$/, '') + '/api/privacy-bridge/register';
  console.log(`[bridge] registering with ${url}`);
  const body = {
    token,
    endpoint_url: tunnelUrl,
    ollama_models: ollamaProbe.models || [],
    ollama_version: '',
  };
  const r = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const text = await r.text();
  let data;
  try { data = JSON.parse(text); } catch { data = { raw: text }; }
  if (!r.ok) {
    console.error(`[bridge] registration FAILED (HTTP ${r.status}): ${data.detail || data.raw || text}`);
    return { ok: false };
  }
  console.log(`[bridge] ✓ registered. status: ${data.status}`);
  if (data.ping_error) {
    console.warn(`[bridge] ⚠ initial health check warning: ${data.ping_error}`);
  }
  return data;
}


// ── Main ──────────────────────────────────────────────────────────────────
async function main() {
  const args = parseArgs(process.argv);
  if (args.help || !args.token || !args.base) {
    printUsage();
    process.exit(args.help ? 0 : 1);
  }

  const expectedModel = args.model || 'llama3.1:8b';

  // 1. Probe Ollama
  console.log('[bridge] checking Ollama...');
  const probe = await probeOllama();
  if (!probe.ok) {
    console.error(`[bridge] Ollama not reachable at ${OLLAMA_HOST}: ${probe.error}`);
    console.error('  Install Ollama from https://ollama.com/download');
    console.error('  Then run:  ollama serve   (it usually auto-starts on Mac/Win)');
    process.exit(2);
  }
  const hasModel = probe.models.some((m) => m.startsWith(expectedModel));
  if (!hasModel) {
    console.warn(`[bridge] ⚠ ${expectedModel} not found in Ollama. Models present:`);
    probe.models.forEach((m) => console.warn(`    - ${m}`));
    console.warn(`  Pull it first:  ollama pull ${expectedModel}`);
    console.warn('  Continuing anyway — registration will succeed but inference will fail until you pull a model.');
  } else {
    console.log(`[bridge] ✓ Ollama ok, ${probe.models.length} model(s) available`);
  }

  // 2. Start Cloudflare Tunnel
  startCloudflareTunnel(OLLAMA_HOST, async (tunnelUrl) => {
    console.log(`[bridge] ✓ tunnel up: ${tunnelUrl}`);

    // 3. Register with the SaaS
    const reg = await registerWithSaaS(args.base, args.token, tunnelUrl, probe);
    if (!reg.ok) {
      console.error('[bridge] giving up — fix the registration error above and rerun');
      process.exit(3);
    }

    console.log('');
    console.log('─────────────────────────────────────────────────────────');
    console.log('Privacy Bridge is live.');
    console.log('  Tunnel : ' + tunnelUrl);
    console.log('  Models : ' + (probe.models.join(', ') || '(none yet)'));
    console.log('  Status : ' + (reg.status || 'registered'));
    console.log('');
    console.log('Sensitive AI prompts from your NexusAgent business will now');
    console.log('compute on THIS laptop. Keep this terminal open. Ctrl+C to');
    console.log('disconnect (sensitive prompts will fall back to cloud-with-redaction).');
    console.log('─────────────────────────────────────────────────────────');
    console.log('');

    // Re-register periodically. If the cloudflared URL is stable (same run)
    // this is a no-op, but it bumps last_pinged_at on the server side.
    setInterval(async () => {
      try {
        await registerWithSaaS(args.base, args.token, tunnelUrl, probe);
      } catch (e) {
        console.warn('[bridge] periodic re-register failed:', e.message || e);
      }
    }, POLL_INTERVAL_MS);
  }, (code) => {
    console.error(`[bridge] tunnel died with exit code ${code} — exiting`);
    process.exit(code || 1);
  });
}

main().catch((err) => {
  console.error('[bridge] fatal:', err);
  process.exit(1);
});
