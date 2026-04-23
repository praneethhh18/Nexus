import { useState, useEffect, useCallback } from 'react';
import { Shield, Smartphone, Key, Laptop, X, Check, AlertTriangle, Copy, RefreshCw } from 'lucide-react';
import {
  twofaStatus, twofaEnroll, twofaVerify, twofaDisable, twofaRegenerate,
  listSessions, revokeSession, revokeAllOther,
} from '../services/security';

function formatWhen(iso) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); }
  catch { return iso.substring(0, 16); }
}

function humanUserAgent(ua) {
  if (!ua) return 'Unknown device';
  const m = ua;
  if (/Edg\//i.test(m)) return 'Edge';
  if (/OPR\//i.test(m) || /Opera/i.test(m)) return 'Opera';
  if (/Firefox/i.test(m)) return 'Firefox';
  if (/Chrome/i.test(m)) return 'Chrome';
  if (/Safari/i.test(m)) return 'Safari';
  if (/curl/i.test(m)) return 'curl / API';
  return m.substring(0, 40);
}

export default function Security() {
  const [twofa, setTwofa] = useState(null);
  const [enrollData, setEnrollData] = useState(null);
  const [verifyCode, setVerifyCode] = useState('');
  const [newRecoveryCodes, setNewRecoveryCodes] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [disableCode, setDisableCode] = useState('');
  const [msg, setMsg] = useState('');

  const reload = useCallback(async () => {
    try {
      const [s, list] = await Promise.all([twofaStatus(), listSessions()]);
      setTwofa(s);
      setSessions(list);
    } catch (e) { setMsg(`Failed: ${e.message}`); }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const handleEnroll = async () => {
    try {
      const data = await twofaEnroll();
      setEnrollData(data);
      setNewRecoveryCodes(null);
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleVerify = async () => {
    if (!verifyCode.trim()) return;
    try {
      const res = await twofaVerify(verifyCode.trim());
      setNewRecoveryCodes(res.recovery_codes);
      setEnrollData(null);
      setVerifyCode('');
      flash('2FA enabled.');
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleDisable = async () => {
    if (!disableCode.trim()) return;
    if (!confirm('Turn off 2FA? Your account will only be protected by your password after this.')) return;
    try {
      await twofaDisable(disableCode.trim());
      setDisableCode('');
      flash('2FA disabled.');
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleRegenerate = async () => {
    const code = prompt('Enter your current 6-digit code to regenerate recovery codes:');
    if (!code) return;
    try {
      const res = await twofaRegenerate(code.trim());
      setNewRecoveryCodes(res.recovery_codes);
      flash('New recovery codes generated. Save them now.');
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleRevoke = async (s) => {
    if (s.is_current) { flash("That's your current session — log out from here instead."); return; }
    if (!confirm(`Revoke this session from ${humanUserAgent(s.user_agent)}?`)) return;
    try { await revokeSession(s.jti); flash('Revoked.'); reload(); }
    catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleRevokeAll = async () => {
    if (!confirm('Log out all other devices? Current session stays.')) return;
    try {
      const r = await revokeAllOther();
      flash(`Revoked ${r.revoked || 0} other session${(r.revoked || 0) === 1 ? '' : 's'}.`);
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const copyCodes = async () => {
    if (!newRecoveryCodes) return;
    await navigator.clipboard.writeText(newRecoveryCodes.join('\n'));
    flash('Copied to clipboard.');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <h1>Security</h1>
        <p>Two-factor authentication and active sessions for your account</p>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: '#60a5fa' }}>{msg}</div>}

      <div className="page-body">
        {/* ── 2FA ──────────────────────────────────────────────────────────────── */}
        <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Shield size={16} color={twofa?.enabled ? '#22c55e' : '#64748b'} />
            Two-factor authentication
          </h3>

          {!twofa ? (
            <p style={{ fontSize: 12, color: '#64748b' }}>Loading…</p>
          ) : twofa.enabled ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <Check size={14} color="#22c55e" />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, color: '#e2e8f0' }}>
                    <strong style={{ color: '#22c55e' }}>Enabled</strong> since {formatWhen(twofa.enabled_at)}
                  </div>
                  <div style={{ fontSize: 10, color: '#64748b' }}>
                    {twofa.recovery_codes_remaining} recovery codes remaining
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginTop: 10 }}>
                <input
                  className="field-input" style={{ fontSize: 12, width: 150, letterSpacing: 3, textAlign: 'center' }}
                  placeholder="123456" value={disableCode} onChange={(e) => setDisableCode(e.target.value)}
                />
                <button className="btn-ghost" style={{ color: '#f87171' }} onClick={handleDisable}>Disable 2FA</button>
                <div style={{ width: 1, background: '#1e293b', height: 20 }} />
                <button className="btn-ghost" onClick={handleRegenerate}>
                  <RefreshCw size={11} /> Regenerate recovery codes
                </button>
              </div>
            </div>
          ) : enrollData ? (
            <div>
              <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 10 }}>
                Scan this QR code in <strong>Google Authenticator</strong>, <strong>Authy</strong>, or <strong>1Password</strong>,
                then type the 6-digit code to verify.
              </p>
              <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', marginBottom: 10 }}>
                {enrollData.qr_data_url ? (
                  <img src={enrollData.qr_data_url} alt="2FA QR code" style={{ width: 180, height: 180, background: '#fff', padding: 8, borderRadius: 8 }} />
                ) : (
                  <div style={{ width: 180, padding: 12, background: '#0f172a', borderRadius: 8, fontSize: 10, color: '#94a3b8', wordBreak: 'break-all' }}>
                    QR rendering unavailable. Copy this URL into your authenticator:
                    <div style={{ marginTop: 6, fontFamily: 'monospace', color: '#60a5fa' }}>{enrollData.otpauth_url}</div>
                  </div>
                )}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Or type this key manually:</div>
                  <code style={{ fontSize: 11, color: '#e2e8f0', background: '#0f172a', padding: '4px 8px', borderRadius: 4, display: 'inline-block', marginBottom: 12, letterSpacing: 2 }}>
                    {enrollData.secret.match(/.{1,4}/g)?.join(' ')}
                  </code>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 6 }}>Enter the current code:</div>
                  <input
                    className="field-input"
                    placeholder="123456"
                    autoFocus
                    value={verifyCode}
                    onChange={(e) => setVerifyCode(e.target.value)}
                    style={{ fontSize: 18, letterSpacing: 4, textAlign: 'center', width: 180 }}
                    onKeyDown={(e) => { if (e.key === 'Enter') handleVerify(); }}
                  />
                  <div style={{ display: 'flex', gap: 6, marginTop: 10 }}>
                    <button className="btn-primary" onClick={handleVerify}>Verify & enable</button>
                    <button className="btn-ghost" onClick={() => { setEnrollData(null); setVerifyCode(''); }}>Cancel</button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div>
              <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 10 }}>
                Add an extra layer on your account. After enabling, you'll need your password <em>and</em> a 6-digit code from your authenticator app to log in.
              </p>
              <button className="btn-primary" onClick={handleEnroll}>
                <Smartphone size={12} /> Enable 2FA
              </button>
            </div>
          )}

          {newRecoveryCodes && (
            <div style={{ marginTop: 14, padding: 12, background: '#f59e0b15', border: '1px solid #f59e0b40', borderRadius: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                <AlertTriangle size={14} color="#fbbf24" />
                <strong style={{ fontSize: 12, color: '#fbbf24' }}>Recovery codes — shown ONCE</strong>
              </div>
              <p style={{ fontSize: 11, color: '#94a3b8', marginBottom: 8 }}>
                Save these somewhere safe. You can use any of them to log in if you lose your phone. Each one works once.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 8 }}>
                {newRecoveryCodes.map((c) => (
                  <code key={c} style={{ padding: '4px 8px', background: '#0f172a', borderRadius: 4, fontSize: 12, color: '#e2e8f0', letterSpacing: 1 }}>
                    {c}
                  </code>
                ))}
              </div>
              <button className="btn-ghost" onClick={copyCodes}><Copy size={11} /> Copy all</button>
              <button className="btn-ghost" style={{ marginLeft: 6 }} onClick={() => setNewRecoveryCodes(null)}>I've saved them</button>
            </div>
          )}
        </div>

        {/* ── Active sessions ────────────────────────────────────────────────── */}
        <div className="panel">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
              <Laptop size={16} color="#60a5fa" /> Active sessions
            </h3>
            {sessions.filter(s => !s.revoked_at && !s.is_current).length > 0 && (
              <button className="btn-ghost" style={{ color: '#f87171' }} onClick={handleRevokeAll}>
                Revoke all other sessions
              </button>
            )}
          </div>
          {sessions.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: 12 }}>Loading…</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {sessions.map((s) => {
                const isActive = !s.revoked_at;
                return (
                  <div key={s.jti} style={{
                    padding: '10px 12px', background: '#0f172a', borderRadius: 6,
                    display: 'flex', alignItems: 'center', gap: 10,
                    borderLeft: `3px solid ${s.is_current ? '#22c55e' : isActive ? '#60a5fa' : '#475569'}`,
                    opacity: isActive ? 1 : 0.5,
                  }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: 8 }}>
                        {humanUserAgent(s.user_agent)}
                        {s.is_current && <span style={{ fontSize: 9, padding: '1px 6px', background: '#22c55e22', color: '#4ade80', borderRadius: 10, fontWeight: 600 }}>THIS DEVICE</span>}
                        {!isActive && <span style={{ fontSize: 9, color: '#64748b' }}>revoked</span>}
                      </div>
                      <div style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>
                        {s.ip || 'unknown ip'} · started {formatWhen(s.created_at)}
                        {s.last_seen_at && <> · last seen {formatWhen(s.last_seen_at)}</>}
                      </div>
                    </div>
                    {isActive && !s.is_current && (
                      <button className="btn-ghost" style={{ padding: 4, color: '#f87171' }} onClick={() => handleRevoke(s)} title="Revoke">
                        <X size={12} />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          <p style={{ fontSize: 10, color: '#64748b', marginTop: 10 }}>
            Revoking a session immediately invalidates its login token — the other device will have to sign in again.
          </p>
        </div>
      </div>
    </div>
  );
}
