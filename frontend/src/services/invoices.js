import { getToken, getBusinessId } from './auth';

const BASE = '/api/invoices';

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

export const listInvoices = (opts = {}) => {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(opts)) if (v) qs.set(k, v);
  const s = qs.toString();
  return req(`${s ? '?' + s : ''}`);
};
export const getInvoice = (id) => req(`/${id}`);
export const createInvoice = (body) => req('', { method: 'POST', body: JSON.stringify(body) });
export const updateInvoice = (id, body) => req(`/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
export const deleteInvoice = (id) => req(`/${id}`, { method: 'DELETE' });
export const renderInvoicePdf = (id) => req(`/${id}/render`, { method: 'POST' });
export const invoiceSummary = () => req('/summary');

// PDF download requires auth headers, so it can't be a plain <a href> — the
// browser won't attach the bearer token. Callers should `await` this to get
// a Blob, then create an object URL from it for download or viewing.
export const fetchInvoicePdfBlob = async (id) => {
  const h = headers();
  delete h['Content-Type'];
  const res = await fetch(`${BASE}/${id}/pdf`, { headers: h });
  if (!res.ok) {
    // Surface the real error rather than letting an HTML error page
    // get written to disk as a `.pdf` (which is what made downloads
    // appear corrupt before).
    let msg = `HTTP ${res.status}`;
    try { msg = (await res.text()) || msg; } catch {}
    throw new Error(msg);
  }
  const blob = await res.blob();
  // Guard against the dev server returning index.html on a misconfigured
  // route — verify the response actually looks like a PDF.
  if (!blob.type.includes('pdf') && blob.type.startsWith('text/')) {
    throw new Error('Server did not return a PDF. Try Regenerate first.');
  }
  return blob;
};

// Back-compat shim. Older call sites pass the result directly to fetch()
// which silently broke (the Promise stringified to "[object Promise]" and
// the dev server returned its SPA shell as the response body).
export const invoicePdfUrl = fetchInvoicePdfBlob;

export const INVOICE_STATUSES = ['draft', 'sent', 'paid', 'overdue', 'cancelled'];
