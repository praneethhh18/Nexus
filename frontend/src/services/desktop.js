/**
 * Desktop bridge — no-op in the browser, native in Electron.
 *
 * The Electron preload exposes a tiny `window.nexus` surface; these helpers
 * check for it before calling so the same code runs cleanly in a regular
 * browser tab too.
 */

export const isDesktop = () =>
  typeof window !== 'undefined' && !!window.nexus && window.nexus.isDesktop === true;


/**
 * Fire a native OS notification when running inside the desktop app.
 * Falls back to the in-browser Notifications API, or silently returns if
 * neither is available.
 */
export async function nativeNotify({ title, body, urgent = false } = {}) {
  if (isDesktop()) {
    try { return await window.nexus.notify({ title, body, urgent }); }
    catch (e) { return { ok: false, error: String(e.message || e) }; }
  }
  // Web fallback — requires the user to have granted notification permission.
  if (typeof window !== 'undefined' && 'Notification' in window && Notification.permission === 'granted') {
    try { new Notification(title || 'NexusAgent', { body }); return { ok: true }; }
    catch (e) { return { ok: false, error: String(e.message || e) }; }
  }
  return { ok: false, error: 'No notification channel available' };
}


/** Open an external URL in the user's default browser (Electron only). */
export function openExternal(url) {
  if (isDesktop()) return window.nexus.openExternal(url);
  if (typeof window !== 'undefined') window.open(url, '_blank', 'noopener');
  return Promise.resolve({ ok: true });
}


/** Probe the local Ollama daemon. Returns null if not running inside Electron. */
export async function probeOllama() {
  if (!isDesktop()) return null;
  try { return await window.nexus.probeOllama(); }
  catch { return null; }
}
