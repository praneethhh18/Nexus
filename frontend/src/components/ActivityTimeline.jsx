/**
 * Per-record activity timeline. Shows tags, tasks, invoices, and tool-call
 * events on one vertical stream, newest first.
 *
 * <ActivityTimeline entityType="contact" entityId="..." />
 */
import { useState, useEffect } from 'react';
import { Tag, CheckSquare, Receipt, Activity, Loader2 } from 'lucide-react';
import { getToken, getBusinessId } from '../services/auth';

const KIND_META = {
  tag_added:        { icon: Tag,        color: 'var(--color-accent)', label: 'Tag' },
  task_created:     { icon: CheckSquare, color: 'var(--color-info)',   label: 'Task' },
  task_completed:   { icon: CheckSquare, color: 'var(--color-ok)',     label: 'Task done' },
  invoice_created:  { icon: Receipt,    color: 'var(--color-warn)',   label: 'Invoice' },
  invoice_paid:     { icon: Receipt,    color: 'var(--color-ok)',     label: 'Paid' },
  contact_linked:   { icon: Activity,   color: 'var(--color-info)',   label: 'Contact' },
  tool_call:        { icon: Activity,   color: 'var(--color-text-dim)', label: 'AI' },
};

function fmtTs(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z');
    const now = Date.now();
    const diff = (now - d.getTime()) / 1000;
    if (diff < 60)   return 'just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch { return iso.slice(0, 16); }
}

export default function ActivityTimeline({ entityType, entityId, limit = 100 }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (!entityType || !entityId) return;
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true); setErr('');
    const t = getToken();
    const b = getBusinessId();
    const hh = { };
    if (t) hh['Authorization'] = `Bearer ${t}`;
    if (b) hh['X-Business-Id'] = b;
    fetch(`/api/activity/${encodeURIComponent(entityType)}/${encodeURIComponent(entityId)}?limit=${limit}`, { headers: hh })
      .then(r => r.ok ? r.json() : Promise.reject(new Error(r.statusText)))
      .then(d => { if (!cancelled) setEvents(d.events || []); })
      .catch(e => { if (!cancelled) setErr(String(e.message || e)); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [entityType, entityId, limit]);

  if (loading) {
    return (
      <div style={{ padding: 20, textAlign: 'center', color: 'var(--color-text-dim)', fontSize: 12 }}>
        <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Loading activity…
      </div>
    );
  }
  if (err) {
    return <div style={{ color: 'var(--color-err)', fontSize: 12, padding: 12 }}>{err}</div>;
  }
  if (events.length === 0) {
    return (
      <div style={{ padding: 20, textAlign: 'center', color: 'var(--color-text-dim)', fontSize: 12 }}>
        No activity yet for this record.
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', paddingLeft: 18 }}>
      <div style={{
        position: 'absolute', left: 7, top: 10, bottom: 10,
        width: 2, background: 'var(--color-surface-2)',
      }} />
      {events.map((e, i) => {
        const meta = KIND_META[e.kind] || KIND_META.tool_call;
        const Icon = meta.icon;
        return (
          <div key={i} style={{ position: 'relative', marginBottom: 14 }}>
            <div style={{
              position: 'absolute', left: -18, top: 2,
              width: 16, height: 16, borderRadius: '50%',
              background: `color-mix(in srgb, ${meta.color} 25%, var(--color-bg))`,
              border: `2px solid ${meta.color}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <Icon size={8} color={meta.color} />
            </div>
            <div>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap',
                fontSize: 12, color: 'var(--color-text)', fontWeight: 500,
              }}>
                {e.kind === 'tag_added' && e.meta?.color && (
                  <span style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: e.meta.color, display: 'inline-block',
                  }} />
                )}
                {e.title}
                <span style={{ fontSize: 10, color: 'var(--color-text-dim)', marginLeft: 'auto' }}>
                  {fmtTs(e.ts)}
                </span>
              </div>
              {e.detail && (
                <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2 }}>
                  {e.detail}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
