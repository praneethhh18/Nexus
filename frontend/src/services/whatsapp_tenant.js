/**
 * WhatsApp multi-tenant API client — talks to the backend, NOT directly
 * to the Node bridge. Backend handles auth + plan-gate + bridge routing.
 *
 * Flow used by the Settings/WhatsAppConnect component:
 *   connect()      → start a Baileys session for the current business
 *   getStatus()    → poll every 2s while QR shows; stops when status='connected'
 *   disconnect()   → wipe auth + force re-scan on next connect
 */
import { getToken, getBusinessId } from './auth';

function authHeaders() {
  const h = { 'Content-Type': 'application/json' };
  const t = getToken();      if (t) h['Authorization']    = `Bearer ${t}`;
  const b = getBusinessId(); if (b) h['X-Business-Id']    = b;
  return h;
}

async function req(path, opts = {}) {
  const res = await fetch(path, { ...opts, headers: { ...authHeaders(), ...(opts.headers || {}) } });
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch { /* leave as-is */ }
    throw new Error(msg);
  }
  return res.json();
}

export const connectWhatsApp = () =>
  req('/api/whatsapp/tenant/connect', { method: 'POST' });

export const getWhatsAppStatus = () =>
  req('/api/whatsapp/tenant/status');

export const disconnectWhatsApp = () =>
  req('/api/whatsapp/tenant/disconnect', { method: 'POST' });
