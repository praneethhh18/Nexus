/**
 * Catch-all 404 page. Renders inside the authenticated Layout so users still
 * have the sidebar nav to recover. Public routes have their own catch
 * via React Router redirecting to /login.
 */
import { useNavigate, useLocation } from 'react-router-dom';
import { Search, Home, ArrowLeft } from 'lucide-react';

export default function NotFound() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div style={{
      minHeight: 'calc(100vh - 60px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 24,
    }}>
      <div style={{
        maxWidth: 480, width: '100%', textAlign: 'center',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border-strong)',
        borderRadius: 16, padding: '40px 32px',
      }}>
        <div style={{
          fontFamily: 'var(--font-mono, monospace)',
          fontSize: 80, fontWeight: 800, lineHeight: 1,
          background: 'linear-gradient(135deg, var(--color-info), var(--color-warn))',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          backgroundClip: 'text', marginBottom: 12,
        }}>
          404
        </div>
        <h1 style={{ fontSize: 22, color: 'var(--color-text)', margin: '0 0 8px' }}>
          Page not found
        </h1>
        <p style={{ fontSize: 14, color: 'var(--color-text-dim)', margin: '0 0 24px', lineHeight: 1.6 }}>
          We couldn't find <code style={{
            background: 'var(--color-surface-2)', padding: '2px 6px',
            borderRadius: 4, fontSize: 12,
          }}>{location.pathname}</code>. It may have moved, or the link could be wrong.
        </p>
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            className="btn btn-primary"
            onClick={() => navigate('/')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            <Home size={14} /> Dashboard
          </button>
          <button
            className="btn-ghost"
            onClick={() => navigate(-1)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            <ArrowLeft size={14} /> Go back
          </button>
        </div>
        <div style={{
          marginTop: 28, paddingTop: 20,
          borderTop: '1px solid var(--color-border-strong)',
          fontSize: 12, color: 'var(--color-text-dim)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
        }}>
          <Search size={12} /> Tip: press <kbd style={{
            background: 'var(--color-surface-2)', padding: '1px 6px',
            borderRadius: 3, fontSize: 11, fontFamily: 'var(--font-mono, monospace)',
          }}>Ctrl+K</kbd> to search anything.
        </div>
      </div>
    </div>
  );
}
