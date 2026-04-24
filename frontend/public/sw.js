/**
 * Service worker stub for PWA installability.
 *
 * Intentionally minimal: we don't cache API responses (stale data would
 * lie about tenant state). We only satisfy the "service worker exists and
 * fetches at least one URL" rule so browsers treat the app as installable.
 * A richer caching strategy is a Phase-8 follow-up.
 */
const CACHE_NAME = 'nexusagent-shell-v1';
const SHELL_URLS = ['/'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  // Never cache /api/* — tenant data must be fresh, not shelf.
  if (url.pathname.startsWith('/api/')) return;
  // Simple cache-first for the shell, fall back to network.
  event.respondWith(
    caches.match(event.request).then((hit) => hit || fetch(event.request).catch(() => hit))
  );
});
