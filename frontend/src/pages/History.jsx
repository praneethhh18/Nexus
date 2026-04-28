/**
 * Query history — every question asked in chat, searchable + re-runnable.
 *
 * The backend tracks: query text, intent classification, tools used, an
 * answer preview, success flag, duration, timestamp, starred bit. We expose
 * filters (search / intent / starred / date window), a stats band, and per-row
 * actions: re-run in chat, star/unstar, delete. There's also a Clear All for
 * the privacy-conscious user who'd rather not keep a record at all.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, Star, Play, Trash2, Clock, RefreshCw, Filter, AlertCircle,
  CheckCircle2, Sparkles, X,
} from 'lucide-react';
import {
  getHistory, toggleStar, deleteHistoryEntry, clearHistory,
} from '../services/api';
import EmptyState from '../components/EmptyState';

const DATE_WINDOWS = [
  { id: 'all',   label: 'All time' },
  { id: 'today', label: 'Today' },
  { id: '7d',    label: 'Last 7 days' },
  { id: '30d',   label: 'Last 30 days' },
];

function inWindow(iso, win) {
  if (win === 'all' || !iso) return true;
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return true;
  const now = Date.now();
  if (win === 'today') {
    const d = new Date(); d.setHours(0, 0, 0, 0);
    return t >= d.getTime();
  }
  if (win === '7d')  return now - t <= 7  * 86400_000;
  if (win === '30d') return now - t <= 30 * 86400_000;
  return true;
}

function formatWhen(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    const now = new Date();
    const sameDay = d.toDateString() === now.toDateString();
    if (sameDay) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const yesterday = new Date(now); yesterday.setDate(yesterday.getDate() - 1);
    if (d.toDateString() === yesterday.toDateString())
      return `Yesterday · ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch { return iso.substring(0, 16); }
}


export default function History() {
  const [data, setData] = useState({ queries: [], stats: {} });
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [intentFilter, setIntentFilter] = useState('');
  const [starredOnly, setStarredOnly] = useState(false);
  const [dateWindow, setDateWindow] = useState('all');
  const [msg, setMsg] = useState('');
  const navigate = useNavigate();

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const r = await getHistory({
        search: search || undefined,
        intent: intentFilter || undefined,
        starred: starredOnly,
        limit: 200,
      });
      setData(r);
    } catch (e) {
      flash(`Failed: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, [search, intentFilter, starredOnly]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    const h = () => load();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [load]);

  // Client-side date filter — backend doesn't accept a window arg yet.
  const visible = useMemo(
    () => (data.queries || []).filter(q => inWindow(q.timestamp, dateWindow)),
    [data.queries, dateWindow],
  );
  const starredCount = useMemo(
    () => (data.queries || []).filter(q => q.starred).length,
    [data.queries],
  );
  const last24h = useMemo(
    () => (data.queries || []).filter(q => inWindow(q.timestamp, 'today')).length,
    [data.queries],
  );

  const handleRerun = (q) => {
    // Send the user to chat with the query pre-staged so they can edit
    // before sending. The Chat page listens for nexus-rerun and fills the
    // input box; Chat doesn't auto-send — keeps the user in control.
    navigate('/chat');
    setTimeout(() => {
      window.dispatchEvent(new CustomEvent('nexus-rerun', { detail: q.query }));
    }, 100);
  };

  const handleClearAll = async () => {
    if (!confirm(`Delete all ${data.queries.length} history entries? This cannot be undone.`)) return;
    try {
      await clearHistory();
      flash('History cleared.');
      load();
    } catch (e) { flash(`Clear failed: ${e.message}`); }
  };

  const handleDelete = async (q) => {
    try {
      await deleteHistoryEntry(q.id);
      load();
    } catch (e) { flash(`Delete failed: ${e.message}`); }
  };

  const handleStar = async (q) => {
    try {
      await toggleStar(q.id);
      load();
    } catch (e) { flash(`Star failed: ${e.message}`); }
  };

  const stats = data.stats || {};
  const total = stats.total_queries || 0;
  const hasHistory = total > 0;
  const hasFilters = !!(search || intentFilter || starredOnly || dateWindow !== 'all');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <h1>Query history</h1>
          <p>Every question you've asked in chat — searchable, starrable, re-runnable.</p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn-ghost btn-sm" onClick={load}><RefreshCw size={11} /> Refresh</button>
          {hasHistory && (
            <button className="btn-ghost btn-sm" onClick={handleClearAll} style={{ color: 'var(--color-err)' }}>
              <Trash2 size={11} /> Clear all
            </button>
          )}
        </div>
      </div>

      {msg && <div style={{ padding: '6px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      <div className="page-body">
        {/* ── Stats band ────────────────────────────────────────────────── */}
        <div className="card-grid card-grid--sm" style={{ marginBottom: 16 }}>
          <Stat label="Total queries"     value={total.toLocaleString()} icon={<Clock size={14} />} tone="info" />
          <Stat label="Today"             value={last24h.toLocaleString()} icon={<Sparkles size={14} />} tone="accent" />
          <Stat label="Avg response"      value={`${Math.round(stats.avg_duration_ms || 0)} ms`} icon={<RefreshCw size={14} />} tone="muted" />
          <Stat label="Success rate"      value={`${Math.round(stats.success_rate_pct || 0)}%`} icon={<CheckCircle2 size={14} />} tone={(stats.success_rate_pct || 0) >= 90 ? 'ok' : 'warn'} />
          <Stat label="Starred"           value={starredCount.toLocaleString()} icon={<Star size={14} />} tone="warn" />
        </div>

        {/* ── Filter bar ───────────────────────────────────────────────── */}
        <div style={{
          display: 'flex', gap: 8, marginBottom: 12,
          padding: 10,
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--r-md)',
          alignItems: 'center', flexWrap: 'wrap',
        }}>
          <div style={{
            flex: 1, minWidth: 240,
            display: 'flex', alignItems: 'center', gap: 8,
            background: 'var(--color-surface-1)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--r-md)',
            padding: '6px 12px',
          }}>
            <Search size={13} color="var(--color-text-dim)" />
            <input
              value={search} onChange={(e) => setSearch(e.target.value)}
              placeholder="Search queries or answers…"
              style={{
                flex: 1, background: 'transparent', border: 'none', outline: 'none',
                color: 'var(--color-text)', fontSize: 12.5,
              }}
            />
            {search && (
              <button onClick={() => setSearch('')} style={{ background: 'transparent', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 2 }} title="Clear search">
                <X size={12} />
              </button>
            )}
          </div>

          <select
            className="field-select"
            value={intentFilter}
            onChange={(e) => setIntentFilter(e.target.value)}
            style={{ fontSize: 12 }}
          >
            <option value="">All intents</option>
            {(stats.top_intents || []).map(i => (
              <option key={i.intent} value={i.intent}>{i.intent} ({i.count})</option>
            ))}
          </select>

          <select
            className="field-select"
            value={dateWindow}
            onChange={(e) => setDateWindow(e.target.value)}
            style={{ fontSize: 12 }}
          >
            {DATE_WINDOWS.map(w => <option key={w.id} value={w.id}>{w.label}</option>)}
          </select>

          <button
            onClick={() => setStarredOnly(!starredOnly)}
            className={starredOnly ? 'btn-primary btn-sm' : 'btn-ghost btn-sm'}
            title="Starred only"
          >
            <Star size={11} fill={starredOnly ? 'currentColor' : 'none'} />
            {starredOnly ? 'Starred' : 'All'}
          </button>

          {hasFilters && (
            <button
              className="btn-ghost btn-sm"
              onClick={() => {
                setSearch(''); setIntentFilter(''); setStarredOnly(false); setDateWindow('all');
              }}
              style={{ color: 'var(--color-text-dim)' }}
            >
              <X size={11} /> Clear filters
            </button>
          )}
        </div>

        {/* ── Results ──────────────────────────────────────────────────── */}
        {loading && visible.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-dim)', fontSize: 12 }}>
            Loading…
          </div>
        ) : visible.length === 0 ? (
          hasHistory ? (
            <EmptyState
              icon={Filter}
              title="No queries match those filters"
              description="Try clearing one of the filters, or widen the date window."
              primaryLabel="Clear filters"
              onPrimary={() => {
                setSearch(''); setIntentFilter(''); setStarredOnly(false); setDateWindow('all');
              }}
            />
          ) : (
            <EmptyState
              icon={Clock}
              title="No query history yet"
              description="Every question you ask in chat lands here with the intent classification, the tools that ran, and a one-click re-run button."
              primaryLabel="Open chat"
              onPrimary={() => navigate('/chat')}
            />
          )
        ) : (
          <>
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginBottom: 8, padding: '0 4px' }}>
              {visible.length} {visible.length === 1 ? 'query' : 'queries'}
              {hasFilters && total > visible.length && ` · filtered from ${total}`}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {visible.map(q => (
                <HistoryRow
                  key={q.id}
                  query={q}
                  onRerun={handleRerun}
                  onStar={handleStar}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}


// ── Row card ─────────────────────────────────────────────────────────────────
function HistoryRow({ query: q, onRerun, onStar, onDelete }) {
  const [confirming, setConfirming] = useState(false);

  return (
    <div className="panel" style={{
      padding: 12,
      display: 'flex', flexDirection: 'column', gap: 8,
      borderLeft: q.starred
        ? '2px solid var(--color-warn)'
        : (q.success === 0 ? '2px solid var(--color-err)' : '2px solid transparent'),
    }}>
      {/* Top: query text + star toggle */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: 13, fontWeight: 500, color: 'var(--color-text)',
            lineHeight: 1.45, wordBreak: 'break-word',
          }}>
            {q.query}
          </div>
          {q.answer_preview && (
            <div style={{
              fontSize: 12, color: 'var(--color-text-muted)',
              marginTop: 4, lineHeight: 1.5,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}>
              {q.answer_preview}
            </div>
          )}
        </div>
        <button
          onClick={() => onStar(q)}
          title={q.starred ? 'Unstar' : 'Star'}
          aria-label={q.starred ? 'Unstar' : 'Star'}
          style={{
            background: 'transparent', border: 'none', cursor: 'pointer',
            color: q.starred ? 'var(--color-warn)' : 'var(--color-text-dim)',
            padding: 4, transition: 'color var(--dur-fast) var(--ease-out)',
          }}
        >
          <Star size={14} fill={q.starred ? 'currentColor' : 'none'} />
        </button>
      </div>

      {/* Meta row */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
        {q.intent && (
          <span className="pill-base pill-info" style={{ textTransform: 'capitalize' }}>
            {q.intent.replace(/_/g, ' ')}
          </span>
        )}
        {(q.tools_used || []).map((t, i) => (
          <span key={i} className="pill-base pill-muted">{t}</span>
        ))}
        {q.success === 0 && (
          <span className="pill-base pill-err" title="Query reported a failure">
            <AlertCircle size={10} /> failed
          </span>
        )}
        <span style={{ marginLeft: 'auto', display: 'flex', gap: 10, fontSize: 10.5, color: 'var(--color-text-dim)', fontFeatureSettings: '"tnum"' }}>
          {q.duration_ms != null && <span>{q.duration_ms}ms</span>}
          <span>{formatWhen(q.timestamp)}</span>
        </span>
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 6, marginTop: 2 }}>
        <button className="btn-ghost btn-sm" onClick={() => onRerun(q)}>
          <Play size={11} /> Re-run in chat
        </button>
        {!confirming ? (
          <button
            className="btn-ghost btn-sm"
            onClick={() => setConfirming(true)}
            style={{ color: 'var(--color-text-dim)' }}
            title="Delete this entry"
          >
            <Trash2 size={11} />
          </button>
        ) : (
          <>
            <button
              className="btn-ghost btn-sm"
              onClick={() => { onDelete(q); setConfirming(false); }}
              style={{ color: 'var(--color-err)' }}
            >
              <Trash2 size={11} /> Delete?
            </button>
            <button
              className="btn-ghost btn-sm"
              onClick={() => setConfirming(false)}
            >
              Cancel
            </button>
          </>
        )}
      </div>
    </div>
  );
}


function Stat({ label, value, icon, tone = 'dim' }) {
  const toneColor = {
    accent: 'var(--color-accent)',
    info:   'var(--color-info)',
    ok:     'var(--color-ok)',
    warn:   'var(--color-warn)',
    err:    'var(--color-err)',
    dim:    'var(--color-text-dim)',
    muted:  'var(--color-text-muted)',
  }[tone];
  return (
    <div className="kpi">
      <div className="kpi-icon" style={{ background: `color-mix(in srgb, ${toneColor} 14%, transparent)`, color: toneColor }}>
        {icon}
      </div>
      <div className="kpi-body">
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">{value}</div>
      </div>
    </div>
  );
}
