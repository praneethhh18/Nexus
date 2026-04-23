import { getToken, getBusinessId } from './auth';

const BASE = '/api/crm';

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

// Overview / pipeline
export const crmOverview = () => req('/overview');
export const pipeline = () => req('/pipeline');

// Companies
export const listCompanies = (search = '') =>
  req(`/companies${search ? `?search=${encodeURIComponent(search)}` : ''}`);
export const getCompany = (id) => req(`/companies/${id}`);
export const createCompany = (body) => req('/companies', { method: 'POST', body: JSON.stringify(body) });
export const updateCompany = (id, body) => req(`/companies/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
export const deleteCompany = (id) => req(`/companies/${id}`, { method: 'DELETE' });

// Contacts
export const listContacts = (opts = {}) => {
  const qs = new URLSearchParams();
  if (opts.search) qs.set('search', opts.search);
  if (opts.company_id) qs.set('company_id', opts.company_id);
  const s = qs.toString();
  return req(`/contacts${s ? '?' + s : ''}`);
};
export const getContact = (id) => req(`/contacts/${id}`);
export const createContact = (body) => req('/contacts', { method: 'POST', body: JSON.stringify(body) });
export const updateContact = (id, body) => req(`/contacts/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
export const deleteContact = (id) => req(`/contacts/${id}`, { method: 'DELETE' });

// Deals
export const listDeals = (opts = {}) => {
  const qs = new URLSearchParams();
  if (opts.stage) qs.set('stage', opts.stage);
  if (opts.search) qs.set('search', opts.search);
  const s = qs.toString();
  return req(`/deals${s ? '?' + s : ''}`);
};
export const getDeal = (id) => req(`/deals/${id}`);
export const createDeal = (body) => req('/deals', { method: 'POST', body: JSON.stringify(body) });
export const updateDeal = (id, body) => req(`/deals/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
export const deleteDeal = (id) => req(`/deals/${id}`, { method: 'DELETE' });

// Interactions
export const listInteractions = (opts = {}) => {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(opts)) if (v) qs.set(k, v);
  const s = qs.toString();
  return req(`/interactions${s ? '?' + s : ''}`);
};
export const createInteraction = (body) => req('/interactions', { method: 'POST', body: JSON.stringify(body) });
export const deleteInteraction = (id) => req(`/interactions/${id}`, { method: 'DELETE' });

export const DEAL_STAGES = ['lead', 'qualified', 'proposal', 'negotiation', 'won', 'lost'];
export const INTERACTION_TYPES = ['call', 'email', 'meeting', 'note'];
