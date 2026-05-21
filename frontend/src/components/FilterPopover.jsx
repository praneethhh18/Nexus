/**
 * Reusable filter popover — Filter button + grouped sections, with active
 * filters rendered as dismissable chips next to the button. Mirrors the
 * pattern established in CRM.jsx so Tasks/Invoices/Documents share the
 * same UX.
 *
 * <FilterPopover
 *   groups={[
 *     { key: 'status',  label: 'Status',  options: [...], multi: false },
 *     { key: 'due',     label: 'Due',     options: [...], multi: false },
 *   ]}
 *   values={{ status: 'active', due: '' }}
 *   onChange={(groupKey, value) => ...}
 * />
 *
 * For single-select groups: value is a string. For multi: value is an array.
 * Empty string / empty array = no filter applied.
 */
import { useState, useEffect, useRef } from 'react';
import { Activity, X } from 'lucide-react';


export default function FilterPopover({ groups, values, onChange, align = 'left' }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  // Click-outside close. Guard against clicks on elements that toggle
  // themselves out of the DOM (same pattern as TagPicker).
  useEffect(() => {
    if (!open) return;
    const onClick = (e) => {
      if (!e.target || !document.body.contains(e.target)) return;
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    window.addEventListener('mousedown', onClick);
    return () => window.removeEventListener('mousedown', onClick);
  }, [open]);

  // Esc closes
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === 'Escape') setOpen(false); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open]);

  const activeCount = groups.reduce((acc, g) => {
    const v = values[g.key];
    if (g.multi) return acc + ((Array.isArray(v) ? v.length : 0));
    return acc + (v ? 1 : 0);
  }, 0);

  const clearAll = () => {
    for (const g of groups) onChange(g.key, g.multi ? [] : '');
  };

  const toggleValue = (g, optValue) => {
    if (g.multi) {
      const arr = Array.isArray(values[g.key]) ? values[g.key] : [];
      const next = arr.includes(optValue) ? arr.filter(x => x !== optValue) : [...arr, optValue];
      onChange(g.key, next);
    } else {
      onChange(g.key, values[g.key] === optValue ? '' : optValue);
    }
  };

  const removeValue = (g, optValue) => {
    if (g.multi) {
      onChange(g.key, (values[g.key] || []).filter(x => x !== optValue));
    } else {
      onChange(g.key, '');
    }
  };

  return (
    <div ref={ref} style={{
      display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center',
      position: 'relative',
    }}>
      <div style={{ position: 'relative' }}>
        <button
          type="button"
          onClick={() => setOpen(o => !o)}
          className={open || activeCount > 0 ? 'btn-primary' : 'btn-ghost'}
          style={{ fontSize: 11, padding: '4px 10px', display: 'inline-flex', gap: 5, alignItems: 'center' }}
        >
          <Activity size={11} /> Filter
          {activeCount > 0 && (
            <span style={{
              fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 10,
              background: 'rgba(255,255,255,0.25)', color: 'inherit',
            }}>{activeCount}</span>
          )}
        </button>
        {open && (
          <div style={{
            position: 'absolute',
            top: 'calc(100% + 6px)',
            [align === 'right' ? 'right' : 'left']: 0,
            width: 320, maxHeight: 'min(520px, 70vh)', overflow: 'auto',
            background: 'var(--color-surface-2)',
            border: '1px solid var(--color-border-strong)',
            borderRadius: 12, zIndex: 51,
            boxShadow: '0 18px 48px rgba(0,0,0,0.45)',
            padding: 12,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text)' }}>Filters</span>
              {activeCount > 0 && (
                <button type="button" onClick={clearAll}
                        style={{ fontSize: 10.5, color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer' }}>
                  Clear all
                </button>
              )}
            </div>
            {groups.map((g) => {
              const v = values[g.key];
              const isActive = (optValue) => g.multi
                ? (Array.isArray(v) && v.includes(optValue))
                : v === optValue;
              return (
                <div key={g.key} style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 0.6, textTransform: 'uppercase', color: 'var(--color-text-dim)', marginBottom: 6 }}>
                    {g.label}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {g.options.map(opt => {
                      const checked = isActive(opt.value);
                      return (
                        <label key={String(opt.value)} style={{
                          display: 'flex', alignItems: 'center', gap: 8, padding: '5px 8px',
                          borderRadius: 6, cursor: 'pointer', fontSize: 12,
                          background: checked ? 'var(--color-accent-soft)' : 'transparent',
                          color: 'var(--color-text)',
                        }}
                        onMouseEnter={(e) => { if (!checked) e.currentTarget.style.background = 'var(--color-surface-1)'; }}
                        onMouseLeave={(e) => { if (!checked) e.currentTarget.style.background = 'transparent'; }}>
                          <input
                            type={g.multi ? 'checkbox' : 'radio'}
                            checked={checked}
                            onChange={() => toggleValue(g, opt.value)}
                            name={g.multi ? undefined : `filter-${g.key}`}
                            style={{ cursor: 'pointer' }}
                          />
                          <span>{opt.label}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Active filter chips */}
      {groups.flatMap((g) => {
        const v = values[g.key];
        if (g.multi) {
          return (Array.isArray(v) ? v : []).map((val) => {
            const opt = g.options.find(o => o.value === val);
            return (
              <FilterChip key={`${g.key}:${val}`}
                label={opt?.label || String(val)}
                onRemove={() => removeValue(g, val)} />
            );
          });
        }
        if (!v) return [];
        const opt = g.options.find(o => o.value === v);
        return [
          <FilterChip key={g.key}
            label={`${g.label}: ${opt?.label || String(v)}`}
            onRemove={() => removeValue(g, v)} />,
        ];
      })}
    </div>
  );
}


function FilterChip({ label, onRemove }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '3px 8px', borderRadius: 12, fontSize: 11,
      background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
    }}>
      {label}
      <button type="button" onClick={onRemove} aria-label="Remove filter"
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0, display: 'flex' }}>
        <X size={11} />
      </button>
    </span>
  );
}
