import { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { resetPassword } from '../services/auth';

// ── Icons ────────────────────────────────────────────────────────────────────
const EyeOn = () => (
  <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.6" viewBox="0 0 24 24">
    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/>
    <circle cx="12" cy="12" r="3"/>
  </svg>
);
const EyeOff = () => (
  <svg width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.6" viewBox="0 0 24 24">
    <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/>
    <line x1="1" y1="1" x2="23" y2="23"/>
  </svg>
);
const CheckIcon = () => (
  <svg width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
    <polyline points="20 6 9 17 4 12"/>
  </svg>
);
const AlertIcon = () => (
  <svg width="28" height="28" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
);

// ── Password strength ────────────────────────────────────────────────────────
function pwScore(pw) {
  if (!pw || pw.length < 8) return 1;
  let s = 1;
  if (pw.length >= 10) s++;
  if (/[A-Z]/.test(pw) && /[0-9!@#$%^&*_-]/.test(pw)) s++;
  return s;
}

function StrengthBar({ password }) {
  if (!password) return null;
  const s = pwScore(password);
  const clr = ['', '#ef4444', '#f59e0b', '#10b981'][s];
  const lbl = ['', 'Weak — add numbers and symbols', 'Fair — getting better', 'Strong password'][s];
  return (
    <div style={{ marginTop: 7 }}>
      <div style={{ display: 'flex', gap: 4 }}>
        {[1, 2, 3].map(i => (
          <div key={i} style={{
            flex: 1, height: 3, borderRadius: 2,
            background: i <= s ? clr : 'var(--color-border)',
            transition: 'background 0.2s',
          }} />
        ))}
      </div>
      <span style={{ fontSize: 10.5, color: clr, marginTop: 4, display: 'block' }}>{lbl}</span>
    </div>
  );
}

// ── Left branding panel (identical to Login) ─────────────────────────────────
const FEATS = [
  { icon: '▸', text: '8 AI agents — CRM, voice calls, WhatsApp & email' },
  { icon: '▸', text: 'Auto follow-ups with smart deal pipeline' },
  { icon: '▸', text: 'Invoice reminders & meeting prep notes' },
  { icon: '▸', text: 'Privacy-first: your data stays on-device' },
];

function LeftPanel() {
  return (
    <div style={{
      flex: '0 0 46%', minWidth: 0,
      background: 'linear-gradient(160deg, #060b14 0%, #0c1927 60%, #070e1b 100%)',
      display: 'flex', flexDirection: 'column', justifyContent: 'center',
      padding: '48px 52px', position: 'relative', overflow: 'hidden',
    }}>
      <div style={{
        position: 'absolute', inset: 0, opacity: 0.07,
        backgroundImage: 'radial-gradient(rgba(255,255,255,0.7) 1px, transparent 1px)',
        backgroundSize: '28px 28px',
      }} />
      <div style={{
        position: 'absolute', bottom: -120, right: -80, width: 400, height: 400,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(16,185,129,0.09) 0%, transparent 65%)',
        pointerEvents: 'none',
      }} />
      <div style={{
        position: 'absolute', top: 30, left: -80, width: 280, height: 280,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.07) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      <div style={{ position: 'relative', zIndex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 11, marginBottom: 44 }}>
          <div style={{
            width: 42, height: 42, borderRadius: 11,
            background: 'linear-gradient(135deg, #10b981, #7c3aed)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 19, fontWeight: 800, color: 'white',
            boxShadow: '0 0 0 1px rgba(16,185,129,0.2), 0 8px 24px rgba(16,185,129,0.12)',
          }}>N</div>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: '#dde0ea', lineHeight: 1 }}>NexusAgent</div>
            <div style={{ fontSize: 11, color: '#4a5068', marginTop: 2 }}>AI Business Platform</div>
          </div>
        </div>

        <h2 style={{ fontSize: 27, fontWeight: 700, lineHeight: 1.25, color: '#dde0ea', marginBottom: 12 }}>
          Your AI team,<br />
          <span style={{
            background: 'linear-gradient(90deg, #10b981 0%, #8b5cf6 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>always on duty</span>
        </h2>
        <p style={{ fontSize: 13.5, color: '#6b7280', lineHeight: 1.65, marginBottom: 36 }}>
          8 specialised agents that handle your CRM,<br />outbound calls, WhatsApp, and email — 24/7.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 44 }}>
          {FEATS.map(({ icon, text }) => (
            <div key={text} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
              <span style={{ color: '#10b981', fontSize: 9, marginTop: 4, flexShrink: 0 }}>{icon}</span>
              <span style={{ fontSize: 13, color: '#8a90a0', lineHeight: 1.45 }}>{text}</span>
            </div>
          ))}
        </div>

        <div style={{
          padding: '16px 18px', borderRadius: 12,
          background: 'rgba(255,255,255,0.025)',
          border: '1px solid rgba(255,255,255,0.06)',
        }}>
          <p style={{ fontSize: 13, color: '#6b7280', fontStyle: 'italic', lineHeight: 1.6, marginBottom: 9 }}>
            "NexusAgent handles our follow-ups automatically. We saved 3 hours every single day."
          </p>
          <p style={{ fontSize: 11, color: '#3d4459' }}>— Vikram S., Founder · Mumbai</p>
        </div>
      </div>
    </div>
  );
}

// ── Shared UI ─────────────────────────────────────────────────────────────────
function ErrorBox({ children }) {
  return (
    <div style={{
      padding: '9px 13px', borderRadius: 8, marginBottom: 14,
      background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
      border: '1px solid color-mix(in srgb, var(--color-err) 18%, transparent)',
      color: 'var(--color-err)', fontSize: 12.5, lineHeight: 1.5,
    }}>{children}</div>
  );
}

function Label({ children }) {
  return (
    <label style={{
      display: 'block', fontSize: 11.5, fontWeight: 500,
      color: 'var(--color-text-muted)', marginBottom: 5,
    }}>{children}</label>
  );
}

const baseInput = {
  width: '100%', padding: '10px 13px',
  borderRadius: 8, fontSize: 13.5,
  background: 'var(--color-surface-2)',
  border: '1px solid var(--color-border)',
  color: 'var(--color-text)', outline: 'none',
  transition: 'border-color 0.15s',
};

// ── Main component ────────────────────────────────────────────────────────────
export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';

  const [newPw, setNewPw] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [error, setError] = useState('');
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (newPw.length < 8) { setError('Password must be at least 8 characters.'); return; }
    if (newPw !== confirm) { setError('Passwords do not match.'); return; }
    setLoading(true);
    try {
      await resetPassword(token, newPw);
      setDone(true);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  // ── Invalid token ────────────────────────────────────────────────────────
  if (!token) {
    return (
      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
        <LeftPanel />
        <div style={{
          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: '32px 40px', background: 'var(--color-bg)',
        }}>
          <div style={{ width: '100%', maxWidth: 400, textAlign: 'center' }}>
            <div style={{
              width: 64, height: 64, borderRadius: '50%', margin: '0 auto 20px',
              background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#ef4444',
            }}>
              <AlertIcon />
            </div>
            <h2 style={{ fontSize: 22, fontWeight: 600, color: 'var(--color-text)', marginBottom: 10 }}>
              Invalid reset link
            </h2>
            <p style={{ fontSize: 13.5, color: 'var(--color-text-muted)', lineHeight: 1.65, marginBottom: 28 }}>
              This link is missing a token or may have expired. Please request a new password reset from the sign-in page.
            </p>
            <button
              className="btn-primary"
              onClick={() => navigate('/login')}
              style={{ width: '100%', justifyContent: 'center', padding: '11px 0', fontSize: 14 }}
            >
              Go to sign in
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Success ──────────────────────────────────────────────────────────────
  if (done) {
    return (
      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
        <LeftPanel />
        <div style={{
          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: '32px 40px', background: 'var(--color-bg)',
        }}>
          <div style={{ width: '100%', maxWidth: 400, textAlign: 'center' }}>
            <div style={{
              width: 64, height: 64, borderRadius: '50%', margin: '0 auto 20px',
              background: 'rgba(16,185,129,0.08)', border: '1px solid rgba(16,185,129,0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#10b981',
            }}>
              <CheckIcon />
            </div>
            <h2 style={{ fontSize: 22, fontWeight: 600, color: 'var(--color-text)', marginBottom: 10 }}>
              Password updated
            </h2>
            <p style={{ fontSize: 13.5, color: 'var(--color-text-muted)', lineHeight: 1.65, marginBottom: 32 }}>
              Your password has been changed successfully. You can now sign in with your new password.
            </p>
            <button
              className="btn-primary"
              onClick={() => navigate('/login')}
              style={{ width: '100%', justifyContent: 'center', padding: '11px 0', fontSize: 14 }}
            >
              Sign in now
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Reset form ───────────────────────────────────────────────────────────
  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <LeftPanel />
      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '32px 40px', overflow: 'auto', background: 'var(--color-bg)',
      }}>
        <div style={{ width: '100%', maxWidth: 400 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 11, marginBottom: 32 }}>
            <div style={{
              width: 42, height: 42, borderRadius: 11,
              background: 'linear-gradient(135deg, #10b981, #7c3aed)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 19, fontWeight: 800, color: 'white',
            }}>N</div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--color-text)' }}>NexusAgent</div>
              <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>AI Business Platform</div>
            </div>
          </div>

          <h2 style={{ fontSize: 22, fontWeight: 600, color: 'var(--color-text)', marginBottom: 8 }}>
            Set a new password
          </h2>
          <p style={{ fontSize: 13.5, color: 'var(--color-text-muted)', lineHeight: 1.6, marginBottom: 28 }}>
            Choose a strong password. It must be at least 8 characters.
          </p>

          <form onSubmit={handleSubmit}>
            {/* New password */}
            <div style={{ marginBottom: 14 }}>
              <Label>New password</Label>
              <div style={{ position: 'relative' }}>
                <input
                  style={{ ...baseInput, paddingRight: 42 }}
                  type={showPw ? 'text' : 'password'}
                  value={newPw}
                  onChange={e => setNewPw(e.target.value)}
                  placeholder="Min 8 characters"
                  required
                  minLength={8}
                  autoFocus
                />
                <button
                  type="button"
                  onClick={() => setShowPw(p => !p)}
                  style={{
                    position: 'absolute', right: 11, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--color-text-dim)', display: 'flex', padding: 2,
                  }}
                >
                  {showPw ? <EyeOff /> : <EyeOn />}
                </button>
              </div>
              <StrengthBar password={newPw} />
            </div>

            {/* Confirm password */}
            <div style={{ marginBottom: 20 }}>
              <Label>Confirm new password</Label>
              <div style={{ position: 'relative' }}>
                <input
                  style={{
                    ...baseInput, paddingRight: 42,
                    borderColor: confirm && newPw !== confirm ? 'var(--color-err)' : undefined,
                  }}
                  type={showConfirm ? 'text' : 'password'}
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                  placeholder="Re-enter your password"
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm(p => !p)}
                  style={{
                    position: 'absolute', right: 11, top: '50%', transform: 'translateY(-50%)',
                    background: 'none', border: 'none', cursor: 'pointer',
                    color: 'var(--color-text-dim)', display: 'flex', padding: 2,
                  }}
                >
                  {showConfirm ? <EyeOff /> : <EyeOn />}
                </button>
              </div>
              {confirm && newPw !== confirm && (
                <span style={{ fontSize: 11, color: 'var(--color-err)', marginTop: 4, display: 'block' }}>
                  Passwords don't match
                </span>
              )}
            </div>

            {error && <ErrorBox>{error}</ErrorBox>}

            <button
              type="submit"
              className="btn-primary"
              disabled={loading || !token}
              style={{ width: '100%', justifyContent: 'center', padding: '11px 0', fontSize: 14 }}
            >
              {loading ? 'Updating…' : 'Update password'}
            </button>
          </form>

          <p style={{ textAlign: 'center', marginTop: 18, fontSize: 12.5, color: 'var(--color-text-dim)' }}>
            <a href="/login" style={{ color: 'var(--color-text-muted)', textDecoration: 'none' }}>
              ← Back to sign in
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
