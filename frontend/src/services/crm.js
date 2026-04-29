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

// AI-drafted outreach — returns { variants: [{ tone, subject, body }, ...] }.
// Privacy: this endpoint runs the prompt with sensitive=True on the backend
// so the LLM call stays on local Ollama.
export const draftOutreach = (contactId) =>
  req(`/contacts/${contactId}/draft-outreach`, { method: 'POST' });

// AI lead scoring — returns { score, bucket, reason, scored_at, icp_set }.
// score is 0-100, bucket is "high"/"medium"/"low"/"spam"/null, both null
// when no ICP is set yet (the response carries icp_set=false in that case).
export const scoreContactFit = (contactId) =>
  req(`/contacts/${contactId}/score-fit`, { method: 'POST' });

// Workspace ICP description — used by the scorer. The CRM `req` helper
// already prefixes /api/crm; for the workspace path we call fetch directly
// using the same auth headers.
const WS_BASE = '/api/workspace';
function _wsHeaders() {
  const h = { 'Content-Type': 'application/json' };
  const t = getToken(); if (t) h.Authorization = `Bearer ${t}`;
  const b = getBusinessId(); if (b) h['X-Business-Id'] = b;
  return h;
}
export const readIcp = async () => {
  const r = await fetch(`${WS_BASE}/icp`, { headers: _wsHeaders() });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
};
export const writeIcp = async (icp_description) => {
  const r = await fetch(`${WS_BASE}/icp`, {
    method: 'PUT', headers: _wsHeaders(),
    body: JSON.stringify({ icp_description }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
};

// Email-paste lead capture: extract preview, then save with edits.
export const extractEmail = (raw_email, override_email = null) =>
  req('/leads/extract-email', {
    method: 'POST',
    body: JSON.stringify({ raw_email, override_email }),
  });
export const saveLeadFromEmail = (payload) =>
  req('/leads/from-email', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// BANT extraction from a pasted prospect reply. Returns the structured
// signals + an optional `suggested_stage` the user can advance the deal
// to with one click. Privacy: prompt sees reply content → sensitive=True.
export const extractBant = (contactId, reply_text) =>
  req(`/contacts/${contactId}/extract-bant`, {
    method: 'POST',
    body: JSON.stringify({ reply_text }),
  });

export const DEAL_STAGES = ['lead', 'qualified', 'proposal', 'negotiation', 'won', 'lost'];
export const INTERACTION_TYPES = ['call', 'email', 'meeting', 'note'];
