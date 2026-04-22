import { useState, useEffect } from 'react';
import { RefreshCw, Trash2, Server, Cpu, HardDrive } from 'lucide-react';
import { getSettings, resetLLM, clearCache } from '../services/api';

export default function Settings() {
  const [s, setS] = useState(null);
  const [msg, setMsg] = useState('');

  useEffect(() => { getSettings().then(setS).catch(() => {}); }, []);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 3000); };

  if (!s) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569' }}>Loading...</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header"><h1>Settings</h1><p>Configure NexusAgent and view system information</p></div>
      <div className="page-body">
        {msg && <div className="panel" style={{ color: '#60a5fa', marginBottom: 12 }}>{msg}</div>}

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

        {/* Integrations */}
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
                  await fetch('/api/settings/update', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: 'DISCORD_WEBHOOK_URL', value: url }) });
                  flash('Discord webhook saved.');
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
                  await fetch('/api/settings/update', { method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ key: 'GMAIL_APP_PASSWORD', value: pw }) });
                  flash('Gmail password saved.');
                } catch (e) { flash('Failed: ' + e.message); }
              }}>Save</button>
            </div>
            <p style={{ fontSize: 9, color: '#475569', marginTop: 4 }}>Get an app password from Google Account &gt; Security &gt; 2-Step Verification &gt; App passwords</p>
          </div>
        </div>

        {/* Maintenance */}
        <div className="panel">
          <h3>Maintenance</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="btn-ghost" onClick={async () => { await resetLLM(); flash('LLM connection reset.'); }}>
              <RefreshCw size={14} /> Reset LLM
            </button>
            <button className="btn-ghost" onClick={async () => { await clearCache(); flash('SQL cache cleared.'); }}>
              <Trash2 size={14} /> Clear Cache
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
