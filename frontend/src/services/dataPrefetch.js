/**
 * Per-route data prefetchers.
 *
 * The story so far:
 *   - dataCache.js gives us stale-while-revalidate so REVISITING a page is
 *     instant.
 *   - routePrefetch.js warms the JS chunks so the page's CODE is ready.
 *   - This file warms the page's DATA so the first time the user clicks
 *     "Invoices" or "Documents", the cache is already filled — no API
 *     round-trip blocking the paint.
 *
 * Strategy:
 *   - Right after Layout mounts (Dashboard rendered, user is reading),
 *     fire a background fetch for every heavy page's data in idle slices.
 *   - Each fetcher writes to the same cache key its page reads from on
 *     mount. The page restores synchronously from cache → instant.
 *   - All fetches are wrapped in catch — a failed prefetch must never
 *     surface an error or break navigation.
 *
 * Why per-route fetchers (not "fetch everything")?
 *   We don't want to thunder-herd the API on first paint. Each route's
 *   prefetcher only runs when scheduled, and re-checks the cache before
 *   hitting the wire. De-dup via an in-flight map so hover-spam doesn't
 *   trigger duplicate fetches.
 */

import { setCached, getCached, keyFor } from './dataCache';

const inflight = new Map();   // path -> Promise (de-dupe hover/idle races)

// Each fetcher is async. Wrap in withDedupe() so multiple triggers (hover +
// idle + click) for the same path share a single in-flight promise.
function withDedupe(path, fn) {
  if (inflight.has(path)) return inflight.get(path);
  const p = (async () => {
    try { await fn(); } catch { /* prefetch is best-effort */ }
  })().finally(() => inflight.delete(path));
  inflight.set(path, p);
  return p;
}


// ── Per-route fetchers ──────────────────────────────────────────────────
// Keys MUST match the cache keys the destination pages use. Logic mirrors
// each page's `reload()` but only the slice needed for the first paint.

async function _prefetchDashboard() {
  const KEY = 'dashboard:overview';
  if (getCached(keyFor(KEY))) return;
  const [api, tasksMod, invMod] = await Promise.all([
    import('./api'), import('./tasks'), import('./invoices'),
  ]);
  const [ns, todayList, inv] = await Promise.all([
    api.getNotifications().catch(() => ({ notifications: [] })),
    tasksMod.listTasks({ due_window: 'today', status: 'active', limit: 5 }).catch(() => []),
    invMod.invoiceSummary().catch(() => null),
  ]);
  // Partial prime — the page's reload() will fill the rest. Enough for
  // TodaysFocus to render the right state instead of the skeleton.
  setCached(keyFor(KEY), {
    notifs: (ns.notifications || []).slice(0, 5),
    todayTasks: todayList,
    invoices: inv,
  });
}

async function _prefetchInvoices() {
  const KEY = 'invoices:page';
  if (getCached(keyFor(KEY))) return;
  const [invMod, crmMod] = await Promise.all([import('./invoices'), import('./crm')]);
  const [list, s, cts, cos] = await Promise.all([
    invMod.listInvoices().catch(() => []),
    invMod.invoiceSummary().catch(() => null),
    crmMod.listContacts().catch(() => []),
    crmMod.listCompanies().catch(() => []),
  ]);
  setCached(keyFor(KEY), { invoices: list, summary: s, contacts: cts, companies: cos });
}

async function _prefetchCRM() {
  const KEY = 'crm:page';
  if (getCached(keyFor(KEY))) return;
  const crmMod = await import('./crm');
  const [ov, cts, cos, dls] = await Promise.all([
    crmMod.crmOverview().catch(() => null),
    crmMod.listContacts({ search: '' }).catch(() => []),
    crmMod.listCompanies('').catch(() => []),
    crmMod.listDeals({ search: '' }).catch(() => []),
  ]);
  setCached(keyFor(KEY), { overview: ov, contacts: cts, companies: cos, deals: dls });
}

async function _prefetchTasks() {
  const KEY = 'tasks:page';
  if (getCached(keyFor(KEY))) return;
  const tasksMod = await import('./tasks');
  const [list, s] = await Promise.all([
    tasksMod.listTasks({ status: 'active' }).catch(() => []),
    tasksMod.taskSummary(false).catch(() => null),
  ]);
  setCached(keyFor(KEY), { tasks: list, summary: s });
}

async function _prefetchDocuments() {
  const KEY = 'documents:page';
  if (getCached(keyFor(KEY))) return;
  const docsMod = await import('./documents');
  const [t, d] = await Promise.all([
    docsMod.listDocTemplates().catch(() => []),
    docsMod.listDocuments().catch(() => []),
  ]);
  setCached(keyFor(KEY), { templates: t.map(x => ({ ...x })), documents: d });
}


// ── Registry ────────────────────────────────────────────────────────────
// Add more pages here as we wire SWR into them. The key is the URL path —
// matches what Layout.jsx hover handlers and Idle scheduler will see.

const REGISTRY = {
  '/':           _prefetchDashboard,
  '/invoices':   _prefetchInvoices,
  '/crm':        _prefetchCRM,
  '/tasks':      _prefetchTasks,
  '/documents':  _prefetchDocuments,
};


export function prefetchData(path) {
  if (!path) return;
  const fn = REGISTRY[path];
  if (!fn) return;
  return withDedupe(path, fn);
}

/**
 * Fire prefetch for every heavy page in the background after the layout
 * mounts. Staggered via requestIdleCallback so we never compete with the
 * Dashboard's own initial paint.
 *
 * Order is intentional: Dashboard first (user is staring at it), then the
 * pages most likely to be clicked next (Invoices, CRM, Tasks).
 */
export function prefetchAllDataIdle() {
  if (typeof window === 'undefined') return;
  const idle = window.requestIdleCallback
    || ((cb, opts) => setTimeout(cb, (opts && opts.timeout) || 200));
  // ~150ms apart so we don't fire 4 simultaneous network bursts.
  const order = ['/', '/invoices', '/crm', '/tasks', '/documents'];
  order.forEach((path, i) => {
    idle(() => prefetchData(path), { timeout: 500 + i * 200 });
  });
}
