/**
 * Global React error boundary.
 *
 * Wraps the protected Layout so any unhandled render error in any page shows
 * a friendly fallback instead of a white screen of death. The user can
 * refresh, go home, or see the technical error toggled behind "Show details".
 *
 * A getDerivedStateFromError + componentDidCatch pair is the only way to
 * catch render errors in React; functional hooks can't do it.
 */
import { Component } from 'react';
import { AlertTriangle, Home, RefreshCw, Bug } from 'lucide-react';
import { reportError } from '../services/errorReporter';


export default class ErrorBoundary extends Component {
  state = { error: null, info: null, showDetails: false };

  static getDerivedStateFromError(error) {
    return { error, info: null, showDetails: false };
  }

  componentDidCatch(error, info) {
    // Ship the error to whatever reporter is configured (Sentry /
    // custom endpoint / in-memory buffer). reportError never throws.
    reportError(error, { componentStack: info?.componentStack });
    this.setState({ info });
    console.error('[ErrorBoundary] unhandled render error:', error, info);
  }

  reset = () => this.setState({ error: null, info: null, showDetails: false });

  render() {
    if (!this.state.error) return this.props.children;

    const { error, info, showDetails } = this.state;
    const msg = error?.message || String(error);

    return (
      <div style={{
        minHeight: '100vh',
        background: 'var(--color-bg)',
        color: 'var(--color-text)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 24,
      }}>
        <div style={{
          maxWidth: 560, width: '100%',
          padding: 28, borderRadius: 'var(--r-lg)',
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border-strong)',
        }}>
          <div style={{
            width: 52, height: 52, borderRadius: '50%',
            background: 'color-mix(in srgb, var(--color-err) 18%, transparent)',
            color: 'var(--color-err)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: 14,
          }}>
            <AlertTriangle size={24} />
          </div>

          <h1 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Something broke</h1>
          <p style={{ marginTop: 8, fontSize: 13, color: 'var(--color-text-muted)', lineHeight: 1.55 }}>
            Your data is safe. This page hit an unexpected error while rendering — try refreshing
            or go back home. If it keeps happening, the detail block below has what you'd paste
            into an issue.
          </p>

          <div style={{ display: 'flex', gap: 8, marginTop: 18, flexWrap: 'wrap' }}>
            <button
              className="btn-primary"
              onClick={() => { this.reset(); window.location.reload(); }}
              style={{ fontSize: 12 }}
            >
              <RefreshCw size={11} /> Refresh
            </button>
            <button
              className="btn-ghost"
              onClick={() => { this.reset(); window.location.assign('/'); }}
              style={{ fontSize: 12 }}
            >
              <Home size={11} /> Dashboard
            </button>
            <button
              className="btn-ghost"
              onClick={() => this.setState({ showDetails: !showDetails })}
              style={{ fontSize: 12 }}
            >
              <Bug size={11} /> {showDetails ? 'Hide' : 'Show'} details
            </button>
          </div>

          {showDetails && (
            <pre style={{
              marginTop: 14, padding: 12, borderRadius: 'var(--r-sm)',
              background: 'var(--color-bg)', border: '1px solid var(--color-border)',
              fontSize: 10, color: 'var(--color-text-muted)',
              whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              maxHeight: 240, overflow: 'auto',
            }}>
{msg}
{info?.componentStack || ''}
            </pre>
          )}
        </div>
      </div>
    );
  }
}
