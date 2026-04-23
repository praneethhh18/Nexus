import { getToken, getBusinessId } from './auth';

export async function seedSampleData() {
  const headers = { 'Content-Type': 'application/json' };
  const t = getToken();
  if (t) headers['Authorization'] = `Bearer ${t}`;
  const b = getBusinessId();
  if (b) headers['X-Business-Id'] = b;
  const res = await fetch('/api/seed/sample-data', { method: 'POST', headers });
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}
