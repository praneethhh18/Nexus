/**
 * Email templates client — talks to /api/email-templates routes.
 * Pairs with the agent-facing tools (list/create/render/send_email_from_template)
 * but exposes the same surface for direct UI users who don't want to chat.
 */
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
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch { /* not json */ }
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

export const listEmailTemplates   = () => req('/api/email-templates').then(r => r.templates || []);
export const getEmailTemplate     = (id) => req(`/api/email-templates/${encodeURIComponent(id)}`);
export const createEmailTemplate  = (data) =>
  req('/api/email-templates', { method: 'POST', body: JSON.stringify(data) });
export const updateEmailTemplate  = (id, data) =>
  req(`/api/email-templates/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(data) });
export const deleteEmailTemplate  = (id) =>
  req(`/api/email-templates/${encodeURIComponent(id)}`, { method: 'DELETE' });
export const renderEmailTemplate  = (id, variables) =>
  req(`/api/email-templates/${encodeURIComponent(id)}/render`, {
    method: 'POST', body: JSON.stringify({ variables: variables || {} }),
  });
