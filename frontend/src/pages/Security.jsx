import { useState, useEffect, useCallback } from 'react';
import { Shield, Smartphone, Laptop, X, Check, AlertTriangle, Copy, RefreshCw,
         Cloud, CloudOff, Eye, EyeOff, Trash2, Lock, ShieldCheck } from 'lucide-react';
import {
  twofaStatus, twofaEnroll, twofaVerify, twofaDisable, twofaRegenerate,
  listSessions, revokeSession, revokeAllOther,
  privacyStatus, privacyAudit, privacyAuditClear,
} from '../services/security';

function formatWhen(iso) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }); }
  catch { return iso.substring(0, 16); }
}

function formatAgo(ts) {
  if (!ts) return '—';
  const s = Math.max(0, Math.floor(Date.now() / 1000 - Number(ts)));
  if (s < 60) return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

function StatusChip({ icon, label, value, sub, tone = 'dim' }) {
  const toneColor = {
    accent: 'var(--color-accent)',
    warn:   'var(--color-warn)',
    dim:    'var(--color-text-dim)',
  }[tone];
  return (
    <div style={{
      padding: '10px 12px',
      borderRadius: 'var(--r-md)',
      background: 'var(--color-surface-1)',
      border: '1px solid var(--color-border)',
      display: 'flex', flexDirection: 'column', gap: 4,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: toneColor, fontSize: 11, textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600 }}>
        {icon}
        {label}
      </div>
      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>{value}</div>
      {sub && <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{sub}</div>}
    </div>
  );
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
  const [privacy, setPrivacy] = useState(null);
  const [privacyLog, setPrivacyLog] = useState({ stats: null, entries: [] });
  const [privacyLoading, setPrivacyLoading] = useState(false);
  const [showRaw, setShowRaw] = useState(false);

  const reload = useCallback(async () => {
    try {
      const [s, list] = await Promise.all([twofaStatus(), listSessions()]);
      setTwofa(s);
      setSessions(list);
    } catch (e) { setMsg(`Failed: ${e.message}`); }
  }, []);

  const reloadPrivacy = useCallback(async () => {
    setPrivacyLoading(true);
    try {
      const [st, log] = await Promise.all([privacyStatus(), privacyAudit(50)]);
      setPrivacy(st);
      setPrivacyLog(log);
    } catch (e) {
      // non-admins get 403 on the audit log — still show status
      try { setPrivacy(await privacyStatus()); } catch {}
    } finally {
      setPrivacyLoading(false);
    }
  }, []);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { reload(); reloadPrivacy(); }, [reload, reloadPrivacy]);

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

  const handleClearAudit = async () => {
    if (!confirm('Clear the cloud audit log? This only removes the local record — it cannot undo calls that already happened.')) return;
    try {
      await privacyAuditClear();
      flash('Audit log cleared.');
      reloadPrivacy();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <h1>Security</h1>
        <p>Two-factor authentication and active sessions for your account</p>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      <div className="page-body">
        {/* ── Cloud privacy ────────────────────────────────────────────────────── */}
        <div className="panel">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
              <ShieldCheck size={16} color="var(--color-accent)" />
              Cloud privacy
            </h3>
            <button className="btn-ghost" onClick={reloadPrivacy} disabled={privacyLoading}>
              <RefreshCw size={11} style={{ animation: privacyLoading ? 'spin 1s linear infinite' : 'none' }} />
              Refresh
            </button>
          </div>

          {!privacy ? (
            <p style={{ fontSize: 12, color: 'var(--color-text-dim)' }}>Loading…</p>
          ) : (
            <>
              {/* Status chips */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 10, marginBottom: 14 }}>
                <StatusChip
                  icon={privacy.allow_cloud_llm && privacy.cloud_configured ? <Cloud size={14} /> : <CloudOff size={14} />}
                  label="Cloud LLM"
                  value={!privacy.cloud_configured ? 'Not configured' : privacy.allow_cloud_llm ? `On · ${privacy.provider}` : 'Disabled'}
                  tone={!privacy.cloud_configured ? 'dim' : privacy.allow_cloud_llm ? 'accent' : 'warn'}
                  sub={privacy.cloud_model || 'Local only'}
                />
                <StatusChip
                  icon={<Lock size={14} />}
                  label="PII redaction"
                  value={privacy.redact_pii ? 'Active' : 'Off'}
                  tone={privacy.redact_pii ? 'accent' : 'warn'}
                  sub={privacy.redact_pii ? 'Emails, IDs, secrets scrubbed' : 'No outbound scrubbing'}
                />
                <StatusChip
                  icon={<Eye size={14} />}
                  label="Audit logging"
                  value={privacy.audit_enabled ? 'Recording' : 'Off'}
                  tone={privacy.audit_enabled ? 'accent' : 'warn'}
                  sub={privacyLog?.stats ? `${privacyLog.stats.total} calls tracked` : ''}
                />
              </div>

              {/* Aggregate stats */}
              {privacyLog?.stats && (
                <div className="stat-grid" style={{ marginBottom: 14 }}>
                  <div className="stat-card">
                    <div className="value">{privacyLog.stats.total}</div>
                    <div className="label">Total cloud calls</div>
                  </div>
                  <div className="stat-card">
                    <div className="value">{privacyLog.stats.last_24h}</div>
                    <div className="label">Last 24 hours</div>
                  </div>
                  <div className="stat-card">
                    <div className="value">{privacyLog.stats.total_redactions}</div>
                    <div className="label">PII tokens redacted</div>
                  </div>
                  <div className="stat-card">
                    <div className="value">{(privacyLog.stats.total_chars || 0).toLocaleString()}</div>
                    <div className="label">Chars sent (lifetime)</div>
                  </div>
                </div>
              )}

              {/* Explanation */}
              <div style={{
                padding: 12, borderRadius: 'var(--r-md)',
                background: 'var(--color-accent-soft)',
                border: '1px solid color-mix(in srgb, var(--color-accent) 25%, transparent)',
                fontSize: 12, color: 'var(--color-text)', marginBottom: 14, lineHeight: 1.55,
              }}>
                <strong style={{ color: 'var(--color-accent)' }}>What this log shows:</strong>{' '}
                every time NexusAgent talks to a cloud LLM, we record the timestamp, provider, model,
                a SHA-256 fingerprint of the (already-redacted) payload, and how many PII tokens were
                scrubbed. <strong>The raw prompt is never stored</strong> — the log itself can't leak
                what it's protecting. Raw database rows, email bodies, and customer records never
                enter this list because those paths are forced to local Ollama.
              </div>

              {/* Entry list */}
              {privacyLog?.entries?.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                    <div style={{ fontSize: 11, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600 }}>
                      Recent cloud calls ({privacyLog.entries.length})
                    </div>
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="btn-ghost" onClick={() => setShowRaw(v => !v)}>
                        {showRaw ? <EyeOff size={11} /> : <Eye size={11} />}
                        {showRaw ? 'Hide hashes' : 'Show hashes'}
                      </button>
                      <button className="btn-ghost" style={{ color: 'var(--color-err)' }} onClick={handleClearAudit}>
                        <Trash2 size={11} /> Clear log
                      </button>
                    </div>
                  </div>

                  <div className="table-panel">
                    <table className="data-table">
                      <thead>
                        <tr>
                          <th>When</th>
                          <th>Provider</th>
                          <th>Model</th>
                          <th>Mode</th>
                          <th style={{ textAlign: 'right' }}>Chars</th>
                          <th style={{ textAlign: 'right' }}>Redactions</th>
                          {showRaw && <th>Payload SHA</th>}
                        </tr>
                      </thead>
                      <tbody>
                        {privacyLog.entries.map((e, i) => (
                          <tr key={`${e.ts}-${i}`}>
                            <td style={{ color: 'var(--color-text-muted)' }}>{formatAgo(e.ts)}</td>
                            <td>
                              <span className="tool-badge tool-sql" style={{ textTransform: 'lowercase' }}>
                                {e.provider}
                              </span>
                            </td>
                            <td style={{ color: 'var(--color-text-dim)', fontSize: 11 }}>{e.model}</td>
                            <td style={{ color: 'var(--color-text-dim)', fontSize: 11 }}>
                              {e.meta?.mode || 'invoke'}
                            </td>
                            <td style={{ textAlign: 'right', fontFamily: 'ui-monospace, Menlo, monospace' }}>
                              {e.prompt_chars ?? 0}
                            </td>
                            <td style={{ textAlign: 'right', color: e.redactions > 0 ? 'var(--color-accent)' : 'var(--color-text-dim)' }}>
                              {e.redactions || 0}
                            </td>
                            {showRaw && (
                              <td style={{ fontFamily: 'ui-monospace, Menlo, monospace', fontSize: 10, color: 'var(--color-text-dim)' }}>
                                {e.prompt_sha256}
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <p style={{ fontSize: 12, color: 'var(--color-text-dim)', padding: '12px 0' }}>
                  {!privacy.cloud_configured
                    ? 'No cloud provider is configured — every LLM call runs on local Ollama. Nothing has left this machine.'
                    : privacyLog?.stats?.total === 0
                    ? 'No cloud calls recorded yet. This log populates the first time the app sends an aggregate or non-sensitive prompt to the cloud.'
                    : 'Audit log access is restricted to admin/owner accounts.'}
                </p>
              )}
            </>
          )}
        </div>

        {/* ── Voice providers ──────────────────────────────────────────────────
            Voice calls placed by Vox cross the network boundary — Twilio carries
            the PSTN audio, Groq does STT + LLM, ElevenLabs does TTS. Listed
            explicitly here because the rest of NexusAgent's privacy story is
            "nothing leaves the box" and voice is the carve-out.
        */}
        <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, margin: 0 }}>
            <Cloud size={16} color="var(--color-accent)" />
            Cloud providers · Voice agent
          </h3>

          <div style={{
            padding: 12, borderRadius: 'var(--r-md)',
            background: 'var(--color-warn-soft, color-mix(in srgb, var(--color-warn) 10%, transparent))',
            border: '1px solid color-mix(in srgb, var(--color-warn) 30%, transparent)',
            fontSize: 12, color: 'var(--color-text)', margin: '12px 0 14px', lineHeight: 1.55,
          }}>
            <strong style={{ color: 'var(--color-warn)' }}>Voice calls leave your machine.</strong>{' '}
            Unlike the rest of NexusAgent, outbound voice uses cloud providers for
            audio routing, transcription, and synthesis. Transcripts and summaries
            are stored locally and never sent to third parties beyond the listed providers.
            Consent gating, per-business daily-minute caps, and the call audit log all
            apply on top of these provider calls.
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { name: 'Twilio',     role: 'PSTN audio routing (outbound voice calls + media stream)' },
              { name: 'Groq',       role: 'Speech-to-text (Whisper large-v3-turbo) + LLM (Llama 3.1 8B Instant)' },
              { name: 'ElevenLabs', role: 'Text-to-speech (Turbo v2.5)' },
            ].map(p => (
              <div key={p.name} style={{
                display: 'flex', alignItems: 'flex-start', gap: 10,
                padding: 10, borderRadius: 'var(--r-md)',
                background: 'var(--color-surface-2)',
                border: '1px solid var(--color-border)',
                fontSize: 12.5, color: 'var(--color-text)',
              }}>
                <Cloud size={13} style={{ color: 'var(--color-text-dim)', flexShrink: 0, marginTop: 2 }} />
                <div>
                  <div style={{ fontWeight: 600, marginBottom: 2 }}>{p.name}</div>
                  <div style={{ color: 'var(--color-text-muted)', lineHeight: 1.45 }}>{p.role}</div>
                </div>
              </div>
            ))}
          </div>

          <p style={{
            fontSize: 11, color: 'var(--color-text-dim)',
            marginTop: 10, lineHeight: 1.5,
          }}>
            Self-hosted plans can swap providers via env vars: <code>OUTBOUND_STT</code>,{' '}
            <code>OUTBOUND_LLM</code>, <code>OUTBOUND_TTS</code>. Disable voice entirely
            by leaving <code>TWILIO_ACCOUNT_SID</code> unset.
          </p>
        </div>

        {/* ── 2FA ──────────────────────────────────────────────────────────────── */}
        <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Shield size={16} color={twofa?.enabled ? 'var(--color-ok)' : 'var(--color-text-dim)'} />
            Two-factor authentication
          </h3>

          {!twofa ? (
            <p style={{ fontSize: 12, color: 'var(--color-text-dim)' }}>Loading…</p>
          ) : twofa.enabled ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                <Check size={14} color="var(--color-ok)" />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, color: 'var(--color-text)' }}>
                    <strong style={{ color: 'var(--color-ok)' }}>Enabled</strong> since {formatWhen(twofa.enabled_at)}
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>
                    {twofa.recovery_codes_remaining} recovery codes remaining
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginTop: 10 }}>
                <input
                  className="field-input" style={{ fontSize: 12, width: 150, letterSpacing: 3, textAlign: 'center' }}
                  placeholder="123456" value={disableCode} onChange={(e) => setDisableCode(e.target.value)}
                />
                <button className="btn-ghost" style={{ color: 'var(--color-err)' }} onClick={handleDisable}>Disable 2FA</button>
                <div style={{ width: 1, background: 'var(--color-surface-2)', height: 20 }} />
                <button className="btn-ghost" onClick={handleRegenerate}>
                  <RefreshCw size={11} /> Regenerate recovery codes
                </button>
              </div>
            </div>
          ) : enrollData ? (
            <div>
              <p style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 10 }}>
                Scan this QR code in <strong>Google Authenticator</strong>, <strong>Authy</strong>, or <strong>1Password</strong>,
                then type the 6-digit code to verify.
              </p>
              <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start', marginBottom: 10 }}>
                {enrollData.qr_data_url ? (
                  <img src={enrollData.qr_data_url} alt="2FA QR code" style={{ width: 180, height: 180, background: '#fff', padding: 8, borderRadius: 8 }} />
                ) : (
                  <div style={{ width: 180, padding: 12, background: 'var(--color-surface-1)', borderRadius: 8, fontSize: 10, color: 'var(--color-text-muted)', wordBreak: 'break-all' }}>
                    QR rendering unavailable. Copy this URL into your authenticator:
                    <div style={{ marginTop: 6, fontFamily: 'monospace', color: 'var(--color-info)' }}>{enrollData.otpauth_url}</div>
                  </div>
                )}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginBottom: 4 }}>Or type this key manually:</div>
                  <code style={{ fontSize: 11, color: 'var(--color-text)', background: 'var(--color-surface-1)', padding: '4px 8px', borderRadius: 4, display: 'inline-block', marginBottom: 12, letterSpacing: 2 }}>
                    {enrollData.secret.match(/.{1,4}/g)?.join(' ')}
                  </code>
                  <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 6 }}>Enter the current code:</div>
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
              <p style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 10 }}>
                Add an extra layer on your account. After enabling, you'll need your password <em>and</em> a 6-digit code from your authenticator app to log in.
              </p>
              <button className="btn-primary" onClick={handleEnroll}>
                <Smartphone size={12} /> Enable 2FA
              </button>
            </div>
          )}

          {newRecoveryCodes && (
            <div style={{ marginTop: 14, padding: 12, background: 'color-mix(in srgb, var(--color-warn) 8%, transparent)', border: '1px solid color-mix(in srgb, var(--color-warn) 25%, transparent)', borderRadius: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                <AlertTriangle size={14} color="var(--color-warn)" />
                <strong style={{ fontSize: 12, color: 'var(--color-warn)' }}>Recovery codes — shown ONCE</strong>
              </div>
              <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 8 }}>
                Save these somewhere safe. You can use any of them to log in if you lose your phone. Each one works once.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, marginBottom: 8 }}>
                {newRecoveryCodes.map((c) => (
                  <code key={c} style={{ padding: '4px 8px', background: 'var(--color-surface-1)', borderRadius: 4, fontSize: 12, color: 'var(--color-text)', letterSpacing: 1 }}>
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
              <Laptop size={16} color="var(--color-info)" /> Active sessions
            </h3>
            {sessions.filter(s => !s.revoked_at && !s.is_current).length > 0 && (
              <button className="btn-ghost" style={{ color: 'var(--color-err)' }} onClick={handleRevokeAll}>
                Revoke all other sessions
              </button>
            )}
          </div>
          {sessions.length === 0 ? (
            <p style={{ color: 'var(--color-text-dim)', fontSize: 12 }}>Loading…</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {sessions.map((s) => {
                const isActive = !s.revoked_at;
                return (
                  <div key={s.jti} style={{
                    padding: '10px 12px', background: 'var(--color-surface-1)', borderRadius: 6,
                    display: 'flex', alignItems: 'center', gap: 10,
                    borderLeft: `3px solid ${s.is_current ? 'var(--color-ok)' : isActive ? 'var(--color-info)' : 'var(--color-text-dim)'}`,
                    opacity: isActive ? 1 : 0.5,
                  }}>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, color: 'var(--color-text)', display: 'flex', alignItems: 'center', gap: 8 }}>
                        {humanUserAgent(s.user_agent)}
                        {s.is_current && <span style={{ fontSize: 9, padding: '1px 6px', background: 'color-mix(in srgb, var(--color-ok) 13%, transparent)', color: 'var(--color-ok)', borderRadius: 10, fontWeight: 600 }}>THIS DEVICE</span>}
                        {!isActive && <span style={{ fontSize: 9, color: 'var(--color-text-dim)' }}>revoked</span>}
                      </div>
                      <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 2 }}>
                        {s.ip || 'unknown ip'} · started {formatWhen(s.created_at)}
                        {s.last_seen_at && <> · last seen {formatWhen(s.last_seen_at)}</>}
                      </div>
                    </div>
                    {isActive && !s.is_current && (
                      <button className="btn-ghost" style={{ padding: 4, color: 'var(--color-err)' }} onClick={() => handleRevoke(s)} title="Revoke">
                        <X size={12} />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
          <p style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 10 }}>
            Revoking a session immediately invalidates its login token — the other device will have to sign in again.
          </p>
        </div>
      </div>
    </div>
  );
}
