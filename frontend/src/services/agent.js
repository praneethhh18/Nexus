import { getToken, getBusinessId } from './auth';

const BASE = '/api';

function headers() {
  const h = { 'Content-Type': 'application/json' };
  const t = getToken();
  if (t) h['Authorization'] = `Bearer ${t}`;
  const b = getBusinessId();
  if (b) h['X-Business-Id'] = b;
  return h;
}

async function req(path, opts = {}) {
  let res;
  try {
    res = await fetch(`${BASE}${path}`, { ...opts, headers: { ...headers(), ...(opts.headers || {}) } });
  } catch (netErr) {
    throw new Error(`Cannot reach backend (is the API server running on :8000?)`);
  }
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Session expired'); }
  const contentType = res.headers.get('content-type') || '';
  if (!res.ok) {
    const txt = await res.text();
    if (contentType.includes('text/html')) {
      throw new Error(`Backend not reachable on ${BASE}${path} (got HTML — check that uvicorn is running on :8000).`);
    }
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  if (!contentType.includes('application/json')) {
    const preview = (await res.text()).slice(0, 60);
    throw new Error(`Expected JSON from ${BASE}${path}, got: ${preview}...`);
  }
  return res.json();
}

// Agent
export const agentChat = (query, conversation_id = null) =>
  req('/agent/chat', { method: 'POST', body: JSON.stringify({ query, conversation_id }) });

export const listAgentTools = () => req('/agent/tools');

// Approvals
export const listApprovals = (status = '', limit = 100) => {
  const qs = new URLSearchParams();
  if (status) qs.set('status', status);
  qs.set('limit', limit);
  return req(`/approvals?${qs}`);
};
export const approvalsPendingCount = () => req('/approvals/pending-count');
export const getApproval = (id) => req(`/approvals/${id}`);
export const approveAction = (id) => req(`/approvals/${id}/approve`, { method: 'POST' });
export const rejectAction = (id, reason = '') =>
  req(`/approvals/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) });

// Memory
export const listMemoryApi = (search = '', limit = 200) => {
  const qs = new URLSearchParams();
  if (search) qs.set('search', search);
  qs.set('limit', limit);
  return req(`/memory?${qs}`);
};
export const addMemoryApi = (body) => req('/memory', { method: 'POST', body: JSON.stringify(body) });
export const updateMemoryApi = (id, body) => req(`/memory/${id}`, { method: 'PATCH', body: JSON.stringify(body) });
export const deleteMemoryApi = (id) => req(`/memory/${id}`, { method: 'DELETE' });
