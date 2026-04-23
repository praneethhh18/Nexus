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
  if (res.status === 401 && !path.includes('preview')) {
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  const contentType = res.headers.get('content-type') || '';
  if (!res.ok) {
    const txt = await res.text();
    if (contentType.includes('text/html')) {
      throw new Error(`Backend not reachable on ${path} (is uvicorn running?)`);
    }
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

export const listInvites = (includeAccepted = false) =>
  req(`/api/team/invites?include_accepted=${includeAccepted}`);
export const createInvite = (email, role = 'member') =>
  req('/api/team/invites', { method: 'POST', body: JSON.stringify({ email, role }) });
export const revokeInvite = (token) =>
  req(`/api/team/invites/${token}`, { method: 'DELETE' });
export const previewInvite = (token) =>
  req(`/api/team/invites/preview?token=${encodeURIComponent(token)}`);
export const acceptInvite = (token) =>
  req('/api/team/invites/accept', { method: 'POST', body: JSON.stringify({ token }) });
export const activityFeed = (limit = 60) =>
  req(`/api/team/activity?limit=${limit}`);
