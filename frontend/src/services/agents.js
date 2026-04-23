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

export const listPersonas = () => req('/api/agents/personas');
export const renamePersona = (key, name) =>
  req(`/api/agents/personas/${encodeURIComponent(key)}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  });
export const togglePersonaEnabled = (key, enabled) =>
  req(`/api/agents/personas/${encodeURIComponent(key)}`, {
    method: 'PATCH',
    body: JSON.stringify({ enabled }),
  });
