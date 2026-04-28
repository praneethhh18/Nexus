/**
 * NexusAgent service worker — real, not a stub.
 *
 * Strategy by request type:
 *
 *   /api/*           → no SW involvement at all (tenant data must be fresh).
 *
 *   navigation       → network-first, fall back to cached /index.html when
 *                      offline. SPAs serve a single index.html for every route,
 *                      so this keeps deep links + back-button navigation
 *                      working without a connection.
 *
 *   /assets/*        → cache-first. Vite emits content-hashed file names
 *                      (`Dashboard-DhDot1Ag.js`), so a stale cache hit is
 *                      always safe — once the hash changes, the cache misses
 *                      and we fetch the new version.
 *
 *   icons / manifest → stale-while-revalidate. Serve from cache instantly,
 *                      refresh the cache in the background.
 *
 * Cache versioning: bump SHELL_CACHE / ASSET_CACHE if the shape changes,
 * old clients self-clean in `activate`.
 */
const SHELL_CACHE  = 'nexus-shell-v2';
const ASSET_CACHE  = 'nexus-assets-v2';
const STATIC_CACHE = 'nexus-static-v2';

const SHELL_URLS = ['/', '/index.html'];

const log = (...a) => { try { console.log('[SW]', ...a); } catch {} };


// ── Install: precache the shell ─────────────────────────────────────────────
self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(SHELL_CACHE);
    // addAll fails as a unit, so swallow and retry individually for resilience.
    try {
      await cache.addAll(SHELL_URLS);
    } catch (e) {
      log('install: bulk addAll failed, falling back to individual', e);
      for (const url of SHELL_URLS) {
        try { await cache.add(url); } catch (err) { log('install: skip', url, err); }
      }
    }
  })());
  self.skipWaiting();
});


// ── Activate: drop old cache versions ───────────────────────────────────────
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keep = new Set([SHELL_CACHE, ASSET_CACHE, STATIC_CACHE]);
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => !keep.has(k)).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});


// ── Fetch ───────────────────────────────────────────────────────────────────
self.addEventListener('fetch', (event) => {
  const req = event.request;
  // Only intercept GETs — anything else (POST/PATCH/DELETE) goes straight through.
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Same-origin only. Cross-origin (e.g. CDN, fonts) we don't touch.
  if (url.origin !== self.location.origin) return;

  // API: never touch.
  if (url.pathname.startsWith('/api/')) return;

  // Navigation request — HTML page load, including SPA route changes.
  if (req.mode === 'navigate' || (req.headers.get('accept') || '').includes('text/html')) {
    event.respondWith(handleNavigation(req));
    return;
  }

  // Vite content-hashed assets — long-lived, cache-first.
  if (url.pathname.startsWith('/assets/')) {
    event.respondWith(cacheFirst(req, ASSET_CACHE));
    return;
  }

  // Other static (favicon, icons, manifest) — stale-while-revalidate.
  if (
    url.pathname === '/manifest.webmanifest' ||
    url.pathname.startsWith('/icons') ||
    url.pathname.startsWith('/favicon') ||
    url.pathname === '/sw.js'
  ) {
    event.respondWith(staleWhileRevalidate(req, STATIC_CACHE));
    return;
  }

  // Default: try network, fall back to whatever cache has.
  event.respondWith(networkFirst(req, STATIC_CACHE));
});


// ── Strategies ───────────────────────────────────────────────────────────────
async function handleNavigation(req) {
  const cache = await caches.open(SHELL_CACHE);
  try {
    const fresh = await fetch(req);
    // Refresh the cached shell on every successful navigation so an updated
    // index.html (= new bundle hashes) becomes the offline fallback.
    if (fresh && fresh.ok) {
      cache.put('/index.html', fresh.clone()).catch(() => {});
    }
    return fresh;
  } catch (e) {
    log('navigation offline; serving cached shell', e);
    const cached = await cache.match('/index.html') || await cache.match('/');
    if (cached) return cached;
    return new Response(
      '<h1>You are offline</h1><p>Reconnect to load NexusAgent.</p>',
      { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } },
    );
  }
}


async function cacheFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req);
  if (hit) return hit;
  try {
    const fresh = await fetch(req);
    if (fresh && fresh.ok) cache.put(req, fresh.clone()).catch(() => {});
    return fresh;
  } catch {
    return hit || new Response('', { status: 504 });
  }
}


async function networkFirst(req, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const fresh = await fetch(req);
    if (fresh && fresh.ok) cache.put(req, fresh.clone()).catch(() => {});
    return fresh;
  } catch {
    const hit = await cache.match(req);
    if (hit) return hit;
    return new Response('', { status: 504 });
  }
}


async function staleWhileRevalidate(req, cacheName) {
  const cache = await caches.open(cacheName);
  const hit = await cache.match(req);
  const fetchPromise = fetch(req).then((fresh) => {
    if (fresh && fresh.ok) cache.put(req, fresh.clone()).catch(() => {});
    return fresh;
  }).catch(() => null);
  return hit || fetchPromise || new Response('', { status: 504 });
}


// Allow the page to trigger an immediate update.
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
