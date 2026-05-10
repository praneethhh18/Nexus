/**
 * Privacy Bridge API client.
 *
 * Backend lives at api/routers/privacy_bridge.py. The shape we expect:
 *
 *   GET    /api/privacy-bridge          → state object
 *   POST   /api/privacy-bridge/token    → { ok, token, next_step }
 *   POST   /api/privacy-bridge/revoke   → state object
 *   POST   /api/privacy-bridge/ping     → state object (after a fresh probe)
 *
 * State object:
 *   {
 *     business_id, status, endpoint_url,
 *     last_pinged_at, last_ping_error,
 *     registered_at, ollama_version, ollama_models: []
 *   }
 *
 * Status enum: 'unconfigured' | 'registered' | 'healthy' | 'down' | 'revoked'
 */
import { getToken, getBusinessId } from './auth';

function headers() {
  const h = { 'Content-Type': 'application/json' };
  const t = getToken();      if (t) h['Authorization']    = `Bearer ${t}`;
  const b = getBusinessId(); if (b) h['X-Business-Id']    = b;
  return h;
}

async function req(path, opts = {}) {
  const res = await fetch(path, { ...opts, headers: { ...headers(), ...(opts.headers || {}) } });
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const t = await res.text();
    let msg = t;
    try { msg = JSON.parse(t).detail || t; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export const getBridgeState = ()  => req('/api/privacy-bridge');
export const issueBridgeToken = () => req('/api/privacy-bridge/token', { method: 'POST' });
export const revokeBridge     = () => req('/api/privacy-bridge/revoke', { method: 'POST' });
export const pingBridge       = () => req('/api/privacy-bridge/ping',   { method: 'POST' });
