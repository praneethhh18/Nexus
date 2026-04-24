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

export const listTags   = () => req('/api/tags');
export const createTag  = (name, color) =>
  req('/api/tags', { method: 'POST', body: JSON.stringify({ name, color }) });
export const deleteTag  = (id) =>
  req(`/api/tags/${encodeURIComponent(id)}`, { method: 'DELETE' });

export const tagsFor = (entityType, entityId) =>
  req(`/api/tags/for/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}`);

export const setTagsFor = (entityType, entityId, tagIds) =>
  req(`/api/tags/for/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}`, {
    method: 'PUT', body: JSON.stringify({ tag_ids: tagIds }),
  });

export const bulkTagsFor = (entityType, ids) =>
  req(`/api/tags/bulk-for/${encodeURIComponent(entityType)}`, {
    method: 'POST', body: JSON.stringify({ ids }),
  });

// ── Bulk actions ──────────────────────────────────────────────────────────
export const bulkDeleteTasks = (ids) =>
  req('/api/tasks/bulk-delete', { method: 'POST', body: JSON.stringify({ ids }) });

export const bulkTaskStatus = (ids, status) =>
  req('/api/tasks/bulk-status', { method: 'POST', body: JSON.stringify({ ids, status }) });

// ── Export ────────────────────────────────────────────────────────────────
export async function downloadFullExport() {
  const res = await fetch('/api/export/all', { headers: headers() });
  if (!res.ok) throw new Error(await res.text());
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `nexusagent-export-${new Date().toISOString().slice(0, 10)}.zip`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
