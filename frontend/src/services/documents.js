import { getToken, getBusinessId } from './auth';

const BASE = '/api/documents';

function headers(extra = {}) {
  const h = { 'Content-Type': 'application/json', ...extra };
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

export const listDocTemplates = () => req('/templates');
export const getDocTemplate = (key) => req(`/templates/${key}`);
export const listDocuments = () => req('');
export const getDocument = (id) => req(`/${id}`);
export const generateDocument = (body) => req('/generate', { method: 'POST', body: JSON.stringify(body) });
export const deleteDocument = (id) => req(`/${id}`, { method: 'DELETE' });

// AI document intake — extract structured fields from pasted text or an
// uploaded file. Preview-only — does not persist anything.
// Returns { doc_type, summary, parties, dates, amounts, line_items, key_terms,
//           source_chars, truncated }.
export const extractDocFromText = (text) =>
  req('/extract-text', { method: 'POST', body: JSON.stringify({ text }) });

export const extractDocFromUpload = async (file) => {
  const fd = new FormData();
  fd.append('file', file);
  // Don't set Content-Type — browser fills in the multipart boundary.
  const h = headers();
  delete h['Content-Type'];
  const res = await fetch(`${BASE}/extract-upload`, {
    method: 'POST', headers: h, body: fd,
  });
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Session expired'); }
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
};

export const downloadDocument = async (id, filename) => {
  const res = await fetch(`${BASE}/${id}/download`, { headers: headers({ 'Content-Type': undefined }) });
  if (!res.ok) throw new Error(await res.text());
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
};
