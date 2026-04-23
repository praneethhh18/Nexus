import { getToken, getBusinessId, setBusinesses } from './auth';

const BASE = '/api/businesses';

function headers() {
  const h = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) h['Authorization'] = `Bearer ${token}`;
  const biz = getBusinessId();
  if (biz) h['X-Business-Id'] = biz;
  return h;
}

async function req(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, { ...opts, headers: { ...headers(), ...(opts.headers || {}) } });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function listBusinesses() {
  const list = await req('');
  setBusinesses(list);
  return list;
}

export const createBusiness = (payload) =>
  req('', { method: 'POST', body: JSON.stringify(payload) }).then(async (biz) => {
    await listBusinesses();
    return biz;
  });

export const getBusiness = (id) => req(`/${id}`);
export const updateBusiness = (id, updates) =>
  req(`/${id}`, { method: 'PATCH', body: JSON.stringify(updates) }).then(async (biz) => {
    await listBusinesses();
    return biz;
  });
export const deleteBusiness = (id) =>
  req(`/${id}`, { method: 'DELETE' }).then(async (r) => {
    await listBusinesses();
    return r;
  });

export const listMembers = (id) => req(`/${id}/members`);
export const addMember = (id, user_id, role = 'member') =>
  req(`/${id}/members`, { method: 'POST', body: JSON.stringify({ user_id, role }) });
export const removeMember = (id, user_id) =>
  req(`/${id}/members/${user_id}`, { method: 'DELETE' });
