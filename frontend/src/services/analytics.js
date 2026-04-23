import { getToken, getBusinessId } from './auth';

function headers() {
  const h = { 'Content-Type': 'application/json' };
  const t = getToken();
  if (t) h['Authorization'] = `Bearer ${t}`;
  const b = getBusinessId();
  if (b) h['X-Business-Id'] = b;
  return h;
}

async function req(path) {
  const res = await fetch(path, { headers: headers() });
  if (res.status === 401) { window.location.href = '/login'; throw new Error('Session expired'); }
  const ctype = res.headers.get('content-type') || '';
  if (!res.ok) {
    const txt = await res.text();
    if (ctype.includes('text/html')) throw new Error(`Backend not reachable on ${path}`);
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export const pipelineVelocity = () => req('/api/analytics/pipeline-velocity');
export const revenueForecast = (months = 6) => req(`/api/analytics/revenue-forecast?horizon_months=${months}`);
export const agentImpact = (days = 30) => req(`/api/analytics/agent-impact?days=${days}`);
export const churnRisk = (maxDeals = 15) => req(`/api/analytics/churn-risk?max_deals=${maxDeals}`);
