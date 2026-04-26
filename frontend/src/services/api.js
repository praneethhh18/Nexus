import { getToken, getBusinessId } from './auth';

const BASE = '/api';

function buildHeaders(extra = {}) {
  const headers = { 'Content-Type': 'application/json', ...extra };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const biz = getBusinessId();
  if (biz) headers['X-Business-Id'] = biz;
  return headers;
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, { ...options, headers: buildHeaders(options.headers) });
  if (res.status === 401 && !path.includes('/auth/')) {
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
  return res.json();
}

// Shared helper for multipart requests (file uploads) — must also send auth + business headers
async function formRequest(path, form) {
  const token = getToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const biz = getBusinessId();
  if (biz) headers['X-Business-Id'] = biz;
  const res = await fetch(`${BASE}${path}`, { method: 'POST', body: form, headers });
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Session expired'); }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Health & Stats
export const getHealth = () => request('/health');
export const getStats = () => request('/stats');

// Chat
export const sendMessage = (query, conversationId = null) =>
  request('/chat', {
    method: 'POST',
    body: JSON.stringify({ query, conversation_id: conversationId }),
  });

// Conversations
export const getConversations = () => request('/conversations');
export const getConversation = (id) => request(`/conversations/${id}`);
export const createConversation = () => request('/conversations', { method: 'POST' });
export const deleteConversation = (id) => request(`/conversations/${id}`, { method: 'DELETE' });
export const setConversationSensitive = (id, sensitive) =>
  request(`/conversations/${id}/sensitive`, {
    method: 'PATCH',
    body: JSON.stringify({ sensitive }),
  });
export const updateConversation = (id, title) =>
  request(`/conversations/${id}`, { method: 'PATCH', body: JSON.stringify({ title }) });

// Database
export const getTables = () => request('/database/tables');
export const getTableDetail = (name, limit = 50) => request(`/database/tables/${name}?limit=${limit}`);
export const importData = async (file, tableName, ifExists = 'fail') => {
  const form = new FormData();
  form.append('file', file);
  return formRequest(`/database/import?table_name=${encodeURIComponent(tableName)}&if_exists=${ifExists}`, form);
};
export const previewImport = async (file) => {
  const form = new FormData();
  form.append('file', file);
  return formRequest('/database/import/preview', form);
};

// Reports
export const generateReport = (query) =>
  request('/reports/generate', { method: 'POST', body: JSON.stringify({ query }) });
export const getReports = () => request('/reports');
export const getReportUrl = (filename) => `${BASE}/reports/download/${filename}`;
export const downloadReport = async (filename) => {
  const token = getToken();
  const biz = getBusinessId();
  const h = {};
  if (token) h['Authorization'] = `Bearer ${token}`;
  if (biz) h['X-Business-Id'] = biz;
  const res = await fetch(`${BASE}/reports/download/${encodeURIComponent(filename)}`, { headers: h });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt || `HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};

// What-If
export const runWhatIf = (scenario) =>
  request('/whatif', { method: 'POST', body: JSON.stringify({ scenario }) });

// Query History
export const getHistory = (params = {}) => {
  const qs = new URLSearchParams();
  if (params.search) qs.set('search', params.search);
  if (params.intent) qs.set('intent', params.intent);
  if (params.starred) qs.set('starred', 'true');
  if (params.limit) qs.set('limit', params.limit);
  return request(`/history?${qs}`);
};
export const toggleStar = (id) => request(`/history/${id}/star`, { method: 'POST' });
export const deleteHistoryEntry = (id) => request(`/history/${id}`, { method: 'DELETE' });
export const clearHistory = () => request('/history', { method: 'DELETE' });

// Knowledge Base
export const getKnowledge = () => request('/knowledge');
export const uploadDocument = async (file) => {
  const form = new FormData();
  form.append('file', file);
  return formRequest('/knowledge/upload', form);
};

// Monitor
export const getMonitorStatus = () => request('/monitor/status');
export const runMonitor = () => request('/monitor/run', { method: 'POST' });

// Settings
export const getSettings = () => request('/settings');
export const resetLLM = () => request('/settings/reset-llm', { method: 'POST' });
export const clearCache = () => request('/settings/clear-cache', { method: 'POST' });

// Export
export const exportMarkdown = (messages) =>
  request('/export/markdown', { method: 'POST', body: JSON.stringify(messages) });
export const exportPdfUrl = `${BASE}/export/pdf`;

// Workflows
export const getWorkflows = () => request('/workflows');
export const getWorkflow = (id) => request(`/workflows/${id}`);
export const saveWorkflow = (wf) => request('/workflows', { method: 'POST', body: JSON.stringify(wf) });
export const deleteWorkflow = (id) => request(`/workflows/${id}`, { method: 'DELETE' });
export const toggleWorkflow = (id, enabled) => request(`/workflows/${id}/toggle`, { method: 'POST', body: JSON.stringify({ enabled }) });
export const runWorkflow = (id) => request(`/workflows/${id}/run`, { method: 'POST' });
export const runWorkflowPreview = (wf) => request('/workflows/run-preview', { method: 'POST', body: JSON.stringify(wf) });
export const getNodeTypes = () => request('/workflows/node-types');
export const getWorkflowTemplates = () => request('/workflows/templates');
export const getSchedulerJobs = () => request('/workflows/scheduler/jobs');
export const getWorkflowHistory = (limit = 30) => request(`/workflows/scheduler/history?limit=${limit}`);
export const generateWorkflowFromText = (description) =>
  request('/workflows/generate-from-text', { method: 'POST', body: JSON.stringify({ description }) });

// Notifications
export const getNotifications = (unread = false) => request(`/notifications?unread=${unread}`);
export const markNotificationRead = (id) => request(`/notifications/${id}/read`, { method: 'POST' });
export const markAllNotificationsRead = () => request('/notifications/read-all', { method: 'POST' });

// SQL Editor
export const runRawSQL = (sql) => {
  return request('/database/tables/__raw_query', { method: 'POST', body: JSON.stringify({ sql }) })
    .catch(() => request('/chat', { method: 'POST', body: JSON.stringify({ query: sql }) }));
};

// Businesses (re-exported for convenience)
export {
  listBusinesses, createBusiness, getBusiness, updateBusiness, deleteBusiness,
  listMembers, addMember, removeMember,
} from './businesses';
