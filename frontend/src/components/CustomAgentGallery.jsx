/**
 * Template gallery — shows the starter agents the user can clone.
 * One click creates a configured custom agent ready to enable.
 */
import { useState, useEffect } from 'react';
import { Plus, Loader2, X } from 'lucide-react';
import { listAgentTemplates, createFromTemplate } from '../services/customAgents';


export default function CustomAgentGallery({ onClose, onCreated }) {
  const [templates, setTemplates] = useState([]);
  const [busy, setBusy] = useState(null);
  const [err, setErr] = useState('');

  useEffect(() => {
    listAgentTemplates().then(setTemplates).catch((e) => setErr(String(e.message || e)));
  }, []);

  const clone = async (key) => {
    setBusy(key); setErr('');
    try {
      const agent = await createFromTemplate(key);
      onCreated?.(agent);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setBusy(null);
    }
  };

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
        zIndex: 390, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)',
          borderRadius: 'var(--r-lg)', padding: 22,
          width: 'min(720px, 96vw)', maxHeight: '90vh', overflow: 'auto',
          boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 16, color: 'var(--color-text)' }}>Agent templates</h3>
            <p style={{ margin: '4px 0 0', fontSize: 11, color: 'var(--color-text-dim)' }}>
              Clone one to get a ready-to-run agent — edit anything before enabling.
            </p>
          </div>
          <button onClick={onClose} className="btn-ghost"><X size={14} /></button>
        </div>

        {err && (
          <div style={{
            padding: 10, marginBottom: 12, borderRadius: 'var(--r-sm)',
            background: 'color-mix(in srgb, var(--color-err) 10%, transparent)',
            color: 'var(--color-err)', fontSize: 12,
          }}>{err}</div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 10 }}>
          {templates.map(t => (
            <div key={t.key} className="panel" style={{
              padding: 14, display: 'flex', flexDirection: 'column', gap: 8,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 20 }}>{t.emoji}</span>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>{t.name}</div>
              </div>
              <p style={{ fontSize: 11, color: 'var(--color-text-muted)', margin: 0, lineHeight: 1.5 }}>
                {t.description}
              </p>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                {t.tool_whitelist.slice(0, 4).map(name => (
                  <span key={name} style={{
                    fontSize: 9, padding: '1px 6px', borderRadius: 'var(--r-pill)',
                    background: 'var(--color-surface-2)', color: 'var(--color-text-muted)',
                    fontFamily: 'var(--font-mono)',
                  }}>{name}</span>
                ))}
              </div>
              <button
                onClick={() => clone(t.key)}
                disabled={busy === t.key}
                className="btn-primary"
                style={{ fontSize: 11, marginTop: 'auto' }}
              >
                {busy === t.key
                  ? <><Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} /> Cloning…</>
                  : <><Plus size={11} /> Clone this</>}
              </button>
            </div>
          ))}
          {templates.length === 0 && !err && (
            <div style={{ fontSize: 12, color: 'var(--color-text-dim)', padding: 20, textAlign: 'center' }}>
              Loading templates…
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
