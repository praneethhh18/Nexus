/**
 * Tiny in-memory data cache with TTL.
 *
 * Goal: stale-while-revalidate for the data-heavy pages (Dashboard, Invoices,
 * CRM, Tasks). Without this, every navigation unmounts the page component →
 * state resets to defaults → skeleton flashes → fetch runs → data re-appears.
 * The user perceives 3-5s of "loading" on every back/forward, even when the
 * data hasn't changed.
 *
 * With this:
 *   - Cache persists across mount/unmount (module-level Map, same JS process)
 *   - Components restore the last-known data SYNCHRONOUSLY on mount
 *   - A background fetch runs anyway, replacing the cached value when fresh
 *     data lands. UI updates smoothly with no skeleton flash.
 *
 * Not used: a request cache (e.g. de-duping in-flight fetches). That's a
 * separate concern; keep this minimal.
 *
 * Tab close / hard refresh clears everything — that's fine, it's a perf
 * hint, not a source of truth. The DB is the source of truth.
 *
 * Business scoping: every key MUST be namespaced by business_id so switching
 * workspaces doesn't show another tenant's data for the first paint. Use
 * `keyFor(prefix)` instead of hand-rolling keys.
 */

const cache = new Map();   // key -> { data, expiresAt }
const DEFAULT_TTL_MS = 60 * 1000;   // 1 minute is the sweet spot for SMB UI

export function getCached(key) {
  const entry = cache.get(key);
  if (!entry) return null;
  if (entry.expiresAt < Date.now()) {
    cache.delete(key);
    return null;
  }
  return entry.data;
}

export function setCached(key, data, ttlMs = DEFAULT_TTL_MS) {
  cache.set(key, { data, expiresAt: Date.now() + ttlMs });
}

/**
 * Drop everything that begins with `prefix`. Call this when an action mutates
 * data so the next mount re-fetches instead of showing a stale snapshot
 * (e.g. invoice marked paid → invalidate the 'invoices:*' and 'dashboard:*'
 * keys for the current business).
 *
 * Pass no prefix to wipe the whole cache (e.g. on logout / business switch).
 */
export function invalidateCache(prefix) {
  if (!prefix) { cache.clear(); return; }
  for (const k of Array.from(cache.keys())) {
    if (k.startsWith(prefix)) cache.delete(k);
  }
}

/**
 * Build a cache key namespaced by the current business id so workspace
 * switches don't leak data between tenants. Falls back to 'anon' for
 * the few endpoints that aren't tenant-scoped.
 */
export function keyFor(prefix) {
  const bid = (typeof localStorage !== 'undefined'
    ? localStorage.getItem('nexus_business_id')
    : '') || 'anon';
  return `${prefix}::${bid}`;
}

// Listen for the business-changed event the auth service dispatches when the
// user switches workspaces. Wipe the cache so we don't paint the previous
// workspace's data for a frame on the new one.
if (typeof window !== 'undefined') {
  window.addEventListener('nexus-business-changed', () => invalidateCache());
}
