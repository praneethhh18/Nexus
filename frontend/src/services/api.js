const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }
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
export const updateConversation = (id, title) =>
  request(`/conversations/${id}`, { method: 'PATCH', body: JSON.stringify({ title }) });

// Database
export const getTables = () => request('/database/tables');
export const getTableDetail = (name, limit = 50) => request(`/database/tables/${name}?limit=${limit}`);
export const importData = async (file, tableName, ifExists = 'fail') => {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/database/import?table_name=${tableName}&if_exists=${ifExists}`, {
    method: 'POST', body: form,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};
export const previewImport = async (file) => {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BASE}/database/import/preview`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
};

// Reports
export const generateReport = (query) =>
  request('/reports/generate', { method: 'POST', body: JSON.stringify({ query }) });
export const getReports = () => request('/reports');
export const getReportUrl = (filename) => `${BASE}/reports/download/${filename}`;

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
  const res = await fetch(`${BASE}/knowledge/upload`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
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
