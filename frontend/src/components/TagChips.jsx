/**
 * Tag chips + picker.
 *
 * <TagChips tags={[...]} />                — display-only, compact pill row
 * <TagPicker entityType="task" entityId="..." onChange={...} />
 *                                         — editable: click to add, click × to remove
 */
import { useState, useEffect, useRef } from 'react';
import { Tag, X, Plus } from 'lucide-react';
import { listTags, createTag, tagsFor, setTagsFor } from '../services/tags';


export function TagChips({ tags, size = 'sm', onRemove = null }) {
  if (!tags || tags.length === 0) return null;
  const fontSize = size === 'xs' ? 9 : 10;
  const pad = size === 'xs' ? '1px 6px' : '2px 7px';
  return (
    <span style={{ display: 'inline-flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
      {tags.map(t => (
        <span
          key={t.id}
          title={t.name}
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 3,
            padding: pad, borderRadius: 'var(--r-pill)',
            fontSize, fontWeight: 600, letterSpacing: 0.2,
            color: t.color,
            background: `color-mix(in srgb, ${t.color} 13%, transparent)`,
            border: `1px solid color-mix(in srgb, ${t.color} 35%, transparent)`,
          }}
        >
          {t.name}
          {onRemove && (
            <button
              onClick={(e) => { e.stopPropagation(); onRemove(t); }}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                padding: 0, color: t.color, opacity: 0.7, display: 'flex',
              }}
              title={`Remove tag ${t.name}`}
            >
              <X size={9} />
            </button>
          )}
        </span>
      ))}
    </span>
  );
}


export function TagPicker({ entityType, entityId, onChange }) {
  const [mine, setMine] = useState([]);
  const [all, setAll] = useState([]);
  const [open, setOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [busy, setBusy] = useState(false);
  const ref = useRef(null);

  const load = async () => {
    try {
      const [m, a] = await Promise.all([
        tagsFor(entityType, entityId),
        listTags(),
      ]);
      setMine(m);
      setAll(a);
    } catch {}
  };

  useEffect(() => { if (entityId) load(); /* eslint-disable-line */ }, [entityType, entityId]);

  useEffect(() => {
    const click = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    if (open) {
      window.addEventListener('mousedown', click);
      return () => window.removeEventListener('mousedown', click);
    }
  }, [open]);

  const save = async (nextIds) => {
    if (busy) return;
    setBusy(true);
    try {
      const fresh = await setTagsFor(entityType, entityId, nextIds);
      setMine(fresh);
      onChange?.(fresh);
    } finally { setBusy(false); }
  };

  const toggle = (tag) => {
    const has = mine.some(t => t.id === tag.id);
    const next = has ? mine.filter(t => t.id !== tag.id).map(t => t.id)
                     : [...mine.map(t => t.id), tag.id];
    save(next);
  };

  const addNew = async () => {
    const name = newName.trim();
    if (!name) return;
    try {
      const t = await createTag(name);
      setAll(prev => prev.some(x => x.id === t.id) ? prev : [...prev, t]);
      await save([...mine.map(x => x.id), t.id]);
      setNewName('');
    } catch {}
  };

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <span style={{ display: 'inline-flex', gap: 4, flexWrap: 'wrap', alignItems: 'center' }}>
        <TagChips tags={mine} onRemove={(t) => toggle(t)} />
        <button
          onClick={() => setOpen(o => !o)}
          className="btn-ghost"
          style={{ fontSize: 10, padding: '2px 8px', display: 'inline-flex', gap: 3, alignItems: 'center' }}
          title="Add or change tags"
        >
          <Tag size={10} /> {mine.length === 0 ? 'Add tag' : 'Edit'}
        </button>
      </span>

      {open && (
        <div
          style={{
            position: 'absolute', top: '100%', left: 0, marginTop: 4,
            background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)',
            borderRadius: 'var(--r-md)', padding: 8, minWidth: 220, zIndex: 200,
            boxShadow: '0 12px 32px rgba(0,0,0,0.5)',
          }}
        >
          <div style={{ display: 'flex', gap: 4, marginBottom: 8 }}>
            <input
              className="field-input"
              placeholder="New tag name…"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addNew(); } }}
              style={{ fontSize: 11, padding: '4px 8px', flex: 1 }}
              maxLength={40}
            />
            <button onClick={addNew} className="btn-ghost" style={{ fontSize: 11, padding: '4px 6px' }}>
              <Plus size={10} />
            </button>
          </div>
          <div style={{ maxHeight: 180, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
            {all.length === 0 && (
              <span style={{ fontSize: 10, color: 'var(--color-text-dim)', padding: 4 }}>
                No tags yet — type a name above and press Enter.
              </span>
            )}
            {all.map(t => {
              const selected = mine.some(x => x.id === t.id);
              return (
                <button
                  key={t.id}
                  onClick={() => toggle(t)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6,
                    padding: '4px 6px', borderRadius: 'var(--r-sm)',
                    border: 'none', cursor: 'pointer', textAlign: 'left',
                    background: selected ? `color-mix(in srgb, ${t.color} 12%, transparent)` : 'transparent',
                    color: 'var(--color-text)',
                    fontSize: 11,
                  }}
                >
                  <span style={{
                    width: 8, height: 8, borderRadius: '50%', background: t.color, flexShrink: 0,
                  }} />
                  <span style={{ flex: 1 }}>{t.name}</span>
                  {selected && <span style={{ color: t.color, fontSize: 10 }}>✓</span>}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
