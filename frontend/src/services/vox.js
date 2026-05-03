/**
 * Vox API client — talks to /api/vox/* and the slice of /api/approvals/* that
 * filters to tool_name="vox_dial".
 *
 * Distinct from `services/voice_calls.js` which targets /api/voice/* (the
 * older lab-bridged path). This file is for the new approval-queue + audit
 * stack (Step 2-4 of the Vox refactor).
 */
import { getToken, getBusinessId } from './auth';

function headers() {
  const h = { 'Content-Type': 'application/json' };
  const t = getToken();
  if (t) h['Authorization'] = `Bearer ${t}`;
  const b = getBusinessId();
  if (b) h['X-Business-Id'] = b;
  return h;
}

async function req(path, opts = {}) {
  const res = await fetch(path, {
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

// ── Recent calls (audit log) ───────────────────────────────────────────────
export const listRecentCalls = (limit = 50) =>
  req(`/api/vox/calls?limit=${limit}`).then((r) => r.calls || []);

export const getCall = (callId) =>
  req(`/api/vox/calls/${encodeURIComponent(callId)}`);

// ── Today's voice-call usage ──────────────────────────────────────────────
export const getUsage = () => req('/api/vox/usage');

// ── Pending approvals filtered to vox_dial ────────────────────────────────
export const listPendingDials = async () => {
  const r = await req('/api/approvals?status=pending&limit=100');
  return (r.actions || []).filter((a) => a.tool_name === 'vox_dial');
};

export const approveDial = (actionId) =>
  req(`/api/approvals/${encodeURIComponent(actionId)}/approve`, { method: 'POST' });

export const rejectDial = (actionId, reason = '') =>
  req(`/api/approvals/${encodeURIComponent(actionId)}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });

// ── On-demand dial (queues OR direct-dials per VOX_BYPASS_APPROVAL_FOR) ───
export const dialContact = (contactId) =>
  req(`/api/vox/dial?contact_id=${encodeURIComponent(contactId)}`, { method: 'POST' });
