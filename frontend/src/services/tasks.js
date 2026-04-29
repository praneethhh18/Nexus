import { getToken, getBusinessId } from './auth';

const BASE = '/api/tasks';

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

export const listTasks = (opts = {}) => {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(opts)) if (v) qs.set(k, v);
  const s = qs.toString();
  return req(`${s ? '?' + s : ''}`);
};
export const getTask = (id) => req(`/${id}`);
export const createTask = (body) => req('', { method: 'POST', body: JSON.stringify(body) });
export const updateTask = (id, body) => req(`/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
export const deleteTask = (id) => req(`/${id}`, { method: 'DELETE' });
export const taskSummary = (mine = false) => req(`/summary${mine ? '?mine=true' : ''}`);

// Extract action items from pasted meeting notes / transcript.
// Returns { items: [{title, description, priority, due_hint, owner_hint}], summary, raw_count }.
// Preview-only — caller still needs to POST /api/tasks per accepted item.
export const extractFromNotes = (notes) =>
  req('/extract-from-notes', { method: 'POST', body: JSON.stringify({ notes }) });

export const STATUSES = ['open', 'in_progress', 'done', 'cancelled'];
export const PRIORITIES = ['low', 'normal', 'high', 'urgent'];
