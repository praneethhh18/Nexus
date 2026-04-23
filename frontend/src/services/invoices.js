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

export const invoicePdfUrl = (id) => {
  // Must download via fetch (auth headers needed), not as a direct link
  return (async () => {
    const res = await fetch(`${BASE}/${id}/pdf`, { headers: headers({ 'Content-Type': undefined }) });
    if (!res.ok) throw new Error(await res.text());
    return res.blob();
  })();
};

export const INVOICE_STATUSES = ['draft', 'sent', 'paid', 'overdue', 'cancelled'];
