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
import path from 'path';
import { fileURLToPath } from 'url';
import pino from 'pino';
import qrcode from 'qrcode-terminal';
import fetch from 'node-fetch';
import makeWASocket, {
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
} from '@whiskeysockets/baileys';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const NEXUS_API_URL = (process.env.NEXUS_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const NEXUS_WEBHOOK_SECRET = process.env.NEXUS_WEBHOOK_SECRET || '';
const AUTH_DIR = process.env.WA_AUTH_DIR || path.join(__dirname, 'auth');

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

async function extractText(message) {
  const m = message.message;
  if (!m) return '';
  if (m.conversation) return m.conversation;
  if (m.extendedTextMessage?.text) return m.extendedTextMessage.text;
  if (m.imageMessage?.caption) return m.imageMessage.caption;
  if (m.videoMessage?.caption) return m.videoMessage.caption;
  // Voice notes / audio: we could transcribe via /api/voice/transcribe, but
  // keep v1 text-only. Politely nudge the user if they send audio.
  if (m.audioMessage || m.pttMessage) {
    return '__audio__';
  }
  return '';
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
      const phone = (sock.user?.id || '').split(':')[0];
      console.log(`[nexus-whatsapp] ✅ Connected as ${phone}. Waiting for messages...`);
    }
    if (connection === 'close') {
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

        const text = await extractText(msg);
        if (!text) continue;

        if (text === '__audio__') {
          await sock.sendMessage(jid, {
            text: "I can't process voice notes yet — please send text. 🙏",
          });
          continue;
        }

        const phone = jid.split('@')[0];
        const messageId = msg.key.id || '';

        console.log(`[nexus-whatsapp] ⇐ ${phone}: ${text.slice(0, 80)}${text.length > 80 ? '…' : ''}`);

        // Indicate typing
        try {
          await sock.sendPresenceUpdate('composing', jid);
        } catch (_) { /* ignore */ }

        let reply;
        try {
          const res = await fetch(`${NEXUS_API_URL}/api/whatsapp/inbound`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Nexus-Secret': NEXUS_WEBHOOK_SECRET,
            },
            body: JSON.stringify({
              from: phone,
              text,
              message_id: messageId,
            }),
            // Agent can be slow — allow up to 3 minutes
            signal: AbortSignal.timeout(180_000),
          });
          if (!res.ok) {
            const err = await res.text();
            reply = { text: `⚠️ Backend error (${res.status}): ${err.slice(0, 200)}`, attachments: [] };
          } else {
            reply = await res.json();
          }
        } catch (e) {
          console.error('[nexus-whatsapp] backend call failed:', e);
          reply = { text: `⚠️ Couldn't reach the NexusAgent backend. Is it running on ${NEXUS_API_URL}?`, attachments: [] };
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
