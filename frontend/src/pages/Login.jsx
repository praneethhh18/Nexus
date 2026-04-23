import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, signup, forgotPassword } from '../services/auth';

export default function Login() {
  const [mode, setMode] = useState('login');
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [needs2fa, setNeeds2fa] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setInfo(''); setLoading(true);
    try {
      if (mode === 'signup') {
        await signup(email, name, password);
        navigate('/');
      } else {
        const res = await login(email, password, needs2fa ? totpCode : null);
        if (res.requires_2fa) {
          setNeeds2fa(true);
          setInfo(res.message || 'Enter the 6-digit code from your authenticator app.');
        } else {
          navigate('/');
        }
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const handleForgot = async () => {
    if (!email.trim()) { setError('Enter your email first'); return; }
    setError(''); setInfo(''); setLoading(true);
    try {
      const r = await forgotPassword(email);
      setInfo(r.message || 'If that email is registered, a reset link has been sent.');
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg)' }}>
      <div style={{ width: 380, padding: 32, borderRadius: 16, background: 'var(--color-surface-1)', border: '1px solid var(--color-surface-2)' }}>
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: 'linear-gradient(135deg, var(--color-accent), #8b5cf6)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: 20, fontWeight: 700, marginBottom: 12 }}>N</div>
          <h1 style={{ fontSize: 20, fontWeight: 600, color: 'white', marginBottom: 4 }}>NexusAgent</h1>
          <p style={{ fontSize: 12, color: 'var(--color-text-dim)' }}>AI Business Assistant</p>
        </div>

        {/* Mode toggle */}
        <div style={{ display: 'flex', marginBottom: 20, background: 'var(--color-surface-2)', borderRadius: 8, padding: 3 }}>
          {['login', 'signup'].map(m => (
            <button key={m} onClick={() => { setMode(m); setError(''); }}
              style={{
                flex: 1, padding: '8px 0', borderRadius: 6, border: 'none', cursor: 'pointer',
                fontSize: 13, fontWeight: 500, transition: 'all 0.15s',
                background: mode === m ? 'var(--color-accent)' : 'transparent',
                color: mode === m ? 'white' : 'var(--color-text-dim)',
              }}>
              {m === 'login' ? 'Sign In' : 'Sign Up'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          {mode === 'signup' && (
            <div style={{ marginBottom: 12 }}>
              <label style={{ fontSize: 11, color: 'var(--color-text-dim)', display: 'block', marginBottom: 4 }}>Full Name</label>
              <input className="field-input" value={name} onChange={e => setName(e.target.value)}
                placeholder="John Doe" required />
            </div>
          )}
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 11, color: 'var(--color-text-dim)', display: 'block', marginBottom: 4 }}>Email</label>
            <input className="field-input" type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="you@company.com" required />
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 11, color: 'var(--color-text-dim)', display: 'block', marginBottom: 4 }}>Password</label>
            <input className="field-input" type="password" value={password} onChange={e => setPassword(e.target.value)}
              placeholder="Enter password" required minLength={3} />
          </div>
          {needs2fa && (
            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 11, color: 'var(--color-text-dim)', display: 'block', marginBottom: 4 }}>
                Authenticator code (or recovery code)
              </label>
              <input className="field-input" autoFocus value={totpCode}
                onChange={(e) => setTotpCode(e.target.value)}
                placeholder="123456"
                style={{ letterSpacing: 4, textAlign: 'center', fontSize: 16 }} />
            </div>
          )}

          {error && (
            <div style={{ padding: '8px 12px', borderRadius: 8, background: 'color-mix(in srgb, var(--color-err) 8%, transparent)', color: 'var(--color-err)', fontSize: 12, marginBottom: 12, border: '1px solid color-mix(in srgb, var(--color-err) 15%, transparent)' }}>
              {error}
            </div>
          )}
          {info && (
            <div style={{ padding: '8px 12px', borderRadius: 8, background: 'color-mix(in srgb, var(--color-ok) 8%, transparent)', color: 'var(--color-ok)', fontSize: 12, marginBottom: 12, border: '1px solid color-mix(in srgb, var(--color-ok) 15%, transparent)' }}>
              {info}
            </div>
          )}

          <button type="submit" className="btn-primary" disabled={loading}
            style={{ width: '100%', justifyContent: 'center', padding: '10px 0', fontSize: 14 }}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        {mode === 'login' && (
          <p style={{ textAlign: 'center', fontSize: 11, marginTop: 12 }}>
            <button
              type="button"
              onClick={handleForgot}
              disabled={loading}
              style={{ background: 'none', border: 'none', color: 'var(--color-info)', cursor: 'pointer', fontSize: 11, textDecoration: 'underline' }}
            >
              Forgot password?
            </button>
          </p>
        )}

        <p style={{ textAlign: 'center', fontSize: 11, color: 'var(--color-text-dim)', marginTop: 16 }}>
          {mode === 'login' ? 'Default: admin@nexusagent.local / admin1234' : ''}
        </p>
      </div>
    </div>
  );
}
