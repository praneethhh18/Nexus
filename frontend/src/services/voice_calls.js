/**
 * Vox outbound-calls API client — talks to NexusAgent's /api/voice/* routes.
 *
 * The audio bridge runs in the lab (nexuscaller-lab); we never call the lab
 * directly from the browser. NexusAgent's server forwards the dial request
 * server-side, then receives the post-call callback and stores the result.
 *
 * Distinct from services/voice.js which handles in-app voice mode
 * (browser-mic → server transcribe). This file is for outbound phone calls.
 */
import { getToken, getBusinessId } from './auth';

const BASE = '/api/voice';

function headers() {
  const h = { 'Content-Type': 'application/json' };
  const t = getToken();
  if (t) h['Authorization'] = `Bearer ${t}`;
  const b = getBusinessId();
  if (b) h['X-Business-Id'] = b;
  return h;
}

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    ...opts,
    headers: { ...headers(), ...(opts.headers || {}) },
  });
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

/** Trigger a Vox call IMMEDIATELY with default stack. Returns { ok, call_sid, watch_url }.
 *  Use prepareDialForContact() for the standard "open precall page" flow. */
export const dialContact = (body) =>
  req('/dial', { method: 'POST', body: JSON.stringify(body) });

/** Build a precall URL for the lab. Operator opens it in a new tab to
 *  pick the STT/LLM/TTS stack before placing the call. Returns
 *  { ok, precall_url }. */
export const prepareDialForContact = (body) =>
  req('/prepare-dial', { method: 'POST', body: JSON.stringify(body) });

/** Recent calls for the current business (newest first). */
export const listRecentCalls = (limit = 50) =>
  req(`/calls?limit=${limit}`).then((r) => r.calls || []);

/** Past Vox calls for one contact, newest first. */
export const listContactCalls = (contactId, limit = 25) =>
  req(`/contacts/${contactId}/calls?limit=${limit}`).then((r) => r.calls || []);

/** Full record for one call (transcript turns + summary blob). */
export const getCall = (idOrSid) => req(`/calls/${idOrSid}`);
