import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit3, Check, X, RotateCcw, Clock, ExternalLink, Loader2, Bot } from 'lucide-react';
import { listPersonas, renamePersona } from '../services/agents';

function formatWhen(iso) {
  if (!iso) return null;
  try {
    const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z');
    const mins = Math.floor((Date.now() - d.getTime()) / 60000);
    if (mins < 1)    return 'just now';
    if (mins < 60)   return `${mins}m ago`;
    if (mins < 1440) return `${Math.floor(mins / 60)}h ago`;
    return `${Math.floor(mins / 1440)}d ago`;
  } catch { return iso.slice(0, 16); }
}

function formatNextRun(iso) {
  if (!iso) return null;
  try {
    const d = new Date(iso);
    return d.toLocaleString([], { weekday: 'short', hour: '2-digit', minute: '2-digit' });
  } catch { return iso.slice(0, 16); }
}

function PersonaCard({ persona, onRenamed, onOpenSurface }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(persona.name);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => { setValue(persona.name); }, [persona.name]);

  const save = async (newVal) => {
    if (busy) return;
    setBusy(true); setErr('');
    try {
      const updated = await renamePersona(persona.agent_key, newVal);
      onRenamed(updated);
      setEditing(false);
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  };

  const reset = () => save('');  // empty name → backend clears override

  return (
    <div className="panel" style={{
      padding: 18,
      display: 'flex', flexDirection: 'column', gap: 12,
      transition: 'border-color var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out)',
    }}>
      {/* Header — avatar + name + role */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 'var(--r-md)',
          background: 'linear-gradient(135deg, color-mix(in srgb, var(--color-accent) 22%, transparent), color-mix(in srgb, var(--color-info) 18%, transparent))',
          border: '1px solid color-mix(in srgb, var(--color-accent) 28%, transparent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 22, flexShrink: 0,
        }}>
          {persona.emoji || <Bot size={20} color="var(--color-accent)" />}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          {editing ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                autoFocus
                className="field-input"
                style={{ fontSize: 16, fontWeight: 600, padding: '5px 10px', maxWidth: 200 }}
                value={value}
                maxLength={40}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') save(value);
                  if (e.key === 'Escape') { setEditing(false); setValue(persona.name); }
                }}
                disabled={busy}
              />
              <button className="btn-ghost" onClick={() => save(value)} disabled={busy} title="Save">
                {busy ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Check size={13} color="var(--color-ok)" />}
              </button>
              <button className="btn-ghost" onClick={() => { setEditing(false); setValue(persona.name); }} title="Cancel">
                <X size={13} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 17, fontWeight: 600, color: 'var(--color-text)', letterSpacing: '-0.01em' }}>
                {persona.name}
              </span>
              <span style={{
                fontSize: 10, padding: '2px 8px', borderRadius: 'var(--r-pill)',
                background: 'var(--color-accent-soft)',
                color: 'var(--color-accent)',
                fontWeight: 600, letterSpacing: 0.3,
                border: '1px solid color-mix(in srgb, var(--color-accent) 25%, transparent)',
              }}>
                {persona.role_tag}
              </span>
              <button
                onClick={() => setEditing(true)}
                title="Rename"
                style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 2, display: 'flex' }}
              >
                <Edit3 size={12} />
              </button>
              {persona.is_custom && (
                <button
                  onClick={reset}
                  title={`Reset to default name "${persona.default_name}"`}
                  style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 2, display: 'flex' }}
                >
                  <RotateCcw size={12} />
                </button>
              )}
            </div>
          )}
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 2 }}>
            {persona.is_custom && <>You renamed — default is <em>{persona.default_name}</em> · </>}
            <code style={{ fontSize: 10 }}>{persona.agent_key}</code>
          </div>
          {err && <div style={{ fontSize: 11, color: 'var(--color-err)', marginTop: 4 }}>{err}</div>}
        </div>
      </div>

      {/* Description */}
      <p style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.55, margin: 0 }}>
        {persona.description}
      </p>

      {/* Activity strip */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        paddingTop: 10, borderTop: '1px solid var(--color-border)',
        fontSize: 11, color: 'var(--color-text-dim)', flexWrap: 'wrap',
      }}>
        {persona.last_activity?.last_ran && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <Clock size={11} /> Last ran {formatWhen(persona.last_activity.last_ran)}
          </span>
        )}
        {persona.last_activity?.last_24h_count > 0 && (
          <span style={{ color: 'var(--color-accent)' }}>
            {persona.last_activity.last_24h_count} in the last 24h
          </span>
        )}
        {persona.next_run && (
          <span>Next run · {formatNextRun(persona.next_run)}</span>
        )}
        {!persona.last_activity?.last_ran && !persona.next_run && (
          <span>No activity yet</span>
        )}
        {persona.last_activity?.surface && (
          <button
            onClick={() => onOpenSurface(persona.last_activity.surface)}
            className="btn-ghost"
            style={{ marginLeft: 'auto', fontSize: 11 }}
          >
            Open <ExternalLink size={11} />
          </button>
        )}
      </div>
    </div>
  );
}

export default function Agents() {
  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const navigate = useNavigate();

  const load = useCallback(async () => {
    setLoading(true); setErr('');
    try { setPersonas(await listPersonas()); }
    catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const onRenamed = (updated) => {
    setPersonas(prev => prev.map(p => p.agent_key === updated.agent_key ? { ...p, ...updated } : p));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <h1>Agents</h1>
        <p>Your autonomous team — each agent has a name, a role, and a shift. Rename them anything you like.</p>
      </div>

      <div className="page-body">
        {loading && (
          <div style={{ color: 'var(--color-text-dim)', fontSize: 12, padding: 20 }}>Loading…</div>
        )}
        {err && (
          <div className="panel" style={{ color: 'var(--color-err)', fontSize: 12 }}>{err}</div>
        )}

        {!loading && !err && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 12 }}>
            {personas.map(p => (
              <PersonaCard
                key={p.agent_key}
                persona={p}
                onRenamed={onRenamed}
                onOpenSurface={(path) => navigate(path)}
              />
            ))}
          </div>
        )}

        <div style={{
          marginTop: 18, padding: 14,
          borderRadius: 'var(--r-lg)',
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
          fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.6,
        }}>
          <strong style={{ color: 'var(--color-text)' }}>How this works.</strong>{' '}
          Each agent runs on its own schedule in the background. Anywhere in NexusAgent where
          you see "<span style={{ color: 'var(--color-accent)' }}>Atlas · Chief of staff</span>" or
          similar, it means that specific agent took the action. Rename any of them to match your
          team's vocabulary — they'll keep their role and behaviour, just wear the new name.
        </div>
      </div>
    </div>
  );
}
