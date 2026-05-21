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
import BrandMark from '../components/BrandMark';

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
    <div className="ve-shell">
      <VerifyStyles />
      <div className="ve-orb ve-orb-1" aria-hidden />
      <div className="ve-orb ve-orb-2" aria-hidden />

      <aside className="ve-rail">
        <div className="ve-brand">
          <BrandMark size={44} />
          <div>
            <div className="ve-brand-name">NexusAgent</div>
            <div className="ve-brand-sub">14-day Pro trial</div>
          </div>
        </div>
        <h1 className="ve-rail-h1">
          Your AI team,<br/>
          <span className="ve-rail-grad">always on duty</span>
        </h1>
        <p className="ve-rail-p">
          We're verifying your email and activating the trial. Takes a few seconds —
          no card, no commitment.
        </p>
        <ul className="ve-rail-list">
          <li>✓ All 8 AI agents unlocked</li>
          <li>✓ 500 WhatsApp + 100 voice minutes</li>
          <li>✓ Industry-tuned templates</li>
        </ul>
      </aside>

      <main className="ve-pane">
        <div className="ve-card">
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
              If that email is registered and not yet verified, a fresh link is
              on its way. The link is valid for 48 hours.
            </p>
            <p style={{ ...p, marginTop: 14, fontSize: 13 }}>
              Already verified your account? Just{' '}
              <Link to="/login" style={a}>sign in</Link>{' '}— no link needed.
            </p>
          </>
        )}
        </div>
      </main>
    </div>
  );
}

function VerifyStyles() {
  return (
    <style>{`
      .ve-shell {
        position: fixed; inset: 0;
        display: grid;
        grid-template-columns: minmax(320px, 480px) 1fr;
        background:
          radial-gradient(1200px 600px at 0% 0%,    rgba(99,102,241,0.10), transparent 60%),
          radial-gradient(900px 500px  at 100% 100%, rgba(16,185,129,0.07), transparent 55%),
          var(--color-bg);
        color: var(--color-text);
        overflow: hidden;
        animation: ve-fade-in 360ms cubic-bezier(.2,.7,.3,1);
      }
      .ve-orb {
        position: absolute; border-radius: 50%; pointer-events: none;
        filter: blur(60px); opacity: 0.55;
        animation: ve-drift 16s ease-in-out infinite alternate;
      }
      .ve-orb-1 {
        width: 360px; height: 360px;
        background: radial-gradient(circle, rgba(139,92,246,0.45), transparent 70%);
        top: -80px; left: -80px;
      }
      .ve-orb-2 {
        width: 460px; height: 460px;
        background: radial-gradient(circle, rgba(16,185,129,0.35), transparent 70%);
        bottom: -120px; right: -120px;
        animation-delay: -8s;
      }
      @keyframes ve-drift {
        0%   { transform: translate(0, 0) scale(1); }
        100% { transform: translate(40px, 20px) scale(1.06); }
      }
      @keyframes ve-fade-in { 0% { opacity: 0; } 100% { opacity: 1; } }

      .ve-rail {
        position: relative; z-index: 1;
        padding: 56px 44px;
        display: flex; flex-direction: column; gap: 28px; justify-content: center;
        background: linear-gradient(165deg, #0c1224 0%, #131b34 60%, #0c1224 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
        color: #c0c4d0;
      }
      .ve-brand { display: flex; align-items: center; gap: 12px; }
      .ve-brand-mark {
        width: 44px; height: 44px; border-radius: 12px;
        background: linear-gradient(135deg, #10b981 0%, #6366f1 60%, #8b5cf6 100%);
        display: grid; place-items: center;
        color: white; font-size: 20px; font-weight: 800;
        box-shadow: 0 0 0 1px rgba(99,102,241,0.25), 0 8px 24px rgba(99,102,241,0.18);
      }
      .ve-brand-name { font-size: 15px; font-weight: 700; color: #e6e8ef; }
      .ve-brand-sub  { font-size: 11px; color: #6b7280; margin-top: 2px; letter-spacing: 0.3px; }

      .ve-rail-h1 {
        margin: 0; font-size: 32px; font-weight: 700; line-height: 1.15;
        letter-spacing: -0.02em; color: #ffffff;
      }
      .ve-rail-grad {
        background: linear-gradient(90deg, #10b981, #8b5cf6);
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent; color: transparent;
      }
      .ve-rail-p {
        margin: 0; font-size: 14px; color: #9aa0b0; line-height: 1.65;
      }
      .ve-rail-list {
        list-style: none; padding: 0; margin: 6px 0 0;
        display: flex; flex-direction: column; gap: 8px;
        font-size: 13px; color: #b8bcc9;
      }
      .ve-rail-list li { display: flex; gap: 6px; }

      .ve-pane {
        position: relative; z-index: 1;
        display: flex; align-items: center; justify-content: center;
        padding: 56px 40px;
        overflow-y: auto;
      }
      .ve-card {
        width: 100%; max-width: 440px;
        background: var(--color-surface-0);
        border: 1px solid var(--color-border);
        border-radius: 16px;
        padding: 40px 36px;
        text-align: center;
        box-shadow: 0 12px 40px rgba(0,0,0,0.06);
        animation: ve-card-in 360ms cubic-bezier(.2,.7,.3,1);
      }
      @keyframes ve-card-in {
        0% { opacity: 0; transform: translateY(12px); }
        100% { opacity: 1; transform: translateY(0); }
      }

      @media (max-width: 900px) {
        .ve-shell { grid-template-columns: 1fr; grid-template-rows: auto 1fr; }
        .ve-rail  { padding: 32px 24px; gap: 16px; }
        .ve-rail-h1 { font-size: 24px; }
        .ve-pane  { padding: 32px 22px; }
      }
    `}</style>
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
