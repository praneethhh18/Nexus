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
    throw new Error(txt || `HTTP ${res.status}`);
  }
  return res.json();
}

export const getSuggestionsFor = (entityType, entityId) =>
  req(`/api/suggestions/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}`);

export const dismissSuggestion = (id) =>
  req(`/api/suggestions/${encodeURIComponent(id)}/dismiss`, { method: 'POST' });
