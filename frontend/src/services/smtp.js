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
  const res = await fetch(path, { ...opts, headers: { ...headers(), ...(opts.headers || {}) } });
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Session expired'); }
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

// Workspace SMTP config — only the configured flag + sender info is visible
// to non-admins. Full host/port/username only returned to admins.
export const readSmtp = () => req('/api/workspace/smtp');
export const saveSmtp = (cfg) => req('/api/workspace/smtp', { method: 'PUT', body: JSON.stringify(cfg) });
export const deleteSmtp = () => req('/api/workspace/smtp', { method: 'DELETE' });
export const testSmtp = (cfg = null) =>
  req('/api/workspace/smtp/test', { method: 'POST', body: JSON.stringify(cfg) });

// Send a real email via the workspace's configured SMTP. Throws if SMTP
// isn't configured — callers should fall back to mailto in that case.
export const sendEmail = (to, subject, body, extras = {}) =>
  req('/api/email/send', {
    method: 'POST',
    body: JSON.stringify({ to, subject, body, ...extras }),
  });
