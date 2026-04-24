import { useState, useEffect } from 'react';
import { RefreshCw, Trash2, Server, Cpu, HardDrive, Code, Briefcase, Users, AlertTriangle, Calendar as CalendarIcon, Check, X, MessageCircle, Copy, Bell, Sparkles } from 'lucide-react';
import { getSettings, resetLLM, clearCache, listMembers, getBusiness, updateBusiness, deleteBusiness } from '../services/api';
import { getNotificationPrefs, setNotificationPrefs, reopenOnboarding } from '../services/onboarding';
import { downloadFullExport } from '../services/tags';
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
        <ExportPanel flash={flash} />

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
