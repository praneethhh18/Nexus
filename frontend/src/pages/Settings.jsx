import { useState, useEffect } from 'react';
import { RefreshCw, Trash2, Server, Cpu, HardDrive, Code, Briefcase, Users, AlertTriangle, Calendar as CalendarIcon, Check, X } from 'lucide-react';
import { getSettings, resetLLM, clearCache, listMembers, getBusiness, updateBusiness, deleteBusiness } from '../services/api';
import { getToken, getBusinessId, getCurrentBusiness, logout } from '../services/auth';
import { calendarStatus, calendarStart, calendarDisconnect } from '../services/calendar';

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

  if (!s) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569' }}>Loading...</div>;

  const myRole = bizDetail?.my_role;
  const canEditBiz = myRole === 'owner' || myRole === 'admin';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header"><h1>Settings</h1><p>Manage your business, integrations, and system</p></div>
      <div className="page-body">
        {msg && <div className="panel" style={{ color: '#60a5fa', marginBottom: 12 }}>{msg}</div>}

        {/* Current Business */}
        {current && (
          <div className="panel">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Briefcase size={16} color="#22c55e" /> Current Business</h3>
            <div style={{ fontSize: 10, color: '#64748b', marginBottom: 12 }}>ID: {current.id} &middot; Your role: <strong style={{ color: '#e2e8f0' }}>{myRole || '...'}</strong></div>
            <div style={{ display: 'grid', gap: 10 }}>
              <div>
                <label style={{ fontSize: 10, color: '#64748b', display: 'block', marginBottom: 2 }}>Name</label>
                <input className="field-input" value={bizName} onChange={(e) => setBizName(e.target.value)} disabled={!canEditBiz} maxLength={120} />
              </div>
              <div>
                <label style={{ fontSize: 10, color: '#64748b', display: 'block', marginBottom: 2 }}>Industry</label>
                <input className="field-input" value={bizIndustry} onChange={(e) => setBizIndustry(e.target.value)} disabled={!canEditBiz} maxLength={80} />
              </div>
              <div>
                <label style={{ fontSize: 10, color: '#64748b', display: 'block', marginBottom: 2 }}>Description</label>
                <textarea className="field-input" rows={2} value={bizDescription} onChange={(e) => setBizDescription(e.target.value)} disabled={!canEditBiz} maxLength={500} />
              </div>
              {canEditBiz && (
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn-ghost" onClick={saveBiz}>Save</button>
                  {myRole === 'owner' && (
                    <button className="btn-ghost" style={{ color: '#ef4444', borderColor: '#7f1d1d' }} onClick={removeBiz}>
                      <AlertTriangle size={12} /> Delete business
                    </button>
                  )}
                </div>
              )}
            </div>
            {bizDetail?.members?.length > 0 && (
              <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid #1e293b' }}>
                <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Users size={12} /> Members ({bizDetail.members.length})
                </div>
                {bizDetail.members.map(m => (
                  <div key={m.user_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: 11, color: '#cbd5e1' }}>
                    <span>{m.name || m.email || m.user_id}</span>
                    <span style={{ color: '#64748b' }}>{m.role}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Google Calendar */}
        <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><CalendarIcon size={16} color="#60a5fa" /> Google Calendar</h3>
          {!calStatus ? (
            <p style={{ fontSize: 12, color: '#64748b' }}>Checking...</p>
          ) : !calStatus.configured ? (
            <p style={{ fontSize: 12, color: '#64748b' }}>
              Not available. An admin needs to set <code>GOOGLE_CLIENT_ID</code> and <code>GOOGLE_CLIENT_SECRET</code> in <code>.env</code> first.
            </p>
          ) : calStatus.connected ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Check size={14} color="#22c55e" />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12, color: '#e2e8f0' }}>Connected: <strong>{calStatus.connection?.account_email || '...'}</strong></div>
                <div style={{ fontSize: 10, color: '#64748b' }}>Since {calStatus.connection?.connected_at?.substring(0, 16)}</div>
              </div>
              <button className="btn-ghost" style={{ color: '#f87171' }} onClick={async () => {
                if (!confirm('Disconnect Google Calendar?')) return;
                try { await calendarDisconnect(); setCalStatus(await calendarStatus()); flash('Disconnected.'); }
                catch (e) { flash(`Failed: ${e.message}`); }
              }}>
                <X size={12} /> Disconnect
              </button>
            </div>
          ) : (
            <div>
              <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8 }}>
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

        {/* Developer Mode */}
        <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Code size={16} color="#a78bfa" /> Developer Mode</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12 }}>
            <div>
              <div style={{ fontSize: 12, color: '#e2e8f0', marginBottom: 4 }}>Show advanced tools in navigation</div>
              <div style={{ fontSize: 10, color: '#64748b' }}>Enables the SQL Editor, Database Explorer, and What-If pages. For power users and debugging.</div>
            </div>
            <button
              onClick={toggleDevMode}
              style={{
                position: 'relative', width: 42, height: 22, borderRadius: 11,
                background: devMode ? '#22c55e' : '#1e293b', border: 'none', cursor: 'pointer', flexShrink: 0,
              }}
            >
              <div style={{
                position: 'absolute', top: 2, left: devMode ? 22 : 2,
                width: 18, height: 18, borderRadius: '50%', background: 'white',
                transition: 'left 0.15s',
              }} />
            </button>
          </div>
        </div>

        {/* Models */}
        <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Cpu size={16} color="#60a5fa" /> LLM Configuration</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[['Primary LLM', s.primary_model], ['Fallback LLM', s.fallback_model], ['Embedding', s.embed_model], ['Ollama URL', s.ollama_url]].map(([k, v], i) => (
              <div key={i} className="info-row" style={{ flexDirection: 'column', background: '#0f172a', borderRadius: 8, padding: 10, border: 'none' }}>
                <span className="key" style={{ fontSize: 9, textTransform: 'uppercase', letterSpacing: 1 }}>{k}</span>
                <span className="val" style={{ fontSize: 12 }}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Available Models */}
        {s.available_models?.length > 0 && (
          <div className="panel">
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Server size={16} color="#a78bfa" /> Available Ollama Models</h3>
            {s.available_models.map((m, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 10px', borderRadius: 6, background: '#0f172a', marginBottom: 4 }}>
                <span style={{ fontSize: 12, fontFamily: 'monospace', color: 'white' }}>{m.name}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontSize: 11, color: '#64748b' }}>{m.size_gb} GB</span>
                  {m.active && <span style={{ fontSize: 9, padding: '2px 8px', borderRadius: 10, background: '#16a34a15', color: '#4ade80', border: '1px solid #4ade8025' }}>Active</span>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* System Info */}
        <div className="panel">
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}><HardDrive size={16} color="#22d3ee" /> System Information</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
            {[['Version', `v${s.version}`], ['Python', s.python_version], ['SQL Retries', s.max_sql_retries],
              ['Reflection Retries', s.max_reflection_retries], ['Chunk Size', s.chunk_size], ['Top-K', s.top_k_retrieval],
              ['Email', s.email_enabled ? 'Enabled' : 'Disabled'], ['Discord', s.discord_enabled ? 'Enabled' : 'Disabled']
            ].map(([k, v], i) => (
              <div key={i} className="info-row"><span className="key">{k}</span><span className="val">{String(v)}</span></div>
            ))}
          </div>
        </div>

        {/* Integrations (admin-only on server) */}
        <div className="panel">
          <h3>Integrations</h3>
          <div style={{ marginBottom: 10 }}>
            <label style={{ fontSize: 10, color: '#64748b', display: 'block', marginBottom: 2 }}>Discord Webhook URL</label>
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
            <label style={{ fontSize: 10, color: '#64748b', display: 'block', marginBottom: 2 }}>Slack Webhook URL</label>
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
            <label style={{ fontSize: 10, color: '#64748b', display: 'block', marginBottom: 2 }}>Gmail App Password</label>
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
            <p style={{ fontSize: 9, color: '#475569', marginTop: 4 }}>Get an app password from Google Account &gt; Security &gt; 2-Step Verification &gt; App passwords</p>
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
            <button className="btn-ghost" onClick={async () => { await resetLLM(); flash('LLM connection reset.'); }}>
              <RefreshCw size={14} /> Reset LLM
            </button>
            <button className="btn-ghost" onClick={async () => { await clearCache(); flash('SQL cache cleared.'); }}>
              <Trash2 size={14} /> Clear Cache
            </button>
            <button className="btn-ghost" onClick={() => {
              localStorage.removeItem('nexus_onboarding_done');
              flash('Onboarding will appear on next reload.');
            }}>
              Replay onboarding
            </button>
            <button className="btn-ghost" onClick={() => { logout(); }}>
              Sign out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
