/**
 * Passive AI suggestions for a single record.
 *
 * <SuggestionPanel entityType="contact" entityId="..." />
 *
 * Loads suggestions once on mount and renders them as dismissable cards.
 * Empty state: renders nothing — keeps record pages clean when there's no nudge.
 */
import { useEffect, useState, useCallback } from 'react';
import { Lightbulb, X } from 'lucide-react';
import { getSuggestionsFor, dismissSuggestion } from '../services/suggestions';

const SEVERITY_COLORS = {
  info: 'var(--color-info)',
  warn: 'var(--color-warn)',
  high: 'var(--color-err)',
};

export default function SuggestionPanel({ entityType, entityId, compact = false }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    if (!entityType || !entityId) return;
    setLoading(true);
    getSuggestionsFor(entityType, entityId)
      .then((d) => setItems(d.suggestions || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [entityType, entityId]);

  useEffect(() => { load(); }, [load]);

  const hide = async (id) => {
    setItems(prev => prev.filter(s => s.id !== id));
    try { await dismissSuggestion(id); } catch {}
  };

  if (loading || items.length === 0) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {items.map(s => {
        const color = SEVERITY_COLORS[s.severity] || SEVERITY_COLORS.info;
        return (
          <div
            key={s.id}
            className="panel"
            style={{
              padding: compact ? '8px 12px' : 12,
              display: 'flex', alignItems: 'flex-start', gap: 10,
              borderLeft: `3px solid ${color}`,
            }}
          >
            <div style={{
              width: 26, height: 26, borderRadius: 'var(--r-sm)',
              background: `color-mix(in srgb, ${color} 18%, transparent)`,
              color, flexShrink: 0,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Lightbulb size={14} />
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: 12, fontWeight: 600, color: 'var(--color-text)',
                display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap',
              }}>
                {s.title}
                {s.agent && (
                  <span style={{
                    fontSize: 9, padding: '1px 6px', borderRadius: 'var(--r-pill)',
                    background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
                    fontWeight: 600, letterSpacing: 0.3,
                  }}>
                    {s.agent}
                  </span>
                )}
              </div>
              <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2, lineHeight: 1.45 }}>
                {s.detail}
              </div>
              {s.cta && (
                <div style={{ fontSize: 11, color, marginTop: 4, fontWeight: 500 }}>
                  → {s.cta}
                </div>
              )}
            </div>
            <button
              onClick={() => hide(s.id)}
              className="btn-ghost"
              style={{ padding: 4, color: 'var(--color-text-dim)' }}
              title="Dismiss — won't show again for this record"
            >
              <X size={11} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
