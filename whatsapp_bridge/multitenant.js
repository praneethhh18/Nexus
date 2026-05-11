/**
 * Multi-tenant WhatsApp bridge — each NexusAgent business connects ITS OWN
 * WhatsApp account via QR scan from the web UI.
 *
 * This module lives ALONGSIDE server.js's existing single-tenant flow. The
 * legacy flow (one shared bridge, scan QR in terminal) keeps working unchanged
 * for dev/test. Anything in this file is opt-in via the multi-tenant HTTP
 * endpoints exposed below.
 *
 * Architecture:
 *   - One `WABusinessInstance` per business_id.
 *   - Each instance has its own Baileys socket + auth dir at
 *     `auth/biz/<business_id>/`.
 *   - QR codes are NOT printed to terminal — they're returned via the HTTP
 *     status endpoint as raw strings the frontend converts to images.
 *   - Inbound messages from any instance forward to NexusAgent with their
 *     business_id baked into the webhook payload, so the backend routes
 *     to the right tenant.
 *
 * HTTP endpoints (mounted by server.js):
 *   POST /tenant/:businessId/connect      → start a new connection (idempotent)
 *   GET  /tenant/:businessId/status       → { status, qr?, profile? }
 *   POST /tenant/:businessId/disconnect   → logout + wipe auth dir
 *   POST /tenant/:businessId/send         → { to, text }
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import pino from 'pino';
import fetch from 'node-fetch';
import makeWASocket, {
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
  downloadMediaMessage,
} from '@whiskeysockets/baileys';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const NEXUS_API_URL = (process.env.NEXUS_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const NEXUS_WEBHOOK_SECRET = process.env.NEXUS_WEBHOOK_SECRET || '';
const AUTH_DIR_BASE = process.env.WA_AUTH_DIR
  ? path.join(process.env.WA_AUTH_DIR, 'biz')
  : path.join(__dirname, 'auth', 'biz');

const logger = pino({ level: process.env.LOG_LEVEL || 'warn' });

/**
 * One Baileys instance scoped to a single NexusAgent business.
 * Tracks its own connection state, QR, and recent messages.
 */
class WABusinessInstance {
  constructor(businessId) {
    this.businessId = businessId;
    this.authDir = path.join(AUTH_DIR_BASE, businessId);
    this.sock = null;
    this.status = 'idle';   // idle | qr_pending | connecting | connected | disconnected | logged_out
    this.qr = null;
    this.profile = null;
    this.lastError = null;
    this.lastUpdate = Date.now();
  }

  _setStatus(status, extra = {}) {
    this.status = status;
    this.lastUpdate = Date.now();
    if ('qr' in extra) this.qr = extra.qr;
    if ('profile' in extra) this.profile = extra.profile;
    if ('lastError' in extra) this.lastError = extra.lastError;
  }

  /** Start (or resume) the Baileys connection. Safe to call multiple times. */
  async start() {
    if (this.sock && this.status === 'connected') return;
    if (!fs.existsSync(this.authDir)) {
      fs.mkdirSync(this.authDir, { recursive: true });
    }
    const { state, saveCreds } = await useMultiFileAuthState(this.authDir);
    const { version } = await fetchLatestBaileysVersion();

    this._setStatus('connecting');

    const sock = makeWASocket({
      version,
      auth: state,
      logger,
      printQRInTerminal: false,
      browser: ['NexusAgent', 'Chrome', '1.0.0'],
      syncFullHistory: false,
    });
    this.sock = sock;

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', (update) => {
      const { connection, lastDisconnect, qr } = update;
      if (qr) {
        // QR appears on first connect AND every ~30s until scanned.
        // Frontend polls status; renders qr as an image client-side.
        this._setStatus('qr_pending', { qr });
        console.log(`[wa-mt:${this.businessId}] QR ready`);
      }
      if (connection === 'open') {
        const phone = (sock.user?.id || '').split(':')[0];
        const name  = sock.user?.name || '';
        this._setStatus('connected', {
          qr: null,
          profile: { phone, name, linked_at: new Date().toISOString() },
        });
        console.log(`[wa-mt:${this.businessId}] ✅ connected as ${phone}`);
      }
      if (connection === 'close') {
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        const loggedOut = statusCode === DisconnectReason.loggedOut;
        const errMsg = lastDisconnect?.error?.message || `code=${statusCode}`;
        if (loggedOut) {
          this._setStatus('logged_out', { qr: null, lastError: errMsg });
          // Auth state still on disk — caller may want to delete it via
          // /disconnect to allow a fresh QR scan with a different number.
          console.log(`[wa-mt:${this.businessId}] logged out (${errMsg})`);
        } else {
          this._setStatus('disconnected', { lastError: errMsg });
          console.log(`[wa-mt:${this.businessId}] disconnected (${errMsg}). Reconnect in 3s.`);
          setTimeout(() => this.start().catch(e => {
            console.error(`[wa-mt:${this.businessId}] reconnect failed:`, e.message);
          }), 3000);
        }
      }
    });

    sock.ev.on('messages.upsert', async ({ messages, type }) => {
      if (type !== 'notify') return;
      for (const msg of messages) {
        await this._handleIncoming(msg).catch(e => {
          console.error(`[wa-mt:${this.businessId}] message handler error:`, e);
        });
      }
    });
  }

  /** Tear down + delete auth dir so a fresh QR scan can pair a new number. */
  async logout({ wipeAuth = true } = {}) {
    try {
      if (this.sock) {
        await this.sock.logout().catch(() => {});
      }
    } finally {
      this.sock = null;
      this._setStatus('disconnected', { qr: null, profile: null });
      if (wipeAuth && fs.existsSync(this.authDir)) {
        // Recursive removal — fs.rmSync needs Node 14+
        try {
          fs.rmSync(this.authDir, { recursive: true, force: true });
        } catch (e) {
          console.warn(`[wa-mt:${this.businessId}] auth dir cleanup failed:`, e.message);
        }
      }
    }
  }

  /** Send a text message to a phone. Throws if not yet connected. */
  async send(to, text) {
    if (!this.sock || this.status !== 'connected') {
      const err = new Error(`Not connected (status=${this.status})`);
      err.code = 'NOT_CONNECTED';
      throw err;
    }
    const digits = String(to).replace(/[^0-9]/g, '');
    if (!digits) throw new Error('Invalid `to` number');
    const jid = `${digits}@s.whatsapp.net`;
    await this.sock.sendMessage(jid, { text: String(text) });
  }

  /** Public snapshot for the /status endpoint. */
  snapshot() {
    return {
      business_id: this.businessId,
      status: this.status,
      qr: this.status === 'qr_pending' ? this.qr : null,
      profile: this.profile,
      last_error: this.lastError,
      last_update: this.lastUpdate,
    };
  }

  /**
   * Forward an inbound message to NexusAgent, tagged with this instance's
   * business_id so the backend routes to the correct tenant.
   */
  async _handleIncoming(msg) {
    if (!msg.message || msg.key.fromMe) return;
    const jid = msg.key.remoteJid || '';
    if (jid.endsWith('@g.us') || jid === 'status@broadcast') return;  // DMs only

    const m = msg.message;
    const text = m.conversation
              || m.extendedTextMessage?.text
              || m.videoMessage?.caption
              || '';
    if (!text) {
      // Media handling deferred to v2 of multi-tenant — for now we only
      // pass text. Audio/document follows the same path as legacy server.js
      // but routed per-business.
      return;
    }

    const senderPn = msg.key?.senderPn;
    const phone = (typeof senderPn === 'string' && senderPn.includes('@'))
                ? senderPn.split('@')[0]
                : jid.split('@')[0];

    console.log(`[wa-mt:${this.businessId}] ⇐ ${phone}: ${text.slice(0, 80)}`);

    let reply;
    try {
      const res = await fetch(`${NEXUS_API_URL}/api/whatsapp/inbound`, {
        method: 'POST',
        headers: {
          'Content-Type':   'application/json',
          'X-Nexus-Secret': NEXUS_WEBHOOK_SECRET,
        },
        body: JSON.stringify({
          from:        phone,
          text,
          message_id:  msg.key.id || '',
          business_id: this.businessId,  // ← tenant routing
        }),
        signal: AbortSignal.timeout(600_000),
      });
      if (!res.ok) {
        const err = await res.text();
        reply = { text: `⚠️ Backend error (${res.status}): ${err.slice(0, 200)}` };
      } else {
        reply = await res.json();
      }
    } catch (e) {
      reply = { text: `⚠️ Couldn't reach NexusAgent backend: ${e.message}` };
    }

    if (reply?.silent) return;
    if (reply?.text) {
      try {
        await this.sock.sendMessage(jid, { text: reply.text });
      } catch (e) {
        console.error(`[wa-mt:${this.businessId}] reply send failed:`, e.message);
      }
    }
  }
}


// ── Bridge registry ────────────────────────────────────────────────────────
const instances = new Map();   // business_id → WABusinessInstance

/** Get-or-create an instance for a business. Doesn't auto-connect. */
function instanceFor(businessId) {
  if (!businessId) throw new Error('business_id required');
  let inst = instances.get(businessId);
  if (!inst) {
    inst = new WABusinessInstance(businessId);
    instances.set(businessId, inst);
  }
  return inst;
}


// ── HTTP handler — mounted by server.js ────────────────────────────────────
/**
 * Returns true if `req` matches one of the multi-tenant routes and is
 * handled fully (response written). Otherwise returns false so server.js
 * can fall through to its legacy handlers.
 *
 * Routes:
 *   POST /tenant/:id/connect
 *   GET  /tenant/:id/status
 *   POST /tenant/:id/disconnect
 *   POST /tenant/:id/send         { to, text }
 */
export async function handleMultiTenantRequest(req, res) {
  const url = req.url || '';
  const m = url.match(/^\/tenant\/([^/]+)\/(connect|status|disconnect|send)$/);
  if (!m) return false;

  const businessId = decodeURIComponent(m[1]);
  const action = m[2];
  const method = req.method;

  const writeJson = (code, body) => {
    res.writeHead(code, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(body));
  };

  try {
    if (action === 'connect' && method === 'POST') {
      const inst = instanceFor(businessId);
      await inst.start();
      writeJson(200, inst.snapshot());
      return true;
    }

    if (action === 'status' && method === 'GET') {
      const inst = instances.get(businessId);
      if (!inst) {
        writeJson(200, {
          business_id: businessId, status: 'idle', qr: null, profile: null,
        });
        return true;
      }
      writeJson(200, inst.snapshot());
      return true;
    }

    if (action === 'disconnect' && method === 'POST') {
      const inst = instances.get(businessId);
      if (inst) {
        await inst.logout({ wipeAuth: true });
        instances.delete(businessId);
      }
      writeJson(200, { ok: true, business_id: businessId, status: 'disconnected' });
      return true;
    }

    if (action === 'send' && method === 'POST') {
      const inst = instances.get(businessId);
      if (!inst) {
        writeJson(503, { ok: false, error: 'Business not connected' });
        return true;
      }
      let body = '';
      req.on('data', d => { body += d; });
      await new Promise(resolve => req.on('end', resolve));
      let payload;
      try {
        payload = JSON.parse(body);
      } catch {
        writeJson(400, { ok: false, error: 'Invalid JSON' });
        return true;
      }
      const { to, text } = payload;
      if (!to || !text) {
        writeJson(400, { ok: false, error: '`to` and `text` required' });
        return true;
      }
      try {
        await inst.send(to, text);
        writeJson(200, { ok: true });
      } catch (e) {
        const code = e.code === 'NOT_CONNECTED' ? 503 : 500;
        writeJson(code, { ok: false, error: e.message });
      }
      return true;
    }

    writeJson(405, { ok: false, error: 'Method not allowed' });
    return true;
  } catch (e) {
    console.error(`[wa-mt] handler error for ${url}:`, e);
    writeJson(500, { ok: false, error: e.message });
    return true;
  }
}

/**
 * Boot any existing per-business sessions on bridge start. Looks at every
 * subdir under auth/biz/ and resumes its connection if creds exist.
 * Lets ops restart the bridge process without making every tenant re-scan.
 */
export async function resumeAllSessions() {
  if (!fs.existsSync(AUTH_DIR_BASE)) return [];
  const resumed = [];
  for (const name of fs.readdirSync(AUTH_DIR_BASE)) {
    const dir = path.join(AUTH_DIR_BASE, name);
    if (!fs.statSync(dir).isDirectory()) continue;
    // Heuristic: if creds.json exists, this session was paired previously.
    if (!fs.existsSync(path.join(dir, 'creds.json'))) continue;
    try {
      const inst = instanceFor(name);
      await inst.start();
      resumed.push(name);
    } catch (e) {
      console.error(`[wa-mt] resume failed for ${name}:`, e.message);
    }
  }
  if (resumed.length) {
    console.log(`[wa-mt] resumed ${resumed.length} session(s): ${resumed.join(', ')}`);
  }
  return resumed;
}
