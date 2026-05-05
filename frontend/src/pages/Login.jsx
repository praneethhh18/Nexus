import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, signup, forgotPassword } from '../services/auth';

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
const MailIcon = () => (
  <svg width="26" height="26" fill="none" stroke="currentColor" strokeWidth="1.4" viewBox="0 0 24 24">
    <rect x="2" y="4" width="20" height="16" rx="3"/>
    <path d="M2 7l10 7 10-7"/>
  </svg>
);
const ArrowLeft = () => (
  <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
    <path d="M19 12H5M12 5l-7 7 7 7"/>
  </svg>
);

// ── Password strength ────────────────────────────────────────────────────────
function pwScore(pw) {
  if (!pw || pw.length < 8) return 1;
  let s = 1;
  if (pw.length >= 10) s++;
  if (/[A-Z]/.test(pw) && /[0-9!@#$%^&*_\-]/.test(pw)) s++;
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

// ── Shared pieces ────────────────────────────────────────────────────────────
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
      {/* subtle dot grid */}
      <div style={{
        position: 'absolute', inset: 0, opacity: 0.07,
        backgroundImage: 'radial-gradient(rgba(255,255,255,0.7) 1px, transparent 1px)',
        backgroundSize: '28px 28px',
      }} />
      {/* green glow bottom-right */}
      <div style={{
        position: 'absolute', bottom: -120, right: -80, width: 400, height: 400,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(16,185,129,0.09) 0%, transparent 65%)',
        pointerEvents: 'none',
      }} />
      {/* purple glow top-left */}
      <div style={{
        position: 'absolute', top: 30, left: -80, width: 280, height: 280,
        borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(139,92,246,0.07) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      <div style={{ position: 'relative', zIndex: 1 }}>
        {/* Logo */}
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

        {/* Headline */}
        <h2 style={{
          fontSize: 27, fontWeight: 700, lineHeight: 1.25,
          color: '#dde0ea', marginBottom: 12,
        }}>
          Your AI team,<br />
          <span style={{
            background: 'linear-gradient(90deg, #10b981 0%, #8b5cf6 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>always on duty</span>
        </h2>
        <p style={{ fontSize: 13.5, color: '#6b7280', lineHeight: 1.65, marginBottom: 36 }}>
          8 specialised agents that handle your CRM,<br />outbound calls, WhatsApp, and email — 24/7.
        </p>

        {/* Features */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 44 }}>
          {FEATS.map(({ icon, text }) => (
            <div key={text} style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
              <span style={{ color: '#10b981', fontSize: 9, marginTop: 4, flexShrink: 0 }}>{icon}</span>
              <span style={{ fontSize: 13, color: '#8a90a0', lineHeight: 1.45 }}>{text}</span>
            </div>
          ))}
        </div>

        {/* Quote */}
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

// ── Main component ───────────────────────────────────────────────────────────
export default function Login() {
  const [view, setView] = useState('login'); // 'login' | 'signup' | 'forgot' | 'sent'
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [totpCode, setTotpCode] = useState('');
  const [needs2fa, setNeeds2fa] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const afterLogin = () => {
    const pendingInvite = sessionStorage.getItem('nexus_pending_invite');
    if (pendingInvite) {
      sessionStorage.removeItem('nexus_pending_invite');
      navigate(`/accept-invite?token=${pendingInvite}`);
    } else {
      navigate('/');
    }
  };

  const switchView = (v) => { setView(v); setError(''); setNeeds2fa(false); };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      if (view === 'signup') {
        await signup(email, name, password);
        afterLogin();
      } else {
        const res = await login(email, password, needs2fa ? totpCode : null);
        if (res.requires_2fa) {
          setNeeds2fa(true);
        } else {
          afterLogin();
        }
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const handleForgot = async (e) => {
    if (e?.preventDefault) e.preventDefault();
    if (!email.trim()) { setError('Enter your email address first.'); return; }
    setError(''); setLoading(true);
    try {
      await forgotPassword(email);
      setView('sent');
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  // ── View: email sent ──────────────────────────────────────────────────────
  if (view === 'sent') {
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
              background: 'rgba(16,185,129,0.08)',
              border: '1px solid rgba(16,185,129,0.2)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#10b981',
            }}>
              <MailIcon />
            </div>
            <h2 style={{ fontSize: 22, fontWeight: 600, color: 'var(--color-text)', marginBottom: 10 }}>
              Check your inbox
            </h2>
            <p style={{ fontSize: 13.5, color: 'var(--color-text-muted)', lineHeight: 1.65, marginBottom: 32 }}>
              We sent a reset link to{' '}
              <strong style={{ color: 'var(--color-text)' }}>{email}</strong>.
              <br />It expires in 1 hour. Check your spam folder too.
            </p>
            <button
              className="btn-primary"
              onClick={() => switchView('login')}
              style={{ width: '100%', justifyContent: 'center', padding: '11px 0', fontSize: 14 }}
            >
              Back to sign in
            </button>
            <p style={{ marginTop: 18, fontSize: 12.5, color: 'var(--color-text-dim)' }}>
              Didn't receive it?{' '}
              <button
                type="button"
                onClick={handleForgot}
                disabled={loading}
                style={{ background: 'none', border: 'none', color: 'var(--color-info)', cursor: 'pointer', fontSize: 12.5 }}
              >
                {loading ? 'Sending…' : 'Resend email'}
              </button>
            </p>
          </div>
        </div>
      </div>
    );
  }

  // ── View: forgot password ─────────────────────────────────────────────────
  if (view === 'forgot') {
    return (
      <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
        <LeftPanel />
        <div style={{
          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: '32px 40px', background: 'var(--color-bg)',
        }}>
          <div style={{ width: '100%', maxWidth: 400 }}>
            <button
              type="button"
              onClick={() => switchView('login')}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                background: 'none', border: 'none', cursor: 'pointer',
                color: 'var(--color-text-muted)', fontSize: 12.5, marginBottom: 28,
                padding: 0,
              }}
            >
              <ArrowLeft /> Back to sign in
            </button>

            <h2 style={{ fontSize: 22, fontWeight: 600, color: 'var(--color-text)', marginBottom: 8 }}>
              Forgot password?
            </h2>
            <p style={{ fontSize: 13.5, color: 'var(--color-text-muted)', lineHeight: 1.6, marginBottom: 28 }}>
              No problem. Enter your email and we'll send a reset link right away.
            </p>

            <form onSubmit={handleForgot}>
              <div style={{ marginBottom: 18 }}>
                <Label>Email address</Label>
                <input
                  style={baseInput}
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  required
                  autoFocus
                />
              </div>
              {error && <ErrorBox>{error}</ErrorBox>}
              <button
                type="submit"
                className="btn-primary"
                disabled={loading}
                style={{ width: '100%', justifyContent: 'center', padding: '11px 0', fontSize: 14 }}
              >
                {loading ? 'Sending…' : 'Send reset link'}
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  // ── View: login / signup ──────────────────────────────────────────────────
  return (
    <div style={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <LeftPanel />

      <div style={{
        flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '32px 40px', overflow: 'auto', background: 'var(--color-bg)',
      }}>
        <div style={{ width: '100%', maxWidth: 400 }}>
          {/* Heading */}
          <h2 style={{ fontSize: 23, fontWeight: 700, color: 'var(--color-text)', marginBottom: 4 }}>
            {view === 'login' ? 'Welcome back' : 'Create your account'}
          </h2>
          <p style={{ fontSize: 13.5, color: 'var(--color-text-muted)', marginBottom: 24 }}>
            {view === 'login'
              ? 'Sign in to your NexusAgent workspace.'
              : 'Get started with NexusAgent for free.'}
          </p>

          {/* Tab toggle */}
          <div style={{
            display: 'flex', background: 'var(--color-surface-2)',
            borderRadius: 9, padding: 3, marginBottom: 28,
          }}>
            {['login', 'signup'].map(v => (
              <button
                key={v}
                type="button"
                onClick={() => switchView(v)}
                style={{
                  flex: 1, padding: '9px 0', borderRadius: 7, border: 'none', cursor: 'pointer',
                  fontSize: 13, fontWeight: 500, transition: 'all 0.15s',
                  background: view === v ? 'var(--color-accent)' : 'transparent',
                  color: view === v ? 'white' : 'var(--color-text-dim)',
                }}
              >
                {v === 'login' ? 'Sign In' : 'Sign Up'}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit}>
            {/* Name — signup only */}
            {view === 'signup' && (
              <div style={{ marginBottom: 14 }}>
                <Label>Full Name</Label>
                <input
                  style={baseInput}
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Priya Sharma"
                  required
                  autoFocus
                />
              </div>
            )}

            {/* Email */}
            <div style={{ marginBottom: 14 }}>
              <Label>Email address</Label>
              <input
                style={baseInput}
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                autoFocus={view === 'login'}
              />
            </div>

            {/* Password */}
            <div style={{ marginBottom: 18 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 5 }}>
                <Label>Password</Label>
                {view === 'login' && !needs2fa && (
                  <button
                    type="button"
                    onClick={() => switchView('forgot')}
                    style={{
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--color-info)', fontSize: 11.5, padding: 0,
                    }}
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div style={{ position: 'relative' }}>
                <input
                  style={{ ...baseInput, paddingRight: 42 }}
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder={view === 'signup' ? 'Min 8 characters' : 'Enter your password'}
                  required
                  minLength={view === 'signup' ? 8 : 1}
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
              {view === 'signup' && <StrengthBar password={password} />}
            </div>

            {/* 2FA */}
            {needs2fa && (
              <div style={{ marginBottom: 18 }}>
                <Label>Authenticator code (or recovery code)</Label>
                <input
                  style={{ ...baseInput, letterSpacing: 8, textAlign: 'center', fontSize: 18, fontWeight: 600 }}
                  autoFocus
                  value={totpCode}
                  onChange={e => setTotpCode(e.target.value)}
                  placeholder="• • • • • •"
                  maxLength={8}
                />
                <p style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 5 }}>
                  Open your authenticator app and enter the 6-digit code.
                </p>
              </div>
            )}

            {error && <ErrorBox>{error}</ErrorBox>}

            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{ width: '100%', justifyContent: 'center', padding: '11px 0', fontSize: 14 }}
            >
              {loading ? 'Please wait…'
                : view === 'login' ? 'Sign In'
                : 'Create Account'}
            </button>
          </form>

          {/* Default credentials hint */}
          {view === 'login' && (
            <div style={{
              marginTop: 20, padding: '10px 13px', borderRadius: 8,
              background: 'var(--color-surface-2)',
              border: '1px solid var(--color-border)',
            }}>
              <p style={{ fontSize: 11, color: 'var(--color-text-dim)', textAlign: 'center' }}>
                Default: <span style={{ color: 'var(--color-text-muted)' }}>admin@nexusagent.local</span>
                {' / '}
                <span style={{ color: 'var(--color-text-muted)' }}>admin1234</span>
              </p>
            </div>
          )}

          {/* Sign up prompt for signup view */}
          {view === 'signup' && (
            <p style={{ textAlign: 'center', marginTop: 20, fontSize: 12.5, color: 'var(--color-text-dim)' }}>
              By creating an account you agree to our terms of service.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
