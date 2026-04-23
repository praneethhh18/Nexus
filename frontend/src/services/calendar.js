import { getToken, getBusinessId } from './auth';

const BASE = '/api/calendar';

function headers() {
  const h = { 'Content-Type': 'application/json' };
  const t = getToken();
  if (t) h['Authorization'] = `Bearer ${t}`;
  const b = getBusinessId();
  if (b) h['X-Business-Id'] = b;
  return h;
}

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, { ...opts, headers: { ...headers(), ...(opts.headers || {}) } });
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Session expired'); }
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

export const calendarStatus = () => req('/status');
export const calendarStart = () => req('/oauth/start', { method: 'POST' });
export const calendarEvents = (days = 14, limit = 20) => req(`/events?days=${days}&limit=${limit}`);
export const calendarDisconnect = () => req('/disconnect', { method: 'DELETE' });
