/**
 * Build or edit a custom agent.
 *
 * <CustomAgentBuilder initial={...} onClose={} onSaved={} />
 *
 * One-page form covering every field the backend cares about. Tool selection
 * is a scrollable multi-select fed by /api/agent/tools. Schedule uses the
 * shared IntervalPicker. Template clones pre-fill the form but users can edit
 * anything before saving.
 */
import { useState, useEffect } from 'react';
import { X, Save, Loader2, Info, Trash2 } from 'lucide-react';
import {
  createCustomAgent, updateCustomAgent, deleteCustomAgent, listAgentTools,
} from '../services/customAgents';
import IntervalPicker from './IntervalPicker';


const OUTPUT_CHOICES = [
  { key: 'inbox',    label: 'Inbox notification',  desc: 'Appears in the bell drawer so you see it immediately.' },
  { key: 'briefing', label: 'Morning briefing',    desc: 'Adds its output as a section to the next daily briefing.' },
  { key: 'none',     label: 'Silent (log only)',   desc: 'Runs and writes to the audit log but doesn\'t notify you.' },
];


export default function CustomAgentBuilder({ initial = null, onClose, onSaved }) {
  const [form, setForm] = useState({
    name: '',
    emoji: '🤖',
    description: '',
    goal: '',
    tool_whitelist: [],
    interval_minutes: 1440,
    output_target: 'inbox',
    ...(initial || {}),
  });
  const [tools, setTools] = useState([]);
  const [toolFilter, setToolFilter] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const isEdit = !!initial?.id;

  useEffect(() => {
    listAgentTools().then(setTools).catch(() => setTools([]));
  }, []);

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }));

  const toggleTool = (name) => {
    const has = form.tool_whitelist.includes(name);
    set('tool_whitelist', has
      ? form.tool_whitelist.filter(t => t !== name)
      : [...form.tool_whitelist, name]);
  };

  const save = async () => {
    setBusy(true); setErr('');
    try {
      const payload = {
        name: form.name,
        emoji: form.emoji,
        description: form.description,
        goal: form.goal,
        tool_whitelist: form.tool_whitelist,
        interval_minutes: form.interval_minutes,
        output_target: form.output_target,
      };
      const saved = isEdit
        ? await updateCustomAgent(initial.id, payload)
        : await createCustomAgent(payload);
      onSaved?.(saved);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!isEdit) return;
    if (!confirm(`Delete agent "${initial.name}"?`)) return;
    setBusy(true); setErr('');
    try {
      await deleteCustomAgent(initial.id);
      onSaved?.(null);
    } catch (e) { setErr(String(e.message || e)); }
    finally { setBusy(false); }
  };

  const filteredTools = toolFilter
    ? tools.filter(t => (t.name + ' ' + (t.description || '')).toLowerCase().includes(toolFilter.toLowerCase()))
    : tools;

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
        zIndex: 400, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)',
          borderRadius: 'var(--r-lg)', padding: 22,
          width: 'min(680px, 96vw)', maxHeight: '92vh',
          overflow: 'auto', boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: 16, color: 'var(--color-text)' }}>
            {isEdit ? 'Edit custom agent' : 'Build a custom agent'}
          </h3>
          <button onClick={onClose} className="btn-ghost"><X size={14} /></button>
        </div>

        {err && (
          <div style={{
            padding: 10, marginBottom: 12, borderRadius: 'var(--r-sm)',
            background: 'color-mix(in srgb, var(--color-err) 10%, transparent)',
            color: 'var(--color-err)', fontSize: 12,
          }}>{err}</div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '60px 1fr', gap: 10, marginBottom: 10 }}>
          <div>
            <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Emoji</label>
            <input
              className="field-input"
              value={form.emoji}
              onChange={(e) => set('emoji', e.target.value.slice(0, 4))}
              maxLength={4}
              style={{ textAlign: 'center', fontSize: 18 }}
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>
              Name *
            </label>
            <input
              className="field-input"
              value={form.name}
              onChange={(e) => set('name', e.target.value)}
              maxLength={60}
              placeholder="e.g. Weekly Revenue Digest"
            />
          </div>
        </div>

        <div style={{ marginBottom: 10 }}>
          <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>
            One-line description
          </label>
          <input
            className="field-input"
            value={form.description}
            onChange={(e) => set('description', e.target.value)}
            maxLength={200}
            placeholder="What this agent does, in one line"
          />
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>
            Goal (in plain English) *
          </label>
          <textarea
            className="field-input"
            rows={4}
            value={form.goal}
            onChange={(e) => set('goal', e.target.value)}
            maxLength={2000}
            placeholder="Describe what this agent should do when it runs. Be specific about data sources, formats, and output."
          />
          <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 2 }}>
            <Info size={9} style={{ verticalAlign: 'middle' }} />
            {' '}The goal is fed directly to the LLM. Think of it as the agent's job description.
          </div>
        </div>

        <div style={{ marginBottom: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
            <label style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>
              Tools the agent can use ({form.tool_whitelist.length} selected)
            </label>
            <input
              placeholder="Filter tools…"
              value={toolFilter}
              onChange={(e) => setToolFilter(e.target.value)}
              className="field-input"
              style={{ fontSize: 10, padding: '2px 6px', width: 140 }}
            />
          </div>
          <div style={{
            maxHeight: 160, overflowY: 'auto',
            border: '1px solid var(--color-border)', borderRadius: 'var(--r-sm)',
            padding: 4,
          }}>
            {filteredTools.length === 0 && (
              <div style={{ fontSize: 11, color: 'var(--color-text-dim)', padding: 10, textAlign: 'center' }}>
                No tools match "{toolFilter}"
              </div>
            )}
            {filteredTools.map(t => {
              const on = form.tool_whitelist.includes(t.name);
              return (
                <label
                  key={t.name}
                  style={{
                    display: 'flex', alignItems: 'flex-start', gap: 8,
                    padding: '5px 8px', borderRadius: 'var(--r-sm)', cursor: 'pointer',
                    background: on ? 'color-mix(in srgb, var(--color-accent) 8%, transparent)' : 'transparent',
                  }}
                >
                  <input
                    type="checkbox" checked={on}
                    onChange={() => toggleTool(t.name)}
                    style={{ marginTop: 2, accentColor: 'var(--color-accent)' }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 11, color: 'var(--color-text)', fontFamily: 'var(--font-mono)' }}>
                      {t.name}
                    </div>
                    {t.description && (
                      <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>
                        {t.description.slice(0, 160)}
                      </div>
                    )}
                  </div>
                </label>
              );
            })}
          </div>
          {form.tool_whitelist.length === 0 && (
            <div style={{ fontSize: 10, color: 'var(--color-warn)', marginTop: 4 }}>
              Tip: pick at least one tool or the agent has no way to act.
            </div>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 14 }}>
          <div>
            <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>
              How often should it run?
            </label>
            <IntervalPicker
              value={form.interval_minutes}
              onChange={(n) => set('interval_minutes', n)}
              size="md"
            />
          </div>
          <div>
            <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>
              Where does the output go?
            </label>
            <select
              className="field-select"
              value={form.output_target}
              onChange={(e) => set('output_target', e.target.value)}
              style={{ width: '100%', fontSize: 12 }}
            >
              {OUTPUT_CHOICES.map(c => (
                <option key={c.key} value={c.key}>{c.label}</option>
              ))}
            </select>
            <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 3 }}>
              {OUTPUT_CHOICES.find(c => c.key === form.output_target)?.desc}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between', alignItems: 'center' }}>
          {isEdit
            ? (
              <button onClick={remove} className="btn-ghost" style={{ color: 'var(--color-err)', fontSize: 12 }} disabled={busy}>
                <Trash2 size={12} /> Delete agent
              </button>
            )
            : <div />}
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={onClose} className="btn-ghost" disabled={busy}>Cancel</button>
            <button
              onClick={save}
              className="btn-primary"
              disabled={busy || !form.name.trim() || !form.goal.trim()}
            >
              {busy ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Save size={12} />}
              {isEdit ? 'Save changes' : 'Create agent'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
