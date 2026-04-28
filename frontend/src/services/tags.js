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

export const bulkDeleteContacts = (ids) =>
  req('/api/crm/contacts/bulk-delete', { method: 'POST', body: JSON.stringify({ ids }) });

export const bulkDeleteCompanies = (ids) =>
  req('/api/crm/companies/bulk-delete', { method: 'POST', body: JSON.stringify({ ids }) });

export const bulkDeleteDeals = (ids) =>
  req('/api/crm/deals/bulk-delete', { method: 'POST', body: JSON.stringify({ ids }) });

export const bulkDealStage = (ids, stage) =>
  req('/api/crm/deals/bulk-stage', { method: 'POST', body: JSON.stringify({ ids, stage }) });

export const bulkDeleteInvoices = (ids) =>
  req('/api/invoices/bulk-delete', { method: 'POST', body: JSON.stringify({ ids }) });

export const bulkInvoiceStatus = (ids, status) =>
  req('/api/invoices/bulk-status', { method: 'POST', body: JSON.stringify({ ids, status }) });

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


// ── Disaster-recovery backup (admin-only) ─────────────────────────────────
// Different from `downloadFullExport` — this includes the raw SQLite DB
// + ChromaDB so the result is restorable on a new machine, not just
// human-readable.
export async function downloadFullBackup() {
  const res = await fetch('/api/admin/backup', {
    method: 'POST',
    headers: headers(),
  });
  if (!res.ok) throw new Error(await res.text());
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  a.download = `nexus-backup-${stamp}.zip`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}


export async function getBackupInfo() {
  const res = await fetch('/api/admin/backup/info', { headers: headers() });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
