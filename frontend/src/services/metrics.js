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
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt; try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

export const getGlobalMetrics = (days = 30) => req(`/api/admin/metrics?days=${days}`);
export const getTenantMetrics = (days = 30) => req(`/api/admin/metrics/tenant?days=${days}`);
export const recordEvent      = (event, count = 1) =>
  req('/api/admin/metrics/record', { method: 'POST', body: JSON.stringify({ event, count }) });
