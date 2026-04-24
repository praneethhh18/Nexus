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

// Custom agent CRUD
export const listCustomAgents = () => req('/api/custom-agents');
export const getCustomAgent   = (id) => req(`/api/custom-agents/${encodeURIComponent(id)}`);
export const createCustomAgent = (data) =>
  req('/api/custom-agents', { method: 'POST', body: JSON.stringify(data) });
export const updateCustomAgent = (id, data) =>
  req(`/api/custom-agents/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(data) });
export const deleteCustomAgent = (id) =>
  req(`/api/custom-agents/${encodeURIComponent(id)}`, { method: 'DELETE' });
export const runCustomAgent = (id) =>
  req(`/api/custom-agents/${encodeURIComponent(id)}/run`, { method: 'POST' });

// Templates
export const listAgentTemplates = () => req('/api/custom-agents/templates');
export const createFromTemplate = (template_key, overrides = {}) =>
  req('/api/custom-agents/from-template', {
    method: 'POST', body: JSON.stringify({ template_key, overrides }),
  });

// Schedule prefs for built-in agents
export const getAgentSchedule = () => req('/api/agents/schedule');
export const setAgentInterval = (agent_key, interval_minutes) =>
  req(`/api/agents/schedule/${encodeURIComponent(agent_key)}`, {
    method: 'PATCH', body: JSON.stringify({ interval_minutes }),
  });
export const resetAgentInterval = (agent_key) =>
  req(`/api/agents/schedule/${encodeURIComponent(agent_key)}`, { method: 'DELETE' });

// Tool registry (from existing agent endpoint)
export const listAgentTools = () => req('/api/agent/tools');
