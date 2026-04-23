import { getToken, getBusinessId } from './auth';

function headers(extra = {}) {
  const h = { 'Content-Type': 'application/json', ...extra };
  const t = getToken(); if (t) h['Authorization'] = `Bearer ${t}`;
  const b = getBusinessId(); if (b) h['X-Business-Id'] = b;
  return h;
}

async function req(path, opts = {}) {
  const res = await fetch(path, { ...opts, headers: { ...headers(), ...(opts.headers || {}) } });
  if (res.status === 401 && !path.startsWith('/api/auth/login')) {
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  const ctype = res.headers.get('content-type') || '';
  if (!res.ok) {
    const txt = await res.text();
    if (ctype.includes('text/html')) throw new Error(`Backend not reachable on ${path}`);
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg);
  }
  if (ctype.includes('application/json')) return res.json();
  return res.text();
}

// 2FA
export const twofaStatus = () => req('/api/auth/2fa/status');
export const twofaEnroll = () => req('/api/auth/2fa/enroll', { method: 'POST' });
export const twofaVerify = (code) => req('/api/auth/2fa/verify', { method: 'POST', body: JSON.stringify({ code }) });
export const twofaDisable = (code) => req('/api/auth/2fa/disable', { method: 'POST', body: JSON.stringify({ code }) });
export const twofaRegenerate = (code) => req('/api/auth/2fa/regenerate-codes', { method: 'POST', body: JSON.stringify({ code }) });

// Sessions
export const listSessions = () => req('/api/auth/sessions');
export const revokeSession = (jti) => req(`/api/auth/sessions/${jti}`, { method: 'DELETE' });
export const revokeAllOther = () => req('/api/auth/sessions/revoke-all-other', { method: 'POST' });

// Audit
export const auditList = (params = {}) => {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== '') qs.set(k, v);
  return req(`/api/audit?${qs.toString()}`);
};

// Privacy / Cloud-LLM audit
export const privacyStatus = () => req('/api/privacy/status');
export const privacyAudit  = (limit = 100) => req(`/api/privacy/audit?limit=${limit}`);
export const privacyAuditClear = () => req('/api/privacy/audit/clear', { method: 'POST' });

// Global search
export const globalSearch = (q, limit = 8) =>
  req(`/api/search?q=${encodeURIComponent(q)}&limit=${limit}`);
