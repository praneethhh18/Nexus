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
export const updateDocumentMeta = (id, body) =>
  req(`/${id}`, { method: 'PATCH', body: JSON.stringify(body) });

// Categories an uploaded doc can be tagged with — used to filter
// knowledge-base searches so e.g. the Competitor Watcher only reads
// competitor PDFs, not our own.
export const DOC_CATEGORIES = [
  { value: 'competitor', label: 'Competitor', description: "Their pricing, plans, marketing" },
  { value: 'internal',   label: 'Internal',   description: 'Our own policies, playbooks, pricing' },
  { value: 'client',     label: 'Client doc', description: 'Client briefs, requirements, agreements' },
  { value: 'contract',   label: 'Contract',   description: 'Signed contracts, NDAs, SOWs' },
  { value: 'social',     label: 'Social / press', description: 'Brand mentions, news, social posts' },
  { value: 'other',      label: 'Other',      description: 'Anything that doesn\'t fit above' },
];

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

// Template autofill — given a reference PDF / text, the model maps content
// onto this template's variables so the user doesn't have to re-type.
// Returns { variables: { name: value, ... }, filled_count, source_chars,
//           truncated }.
export const autofillTemplateFromText = (template_key, text) =>
  req('/autofill-template', { method: 'POST', body: JSON.stringify({ template_key, text }) });

export const autofillTemplateFromUpload = async (template_key, file) => {
  const fd = new FormData();
  fd.append('file', file);
  const h = headers();
  delete h['Content-Type'];
  const res = await fetch(
    `${BASE}/autofill-template-upload?template_key=${encodeURIComponent(template_key)}`,
    { method: 'POST', headers: h, body: fd },
  );
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Session expired'); }
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
};

// Upload a PDF / DOCX / TXT into the knowledge base so agents can search
// it. Auto-categorised by the picker the user chose in the upload modal.
export const uploadToKnowledgeBase = async (file, { category = 'other', title = '' } = {}) => {
  const fd = new FormData();
  fd.append('file', file);
  const qs = new URLSearchParams();
  if (category) qs.set('category', category);
  if (title) qs.set('title', title);
  const h = headers();
  delete h['Content-Type'];
  const url = `${BASE}/upload${qs.toString() ? '?' + qs.toString() : ''}`;
  const res = await fetch(url, { method: 'POST', headers: h, body: fd });
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Session expired'); }
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
};


// Upload an image asset (logo / header) for embedding in generated docs.
// Returns { path, filename } — pass `path` back into generateDocument as
// `logo_path`.
export const uploadDocumentAsset = async (file) => {
  const fd = new FormData();
  fd.append('file', file);
  const h = headers();
  delete h['Content-Type'];
  const res = await fetch(`${BASE}/upload-asset`, {
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
  const h = headers();
  delete h['Content-Type'];
  const res = await fetch(`${BASE}/${id}/download`, { headers: h });
  if (!res.ok) throw new Error(await res.text());
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
};
