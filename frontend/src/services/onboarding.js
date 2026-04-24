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

export const getOnboardingState = () => req('/api/onboarding');
export const completeOnboardingStep = (stepKey) =>
  req(`/api/onboarding/complete/${encodeURIComponent(stepKey)}`, { method: 'POST' });
export const skipOnboarding = () => req('/api/onboarding/skip', { method: 'POST' });
export const reopenOnboarding = () => req('/api/onboarding/reopen', { method: 'POST' });

// Notification preferences
export const getNotificationPrefs = () => req('/api/notifications/prefs');
export const setNotificationPrefs = (updates) =>
  req('/api/notifications/prefs', { method: 'PATCH', body: JSON.stringify(updates) });

export const markNotificationRead = (id) =>
  req(`/api/notifications/${encodeURIComponent(id)}/read`, { method: 'POST' });
export const deleteNotification = (id) =>
  req(`/api/notifications/${encodeURIComponent(id)}`, { method: 'DELETE' });
