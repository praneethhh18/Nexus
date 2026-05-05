/**
 * NexusAgent WhatsApp bridge.
 *
 * Connects to WhatsApp Web via Baileys, forwards every incoming text message
 * to the NexusAgent backend, and replies with whatever the agent returns —
 * including PDF / docx attachments.
 *
 * First run: scan the QR code printed in this terminal with WhatsApp on your
 * phone (Linked devices → Link a device). Session state is cached under
 * ./auth/ so you only do this once per install.
 *
 * Env vars (via .env or process env):
 *   NEXUS_API_URL             default http://localhost:8000
 *   NEXUS_WEBHOOK_SECRET      REQUIRED — match the backend's WHATSAPP_WEBHOOK_SECRET
 *                             (or the value from /api/whatsapp/bridge-secret)
 *   WA_AUTH_DIR               default ./auth
 */

import 'dotenv/config';
import fs from 'fs';
import http from 'http';
import path from 'path';
import { fileURLToPath } from 'url';
import pino from 'pino';
import qrcode from 'qrcode-terminal';
import fetch from 'node-fetch';
// FormData and Blob are globals in Node 18+ (Web Platform APIs).
import makeWASocket, {
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
  downloadMediaMessage,
} from '@whiskeysockets/baileys';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const NEXUS_API_URL = (process.env.NEXUS_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const NEXUS_WEBHOOK_SECRET = process.env.NEXUS_WEBHOOK_SECRET || '';
const AUTH_DIR = process.env.WA_AUTH_DIR || path.join(__dirname, 'auth');
const WA_HTTP_PORT = parseInt(process.env.WA_HTTP_PORT || '3001', 10);

// Active Baileys socket — set once connected, cleared on logout.
let _activeSock = null;

// ── Outbound HTTP server ─────────────────────────────────────────────────────
// POST /send  { to: "91XXXXXXXXXX", text: "..." }  → sends a WA message
// GET  /health                                     → { ok, connected }
const outboundServer = http.createServer((req, res) => {
  const secret = req.headers['x-nexus-secret'] || '';
  if (NEXUS_WEBHOOK_SECRET && secret !== NEXUS_WEBHOOK_SECRET) {
    res.writeHead(403, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: false, error: 'Forbidden' }));
    return;
  }

  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, connected: !!_activeSock }));
    return;
  }

  if (req.method === 'POST' && req.url === '/send') {
    let body = '';
    req.on('data', d => { body += d; });
    req.on('end', async () => {
      try {
        const { to, text } = JSON.parse(body);
        if (!_activeSock) {
          res.writeHead(503, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ ok: false, error: 'WhatsApp not connected yet' }));
          return;
        }
        if (!to || !text) {
          res.writeHead(400, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ ok: false, error: '`to` and `text` are required' }));
          return;
        }
        const digits = to.replace(/[^0-9]/g, '');
        const jid = `${digits}@s.whatsapp.net`;
        await _activeSock.sendMessage(jid, { text });
        console.log(`[nexus-whatsapp] ⇒ outbound to ${digits}: ${text.slice(0, 60)}${text.length > 60 ? '…' : ''}`);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true }));
      } catch (e) {
        console.error('[nexus-whatsapp] outbound send failed:', e.message);
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: e.message }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end('Not found');
});

outboundServer.listen(WA_HTTP_PORT, () => {
  console.log(`[nexus-whatsapp] Outbound HTTP server on port ${WA_HTTP_PORT}`);
});

if (!NEXUS_WEBHOOK_SECRET) {
  console.error('[nexus-whatsapp] NEXUS_WEBHOOK_SECRET is required in .env');
  console.error('   Get it from NexusAgent Settings → WhatsApp → "Copy bridge secret"');
  process.exit(1);
}

const logger = pino({ level: process.env.LOG_LEVEL || 'warn' });

async function downloadAttachment(absolutePath) {
  const url = `${NEXUS_API_URL}/api/whatsapp/attachment?path=${encodeURIComponent(absolutePath)}`;
  const res = await fetch(url, { headers: { 'X-Nexus-Secret': NEXUS_WEBHOOK_SECRET } });
  if (!res.ok) {
    throw new Error(`attachment fetch failed: ${res.status} ${await res.text()}`);
  }
  return Buffer.from(await res.arrayBuffer());
}

/**
 * Inspect a Baileys message and classify it as text / audio / document / image.
 * The classifier returns an object the main loop dispatches on.
 *   { kind: 'text',     text: '...' }
 *   { kind: 'audio',    mime, ext }
 *   { kind: 'document', mime, ext, filename }
 *   { kind: 'image',    mime, ext, caption }
 *   { kind: 'unknown' }
 */
function classify(message) {
  const m = message.message;
  if (!m) return { kind: 'unknown' };
  if (m.conversation)              return { kind: 'text', text: m.conversation };
  if (m.extendedTextMessage?.text) return { kind: 'text', text: m.extendedTextMessage.text };

  // Voice note (PTT) or general audio.
  if (m.audioMessage || m.pttMessage) {
    const a = m.audioMessage || m.pttMessage;
    return {
      kind: 'audio',
      mime: a.mimetype || 'audio/ogg; codecs=opus',
      ext:  (a.mimetype || '').includes('mp4') ? '.m4a'
            : (a.mimetype || '').includes('webm') ? '.webm'
            : '.ogg',
    };
  }

  // Document upload (PDF, .docx, etc.)
  if (m.documentMessage) {
    const d = m.documentMessage;
    return {
      kind: 'document',
      mime: d.mimetype || 'application/octet-stream',
      ext:  path.extname(d.fileName || '') || '.bin',
      filename: d.fileName || 'document',
      caption: d.caption || '',
    };
  }

  // Image — we don't OCR yet; backend returns a polite message. Pass it through
  // so the user gets a clear answer instead of silence.
  if (m.imageMessage) {
    const i = m.imageMessage;
    return {
      kind: 'image',
      mime: i.mimetype || 'image/jpeg',
      ext:  (i.mimetype || '').includes('png') ? '.png'
            : (i.mimetype || '').includes('webp') ? '.webp'
            : '.jpg',
      caption: i.caption || '',
    };
  }

  if (m.videoMessage?.caption) return { kind: 'text', text: m.videoMessage.caption };
  return { kind: 'unknown' };
}

/**
 * Resolve a Baileys jid to the user-facing phone identifier.
 *
 * WhatsApp now ships some accounts as "@lid" (Local Identifier) instead of
 * "@s.whatsapp.net". When that happens, `msg.key.senderPn` (Baileys 6.7+)
 * carries the real phone number — we prefer it. Otherwise fall back to the
 * jid's local part. Returns the digits-only phone string the backend expects.
 */
function resolvePhone(msg) {
  // Newer Baileys: key.senderPn = "<countrycode><number>@s.whatsapp.net"
  const senderPn = msg.key?.senderPn;
  if (typeof senderPn === 'string' && senderPn.includes('@')) {
    return senderPn.split('@')[0];
  }
  const jid = msg.key?.remoteJid || '';
  // For LID jids, the local part is a stable identifier but not a real phone.
  // Backend stores whatever it gets; this is fine for routing, only the
  // Settings display will show the LID instead of the phone.
  return jid.split('@')[0];
}

async function postMedia(endpointPath, mediaBuffer, fields, ext, mime) {
  const form = new FormData();
  const blob = new Blob([mediaBuffer], { type: mime || 'application/octet-stream' });
  form.append('file', blob, `wa${ext || '.bin'}`);
  for (const [k, v] of Object.entries(fields)) form.append(k, v);
  return fetch(`${NEXUS_API_URL}${endpointPath}`, {
    method: 'POST',
    headers: { 'X-Nexus-Secret': NEXUS_WEBHOOK_SECRET },
    body: form,
    signal: AbortSignal.timeout(600_000),
  });
}

async function startBridge() {
  if (!fs.existsSync(AUTH_DIR)) fs.mkdirSync(AUTH_DIR, { recursive: true });
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
  const { version } = await fetchLatestBaileysVersion();

  const sock = makeWASocket({
    version,
    auth: state,
    logger,
    printQRInTerminal: false, // we render it ourselves below so it's visible
    browser: ['NexusAgent', 'Chrome', '1.0.0'],
    syncFullHistory: false,
  });

  sock.ev.on('creds.update', saveCreds);

  sock.ev.on('connection.update', (update) => {
    const { connection, lastDisconnect, qr } = update;
    if (qr) {
      console.log('\n[nexus-whatsapp] Scan this QR with WhatsApp (Linked devices → Link a device):\n');
      qrcode.generate(qr, { small: true });
    }
    if (connection === 'open') {
      _activeSock = sock;
      const phone = (sock.user?.id || '').split(':')[0];
      console.log(`[nexus-whatsapp] ✅ Connected as ${phone}. Waiting for messages...`);
    }
    if (connection === 'close') {
      _activeSock = null;
      const statusCode = lastDisconnect?.error?.output?.statusCode;
      const loggedOut = statusCode === DisconnectReason.loggedOut;
      console.log(`[nexus-whatsapp] disconnected (code=${statusCode}, loggedOut=${loggedOut})`);
      if (!loggedOut) {
        console.log('[nexus-whatsapp] Reconnecting in 3s...');
        setTimeout(startBridge, 3000);
      } else {
        console.log('[nexus-whatsapp] Logged out. Delete auth/ to re-pair, then restart.');
      }
    }
  });

  sock.ev.on('messages.upsert', async ({ messages, type }) => {
    if (type !== 'notify') return;
    for (const msg of messages) {
      try {
        if (!msg.message) continue;
        if (msg.key.fromMe) continue; // ignore our own echoes
        const jid = msg.key.remoteJid || '';
        // Ignore groups & broadcasts — DM only for v1
        if (jid.endsWith('@g.us') || jid === 'status@broadcast') continue;

        const cls = classify(msg);
        if (cls.kind === 'unknown') continue;

        const phone = resolvePhone(msg);
        const messageId = msg.key.id || '';
        const isLid = jid.endsWith('@lid');

        const previewText = cls.kind === 'text'  ? cls.text
                          : cls.kind === 'audio' ? '[voice note]'
                          : cls.kind === 'document' ? `[document: ${cls.filename}]`
                          : cls.kind === 'image' ? '[image]'
                          : '[?]';
        console.log(`[nexus-whatsapp] ⇐ ${phone}${isLid ? ' (lid)' : ''}: ${previewText.slice(0, 80)}${previewText.length > 80 ? '…' : ''}`);

        // Indicate typing — refresh every 25s so WA doesn't clear it during
        // long agent runs (DB queries on local Ollama can take a few minutes).
        try { await sock.sendPresenceUpdate('composing', jid); } catch (_) { /* ignore */ }
        const typingPing = setInterval(() => {
          sock.sendPresenceUpdate('composing', jid).catch(() => {});
        }, 25_000);

        let reply;
        try {
          let res;
          if (cls.kind === 'text') {
            res = await fetch(`${NEXUS_API_URL}/api/whatsapp/inbound`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'X-Nexus-Secret': NEXUS_WEBHOOK_SECRET,
              },
              body: JSON.stringify({ from: phone, text: cls.text, message_id: messageId }),
              signal: AbortSignal.timeout(600_000),
            });
          } else if (cls.kind === 'audio') {
            const buf = await downloadMediaMessage(msg, 'buffer', {});
            res = await postMedia('/api/whatsapp/inbound-audio', buf,
              { from: phone, message_id: messageId },
              cls.ext, cls.mime);
          } else if (cls.kind === 'document') {
            const buf = await downloadMediaMessage(msg, 'buffer', {});
            res = await postMedia('/api/whatsapp/inbound-document', buf,
              { from: phone, message_id: messageId, mime_type: cls.mime },
              cls.ext, cls.mime);
          } else if (cls.kind === 'image') {
            // Forward to inbound-document so the backend gets to send the
            // "no OCR yet, send the PDF" message — keeps copy in one place.
            const buf = await downloadMediaMessage(msg, 'buffer', {});
            res = await postMedia('/api/whatsapp/inbound-document', buf,
              { from: phone, message_id: messageId, mime_type: cls.mime },
              cls.ext, cls.mime);
          }

          if (!res || !res.ok) {
            const status = res?.status ?? 'no-response';
            const err = res ? await res.text() : 'no-response';
            reply = { text: `⚠️ Backend error (${status}): ${err.slice(0, 200)}`, attachments: [] };
          } else {
            reply = await res.json();
          }
        } catch (e) {
          console.error('[nexus-whatsapp] backend call failed:', e);
          const errMsg = e?.name === 'TimeoutError' || e?.type === 'aborted'
            ? `⚠️ That one took longer than 10 minutes — it may still be running on the server. Check the web UI to see the result.`
            : `⚠️ Couldn't reach the NexusAgent backend. Is it running on ${NEXUS_API_URL}?`;
          reply = { text: errMsg, attachments: [] };
        } finally {
          clearInterval(typingPing);
        }

        if (reply?.silent) continue;

        // Send text
        if (reply?.text) {
          try {
            await sock.sendMessage(jid, { text: reply.text });
          } catch (e) {
            console.error('[nexus-whatsapp] sendMessage (text) failed:', e);
          }
        }

        // Send attachments
        for (const att of reply?.attachments || []) {
          try {
            const buf = await downloadAttachment(att.path);
            await sock.sendMessage(jid, {
              document: buf,
              fileName: att.filename,
              mimetype: att.mime_type || 'application/octet-stream',
            });
            console.log(`[nexus-whatsapp] ⇒ ${phone}: sent file ${att.filename}`);
          } catch (e) {
            console.error('[nexus-whatsapp] attachment send failed:', e);
            await sock.sendMessage(jid, { text: `(Couldn't attach ${att.filename}: ${e.message})` });
          }
        }

        try {
          await sock.sendPresenceUpdate('paused', jid);
        } catch (_) { /* ignore */ }
      } catch (e) {
        console.error('[nexus-whatsapp] message handler error:', e);
      }
    }
  });
}

startBridge().catch((e) => {
  console.error('[nexus-whatsapp] fatal:', e);
  process.exit(1);
});
