import { useState, useEffect } from 'react';
import { Search, Star, Play, Trash2, Clock } from 'lucide-react';
import { getHistory, toggleStar, deleteHistoryEntry } from '../services/api';
import { useNavigate } from 'react-router-dom';
import EmptyState from '../components/EmptyState';

export default function History() {
  const [data, setData] = useState({ queries: [], stats: {} });
  const [search, setSearch] = useState('');
  const [intentFilter, setIntentFilter] = useState('');
  const [starredOnly, setStarredOnly] = useState(false);
  const navigate = useNavigate();

  const load = () => { getHistory({ search: search || undefined, intent: intentFilter || undefined, starred: starredOnly }).then(setData).catch(() => {}); };
  useEffect(load, [search, intentFilter, starredOnly]);

  const { stats } = data;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header"><h1>Query History</h1><p>Search, filter, and re-run past queries</p></div>
      <div className="page-body">
        <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
          <div className="stat-card"><div className="value">{stats.total_queries || 0}</div><div className="label">Total Queries</div></div>
          <div className="stat-card"><div className="value">{stats.avg_duration_ms || 0}ms</div><div className="label">Avg Response</div></div>
          <div className="stat-card"><div className="value">{stats.success_rate_pct || 0}%</div><div className="label">Success Rate</div></div>
        </div>

        <div style={{ display: 'flex', gap: 8, marginBottom: 12, alignItems: 'center' }}>
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: 8, background: 'var(--color-surface-2)', border: '1px solid var(--color-border-strong)', borderRadius: 8, padding: '6px 12px' }}>
            <Search size={14} color="var(--color-text-dim)" />
            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search queries..."
              style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', color: 'white', fontSize: 12 }} />
          </div>
          <select className="field-select" value={intentFilter} onChange={e => setIntentFilter(e.target.value)}>
            <option value="">All Types</option>
            {(stats.top_intents || []).map(i => <option key={i.intent} value={i.intent}>{i.intent} ({i.count})</option>)}
          </select>
          <button onClick={() => setStarredOnly(!starredOnly)}
            style={{ padding: 6, borderRadius: 6, border: 'none', cursor: 'pointer', background: starredOnly ? 'color-mix(in srgb, var(--color-warn) 8%, transparent)' : 'transparent', color: starredOnly ? 'var(--color-warn)' : 'var(--color-text-dim)' }}>
            <Star size={16} fill={starredOnly ? 'currentColor' : 'none'} />
          </button>
        </div>

        {data.queries.length === 0 ? (
          <EmptyState
            icon={Clock}
            title="No query history yet"
            description="Every question you ask in Chat shows up here with its intent, tools used, and a replay button. Start by asking something in Chat."
            primaryLabel="Go to chat"
            onPrimary={() => navigate('/chat')}
          />
        ) : data.queries.map(q => (
          <div key={q.id} className="history-item">
            <div className="history-query">{q.query}</div>
            {q.answer_preview && <div className="history-answer">{q.answer_preview}</div>}
            <div className="history-meta">
              <span className="chip">{q.intent}</span>
              {q.tools_used?.map((t, i) => <span key={i}>{t}</span>)}
              <span>{q.duration_ms}ms</span>
              <span>{q.timestamp?.substring(0, 16)}</span>
            </div>
            <div className="history-actions">
              <button onClick={() => { navigate('/'); setTimeout(() => window.dispatchEvent(new CustomEvent('nexus-rerun', { detail: q.query })), 100); }}>
                <Play size={12} /> Re-run
              </button>
              <button onClick={async () => { await toggleStar(q.id); load(); }} style={q.starred ? { color: 'var(--color-warn)' } : {}}>
                <Star size={12} fill={q.starred ? 'currentColor' : 'none'} /> {q.starred ? 'Unstar' : 'Star'}
              </button>
              <button onClick={async () => { await deleteHistoryEntry(q.id); load(); }} style={{ color: 'var(--color-text-dim)' }}>
                <Trash2 size={12} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
