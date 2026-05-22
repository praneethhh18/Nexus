/**
 * Route prefetch registry.
 *
 * Why: every page in App.jsx is `lazy(() => import('./pages/X'))`. The chunk
 * for a page isn't downloaded until the user actually navigates, and in dev,
 * Vite compiles each chunk on the first request, so clicks have a visible
 * 1-3s lag. In prod, chunks are pre-built but still cost a network round-trip
 * + parse on first visit.
 *
 * This module exposes `prefetchRoute(path)` so the sidebar can call it on
 * hover. By the time the user clicks, the chunk is already in the browser's
 * module cache and the page mounts instantly.
 *
 * The keys MUST match the route paths in App.jsx. Each value is a function
 * that returns the same dynamic import as the App.jsx `lazy(...)` wrapper , 
 * so the bundler de-duplicates and we don't end up with two chunks for the
 * same page.
 */

const REGISTRY = {
  '/':                       () => import('../pages/Dashboard'),
  '/chat':                   () => import('../pages/Chat'),
  '/crm':                    () => import('../pages/CRM'),
  '/tasks':                  () => import('../pages/Tasks'),
  '/invoices':               () => import('../pages/Invoices'),
  '/email-templates':        () => import('../pages/EmailTemplates'),
  '/documents':              () => import('../pages/Documents'),
  '/reports':                () => import('../pages/Reports'),
  '/workflows':              () => import('../pages/Workflows'),
  '/integrations':           () => import('../pages/Integrations'),
  '/inbox':                  () => import('../pages/Inbox'),
  '/agents':                 () => import('../pages/Agents'),
  '/agents/vox':             () => import('../pages/VoxAgent'),
  '/team':                   () => import('../pages/Team'),
  '/memory':                 () => import('../pages/Memory'),
  '/security':               () => import('../pages/Security'),
  '/settings/privacy-mode':  () => import('../pages/PrivacyMode'),
  '/audit':                  () => import('../pages/AuditLog'),
  '/admin/metrics':          () => import('../pages/AdminMetrics'),
  '/history':                () => import('../pages/History'),
  '/pricing':                () => import('../pages/Pricing'),
  '/settings':               () => import('../pages/Settings'),
  '/analytics':              () => import('../pages/Analytics'),
  '/database':               () => import('../pages/Database'),
  '/sql':                    () => import('../pages/SQLEditor'),
  '/whatif':                 () => import('../pages/WhatIf'),
};

// Track which routes we've already kicked off so multi-hover doesn't queue
// duplicate work. Once an import promise resolves it's in the module cache
// for the life of the page anyway, but de-duping is cheap and tidy.
const STARTED = new Set();

export function prefetchRoute(path) {
  if (!path) return;
  if (STARTED.has(path)) return;
  const loader = REGISTRY[path];
  if (!loader) return;
  STARTED.add(path);
  // Fire-and-forget. Swallow rejections, a failed prefetch shouldn't surface
  // an error to the user; if the click happens, the lazy() boundary will
  // catch + retry anyway.
  loader().catch(() => STARTED.delete(path));
}

/**
 * Prefetch every page after the browser is idle. Called once from Layout on
 * mount. By the time the user clicks anywhere, all chunks are warm.
 *
 * Wrapped in requestIdleCallback so we don't compete with the initial paint
 * or any in-flight data fetches.
 */
export function prefetchAllRoutesIdle() {
  if (typeof window === 'undefined') return;
  const idle = window.requestIdleCallback
    || ((cb) => setTimeout(cb, 1));   // Safari < 16 fallback
  // Stagger so we don't fire 25 imports in the same tick.
  Object.keys(REGISTRY).forEach((path, i) => {
    idle(() => prefetchRoute(path), { timeout: 2000 + i * 50 });
  });
}
