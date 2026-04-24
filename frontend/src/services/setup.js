// Unauthenticated setup wizard client.
// Deliberately skips headers() — at install time no user exists yet.

async function req(path, opts = {}) {
  const res = await fetch(path, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
  });
  if (!res.ok) {
    const txt = await res.text();
    let msg = txt;
    try { msg = JSON.parse(txt).detail || txt; } catch {}
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return res.json();
}

export const getSetupStatus = () => req('/api/setup/status');
export const pullSetupModel = (name) =>
  req('/api/setup/pull-model', { method: 'POST', body: JSON.stringify({ name }) });
export const chooseSetupModel = (name) =>
  req('/api/setup/choose-model', { method: 'POST', body: JSON.stringify({ name }) });
export const completeSetup = () =>
  req('/api/setup/complete', { method: 'POST' });
