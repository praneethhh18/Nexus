import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { previewInvite, acceptInvite } from '../services/team';
import { isLoggedIn, getUser, setBusinessId } from '../services/auth';

export default function AcceptInvite() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') || '';
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (!token) { setError('Missing invite token.'); return; }
    previewInvite(token).then(setPreview).catch(e => setError(e.message));
  }, [token]);

  const handleAccept = async () => {
    if (!isLoggedIn()) {
      sessionStorage.setItem('nexus_pending_invite', token);
      navigate('/login');
      return;
    }
    const user = getUser();
    if (preview?.email && user?.email && preview.email.toLowerCase() !== user.email.toLowerCase()) {
      setError(`This invite is for ${preview.email}. Log in as that user to accept.`);
      return;
    }
    setLoading(true);
    try {
      const res = await acceptInvite(token);
      setBusinessId(res.business_id);
      setInfo(`Joined! Redirecting...`);
      setTimeout(() => { window.location.href = '/'; }, 1200);
    } catch (e) {
      setError(e.message);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--color-bg)' }}>
      <div style={{ width: 420, padding: 32, borderRadius: 16, background: 'var(--color-surface-1)', border: '1px solid var(--color-surface-2)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: 'linear-gradient(135deg, var(--color-accent), #8b5cf6)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: 20, fontWeight: 700, marginBottom: 12 }}>N</div>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: 'white' }}>NexusAgent invite</h1>
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

        {!preview && !error && (
          <p style={{ textAlign: 'center', color: 'var(--color-text-dim)' }}>Loading invite...</p>
        )}

        {preview?.status === 'pending' && (
          <>
            <p style={{ fontSize: 13, color: 'var(--color-text)', marginBottom: 8 }}>
              You've been invited to join <strong>{preview.business_name}</strong>
            </p>
            <div style={{ padding: 12, background: 'var(--color-surface-2)', borderRadius: 8, fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 16 }}>
              <div>Email: <strong style={{ color: 'var(--color-text)' }}>{preview.email}</strong></div>
              <div>Role: <strong style={{ color: 'var(--color-text)' }}>{preview.role}</strong></div>
            </div>
            <button onClick={handleAccept} className="btn-primary" disabled={loading}
              style={{ width: '100%', justifyContent: 'center', padding: '10px 0', fontSize: 14 }}>
              {loading ? 'Accepting...' : isLoggedIn() ? 'Accept invite' : 'Log in to accept'}
            </button>
            {!isLoggedIn() && (
              <p style={{ textAlign: 'center', fontSize: 10, color: 'var(--color-text-dim)', marginTop: 8 }}>
                Don't have an account? <a href="/login" style={{ color: 'var(--color-info)' }}>Sign up</a>
              </p>
            )}
          </>
        )}

        {preview?.status === 'accepted' && (
          <p style={{ color: 'var(--color-text-muted)', fontSize: 13 }}>This invite has already been accepted. <a href="/" style={{ color: 'var(--color-info)' }}>Open NexusAgent</a></p>
        )}
        {preview?.status === 'expired' && (
          <p style={{ color: 'var(--color-err)', fontSize: 13 }}>This invite has expired. Ask the inviter to send a new one.</p>
        )}
        {preview?.status === 'revoked' && (
          <p style={{ color: 'var(--color-err)', fontSize: 13 }}>This invite was revoked.</p>
        )}
      </div>
    </div>
  );
}
