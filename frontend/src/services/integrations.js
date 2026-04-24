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
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

export const listProviders    = () => req('/api/integrations/providers');
export const listConnections  = () => req('/api/integrations');
export const connectProvider  = (provider, config) =>
  req(`/api/integrations/${encodeURIComponent(provider)}/connect`, {
    method: 'POST', body: JSON.stringify(config || {}),
  });
export const disconnectProvider = (provider) =>
  req(`/api/integrations/${encodeURIComponent(provider)}`, { method: 'DELETE' });
export const pingProvider = (provider) =>
  req(`/api/integrations/${encodeURIComponent(provider)}/ping`, { method: 'POST' });
