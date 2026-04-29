import { useState, useEffect } from 'react';
import { RefreshCw, Trash2, Server, Cpu, HardDrive, Code, Briefcase, Users, AlertTriangle, Calendar as CalendarIcon, Check, X, MessageCircle, Copy, Bell, Sparkles, Database, Loader2, ShieldCheck } from 'lucide-react';
import { getSettings, resetLLM, clearCache, listMembers, getBusiness, updateBusiness, deleteBusiness } from '../services/api';
import { getNotificationPrefs, setNotificationPrefs, reopenOnboarding } from '../services/onboarding';
import { downloadFullExport, downloadFullBackup, getBackupInfo, restoreBackup } from '../services/tags';
import { readIcp, writeIcp } from '../services/crm';
import { readSmtp, saveSmtp, deleteSmtp, testSmtp } from '../services/smtp';
import { Download } from 'lucide-react';
import { getToken, getBusinessId, getCurrentBusiness, logout } from '../services/auth';
import { calendarStatus, calendarStart, calendarDisconnect } from '../services/calendar';
import { getToken as getTok, getBusinessId as getBiz } from '../services/auth';

function etFetch(path, init = {}) {
  const h = { 'Content-Type': 'application/json', ...(init.headers || {}) };
  const t = getTok(); if (t) h['Authorization'] = `Bearer ${t}`;
  const b = getBiz(); if (b) h['X-Business-Id'] = b;
  return fetch(path, { ...init, headers: h });
}

function authFetch(path, init = {}) {
  const h = { 'Content-Type': 'application/json', ...(init.headers || {}) };
  const t = getToken();
  if (t) h['Authorization'] = `Bearer ${t}`;
  const b = getBusinessId();
  if (b) h['X-Business-Id'] = b;
  return fetch(path, { ...init, headers: h });
}

export default function Settings() {
  const [s, setS] = useState(null);
  const [msg, setMsg] = useState('');
  const [devMode, setDevMode] = useState(localStorage.getItem('nexus_dev_mode') === '1');
  const current = getCurrentBusiness();
  const [bizDetail, setBizDetail] = useState(null);
  const [bizName, setBizName] = useState('');
  const [bizIndustry, setBizIndustry] = useState('');
  const [bizDescription, setBizDescription] = useState('');
  const [calStatus, setCalStatus] = useState(null);
  const [etAccount, setEtAccount] = useState(null);
  const [etForm, setEtForm] = useState({ imap_host: 'imap.gmail.com', imap_port: 993, username: '', password: '', folder: 'INBOX', enabled: true, auto_draft_reply: true });
  const [waAccount, setWaAccount] = useState(null);
  const [waCode, setWaCode] = useState(null);
  const [waSecret, setWaSecret] = useState(null);
  const isAdmin = (() => {
    try { return (JSON.parse(localStorage.getItem('nexus_user')) || {}).role === 'admin'; } catch { return false; }
  })();

  const loadWaAccount = async () => {
    try {
      const r = await etFetch('/api/whatsapp/account');
      if (r.ok) setWaAccount(await r.json());
    } catch {}
  };
  useEffect(() => { loadWaAccount(); }, []);

  useEffect(() => {
    etFetch('/api/email-triage/account').then(r => r.json()).then((a) => {
      setEtAccount(a);
      if (a?.username) setEtForm((p) => ({ ...p, imap_host: a.imap_host || p.imap_host, imap_port: a.imap_port || 993, username: a.username, folder: a.folder || 'INBOX', enabled: !!a.enabled, auto_draft_reply: !!a.auto_draft_reply, password: '' }));
    }).catch(() => {});
  }, []);

  useEffect(() => {
    calendarStatus().then(setCalStatus).catch(() => {});
  }, []);

  useEffect(() => {
    getSettings().then(setS).catch(() => {});
    if (current) {
      getBusiness(current.id).then((b) => {
        setBizDetail(b);
        setBizName(b.name || '');
        setBizIndustry(b.industry || '');
        setBizDescription(b.description || '');
      }).catch(() => {});
    }
  }, [current?.id]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 3000); };

  const toggleDevMode = () => {
    const next = !devMode;
    setDevMode(next);
    localStorage.setItem('nexus_dev_mode', next ? '1' : '0');
    window.dispatchEvent(new Event('nexus-devmode-changed'));
    flash(next ? 'Developer Mode enabled — SQL Editor & Database Explorer are now visible.' : 'Developer Mode disabled.');
  };

  const saveBiz = async () => {
    if (!current) return;
    try {
      const updated = await updateBusiness(current.id, {
        name: bizName,
        industry: bizIndustry,
        description: bizDescription,
      });
      setBizDetail(updated);
      flash('Business saved.');
    } catch (e) {
      flash('Failed: ' + e.message);
    }
  };

  const removeBiz = async () => {
    if (!current) return;
    if (!confirm(`Delete "${current.name}"? This hides the business and its data; contact an admin to fully purge.`)) return;
    try {
      await deleteBusiness(current.id);
      localStorage.removeItem('nexus_business_id');
      window.location.href = '/';
    } catch (e) {
      flash('Failed: ' + e.message);
    }
  };

  if (!s) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--color-text-dim)' }}>Loading...</div>;

  const myRole = bizDetail?.my_role;
  const canEditBiz = myRole === 'owner' || myRole === 'admin';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header"><h1>Settings</h1><p>Manage your business, integrations, and system</p></div>
      <div className="page-body">
        {msg && <div className="panel" style={{ color: 'var(--color-info)', marginBottom: 12 }}>{msg}</div>}

        <NotificationPrefsPanel />
        <OnboardingReopenPanel />
        {isAdmin && <IcpPanel flash={flash} />}
        {isAdmin && <SmtpPanel flash={flash} />}
        <ExportPanel flash={flash} />
        {isAdmin && <BackupPanel flash={flash} />}
        {isAdmin && <RestorePanel flash={flash} />}

        {/* Developer Mode — moved to top as the master toggle */}
        <div className="panel" style={{ borderColor: devMode ? 'color-mix(in srgb, var(--color-accent) 35%, transparent)' : 'var(--color-border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Code size={18} color={devMode ? 'var(--color-accent)' : 'var(--color-text-dim)'} />
              <div>
                <div style={{ fontSize: 13, color: 'var(--color-text)', fontWeight: 600 }}>Developer mode</div>
                <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
                  {devMode
                    ? 'Showing advanced configuration — LLM, system info, email triage, SQL editor.'
                    : 'Showing the essentials. Turn this on to access advanced system configuration.'}
                </div>
              </div>
            </div>
            <button
              onClick={toggleDevMode}
              aria-pressed={devMode}
              style={{
                position: 'relative', width: 42, height: 22, borderRadius: 11,
                background: devMode ? 'var(--color-accent)' : 'var(--color-surface-3)',
                border: 'none', cursor: 'pointer', flexShrink: 0,
                transition: 'background var(--dur-fast) var(--ease-out)',
              }}
            >
              <div style={{
                position: 'absolute', top: 2, left: devMode ? 22 : 2,
                width: 18, height: 18, borderRadius: '50%', background: 'white',
                transition: 'left var(--dur-fast) var(--ease-out)',
                boxShadow: 'var(--shadow-1)',
              }} />
            </button>
          </div>
        </div>

        {/* Current Business */}
        {current && (
          <div className="panel">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Briefcase size={16} color="var(--color-ok)" /> Current Business</h3>
            <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginBottom: 12 }}>ID: {current.id} &middot; Your role: <strong style={{ color: 'var(--color-text)' }}>{myRole || '...'}</strong></div>
            <div style={{ display: 'grid', gap: 10 }}>
              <div>
                <label style={{ fontSize: 10, color: 'var(--color-text-dim)', display: 'block', marginBottom: 2 }}>Name</label>
                <input className="field-input" value={bizName} onChange={(e) => setBizName(e.target.value)} disabled={!canEditBiz} maxLength={120} />
              </div>
              <div>
                <label style={{ fontSize: 10, color: 'var(--color-text-dim)', display: 'block', marginBottom: 2 }}>Industry</label>
                <input className="field-input" value={bizIndustry} onChange={(e) => setBizIndustry(e.target.value)} disabled={!canEditBiz} maxLength={80} />
              </div>
              <div>
                <label style={{ fontSize: 10, color: 'var(--color-text-dim)', display: 'block', marginBottom: 2 }}>Description</label>
                <textarea className="field-input" rows={2} value={bizDescription} onChange={(e) => setBizDescription(e.target.value)} disabled={!canEditBiz} maxLength={500} />
              </div>
              {canEditBiz && (
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn-ghost" onClick={saveBiz}>Save</button>
                  {myRole === 'owner' && (
                    <button className="btn-ghost" style={{ color: 'var(--color-err)', borderColor: '#7f1d1d' }} onClick={removeBiz}>
                      <AlertTriangle size={12} /> Delete business
                    </button>
                  )}
                </div>
              )}
            </div>
            {bizDetail?.members?.length > 0 && (
              <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--color-surface-2)' }}>
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Users size={12} /> Members ({bizDetail.members.length})
                </div>
                {bizDetail.members.map(m => (
                  <div key={m.user_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 11, color: 'var(--color-text)' }}>
                    <span>{m.name || m.email || m.user_id}</span>
                    <span style={{ color: 'var(--color-text-dim)' }}>{m.role}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* WhatsApp */}
        <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <MessageCircle size={16} color="#25D366" /> WhatsApp
          </h3>
          <p style={{ fontSize: 11, color: 'var(--color-text-dim)', marginBottom: 10 }}>
            Text the agent on WhatsApp to get tasks, reports, and updates on the go.
            Open-source bridge using Baileys — no Twilio, no Meta business verification.
            See <code>whatsapp_bridge/README.md</code> for bridge setup.
          </p>

          {waAccount?.phone ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <Check size={14} color="var(--color-ok)" />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, color: 'var(--color-text)' }}>Linked: <strong>+{waAccount.phone}</strong></div>
                <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>
                  Since {waAccount.linked_at?.substring(0, 16)} · {waAccount.messages_count || 0} messages
                </div>
              </div>
              <button className="btn-ghost" style={{ color: 'var(--color-err)' }} onClick={async () => {
                if (!confirm('Unlink this phone from your account?')) return;
                await etFetch('/api/whatsapp/account', { method: 'DELETE' });
                await loadWaAccount();
                flash('Unlinked.');
              }}>
                <X size={12} /> Unlink
              </button>
            </div>
          ) : (
            <div style={{ padding: 12, background: 'var(--color-surface-1)', borderRadius: 8, marginBottom: 12 }}>
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 8 }}>
                <strong style={{ color: 'var(--color-text)' }}>Not linked yet.</strong> To link your phone:
              </div>
              <ol style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 18, lineHeight: 1.7 }}>
                <li>Click <em>Generate link code</em> below</li>
                <li>Text the 6-character code to the WhatsApp number running your bridge</li>
                <li>You're linked — ask the bot anything</li>
              </ol>

              {waCode ? (
                <div style={{ marginTop: 10, padding: 12, background: 'var(--color-bg)', border: '1px dashed color-mix(in srgb, var(--color-ok) 31%, transparent)', borderRadius: 8, textAlign: 'center' }}>
                  <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginBottom: 4 }}>Send this code to the WhatsApp bot now:</div>
                  <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: 6, color: 'var(--color-ok)', fontFamily: 'monospace' }}>{waCode.code}</div>
                  <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 4 }}>
                    Expires in {waCode.ttl_minutes} minutes · The phone you text from becomes your linked number.
                  </div>
                  <button className="btn-ghost" style={{ marginTop: 8 }} onClick={async () => {
                    await navigator.clipboard.writeText(waCode.code);
                    flash('Copied.');
                  }}>
                    <Copy size={11} /> Copy
                  </button>
                  <button className="btn-ghost" style={{ marginTop: 8, marginLeft: 6 }} onClick={async () => {
                    await loadWaAccount();
                    flash(waAccount?.phone ? 'Linked!' : 'Not linked yet — send the code on WhatsApp.');
                  }}>
                    Check status
                  </button>
                </div>
              ) : (
                <button className="btn-primary" style={{ marginTop: 8 }} onClick={async () => {
                  try {
                    const r = await etFetch('/api/whatsapp/link/generate', { method: 'POST' });
                    if (!r.ok) throw new Error(await r.text());
                    setWaCode(await r.json());
                  } catch (e) { flash(`Failed: ${e.message}`); }
                }}>
                  Generate link code
                </button>
              )}
            </div>
          )}

          {isAdmin && devMode && (
            <div style={{ padding: 10, background: 'var(--color-bg)', border: '1px solid var(--color-border-strong)', borderRadius: 6 }}>
              <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
                Bridge secret (admin only)
              </div>
              <p style={{ fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 6 }}>
                Paste this into <code>whatsapp_bridge/.env</code> as <code>NEXUS_WEBHOOK_SECRET</code>.
              </p>
              {waSecret ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <code style={{ flex: 1, padding: 6, background: 'var(--color-bg)', borderRadius: 4, fontSize: 10, color: 'var(--color-text)', overflow: 'auto', whiteSpace: 'nowrap' }}>
                    {waSecret}
                  </code>
                  <button className="btn-ghost" onClick={async () => {
                    await navigator.clipboard.writeText(waSecret);
                    flash('Copied to clipboard.');
                  }}><Copy size={12} /></button>
                  <button className="btn-ghost" onClick={() => setWaSecret(null)}>Hide</button>
                </div>
              ) : (
                <button className="btn-ghost" onClick={async () => {
                  try {
                    const r = await etFetch('/api/whatsapp/bridge-secret');
                    if (!r.ok) throw new Error(await r.text());
                    const data = await r.json();
                    setWaSecret(data.secret);
                  } catch (e) { flash(`Failed: ${e.message}`); }
                }}>Show bridge secret</button>
              )}
            </div>
          )}
        </div>

        {/* Email triage — advanced IMAP config, dev-only */}
        {devMode && <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>📬 Email Triage Agent</h3>
          <p style={{ fontSize: 11, color: 'var(--color-text-dim)', marginBottom: 10 }}>
            Connect an IMAP inbox. Every 15 minutes the agent reads unread messages, classifies each as
            lead/invoice/support/noise, auto-logs CRM interactions for known contacts, and queues reply drafts
            for your approval. Nothing is ever sent without your OK.
          </p>
          {etAccount?.username ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
              <Check size={14} color={etAccount.enabled ? 'var(--color-ok)' : 'var(--color-text-dim)'} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, color: 'var(--color-text)' }}>
                  {etAccount.username} @ {etAccount.imap_host}:{etAccount.imap_port} · {etAccount.folder}
                </div>
                <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>
                  {etAccount.enabled ? 'Enabled' : 'Disabled'} · {etAccount.auto_draft_reply ? 'auto-drafts replies' : 'classify only'}
                </div>
              </div>
              <button className="btn-ghost" onClick={async () => {
                const r = await etFetch('/api/email-triage/run', { method: 'POST' });
                const d = await r.json();
                flash(`Processed ${d.processed || 0} messages.`);
              }}>Run now</button>
              <button className="btn-ghost" style={{ color: 'var(--color-err)' }} onClick={async () => {
                if (!confirm('Disconnect email triage? Saved message logs will remain.')) return;
                await etFetch('/api/email-triage/account', { method: 'DELETE' });
                setEtAccount(null);
                flash('Disconnected.');
              }}>
                <X size={12} /> Disconnect
              </button>
            </div>
          ) : null}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <div>
              <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>IMAP host</label>
              <input className="field-input" value={etForm.imap_host} onChange={(e) => setEtForm({ ...etForm, imap_host: e.target.value })} placeholder="imap.gmail.com" />
            </div>
            <div>
              <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>Port</label>
              <input className="field-input" type="number" value={etForm.imap_port} onChange={(e) => setEtForm({ ...etForm, imap_port: parseInt(e.target.value) || 993 })} />
            </div>
            <div>
              <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>Username (email)</label>
              <input className="field-input" value={etForm.username} onChange={(e) => setEtForm({ ...etForm, username: e.target.value })} />
            </div>
            <div>
              <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>Password (app-specific)</label>
              <input className="field-input" type="password" value={etForm.password} onChange={(e) => setEtForm({ ...etForm, password: e.target.value })} placeholder={etAccount?.username ? '(leave blank to keep)' : ''} />
            </div>
            <div>
              <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>Folder</label>
              <input className="field-input" value={etForm.folder} onChange={(e) => setEtForm({ ...etForm, folder: e.target.value })} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, paddingTop: 16 }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--color-text-muted)', cursor: 'pointer' }}>
                <input type="checkbox" checked={etForm.enabled} onChange={(e) => setEtForm({ ...etForm, enabled: e.target.checked })} />
                Enabled
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--color-text-muted)', cursor: 'pointer' }}>
                <input type="checkbox" checked={etForm.auto_draft_reply} onChange={(e) => setEtForm({ ...etForm, auto_draft_reply: e.target.checked })} />
                Auto-draft replies
              </label>
            </div>
          </div>
          <div style={{ marginTop: 10 }}>
            <button className="btn-primary" onClick={async () => {
              if (!etForm.username || (!etForm.password && !etAccount?.username)) {
                flash('Username and password are required.');
                return;
              }
              const body = { ...etForm };
              if (!body.password && etAccount?.username) delete body.password;
              const r = await etFetch('/api/email-triage/account', { method: 'POST', body: JSON.stringify(body) });
              if (!r.ok) { flash(`Failed: ${await r.text()}`); return; }
              const saved = await r.json();
              setEtAccount(saved);
              setEtForm((p) => ({ ...p, password: '' }));
              flash('Saved. Click "Run now" to test.');
            }}>
              {etAccount?.username ? 'Update' : 'Connect'}
            </button>
          </div>
        </div>}

        {/* Google Calendar */}
        <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><CalendarIcon size={16} color="var(--color-info)" /> Google Calendar</h3>
          {!calStatus ? (
            <p style={{ fontSize: 12, color: 'var(--color-text-dim)' }}>Checking...</p>
          ) : !calStatus.configured ? (
            <p style={{ fontSize: 12, color: 'var(--color-text-dim)' }}>
              Not available. An admin needs to set <code>GOOGLE_CLIENT_ID</code> and <code>GOOGLE_CLIENT_SECRET</code> in <code>.env</code> first.
            </p>
          ) : calStatus.connected ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Check size={14} color="var(--color-ok)" />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, color: 'var(--color-text)' }}>Connected: <strong>{calStatus.connection?.account_email || '...'}</strong></div>
                <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>Since {calStatus.connection?.connected_at?.substring(0, 16)}</div>
              </div>
              <button className="btn-ghost" style={{ color: 'var(--color-err)' }} onClick={async () => {
                if (!confirm('Disconnect Google Calendar?')) return;
                try { await calendarDisconnect(); setCalStatus(await calendarStatus()); flash('Disconnected.'); }
                catch (e) { flash(`Failed: ${e.message}`); }
              }}>
                <X size={12} /> Disconnect
              </button>
            </div>
          ) : (
            <div>
              <p style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 8 }}>
                Connect your Google Calendar to see upcoming meetings on your dashboard.
              </p>
              <button className="btn-primary" onClick={async () => {
                try {
                  const { authorize_url } = await calendarStart();
                  const w = window.open(authorize_url, 'nexus-calendar-oauth', 'width=520,height=700');
                  // Poll for the popup closing, then re-check status
                  const iv = setInterval(async () => {
                    if (w && w.closed) {
                      clearInterval(iv);
                      try { setCalStatus(await calendarStatus()); } catch {}
                    }
                  }, 1000);
                } catch (e) { flash(`Failed: ${e.message}`); }
              }}>
                Connect Google Calendar
              </button>
            </div>
          )}
        </div>

        {/* Models — dev-only */}
        {devMode && <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Cpu size={16} color="var(--color-info)" /> LLM Configuration</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[['Primary LLM', s.primary_model], ['Fallback LLM', s.fallback_model], ['Embedding', s.embed_model], ['Ollama URL', s.ollama_url]].map(([k, v], i) => (
              <div key={i} className="info-row" style={{ flexDirection: 'column', background: 'var(--color-surface-1)', borderRadius: 8, padding: 10, border: 'none' }}>
                <span className="key" style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 1 }}>{k}</span>
                <span className="val" style={{ fontSize: 12 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>}

        {/* Available Models — dev-only */}
        {devMode && s.available_models?.length > 0 && (
          <div className="panel">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Server size={16} color="#a78bfa" /> Available Ollama Models</h3>
            {s.available_models.map((m, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 10px', borderRadius: 6, background: 'var(--color-surface-1)', marginBottom: 4 }}>
                <span style={{ fontSize: 12, fontFamily: 'monospace', color: 'white' }}>{m.name}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>{m.size_gb} GB</span>
                  {m.active && <span style={{ fontSize: 9, padding: '2px 8px', borderRadius: 10, background: 'color-mix(in srgb, var(--color-ok) 8%, transparent)', color: 'var(--color-ok)', border: '1px solid color-mix(in srgb, var(--color-ok) 15%, transparent)' }}>Active</span>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* System Info — dev-only */}
        {devMode && <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><HardDrive size={16} color="#22d3ee" /> System Information</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
            {[['Version', `v${s.version}`], ['Python', s.python_version], ['SQL Retries', s.max_sql_retries],
              ['Reflection Retries', s.max_reflection_retries], ['Chunk Size', s.chunk_size], ['Top-K', s.top_k_retrieval],
              ['Email', s.email_enabled ? 'Enabled' : 'Disabled'], ['Discord', s.discord_enabled ? 'Enabled' : 'Disabled']
            ].map(([k, v], i) => (
              <div key={i} className="info-row"><span className="key">{k}</span><span className="val">{String(v)}</span></div>
            ))}
          </div>
        </div>}

        {/* Integrations (admin-only on server) */}
        <div className="panel">
          <h3>Integrations</h3>
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 10, color: 'var(--color-text-dim)', display: 'block', marginBottom: 2 }}>Discord Webhook URL</label>
            <div style={{ display: 'flex', gap: 6 }}>
              <input className="field-input" placeholder="https://discord.com/api/webhooks/..." id="discord-url"
                defaultValue={s.discord_enabled ? '(configured)' : ''} style={{ fontSize: 12 }} />
              <button className="btn-ghost" onClick={async () => {
                const url = document.getElementById('discord-url').value;
                if (!url || url === '(configured)') return;
                try {
                  const r = await authFetch('/api/settings/update', { method: 'POST',
                    body: JSON.stringify({ key: 'DISCORD_WEBHOOK_URL', value: url }) });
                  if (!r.ok) throw new Error(await r.text());
                  flash('Discord webhook saved.');
                } catch (e) { flash('Failed: ' + e.message); }
              }}>Save</button>
            </div>
          </div>
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 10, color: 'var(--color-text-dim)', display: 'block', marginBottom: 2 }}>Slack Webhook URL</label>
            <div style={{ display: 'flex', gap: 6 }}>
              <input className="field-input" placeholder="https://hooks.slack.com/services/..." id="slack-url" style={{ fontSize: 12 }} />
              <button className="btn-ghost" onClick={async () => {
                const url = document.getElementById('slack-url').value;
                if (!url) return;
                try {
                  const r = await authFetch('/api/settings/update', { method: 'POST',
                    body: JSON.stringify({ key: 'SLACK_WEBHOOK_URL', value: url }) });
                  if (!r.ok) throw new Error(await r.text());
                  flash('Slack webhook saved.');
                } catch (e) { flash('Failed: ' + e.message); }
              }}>Save</button>
            </div>
          </div>
          <div>
            <label style={{ fontSize: 10, color: 'var(--color-text-dim)', display: 'block', marginBottom: 2 }}>Gmail App Password</label>
            <div style={{ display: 'flex', gap: 6 }}>
              <input className="field-input" type="password" placeholder="16-char app password" id="gmail-pw" style={{ fontSize: 12 }} />
              <button className="btn-ghost" onClick={async () => {
                const pw = document.getElementById('gmail-pw').value;
                if (!pw) return;
                try {
                  const r = await authFetch('/api/settings/update', { method: 'POST',
                    body: JSON.stringify({ key: 'GMAIL_APP_PASSWORD', value: pw }) });
                  if (!r.ok) throw new Error(await r.text());
                  flash('Gmail password saved.');
                } catch (e) { flash('Failed: ' + e.message); }
              }}>Save</button>
            </div>
            <p style={{ fontSize: 9, color: 'var(--color-text-dim)', marginTop: 4 }}>Get an app password from Google Account &gt; Security &gt; 2-Step Verification &gt; App passwords</p>
          </div>
        </div>

        {/* Change password */}
        <div className="panel">
          <h3>Change password</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 6 }}>
            <input id="pw-current" className="field-input" type="password" placeholder="Current password" style={{ fontSize: 12 }} />
            <input id="pw-new" className="field-input" type="password" placeholder="New password (min 8)" style={{ fontSize: 12 }} />
            <input id="pw-confirm" className="field-input" type="password" placeholder="Confirm new password" style={{ fontSize: 12 }} />
            <button className="btn-primary" onClick={async () => {
              const cur = document.getElementById('pw-current').value;
              const nw = document.getElementById('pw-new').value;
              const cf = document.getElementById('pw-confirm').value;
              if (!cur || !nw) { flash('Fill all fields.'); return; }
              if (nw !== cf) { flash('New passwords do not match.'); return; }
              try {
                const r = await authFetch('/api/auth/change-password', {
                  method: 'POST',
                  body: JSON.stringify({ current_password: cur, new_password: nw }),
                });
                if (!r.ok) throw new Error(await r.text());
                document.getElementById('pw-current').value = '';
                document.getElementById('pw-new').value = '';
                document.getElementById('pw-confirm').value = '';
                flash('Password updated.');
              } catch (e) { flash(`Failed: ${e.message}`); }
            }}>Change</button>
          </div>
        </div>

        {/* Maintenance */}
        <div className="panel">
          <h3>Maintenance</h3>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <button className="btn-ghost" onClick={() => {
              localStorage.removeItem('nexus_onboarding_done');
              flash('Onboarding will appear on next reload.');
            }}>
              Replay onboarding
            </button>
            <button className="btn-ghost" onClick={() => { logout(); }}>
              Sign out
            </button>
            {devMode && (
              <>
                <button className="btn-ghost" onClick={async () => { await resetLLM(); flash('LLM connection reset.'); }}>
                  <RefreshCw size={14} /> Reset LLM
                </button>
                <button className="btn-ghost" onClick={async () => { await clearCache(); flash('SQL cache cleared.'); }}>
                  <Trash2 size={14} /> Clear Cache
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Notification preferences ────────────────────────────────────────────────
const EVENT_LABELS = {
  agent_completed:    { label: 'Agent completed a run',       description: 'When a scheduled agent finishes its work' },
  approval_waiting:   { label: 'Approval waiting',            description: 'A drafted action needs your review' },
  anomaly_detected:   { label: 'Anomaly detected',            description: 'A KPI moved outside its expected range' },
  invoice_overdue:    { label: 'Invoice overdue',             description: 'An invoice passed its due date' },
  meeting_soon:       { label: 'Meeting in 30 minutes',       description: 'Heads-up when a meeting is approaching' },
  document_processed: { label: 'Document processed',          description: 'A document finished ingestion into the knowledge base' },
  workflow_completed: { label: 'Workflow completed',          description: 'A workflow finished its run' },
  email_sent:         { label: 'Email sent',                  description: 'Quieter by default — noisy for heavy email users' },
};

function NotificationPrefsPanel() {
  const [prefs, setPrefs] = useState(null);
  const [busy, setBusy] = useState(null);

  useEffect(() => {
    getNotificationPrefs().then(setPrefs).catch(() => {});
  }, []);

  if (!prefs) return null;

  const toggle = async (key, next) => {
    setBusy(key);
    try {
      const fresh = await setNotificationPrefs({ [key]: next });
      setPrefs(fresh);
    } catch {} finally { setBusy(null); }
  };

  return (
    <div className="panel" style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        <Bell size={16} color="var(--color-accent)" />
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>Notifications</div>
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
            Pick which events ring the bell. Muted events still happen — they just stay out of your way.
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {Object.entries(EVENT_LABELS).map(([key, meta]) => {
          const on = prefs[key];
          return (
            <div key={key} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '8px 10px', borderRadius: 'var(--r-sm)',
              background: 'var(--color-surface-1)',
            }}>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, color: 'var(--color-text)', fontWeight: 500 }}>{meta.label}</div>
                <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{meta.description}</div>
              </div>
              <button
                onClick={() => toggle(key, !on)}
                disabled={busy === key}
                aria-pressed={on}
                style={{
                  position: 'relative', width: 36, height: 20, borderRadius: 10,
                  background: on ? 'var(--color-accent)' : 'var(--color-surface-3)',
                  border: 'none', cursor: 'pointer', flexShrink: 0,
                }}
              >
                <div style={{
                  position: 'absolute', top: 2, left: on ? 18 : 2,
                  width: 16, height: 16, borderRadius: '50%', background: 'white',
                  transition: 'left 0.15s',
                }} />
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Workspace export ────────────────────────────────────────────────────────
function ExportPanel({ flash }) {
  const [busy, setBusy] = useState(false);
  const run = async () => {
    setBusy(true);
    try {
      await downloadFullExport();
      flash?.('Export downloaded.');
    } catch (e) {
      flash?.(`Export failed: ${e.message || e}`);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="panel" style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
      <Download size={16} color="var(--color-accent)" />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
          Export my data
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
          Downloads a ZIP of every record owned by this business — contacts, tasks, invoices, documents, briefings, agent runs, and more. Your backup copy, portable anywhere.
        </div>
      </div>
      <button onClick={run} disabled={busy} className="btn-ghost" style={{ fontSize: 12 }}>
        {busy ? 'Building…' : 'Download ZIP'}
      </button>
    </div>
  );
}


// ── Disaster-recovery backup (admin-only) ────────────────────────────────────
// Different from ExportPanel above:
//   ExportPanel  → CSV per table, human-readable, portable, no vector store.
//   BackupPanel  → SQLite snapshot + ChromaDB folder + manifest. Restorable
//                  on a new machine. Bigger; admin-only.
function BackupPanel({ flash }) {
  const [info, setInfo] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getBackupInfo().then(setInfo).catch(() => setInfo(null));
  }, []);

  const fmtBytes = (n) => {
    if (!n) return '—';
    const u = ['B', 'KB', 'MB', 'GB'];
    let i = 0; let v = n;
    while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
    return `${v.toFixed(v < 10 && i > 0 ? 1 : 0)} ${u[i]}`;
  };

  const run = async () => {
    setBusy(true);
    try {
      await downloadFullBackup();
      flash?.('Backup downloaded.');
    } catch (e) {
      flash?.(`Backup failed: ${e.message || e}`);
    } finally {
      setBusy(false);
    }
  };

  const total = info ? (info.db_bytes + info.chroma_bytes) : 0;
  const estZip = info ? info.estimated_zip_bytes : 0;
  const isLarge = total > 500 * 1024 * 1024;  // >500 MB

  return (
    <div className="panel" style={{
      marginBottom: 12, padding: 14,
      borderColor: 'color-mix(in srgb, var(--color-accent) 22%, var(--color-border))',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 'var(--r-md)',
          background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          <ShieldCheck size={18} />
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
              Disaster-recovery backup
            </span>
            <span className="pill-base pill-warn" style={{ fontSize: 9 }}>
              admin-only
            </span>
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', lineHeight: 1.55, marginBottom: 8 }}>
            A full snapshot you can restore on a new machine: SQLite database,
            vector store (RAG embeddings), and a manifest.
          </div>

          {info && (
            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 8,
              padding: '8px 10px',
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--r-sm)',
              fontSize: 11, color: 'var(--color-text-muted)',
              fontFeatureSettings: '"tnum"',
              marginBottom: 8,
            }}>
              <div>
                <div style={{ fontSize: 10, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Database</div>
                <div style={{ color: 'var(--color-text)' }}>{fmtBytes(info.db_bytes)}</div>
              </div>
              <div>
                <div style={{ fontSize: 10, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Vector store</div>
                <div style={{ color: 'var(--color-text)' }}>
                  {fmtBytes(info.chroma_bytes)} <span style={{ color: 'var(--color-text-dim)' }}>({info.chroma_files} files)</span>
                </div>
              </div>
              <div>
                <div style={{ fontSize: 10, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Estimated zip</div>
                <div style={{ color: 'var(--color-text)' }}>~{fmtBytes(estZip)}</div>
              </div>
            </div>
          )}

          {isLarge && (
            <div style={{
              padding: '6px 10px', marginBottom: 8,
              background: 'color-mix(in srgb, var(--color-warn) 12%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-warn) 28%, transparent)',
              borderRadius: 'var(--r-sm)',
              fontSize: 11, color: 'var(--color-warn)',
              display: 'flex', alignItems: 'center', gap: 6,
            }}>
              <AlertTriangle size={11} />
              Large workspace — the backup may take 30+ seconds to build.
            </div>
          )}

          <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', lineHeight: 1.55 }}>
            Restore is currently manual: stop the server, replace
            <code style={{ margin: '0 4px' }}>data/nexusagent.db</code>
            and the <code>chroma_db/</code> folder with the contents of the zip,
            then restart. A guided one-click restore is on the roadmap.
          </div>
        </div>

        <button
          onClick={run}
          disabled={busy}
          className="btn-primary"
          style={{ fontSize: 12, alignSelf: 'flex-start' }}
        >
          {busy
            ? <><Loader2 size={12} className="animate-spin" /> Building…</>
            : <><Database size={12} /> Download backup</>}
        </button>
      </div>
    </div>
  );
}


// ── Onboarding reopener ─────────────────────────────────────────────────────
function OnboardingReopenPanel() {
  const [done, setDone] = useState(false);
  const reopen = async () => {
    try {
      await reopenOnboarding();
      setDone(true);
      setTimeout(() => window.location.assign('/'), 400);
    } catch {}
  };
  return (
    <div className="panel" style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 12 }}>
      <Sparkles size={16} color="var(--color-accent)" />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
          Replay setup guide
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
          Brings back the onboarding checklist on the dashboard — useful after dismissing it too early.
        </div>
      </div>
      <button onClick={reopen} className="btn-ghost" style={{ fontSize: 12 }}>
        {done ? 'Opening…' : 'Reopen'}
      </button>
    </div>
  );
}


// ── Restore from a previously-downloaded backup ─────────────────────────────
// Two-step flow with strong guardrails:
//   1. User picks a zip → frontend hits restore with dry_run=true → shows
//      manifest preview + DB user-count from the backup. Nothing changes.
//   2. User clicks "Replace live data" (with explicit confirm dialog) →
//      backend writes a before-restore safety snapshot, then swaps.
//   3. Server restart instruction surfaces clearly post-swap.
//
// Bad zips, manifest mismatches, schema mismatches, future-format
// backups — all rejected at step 1 before anything is at risk.
function RestorePanel({ flash }) {
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState(null);  // dry-run result
  const [error, setError] = useState('');
  const [done, setDone] = useState(null);        // post-swap result

  const reset = () => {
    setFile(null);
    setPreview(null);
    setError('');
    setDone(null);
  };

  const handleValidate = async () => {
    if (!file) return;
    setBusy(true); setError(''); setPreview(null); setDone(null);
    try {
      const r = await restoreBackup(file, { dryRun: true });
      setPreview(r);
    } catch (e) {
      setError(e.message || 'Validation failed.');
    }
    setBusy(false);
  };

  const handleSwap = async () => {
    if (!file || !preview) return;
    if (!confirm(
      'Replace live data with this backup?\n\n' +
      'A safety snapshot of the current DB will be saved first. The server ' +
      'will need a restart afterwards. Continue?'
    )) return;
    setBusy(true); setError('');
    try {
      const r = await restoreBackup(file, { dryRun: false });
      setDone(r);
      flash?.('Restore complete — restart the server to finish.');
    } catch (e) {
      setError(e.message || 'Restore failed.');
    }
    setBusy(false);
  };

  const fmtBytes = (n) => {
    if (!n) return '—';
    const u = ['B', 'KB', 'MB', 'GB'];
    let i = 0; let v = n;
    while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
    return `${v.toFixed(v < 10 && i > 0 ? 1 : 0)} ${u[i]}`;
  };

  return (
    <div className="panel" style={{
      marginBottom: 12, padding: 14,
      borderColor: 'color-mix(in srgb, var(--color-warn) 22%, var(--color-border))',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 'var(--r-md)',
          background: 'color-mix(in srgb, var(--color-warn) 14%, transparent)',
          color: 'var(--color-warn)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          <AlertTriangle size={18} />
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
              Restore from backup
            </span>
            <span className="pill-base pill-warn" style={{ fontSize: 9 }}>destructive</span>
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', lineHeight: 1.55, marginBottom: 10 }}>
            Replace live data with a previously-downloaded NexusAgent backup. We always validate the zip first
            (no changes), then save a <code>before-restore</code> snapshot of your current DB before swapping
            so you can revert with a manual file copy.
          </div>

          {!done && (
            <>
              <input
                type="file"
                accept=".zip,application/zip"
                onChange={(e) => { setFile(e.target.files?.[0] || null); setPreview(null); setError(''); }}
                style={{
                  fontSize: 12, marginBottom: 10,
                  padding: 6, border: '1px solid var(--color-border)',
                  borderRadius: 'var(--r-sm)', background: 'var(--color-surface-1)',
                  color: 'var(--color-text)', width: '100%',
                }}
              />

              {error && (
                <div style={{
                  padding: '8px 10px', marginBottom: 10,
                  background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
                  border: '1px solid color-mix(in srgb, var(--color-err) 28%, transparent)',
                  borderRadius: 'var(--r-sm)',
                  fontSize: 12, color: 'var(--color-err)',
                }}>
                  {error}
                </div>
              )}

              {preview && (
                <div style={{
                  padding: 10, marginBottom: 10,
                  background: 'var(--color-surface-1)',
                  border: '1px solid color-mix(in srgb, var(--color-accent) 22%, var(--color-border))',
                  borderRadius: 'var(--r-sm)',
                  fontSize: 11.5,
                }}>
                  <div style={{ fontWeight: 600, color: 'var(--color-accent)', marginBottom: 6 }}>
                    <Check size={11} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                    Validation passed — preview before you swap
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 8 }}>
                    <Stat label="Format version" value={`v${preview.manifest?.version ?? '?'}`} />
                    <Stat label="DB" value={fmtBytes(preview.manifest?.db?.bytes)} />
                    <Stat label="Vector store" value={preview.has_chroma ? `${preview.chroma_file_count} files · ${fmtBytes(preview.manifest?.chroma?.bytes)}` : 'not included'} />
                    <Stat label="Users in backup" value={preview.user_count_in_backup} />
                    <Stat label="Created" value={preview.manifest?.created_at ? new Date(preview.manifest.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '?'} />
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  className="btn-ghost"
                  onClick={handleValidate}
                  disabled={!file || busy}
                  style={{ fontSize: 12 }}
                >
                  {busy && !preview ? 'Validating…' : preview ? 'Re-validate' : 'Validate backup'}
                </button>
                {preview && (
                  <button
                    className="btn-primary"
                    onClick={handleSwap}
                    disabled={busy}
                    style={{
                      fontSize: 12,
                      background: 'var(--color-warn)',
                      borderColor: 'var(--color-warn)',
                    }}
                  >
                    {busy ? 'Restoring…' : (
                      <><AlertTriangle size={12} /> Replace live data</>
                    )}
                  </button>
                )}
              </div>
            </>
          )}

          {done && (
            <div style={{
              padding: 12,
              background: 'color-mix(in srgb, var(--color-ok) 8%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-ok) 28%, transparent)',
              borderRadius: 'var(--r-sm)',
            }}>
              <div style={{ fontWeight: 600, color: 'var(--color-ok)', marginBottom: 6 }}>
                <Check size={11} style={{ verticalAlign: 'middle', marginRight: 4 }} />
                Restore complete · {done.user_count_restored} users
              </div>
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.55, marginBottom: 8 }}>
                {done.message}
              </div>
              <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', wordBreak: 'break-all' }}>
                <div><strong>Safety snapshot (DB):</strong> {done.safety_snapshot_db}</div>
                {done.safety_snapshot_chroma && (
                  <div><strong>Safety snapshot (chroma):</strong> {done.safety_snapshot_chroma}</div>
                )}
              </div>
              <button className="btn-ghost btn-sm" style={{ marginTop: 10 }} onClick={reset}>
                Done
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


// Tiny stat row used inside the restore preview panel.
function Stat({ label, value }) {
  return (
    <div>
      <div style={{ fontSize: 10, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
        {label}
      </div>
      <div style={{ color: 'var(--color-text)', fontFeatureSettings: '"tnum"' }}>{value}</div>
    </div>
  );
}


// ── SMTP — workspace outbound email ─────────────────────────────────────────
// Plug in the workspace's own SMTP credentials so AI-drafted outreach can
// actually send (rather than dumping the user into their mail client via
// mailto:). Per-workspace by design: each tenant sends from their own
// domain, not a shared "from" address. Password is encrypted at rest.
function SmtpPanel({ flash }) {
  const [loading, setLoading] = useState(true);
  const [configured, setConfigured] = useState(false);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({
    host: '', port: 587, username: '', password: '',
    from_email: '', from_name: '', use_tls: true,
  });
  const [updatedAt, setUpdatedAt] = useState(null);
  const [busy, setBusy] = useState(false);
  const [testResult, setTestResult] = useState(null);  // { ok, error }

  const refresh = async () => {
    setLoading(true);
    setTestResult(null);
    try {
      const r = await readSmtp();
      setConfigured(!!r.configured);
      if (r.configured) {
        setForm((f) => ({
          ...f,
          host: r.host || '', port: r.port || 587,
          username: r.username || '', password: '',
          from_email: r.from_email || '', from_name: r.from_name || '',
          use_tls: r.use_tls !== false,
        }));
        setUpdatedAt(r.updated_at || null);
      }
    } catch {
      // Don't error-out the page if endpoint is unreachable — just show "not configured".
      setConfigured(false);
    }
    setLoading(false);
  };

  useEffect(() => { refresh(); }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const handleSave = async () => {
    if (!form.host || !form.username || !form.from_email) {
      flash('Host, username, and From email are required.');
      return;
    }
    setBusy(true);
    setTestResult(null);
    try {
      await saveSmtp(form);
      flash('SMTP saved.');
      setEditing(false);
      setForm((f) => ({ ...f, password: '' }));  // never keep plaintext in memory
      refresh();
    } catch (e) {
      flash(`Save failed: ${e.message}`);
    }
    setBusy(false);
  };

  const handleTest = async () => {
    if (!editing && !configured) return;
    setBusy(true);
    setTestResult(null);
    try {
      // If editing, test with the typed-in values; otherwise test stored.
      const r = await testSmtp(editing ? form : null);
      setTestResult(r);
    } catch (e) {
      setTestResult({ ok: false, error: e.message });
    }
    setBusy(false);
  };

  const handleDelete = async () => {
    if (!confirm('Disconnect SMTP? AI-drafted emails will fall back to your mail client (mailto).')) return;
    setBusy(true);
    try {
      await deleteSmtp();
      flash('SMTP disconnected.');
      setForm({ host: '', port: 587, username: '', password: '',
                from_email: '', from_name: '', use_tls: true });
      setConfigured(false);
      setEditing(false);
    } catch (e) {
      flash(`Disconnect failed: ${e.message}`);
    }
    setBusy(false);
  };

  if (loading) return null;

  return (
    <div className="panel" style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
        <Server size={15} color={configured ? 'var(--color-ok)' : 'var(--color-text-dim)'} />
        <h3 style={{ margin: 0, fontSize: 13, fontWeight: 600 }}>Email (SMTP)</h3>
        {configured && (
          <span style={{
            fontSize: 10, padding: '2px 7px', borderRadius: 'var(--r-pill)',
            background: 'color-mix(in srgb, var(--color-ok) 14%, transparent)',
            color: 'var(--color-ok)', fontWeight: 600, letterSpacing: 0.4, textTransform: 'uppercase',
          }}>
            Connected
          </span>
        )}
      </div>
      <p style={{ fontSize: 11.5, color: 'var(--color-text-muted)', margin: '0 0 10px', lineHeight: 1.55 }}>
        Connect your workspace's SMTP server so AI-drafted emails can actually send. Without this, drafts open in your mail client (mailto:). Password is encrypted at rest.
      </p>

      {!editing && !configured && (
        <button className="btn-primary btn-sm" onClick={() => setEditing(true)}>
          <Server size={11} /> Connect SMTP
        </button>
      )}

      {!editing && configured && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            <strong style={{ color: 'var(--color-text)' }}>{form.from_name ? `${form.from_name} <${form.from_email}>` : form.from_email}</strong>
            <br />
            {form.host}:{form.port} · {form.username} {form.use_tls ? '· TLS' : ''}
          </div>
          {updatedAt && (
            <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)' }}>
              Updated {new Date(updatedAt).toLocaleString()}
            </div>
          )}
          <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
            <button className="btn-ghost btn-sm" onClick={() => setEditing(true)}>Edit</button>
            <button className="btn-ghost btn-sm" onClick={handleTest} disabled={busy}>
              {busy ? <Loader2 size={11} className="animate-spin" /> : <Check size={11} />} Test connection
            </button>
            <button className="btn-ghost btn-sm" style={{ color: 'var(--color-err)' }} onClick={handleDelete} disabled={busy}>
              <Trash2 size={11} /> Disconnect
            </button>
          </div>
        </div>
      )}

      {editing && (
        <div style={{ display: 'grid', gap: 8 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 8 }}>
            <div>
              <label style={{ fontSize: 10.5, color: 'var(--color-text-muted)', fontWeight: 600, letterSpacing: 0.3 }}>SMTP host</label>
              <input className="field-input" value={form.host} onChange={(e) => set('host', e.target.value)} placeholder="smtp.gmail.com" />
            </div>
            <div>
              <label style={{ fontSize: 10.5, color: 'var(--color-text-muted)', fontWeight: 600, letterSpacing: 0.3 }}>Port</label>
              <input className="field-input" type="number" value={form.port} onChange={(e) => set('port', parseInt(e.target.value) || 587)} />
            </div>
          </div>
          <div>
            <label style={{ fontSize: 10.5, color: 'var(--color-text-muted)', fontWeight: 600, letterSpacing: 0.3 }}>Username</label>
            <input className="field-input" value={form.username} onChange={(e) => set('username', e.target.value)} placeholder="outbound@yourdomain.com" />
          </div>
          <div>
            <label style={{ fontSize: 10.5, color: 'var(--color-text-muted)', fontWeight: 600, letterSpacing: 0.3 }}>
              Password {configured && <em style={{ fontWeight: 400, color: 'var(--color-text-dim)' }}>(leave blank to keep existing)</em>}
            </label>
            <input className="field-input" type="password" value={form.password} onChange={(e) => set('password', e.target.value)} placeholder="App password or service token" autoComplete="new-password" />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            <div>
              <label style={{ fontSize: 10.5, color: 'var(--color-text-muted)', fontWeight: 600, letterSpacing: 0.3 }}>From email</label>
              <input className="field-input" type="email" value={form.from_email} onChange={(e) => set('from_email', e.target.value)} placeholder="hello@yourdomain.com" />
            </div>
            <div>
              <label style={{ fontSize: 10.5, color: 'var(--color-text-muted)', fontWeight: 600, letterSpacing: 0.3 }}>From name (optional)</label>
              <input className="field-input" value={form.from_name} onChange={(e) => set('from_name', e.target.value)} placeholder="Acme Sales" />
            </div>
          </div>
          <label style={{ fontSize: 11.5, color: 'var(--color-text)', display: 'inline-flex', gap: 6, alignItems: 'center' }}>
            <input type="checkbox" checked={form.use_tls} onChange={(e) => set('use_tls', e.target.checked)} />
            Use STARTTLS (recommended for ports 587/25)
          </label>

          <div style={{ display: 'flex', gap: 6, marginTop: 4, flexWrap: 'wrap' }}>
            <button className="btn-primary btn-sm" onClick={handleSave} disabled={busy}>
              {busy ? <Loader2 size={11} className="animate-spin" /> : <Check size={11} />} Save
            </button>
            <button className="btn-ghost btn-sm" onClick={handleTest} disabled={busy}>
              {busy ? <Loader2 size={11} className="animate-spin" /> : null} Test connection
            </button>
            <button className="btn-ghost btn-sm" onClick={() => { setEditing(false); refresh(); }}>Cancel</button>
          </div>
        </div>
      )}

      {testResult && (
        <div style={{
          marginTop: 8, padding: '8px 10px',
          background: testResult.ok
            ? 'color-mix(in srgb, var(--color-ok) 8%, transparent)'
            : 'color-mix(in srgb, var(--color-err) 8%, transparent)',
          border: `1px solid color-mix(in srgb, ${testResult.ok ? 'var(--color-ok)' : 'var(--color-err)'} 28%, transparent)`,
          borderRadius: 'var(--r-sm)',
          fontSize: 12, color: testResult.ok ? 'var(--color-ok)' : 'var(--color-err)',
          display: 'flex', alignItems: 'flex-start', gap: 6,
        }}>
          {testResult.ok ? <Check size={13} /> : <AlertTriangle size={13} style={{ marginTop: 1, flexShrink: 0 }} />}
          <span>{testResult.ok ? 'Connection successful — credentials are valid.' : testResult.error}</span>
        </div>
      )}
    </div>
  );
}


// ── Ideal Customer Profile (ICP) — for AI lead scoring ──────────────────────
// One short paragraph describing who buys from you. The scorer uses this
// against every inbound lead — high-fit ones get flagged in the CRM Leads
// tab so the user spends time on the right people. Without an ICP set,
// scoring stays inert and tells the user how to fix that.
function IcpPanel({ flash }) {
  const [text, setText] = useState('');
  const [original, setOriginal] = useState('');
  const [updatedAt, setUpdatedAt] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    readIcp().then((r) => {
      setText(r.icp_description || '');
      setOriginal(r.icp_description || '');
      setUpdatedAt(r.icp_updated_at);
    }).catch(() => {});
  }, []);

  const dirty = text !== original;

  const handleSave = async () => {
    setBusy(true);
    try {
      await writeIcp(text);
      setOriginal(text);
      setUpdatedAt(new Date().toISOString());
      flash?.('ICP saved. New leads will be scored against this.');
    } catch (e) {
      flash?.(`Save failed: ${e.message || e}`);
    }
    setBusy(false);
  };

  return (
    <div className="panel" style={{
      marginBottom: 12, padding: 14,
      borderColor: 'color-mix(in srgb, var(--color-accent) 22%, var(--color-border))',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 'var(--r-md)',
          background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
        }}>
          <Sparkles size={18} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)', marginBottom: 4 }}>
            Ideal Customer Profile
          </div>
          <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', lineHeight: 1.55, marginBottom: 10 }}>
            Two or three sentences describing who buys from you. New inbound leads are scored
            against this on the way in — high-fit ones get flagged in the CRM Leads tab so you
            spend time on the right people.
          </div>

          <textarea
            className="field-input"
            rows={4}
            value={text}
            onChange={(e) => setText(e.target.value)}
            maxLength={4000}
            placeholder="e.g. We sell to B2B SaaS companies in India with 50–500 employees that have raised at least Series A. Buyers are usually Heads of Sales, RevOps leads, or founders. Look for product-led companies with active hiring in revenue roles."
            style={{ fontFamily: 'inherit' }}
          />

          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 8, flexWrap: 'wrap' }}>
            <button
              className="btn-primary btn-sm"
              onClick={handleSave}
              disabled={busy || !dirty}
            >
              {busy ? 'Saving…' : dirty ? 'Save ICP' : 'Saved'}
            </button>
            {updatedAt && (
              <span style={{ fontSize: 10.5, color: 'var(--color-text-dim)' }}>
                last updated {new Date(updatedAt).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
            {!text.trim() && (
              <span style={{ fontSize: 10.5, color: 'var(--color-warn)' }}>
                Without an ICP, lead scoring is inert.
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

