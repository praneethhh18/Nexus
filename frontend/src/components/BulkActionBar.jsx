/**
 * Bulk selection primitives.
 *
 * useBulkSelection(items, getId)
 *   - returns { selected, toggle, toggleAll, clear, all, any, count }
 *   - lightweight state holder shared between the checkbox column and the
 *     action bar below.
 *
 * <BulkActionBar>
 *   - sticky bar that appears when count > 0; renders Cancel + children
 *     (caller supplies domain-specific buttons like Delete / Mark done).
 */
import { useState, useMemo, useCallback } from 'react';
import { X, Check } from 'lucide-react';


export function useBulkSelection(items, getId = (i) => i.id) {
  const [selected, setSelected] = useState(new Set());

  const ids = useMemo(() => new Set((items || []).map(getId)), [items, getId]);

  // Drop IDs that aren't in the current list (happens on filter change).
  const cleanSelected = useMemo(() => {
    const out = new Set();
    for (const id of selected) if (ids.has(id)) out.add(id);
    return out;
  }, [selected, ids]);

  const toggle = useCallback((id) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  }, []);

  const toggleAll = useCallback(() => {
    setSelected(prev => {
      const allIds = Array.from(ids);
      const allSelected = allIds.length > 0 && allIds.every(x => prev.has(x));
      return allSelected ? new Set() : new Set(allIds);
    });
  }, [ids]);

  const clear = useCallback(() => setSelected(new Set()), []);

  const allIds = Array.from(ids);
  const any = cleanSelected.size > 0;
  const all = allIds.length > 0 && allIds.every(x => cleanSelected.has(x));
  const some = any && !all;

  return {
    selected: cleanSelected,
    isSelected: (id) => cleanSelected.has(id),
    toggle, toggleAll, clear,
    all, some, any,
    count: cleanSelected.size,
  };
}


export function BulkCheckbox({ checked, indeterminate = false, onChange, size = 14, title }) {
  const ref = (el) => {
    if (el) el.indeterminate = !checked && indeterminate;
  };
  return (
    <input
      ref={ref}
      type="checkbox"
      checked={!!checked}
      onChange={(e) => onChange?.(e.target.checked)}
      onClick={(e) => e.stopPropagation()}
      title={title}
      style={{ width: size, height: size, cursor: 'pointer', accentColor: 'var(--color-accent)' }}
    />
  );
}


export function BulkActionBar({ count, onCancel, children }) {
  if (!count) return null;
  return (
    <div
      style={{
        position: 'sticky', bottom: 8, zIndex: 80,
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 14px', borderRadius: 'var(--r-md)',
        background: 'color-mix(in srgb, var(--color-accent) 12%, var(--color-bg))',
        border: '1px solid color-mix(in srgb, var(--color-accent) 35%, transparent)',
        boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
        margin: '8px 0',
      }}
    >
      <Check size={14} color="var(--color-accent)" />
      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text)' }}>
        {count} selected
      </span>
      <div style={{ flex: 1 }} />
      {children}
      <button
        onClick={onCancel}
        className="btn-ghost"
        style={{ fontSize: 11, padding: '4px 10px' }}
        title="Clear selection"
      >
        <X size={11} /> Cancel
      </button>
    </div>
  );
}


/**
 * Toast with an undo button — shown after a bulk action.
 * The action fires immediately; user has `timeoutMs` to hit Undo.
 * Undo isn't truly transactional — it's the caller's responsibility to
 * provide an `onUndo` that re-creates or re-enables the affected rows.
 */
export function UndoToast({ message, onUndo, onClose, timeoutMs = 5000 }) {
  // auto-close handled by caller via setTimeout; we just render.
  return (
    <div style={{
      position: 'fixed', bottom: 24, left: '50%', transform: 'translateX(-50%)',
      background: 'var(--color-surface-2)', color: 'var(--color-text)',
      border: '1px solid var(--color-border-strong)', borderRadius: 'var(--r-md)',
      padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 10,
      boxShadow: '0 12px 32px rgba(0,0,0,0.6)', zIndex: 500, fontSize: 12,
    }}>
      <span>{message}</span>
      {onUndo && (
        <button onClick={onUndo} className="btn-ghost" style={{ fontSize: 11 }}>
          Undo
        </button>
      )}
      <button onClick={onClose} className="btn-ghost" style={{ fontSize: 11, padding: 4 }}>
        <X size={11} />
      </button>
    </div>
  );
}
