/**
 * /verify-email?token=<urlsafe>
 *
 * Lands here from the email link. Calls POST /api/auth/verify-email with the
 * token; on success the user is logged in (tokens stored via setSession) and
 * we redirect to /?welcome=trial so the confetti PlanWelcomeModal fires on
 * the dashboard.
 *
 * Failure modes:
 *   - invalid / expired token   → show error + "request new link" CTA
 *   - already verified          → friendly "you're good" + link to /login
 *   - network blip              → "try again" button
 */
import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { verifyEmail, resendVerification } from '../services/auth';
import { CheckCircle2, XCircle, Loader2, Mail } from 'lucide-react';

export default function VerifyEmail() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [status, setStatus] = useState('verifying'); // verifying | ok | bad | resent
  const [error, setError] = useState('');
  const [resendEmail, setResendEmail] = useState('');
  const fired = useRef(false);

  useEffect(() => {
    if (fired.current) return;
    fired.current = true;

    const token = params.get('token') || '';
    if (!token) {
      setStatus('bad');
      setError('No verification token in the URL. Open the link from your email.');
      return;
    }

    (async () => {
      try {
        await verifyEmail(token);
        setStatus('ok');
        // Tiny delay so the user SEES the success state before the modal opens.
        setTimeout(() => navigate('/?welcome=trial'), 900);
      } catch (e) {
        setStatus('bad');
        setError(String(e?.message || 'Verification failed.'));
      }
    })();
  }, [params, navigate]);

  const onResend = async (e) => {
    e.preventDefault();
    if (!resendEmail.trim()) return;
    try {
      await resendVerification(resendEmail.trim());
      setStatus('resent');
    } catch {
      setStatus('resent');   // privacy-preserving: same UI either way
    }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'grid', placeItems: 'center',
      background: 'var(--color-bg)', padding: 24,
    }}>
      <div style={{
        width: '100%', maxWidth: 460,
        background: 'var(--color-surface-0)',
        border: '1px solid var(--color-border)',
        borderRadius: 16, padding: '36px 32px',
        textAlign: 'center',
        boxShadow: '0 8px 32px rgba(0,0,0,0.05)',
      }}>
        {status === 'verifying' && (
          <>
            <Spinner />
            <h2 style={h2}>Activating your trial…</h2>
            <p style={p}>Hold on, verifying your email.</p>
          </>
        )}

        {status === 'ok' && (
          <>
            <IconWrap color="#10B981" bg="rgba(16,185,129,0.10)" border="rgba(16,185,129,0.25)">
              <CheckCircle2 size={32} />
            </IconWrap>
            <h2 style={h2}>You're in.</h2>
            <p style={p}>
              Email verified · 14-day Pro trial activated.<br/>
              Taking you to your dashboard…
            </p>
          </>
        )}

        {status === 'bad' && (
          <>
            <IconWrap color="#EF4444" bg="rgba(239,68,68,0.08)" border="rgba(239,68,68,0.2)">
              <XCircle size={30} />
            </IconWrap>
            <h2 style={h2}>This link didn't work</h2>
            <p style={p}>{error}</p>

            <form onSubmit={onResend} style={{ marginTop: 22, textAlign: 'left' }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text-dim)' }}>
                Email
              </label>
              <input
                type="email"
                required
                value={resendEmail}
                onChange={(e) => setResendEmail(e.target.value)}
                placeholder="you@company.com"
                style={input}
              />
              <button type="submit" className="btn-primary"
                      style={{ width: '100%', padding: '11px 0', justifyContent: 'center', fontSize: 14 }}>
                Send me a new link
              </button>
            </form>
            <p style={{ ...p, marginTop: 18, fontSize: 12.5 }}>
              Already verified? <Link to="/login" style={a}>Sign in</Link>
            </p>
          </>
        )}

        {status === 'resent' && (
          <>
            <IconWrap color="#6366F1" bg="rgba(99,102,241,0.10)" border="rgba(99,102,241,0.22)">
              <Mail size={28} />
            </IconWrap>
            <h2 style={h2}>Check your inbox</h2>
            <p style={p}>
              If that email is registered, a fresh verification link is on its way.
              The link is valid for 48 hours.
            </p>
            <Link to="/login" style={{
              display: 'inline-block', marginTop: 18, fontSize: 13, color: 'var(--color-info)',
            }}>← Back to sign in</Link>
          </>
        )}
      </div>
    </div>
  );
}

// ── Styles ──────────────────────────────────────────────────────────────
const h2 = { fontSize: 22, fontWeight: 700, color: 'var(--color-text)', margin: '14px 0 8px' };
const p  = { fontSize: 13.5, color: 'var(--color-text-muted)', lineHeight: 1.6, margin: 0 };
const a  = { color: 'var(--color-info)', textDecoration: 'none' };
const input = {
  width: '100%', boxSizing: 'border-box',
  padding: '10px 12px', borderRadius: 8, marginTop: 6, marginBottom: 12,
  background: 'var(--color-surface-1)', border: '1px solid var(--color-border)',
  color: 'var(--color-text)', fontSize: 14,
};

function IconWrap({ color, bg, border, children }) {
  return (
    <div style={{
      width: 64, height: 64, borderRadius: '50%', margin: '0 auto',
      background: bg, border: `1px solid ${border}`, color,
      display: 'grid', placeItems: 'center',
    }}>
      {children}
    </div>
  );
}

function Spinner() {
  return (
    <div style={{
      width: 64, height: 64, borderRadius: '50%', margin: '0 auto',
      background: 'rgba(99,102,241,0.10)',
      border: '1px solid rgba(99,102,241,0.22)',
      color: '#6366F1', display: 'grid', placeItems: 'center',
    }}>
      <Loader2 size={28} style={{ animation: 'spin 1s linear infinite' }} />
    </div>
  );
}
