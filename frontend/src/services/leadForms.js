import { getToken, getBusinessId } from './auth';

function headers() {
  const h = { 'Content-Type': 'application/json' };
  const t = getToken();
  if (t) h.Authorization = `Bearer ${t}`;
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

// ── Auth-gated CRUD ───────────────────────────────────────────────────────
export const listLeadForms = () => req('/api/lead-forms');

export const createLeadForm = (payload) =>
  req('/api/lead-forms', { method: 'POST', body: JSON.stringify(payload) });

export const updateLeadForm = (id, payload) =>
  req(`/api/lead-forms/${encodeURIComponent(id)}`, {
    method: 'PATCH', body: JSON.stringify(payload),
  });

export const archiveLeadForm = (id) =>
  req(`/api/lead-forms/${encodeURIComponent(id)}`, { method: 'DELETE' });

// ── Public (no-auth) helpers ──────────────────────────────────────────────
export async function getPublicForm(slug) {
  const r = await fetch(`/api/public/forms/${encodeURIComponent(slug)}`);
  if (!r.ok) {
    let msg = `HTTP ${r.status}`;
    try { msg = (await r.json()).detail || msg; } catch {}
    throw new Error(msg);
  }
  return r.json();
}

export async function submitPublicForm(slug, payload, via = '') {
  const body = { form_slug: slug, ...payload };
  if (via) body.via = via;
  const r = await fetch('/api/public/leads', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    let msg = `HTTP ${r.status}`;
    try { msg = (await r.json()).detail || msg; } catch {}
    throw new Error(msg);
  }
  return r.json();
}

// ── URL helpers ──────────────────────────────────────────────────────────
export function formShareUrl(slug, via = '') {
  const origin = typeof window !== 'undefined' && window.location
    ? window.location.origin : '';
  const u = `${origin}/f/${encodeURIComponent(slug)}`;
  return via ? `${u}?via=${encodeURIComponent(via)}` : u;
}

// ── Field catalogue, used by the builder UI ─────────────────────────────
// Mirrors api/routers/lead_forms.py ALLOWED_FIELD_KEYS. Keeping it client-
// side means the builder doesn't have to round-trip to know what's allowed.
export const FORM_FIELD_CATALOGUE = [
  { key: 'name',     label: 'Full name',        defaultRequired: true,
    placeholder: 'Your name',                   inputType: 'text' },
  { key: 'email',    label: 'Email',            defaultRequired: true,
    placeholder: 'you@company.com',             inputType: 'email' },
  { key: 'phone',    label: 'Phone / WhatsApp', defaultRequired: false,
    placeholder: '+91 98765 43210',             inputType: 'tel' },
  { key: 'company',  label: 'Company',          defaultRequired: false,
    placeholder: 'Company name',                inputType: 'text' },
  { key: 'title',    label: 'Your role',        defaultRequired: false,
    placeholder: 'Founder / Sales head / …',    inputType: 'text' },
  { key: 'city',     label: 'City',             defaultRequired: false,
    placeholder: 'Bangalore',                   inputType: 'text' },
  { key: 'industry', label: 'Industry',         defaultRequired: false,
    placeholder: 'SaaS / Retail / …',           inputType: 'text' },
  { key: 'budget',   label: 'Budget',           defaultRequired: false,
    placeholder: '₹50k – ₹2L',                  inputType: 'text' },
  { key: 'timeline', label: 'Timeline',         defaultRequired: false,
    placeholder: 'When do you want to start?',  inputType: 'text' },
  { key: 'message',  label: 'Message',          defaultRequired: false,
    placeholder: 'What can we help with?',      inputType: 'textarea' },
];
