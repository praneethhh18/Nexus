import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { resetPassword } from '../services/auth';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [newPw, setNewPw] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) setError('Missing reset token. Use the link from your email.');
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(''); setInfo('');
    if (newPw.length < 8) { setError('Password must be at least 8 characters.'); return; }
    if (newPw !== confirm) { setError('Passwords do not match.'); return; }
    setLoading(true);
    try {
      const r = await resetPassword(token, newPw);
      setInfo(r.message || 'Password updated. Redirecting to sign-in...');
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg)' }}>
      <div style={{ width: 380, padding: 32, borderRadius: 16, background: 'var(--color-surface-1)', border: '1px solid var(--color-surface-2)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: 'linear-gradient(135deg, var(--color-accent), #8b5cf6)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: 20, fontWeight: 700, marginBottom: 12 }}>N</div>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: 'white', marginBottom: 4 }}>Reset your password</h1>
          <p style={{ fontSize: 12, color: 'var(--color-text-dim)' }}>Enter a new password below.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 12 }}>
            <label style={{ fontSize: 11, color: 'var(--color-text-dim)', display: 'block', marginBottom: 4 }}>New password</label>
            <input className="field-input" type="password" value={newPw} onChange={(e) => setNewPw(e.target.value)} required minLength={8} />
          </div>
          <div style={{ marginBottom: 16 }}>
            <label style={{ fontSize: 11, color: 'var(--color-text-dim)', display: 'block', marginBottom: 4 }}>Confirm new password</label>
            <input className="field-input" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required minLength={8} />
          </div>

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

          <button type="submit" className="btn-primary" disabled={loading || !token}
            style={{ width: '100%', justifyContent: 'center', padding: '10px 0', fontSize: 14 }}>
            {loading ? 'Please wait...' : 'Update password'}
          </button>
        </form>

        <p style={{ textAlign: 'center', fontSize: 11, color: 'var(--color-text-dim)', marginTop: 16 }}>
          <a href="/login" style={{ color: 'var(--color-info)' }}>Back to sign in</a>
        </p>
      </div>
    </div>
  );
}
