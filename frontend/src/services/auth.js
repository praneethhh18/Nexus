const BASE = '/api/auth';

export function getToken() { return localStorage.getItem('nexus_token'); }
export function getUser() { try { return JSON.parse(localStorage.getItem('nexus_user')); } catch { return null; } }
export function isLoggedIn() { return !!getToken(); }

export function getBusinessId() { return localStorage.getItem('nexus_business_id') || ''; }
export function setBusinessId(id) {
  if (id) localStorage.setItem('nexus_business_id', id);
  else localStorage.removeItem('nexus_business_id');
}
export function getBusinesses() {
  try { return JSON.parse(localStorage.getItem('nexus_businesses')) || []; }
  catch { return []; }
}
export function setBusinesses(list) {
  localStorage.setItem('nexus_businesses', JSON.stringify(list || []));
}
export function getCurrentBusiness() {
  const id = getBusinessId();
  return getBusinesses().find(b => b.id === id) || getBusinesses()[0] || null;
}

export function setSession(data) {
  localStorage.setItem('nexus_token', data.access_token);
  if (data.refresh_token) localStorage.setItem('nexus_refresh', data.refresh_token);
  localStorage.setItem('nexus_user', JSON.stringify(data.user));
  if (data.businesses) setBusinesses(data.businesses);
  if (data.current_business_id) setBusinessId(data.current_business_id);
  else if (data.businesses?.[0]?.id) setBusinessId(data.businesses[0].id);
}

export function clearSession() {
  localStorage.removeItem('nexus_token');
  localStorage.removeItem('nexus_refresh');
  localStorage.removeItem('nexus_user');
  localStorage.removeItem('nexus_businesses');
  localStorage.removeItem('nexus_business_id');
}

async function authRequest(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function signup(email, name, password) {
  const data = await authRequest('/signup', { email, name, password });
  setSession(data);
  return data;
}

export async function login(email, password) {
  const data = await authRequest('/login', { email, password });
  setSession(data);
  return data;
}

export function logout() { clearSession(); window.location.href = '/login'; }

export async function refreshToken() {
  const refresh = localStorage.getItem('nexus_refresh');
  if (!refresh) throw new Error('No refresh token');
  const data = await authRequest('/refresh', { refresh_token: refresh });
  localStorage.setItem('nexus_token', data.access_token);
  return data;
}

export async function forgotPassword(email) {
  return authRequest('/forgot-password', { email });
}

export async function resetPassword(token, new_password) {
  return authRequest('/reset-password', { token, new_password });
}

export function switchBusiness(businessId) {
  const biz = getBusinesses().find(b => b.id === businessId);
  if (!biz) throw new Error('Unknown business');
  setBusinessId(businessId);
  // Inform the rest of the app so pages can re-fetch
  window.dispatchEvent(new CustomEvent('nexus-business-changed', { detail: businessId }));
  return biz;
}
