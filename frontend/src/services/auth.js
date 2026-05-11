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

async function readAuthError(res) {
  const text = await res.text().catch(() => '');
  if (!text) return `HTTP ${res.status}`;

  try {
    const data = JSON.parse(text);
    if (typeof data.detail === 'string') return data.detail;
    if (typeof data.message === 'string') return data.message;
    return JSON.stringify(data);
  } catch {
    return text;
  }
}

async function authRequest(path, body) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 15000);

  let res;
  try {
    res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('API did not respond. Restart the backend on port 8000 and try again.');
    }
    throw new Error('Cannot reach the API. Make sure the backend is running on port 8000.');
  } finally {
    window.clearTimeout(timeoutId);
  }

  if (!res.ok) {
    throw new Error(await readAuthError(res));
  }
  return res.json();
}

export async function signup(email, name, password) {
  const data = await authRequest('/signup', { email, name, password });
  // verification_required=true → no access token returned. Caller (Login.jsx)
  // shows the "check your inbox" screen instead of redirecting to dashboard.
  // verification_required=false / undefined → legacy auto-login flow (dev).
  if (!data.verification_required) setSession(data);
  return data;
}

export async function verifyEmail(token) {
  const data = await authRequest('/verify-email', { token });
  setSession(data);   // verify returns full tokens — log the user straight in
  return data;
}

export async function resendVerification(email) {
  return authRequest('/resend-verification', { email });
}

export async function login(email, password, totpCode = null) {
  const body = { email, password };
  if (totpCode) body.totp_code = totpCode;
  const data = await authRequest('/login', body);
  if (data.requires_2fa) {
    // Don't call setSession — no token yet. Caller shows 2FA prompt.
    return data;
  }
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
