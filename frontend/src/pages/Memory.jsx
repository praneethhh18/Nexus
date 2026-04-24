import { useState, useEffect, useCallback } from 'react';
import { Brain, Plus, Pin, PinOff, Search, Trash2, Edit3, X, Sparkles } from 'lucide-react';
import { listMemoryApi, addMemoryApi, updateMemoryApi, deleteMemoryApi } from '../services/agent';
import EmptyState from '../components/EmptyState';
import { getToken, getBusinessId } from '../services/auth';

function Modal({ title, onClose, children }) {
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 12,
        padding: 20, width: 480, maxHeight: '92vh', overflow: 'auto',
        boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--color-text)', margin: 0 }}>{title}</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer' }}><X size={16} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

function MemoryForm({ initial, onSubmit, onCancel }) {
  const [f, setF] = useState({
    content: '', kind: 'fact', tags: '', is_pinned: false, ...(initial || {}),
  });
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(f); }}>
      <div style={{ marginBottom: 10 }}>
        <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>What should the agent remember? *</label>
        <textarea
          className="field-input" rows={4} required autoFocus
          value={f.content} onChange={(e) => set('content', e.target.value)}
          maxLength={2000}
          placeholder="e.g. We bill NET-30 by default. Send invoice reminders at 7/14/21 days past due."
        />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: 10, marginBottom: 10 }}>
        <div>
          <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Kind</label>
          <select className="field-select" value={f.kind} onChange={(e) => set('kind', e.target.value)} style={{ width: '100%' }}>
            {['fact', 'preference', 'policy', 'contact'].map((k) => <option key={k}>{k}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Tags</label>
          <input className="field-input" value={f.tags} onChange={(e) => set('tags', e.target.value)} placeholder="e.g. billing, sales" maxLength={300} />
        </div>
      </div>
      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--color-text-muted)', cursor: 'pointer' }}>
        <input type="checkbox" checked={f.is_pinned} onChange={(e) => set('is_pinned', e.target.checked)} />
        Pin (always include in the agent's context)
      </label>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary">{initial ? 'Save' : 'Add to memory'}</button>
      </div>
    </form>
  );
}

const KIND_COLORS = {
  fact: 'var(--color-info)', preference: 'var(--color-ok)', policy: 'var(--color-warn)', contact: '#a78bfa',
};

export default function Memory() {
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState(null);
  const [msg, setMsg] = useState('');

  const reload = useCallback(async () => {
    try { setItems(await listMemoryApi(search)); }
    catch (e) { setMsg(`Failed: ${e.message}`); }
  }, [search]);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    const h = () => reload();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reload]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const handleSubmit = async (data) => {
    try {
      if (modal.record) await updateMemoryApi(modal.record.id, data);
      else await addMemoryApi(data);
      setModal(null); flash('Saved.'); reload();
    } catch (e) { alert(`Failed: ${e.message}`); }
  };

  const handleDelete = async (m) => {
    if (!confirm('Forget this?')) return;
    try { await deleteMemoryApi(m.id); flash('Forgotten.'); reload(); }
    catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleTogglePin = async (m) => {
    try { await updateMemoryApi(m.id, { is_pinned: !m.is_pinned }); reload(); }
    catch (e) { flash(`Failed: ${e.message}`); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Memory</h1>
          <p>Long-term facts and preferences the agent remembers about this business</p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn-ghost" onClick={async () => {
            const h = { 'Content-Type': 'application/json' };
            const t = getToken(); if (t) h['Authorization'] = `Bearer ${t}`;
            const b = getBusinessId(); if (b) h['X-Business-Id'] = b;
            try {
              const preview = await fetch('/api/memory/consolidate', {
                method: 'POST', headers: h, body: JSON.stringify({ apply: false }),
              }).then(r => r.json());
              if (!preview.plan) { flash(preview.reason || 'Nothing to consolidate.'); return; }
              const s = preview.plan.stats;
              const ok = confirm(
                `Consolidation plan:\n` +
                `• Merge ${s.proposed_merges} groups\n` +
                `• Drop ${s.proposed_drops} redundant entries\n` +
                `• Keep ${s.input_entries - s.proposed_drops - s.proposed_merges} unchanged\n\n` +
                `Apply now?`,
              );
              if (!ok) return;
              const applied = await fetch('/api/memory/consolidate', {
                method: 'POST', headers: h, body: JSON.stringify({ apply: true }),
              }).then(r => r.json());
              const sa = applied?.plan?.stats || {};
              flash(`Merged ${sa.applied_merges || 0}, dropped ${sa.applied_drops || 0}.`);
              reload();
            } catch (e) { flash(`Failed: ${e.message}`); }
          }}>
            <Sparkles size={12} /> Consolidate
          </button>
          <button className="btn-primary" onClick={() => setModal({ record: null })}>
            <Plus size={13} /> Add memory
          </button>
        </div>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      <div style={{ display: 'flex', gap: 8, padding: '0 24px 8px', borderBottom: '1px solid var(--color-surface-2)', alignItems: 'center' }}>
        <Search size={12} color="var(--color-text-dim)" />
        <input className="field-input" placeholder="Search memory..." value={search} onChange={(e) => setSearch(e.target.value)} style={{ fontSize: 11, width: 320 }} />
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {items.length === 0 ? (
          <EmptyState
            icon={Brain}
            title="No memories yet"
            description={'Teach the agents about how you run this business. Example: "Our pricing tiers are A: $5k/mo, B: $12k/mo" or "Slack alerts go to #sales-ops".'}
            primaryLabel="Add memory"
            onPrimary={() => setModal({ record: null })}
          />
        ) : (
          items.map((m) => {
            const color = KIND_COLORS[m.kind] || 'var(--color-text-dim)';
            return (
              <div key={m.id} className="panel" style={{ padding: 12, display: 'flex', alignItems: 'flex-start', gap: 10, borderLeft: `3px solid ${color}` }}>
                <button onClick={() => handleTogglePin(m)} style={{ background: 'none', border: 'none', color: m.is_pinned ? 'var(--color-warn)' : 'var(--color-text-dim)', cursor: 'pointer', padding: 2 }} title={m.is_pinned ? 'Unpin' : 'Pin'}>
                  {m.is_pinned ? <Pin size={14} /> : <PinOff size={14} />}
                </button>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, color: 'var(--color-text)', marginBottom: 4, whiteSpace: 'pre-wrap' }}>{m.content}</div>
                  <div style={{ fontSize: 9, color: 'var(--color-text-dim)', display: 'flex', gap: 8 }}>
                    <span style={{ color, fontWeight: 600, textTransform: 'uppercase' }}>{m.kind}</span>
                    {m.tags && <span>· {m.tags}</span>}
                    <span>· updated {m.updated_at?.substring(0, 16)}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                  <button className="btn-ghost" style={{ padding: 4 }} onClick={() => setModal({ record: m })}><Edit3 size={11} /></button>
                  <button className="btn-ghost" style={{ padding: 4, color: 'var(--color-err)' }} onClick={() => handleDelete(m)}><Trash2 size={11} /></button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {modal && (
        <Modal title={modal.record ? 'Edit memory' : 'New memory'} onClose={() => setModal(null)}>
          <MemoryForm initial={modal.record} onSubmit={handleSubmit} onCancel={() => setModal(null)} />
        </Modal>
      )}
    </div>
  );
}
