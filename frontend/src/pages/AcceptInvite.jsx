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
    <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: '#06080f' }}>
      <div style={{ width: 420, padding: 32, borderRadius: 16, background: '#0f172a', border: '1px solid #1e293b' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div style={{ width: 48, height: 48, borderRadius: 12, background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontSize: 20, fontWeight: 700, marginBottom: 12 }}>N</div>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: 'white' }}>NexusAgent invite</h1>
        </div>

        {error && (
          <div style={{ padding: '8px 12px', borderRadius: 8, background: '#ef444415', color: '#f87171', fontSize: 12, marginBottom: 12, border: '1px solid #ef444425' }}>
            {error}
          </div>
        )}
        {info && (
          <div style={{ padding: '8px 12px', borderRadius: 8, background: '#22c55e15', color: '#4ade80', fontSize: 12, marginBottom: 12, border: '1px solid #22c55e25' }}>
            {info}
          </div>
        )}

        {!preview && !error && (
          <p style={{ textAlign: 'center', color: '#64748b' }}>Loading invite...</p>
        )}

        {preview?.status === 'pending' && (
          <>
            <p style={{ fontSize: 13, color: '#e2e8f0', marginBottom: 8 }}>
              You've been invited to join <strong>{preview.business_name}</strong>
            </p>
            <div style={{ padding: 12, background: '#0f1e33', borderRadius: 8, fontSize: 12, color: '#94a3b8', marginBottom: 16 }}>
              <div>Email: <strong style={{ color: '#e2e8f0' }}>{preview.email}</strong></div>
              <div>Role: <strong style={{ color: '#e2e8f0' }}>{preview.role}</strong></div>
            </div>
            <button onClick={handleAccept} className="btn-primary" disabled={loading}
              style={{ width: '100%', justifyContent: 'center', padding: '10px 0', fontSize: 14 }}>
              {loading ? 'Accepting...' : isLoggedIn() ? 'Accept invite' : 'Log in to accept'}
            </button>
            {!isLoggedIn() && (
              <p style={{ textAlign: 'center', fontSize: 10, color: '#64748b', marginTop: 8 }}>
                Don't have an account? <a href="/login" style={{ color: '#60a5fa' }}>Sign up</a>
              </p>
            )}
          </>
        )}

        {preview?.status === 'accepted' && (
          <p style={{ color: '#94a3b8', fontSize: 13 }}>This invite has already been accepted. <a href="/" style={{ color: '#60a5fa' }}>Open NexusAgent</a></p>
        )}
        {preview?.status === 'expired' && (
          <p style={{ color: '#f87171', fontSize: 13 }}>This invite has expired. Ask the inviter to send a new one.</p>
        )}
        {preview?.status === 'revoked' && (
          <p style={{ color: '#f87171', fontSize: 13 }}>This invite was revoked.</p>
        )}
      </div>
    </div>
  );
}
