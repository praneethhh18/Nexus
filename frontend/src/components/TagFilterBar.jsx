/**
 * Tag filter strip for list pages.
 *
 * <TagFilterBar selectedIds={...} onChange={...} />
 *
 * Shows every tag in the business as a clickable chip. Selected tags light up.
 * Callers pair this with their own filtering logic: the filter passes an item
 * only if its tag IDs include *all* selected tag IDs (AND semantics).
 *
 * `filterItems(items, itemTags, selectedIds)` is a small helper for that.
 */
import { useState, useEffect } from 'react';
import { Tag as TagIcon } from 'lucide-react';
import { listTags } from '../services/tags';


export default function TagFilterBar({ selectedIds = [], onChange }) {
  const [all, setAll] = useState([]);

  useEffect(() => {
    listTags().then(setAll).catch(() => {});
  }, []);

  if (all.length === 0) return null;

  const toggle = (id) => {
    const next = selectedIds.includes(id)
      ? selectedIds.filter(x => x !== id)
      : [...selectedIds, id];
    onChange?.(next);
  };

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap',
      padding: '4px 0', fontSize: 11,
    }}>
      <TagIcon size={11} color="var(--color-text-dim)" />
      <span style={{ color: 'var(--color-text-dim)', marginRight: 4 }}>Filter by tag:</span>
      {all.map(t => {
        const on = selectedIds.includes(t.id);
        return (
          <button
            key={t.id}
            onClick={() => toggle(t.id)}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 4,
              padding: '2px 8px', borderRadius: 'var(--r-pill)',
              fontSize: 10, fontWeight: 600, cursor: 'pointer',
              color: on ? 'white' : t.color,
              background: on
                ? t.color
                : `color-mix(in srgb, ${t.color} 10%, transparent)`,
              border: `1px solid color-mix(in srgb, ${t.color} 35%, transparent)`,
            }}
          >
            <span style={{
              width: 6, height: 6, borderRadius: '50%',
              background: on ? 'white' : t.color,
            }} />
            {t.name}
          </button>
        );
      })}
      {selectedIds.length > 0 && (
        <button
          onClick={() => onChange?.([])}
          className="btn-ghost"
          style={{ fontSize: 10, padding: '2px 8px' }}
        >
          Clear
        </button>
      )}
    </div>
  );
}


export function filterItems(items, itemTags, selectedTagIds) {
  if (!selectedTagIds || selectedTagIds.length === 0) return items;
  return items.filter(item => {
    const tags = itemTags[item.id] || [];
    const ids = new Set(tags.map(t => t.id));
    return selectedTagIds.every(id => ids.has(id));
  });
}
