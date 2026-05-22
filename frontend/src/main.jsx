import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react';
import './index.css'
import App from './App.jsx'
import { initGlobalErrorHandlers } from './services/errorReporter';

// ── Sentry, production error reporting ────────────────────────────────
// Vite exposes only env vars prefixed with VITE_ to the client bundle. The
// DSN is safe-ish to ship (frontend Sentry DSNs are designed to be visible),
// but we still gate init on its presence so dev builds without the env var
// stay quiet.
const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN;
if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: import.meta.env.VITE_SENTRY_ENV || import.meta.env.MODE,
    release: import.meta.env.VITE_APP_VERSION,
    // 10% of transactions traced, keeps spans well under the 5M/mo
    // Education quota at expected SMB SaaS volume.
    tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_RATE || 0.1),
    // Capture 10% of sessions for replay; jump to 100% on errors so you
    // see exactly what the user did before the crash. Mask text + media
    // so we never record customer PII into the replay.
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({ maskAllText: true, blockAllMedia: true }),
    ],
    // Strip query-string PII from breadcrumbs (e.g. ?email=foo@bar.com).
    beforeSend(event) {
      if (event.request?.url) {
        try { event.request.url = event.request.url.split('?')[0]; } catch { /* leave as-is */ }
      }
      return event;
    },
  });
}

// Apply the persisted theme before React's first render so users don't see
// a dark-mode flash when they've chosen light, or vice versa.
try {
  const saved = localStorage.getItem('nexus_theme');
  if (saved === 'light' || saved === 'dark') {
    document.documentElement.setAttribute('data-theme', saved);
  }
} catch { /* localStorage disabled, fall back to default dark */ }

// Catch uncaught errors + unhandled promise rejections before React mounts.
initGlobalErrorHandlers();

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
