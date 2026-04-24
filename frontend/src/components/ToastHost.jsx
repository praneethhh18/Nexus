/**
 * Lightweight toast notifications.
 *
 * Usage anywhere in the app:
 *   import { toast } from './components/ToastHost';
 *   toast.success('Saved');
 *   toast.error('Network blip — retry?');
 *   toast.info('Atlas wrote your briefing');
 *
 * The host component subscribes to a module-scoped event bus so any file
 * can fire a toast without React context plumbing. Mount `<ToastHost />`
 * once near the top of the tree (done in Layout).
 */
import { useEffect, useState } from 'react';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';


// ── Event bus ───────────────────────────────────────────────────────────────
const _listeners = new Set();
let _nextId = 1;

function _push(kind, message, { duration = 3500 } = {}) {
  const id = _nextId++;
  const item = { id, kind, message, duration, ts: Date.now() };
  _listeners.forEach(fn => { try { fn(item); } catch {} });
  return id;
}

export const toast = {
  success: (m, opts) => _push('success', m, opts),
  error:   (m, opts) => _push('error',   m, { duration: 6000, ...(opts || {}) }),
  info:    (m, opts) => _push('info',    m, opts),
};


// ── Host component ─────────────────────────────────────────────────────────
const META = {
  success: { Icon: CheckCircle2, color: 'var(--color-ok)'   },
  error:   { Icon: AlertTriangle, color: 'var(--color-err)' },
  info:    { Icon: Info,          color: 'var(--color-info)' },
};

export default function ToastHost() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    const onPush = (item) => {
      setItems(prev => [...prev, item]);
      if (item.duration > 0) {
        setTimeout(() => {
          setItems(prev => prev.filter(x => x.id !== item.id));
        }, item.duration);
      }
    };
    _listeners.add(onPush);
    return () => _listeners.delete(onPush);
  }, []);

  const dismiss = (id) => setItems(prev => prev.filter(x => x.id !== id));

  if (items.length === 0) return null;

  return (
    <div style={{
      position: 'fixed', bottom: 16, right: 16, zIndex: 600,
      display: 'flex', flexDirection: 'column', gap: 8,
      pointerEvents: 'none',
    }}>
      {items.map(t => {
        const m = META[t.kind] || META.info;
        const Icon = m.Icon;
        return (
          <div
            key={t.id}
            style={{
              minWidth: 260, maxWidth: 360,
              display: 'flex', alignItems: 'flex-start', gap: 10,
              padding: '10px 12px', borderRadius: 'var(--r-md)',
              background: 'var(--color-surface-2)',
              border: `1px solid color-mix(in srgb, ${m.color} 35%, transparent)`,
              borderLeft: `4px solid ${m.color}`,
              boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
              color: 'var(--color-text)',
              fontSize: 12, lineHeight: 1.45,
              pointerEvents: 'auto',
              animation: 'toast-in 0.18s ease-out',
            }}
          >
            <Icon size={14} color={m.color} style={{ flexShrink: 0, marginTop: 1 }} />
            <div style={{ flex: 1 }}>{t.message}</div>
            <button
              onClick={() => dismiss(t.id)}
              style={{
                background: 'none', border: 'none', padding: 2, cursor: 'pointer',
                color: 'var(--color-text-dim)', opacity: 0.7,
              }}
            >
              <X size={11} />
            </button>
          </div>
        );
      })}
      <style>{`
        @keyframes toast-in {
          from { opacity: 0; transform: translateX(6px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>
    </div>
  );
}
