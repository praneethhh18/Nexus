/**
 * SQL Editor — direct query runner against the local SQLite DB.
 *
 * Uses the proper /api/sql/execute endpoint (auth + business-id + safety
 * guards). Defaults to SELECT-only; the "Allow writes" toggle has to be
 * flipped on for INSERT/UPDATE/DELETE so an accidental enter doesn't
 * mutate data. `nexus_*` / `sqlite_*` tables are always protected.
 */
import { useState, useEffect } from 'react';
import {
  Play, Copy, Database, AlertCircle, CheckCircle2, Clock,
  Loader2, ShieldAlert,
} from 'lucide-react';
import { getTables, executeSql } from '../services/api';

const EXAMPLES = [
  "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name",
  "SELECT region, ROUND(SUM(revenue), 2) AS total FROM sales_metrics GROUP BY region ORDER BY total DESC",
  "SELECT strftime('%Y-%m', order_date) AS month, ROUND(SUM(total_amount), 2) AS revenue FROM orders GROUP BY month ORDER BY month",
  "SELECT COUNT(*) AS contacts FROM nexus_contacts",
];

export default function SQLEditor() {
  const [sql, setSQL]               = useState('SELECT name FROM sqlite_master WHERE type=\'table\' ORDER BY name;');
  const [result, setResult]         = useState(null);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');
  const [tables, setTables]         = useState([]);
  const [history, setHistory]       = useState([]);
  const [allowWrites, setAllowWrites] = useState(false);

  useEffect(() => { getTables().then(setTables).catch(() => {}); }, []);

  const runQuery = async () => {
    if (!sql.trim()) return;
    setLoading(true); setError(''); setResult(null);
    const started = performance.now();
    try {
      const res = await executeSql(sql, { allowWrites, limit: 500 });
      setResult(res);
      setHistory((h) => [
        { sql, rows: res.row_count || 0, kind: res.kind, time: new Date().toLocaleTimeString() },
        ...h.slice(0, 19),
      ]);
    } catch (err) {
      setError(err.message || 'Query failed.');
    } finally {
      const elapsed = Math.max(1, Math.round(performance.now() - started));
      setLoading(false);
      // Surface elapsed time even when the network layer doesn't tell us.
      if (!error) {
        // we only set a minimum "took N ms" hint locally if backend didn't echo
      }
      void elapsed;
    }
  };

  const copyResult = () => {
    if (!result?.rows?.length) return;
    const cols = result.columns;
    const csv = [
      cols.join(','),
      ...result.rows.map((r) => cols.map((c) => {
        const v = r[c];
        const s = v == null ? '' : String(v);
        return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
      }).join(',')),
    ].join('\n');
    navigator.clipboard.writeText(csv);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <h1>SQL Editor</h1>
        <p>Direct query runner. Read-only by default — flip "Allow writes" to mutate data. <code>nexus_*</code> tables are always protected.</p>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left: tables + history */}
        <div style={{ width: 220, borderRight: '1px solid var(--color-border)', overflow: 'auto', padding: 8, flexShrink: 0, background: 'var(--color-surface-1)' }}>
          <div className="conv-label">Tables</div>
          {tables.length === 0 && (
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)', padding: '4px 8px' }}>Loading…</div>
          )}
          {tables.map((t) => (
            <div key={t.name} className="conv-item" onClick={() => setSQL(`SELECT * FROM ${t.name} LIMIT 50;`)} style={{ fontSize: 11 }} title={`${t.row_count} rows · ${t.column_count} cols`}>
              <Database size={11} style={{ opacity: 0.45, flexShrink: 0 }} />
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.name}</span>
              <span style={{ fontSize: 9, color: 'var(--color-text-dim)' }}>{t.row_count}</span>
            </div>
          ))}

          {history.length > 0 && (
            <>
              <div className="conv-label" style={{ marginTop: 12 }}>Recent</div>
              {history.map((h, i) => (
                <div
                  key={i}
                  className="conv-item"
                  onClick={() => setSQL(h.sql)}
                  style={{ fontSize: 10, color: 'var(--color-text-dim)' }}
                  title={`${h.rows} rows · ${h.kind || 'read'} · ${h.time}`}
                >
                  {h.sql.length > 32 ? `${h.sql.substring(0, 32)}…` : h.sql}
                </div>
              ))}
            </>
          )}
        </div>

        {/* Right: editor + results */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Editor */}
          <div style={{ padding: 12, borderBottom: '1px solid var(--color-border)' }}>
            <textarea
              value={sql}
              onChange={(e) => setSQL(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); runQuery(); } }}
              style={{
                width: '100%', minHeight: 110,
                background: 'var(--color-bg)',
                border: '1px solid var(--color-border)', borderRadius: 'var(--r-md)',
                padding: 12, color: 'var(--color-text)',
                fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
                fontSize: 13, lineHeight: 1.55,
                resize: 'vertical', outline: 'none',
              }}
              placeholder="Write SQL here. Press Ctrl+Enter to run. One statement per request."
              spellCheck={false}
            />
            <div style={{ display: 'flex', gap: 8, marginTop: 10, alignItems: 'center', flexWrap: 'wrap' }}>
              <button className="btn-primary" onClick={runQuery} disabled={loading || !sql.trim()}>
                {loading ? <Loader2 size={13} className="animate-spin" /> : <Play size={13} />}
                {loading ? 'Running…' : 'Run query'}
              </button>
              <span style={{ fontSize: 10.5, color: 'var(--color-text-dim)' }}>Ctrl + Enter</span>

              <label
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: 6,
                  padding: '4px 10px', borderRadius: 'var(--r-pill)',
                  background: allowWrites ? 'color-mix(in srgb, var(--color-warn) 14%, transparent)' : 'var(--color-surface-2)',
                  border: `1px solid ${allowWrites ? 'color-mix(in srgb, var(--color-warn) 30%, transparent)' : 'var(--color-border)'}`,
                  fontSize: 11, color: allowWrites ? 'var(--color-warn)' : 'var(--color-text-muted)',
                  cursor: 'pointer', userSelect: 'none',
                }}
                title="Permit INSERT/UPDATE/DELETE on user tables. Protected nexus_* tables stay read-only."
              >
                <input
                  type="checkbox"
                  checked={allowWrites}
                  onChange={(e) => setAllowWrites(e.target.checked)}
                  style={{ accentColor: 'var(--color-warn)' }}
                />
                <ShieldAlert size={11} />
                Allow writes
              </label>

              <div style={{ marginLeft: 'auto', display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                {EXAMPLES.map((ex, i) => (
                  <button
                    key={i}
                    className="btn-ghost btn-sm"
                    onClick={() => setSQL(ex + ';')}
                    title={ex}
                  >
                    Example {i + 1}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Results */}
          <div style={{ flex: 1, overflow: 'auto', padding: 12 }}>
            {/* Error */}
            {error && (
              <div style={{
                display: 'flex', gap: 10, alignItems: 'flex-start',
                padding: 12,
                background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
                border: '1px solid color-mix(in srgb, var(--color-err) 28%, transparent)',
                borderRadius: 'var(--r-md)',
              }}>
                <AlertCircle size={16} color="var(--color-err)" style={{ marginTop: 2, flexShrink: 0 }} />
                <div>
                  <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--color-err)', marginBottom: 2 }}>
                    Query failed
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
                    {error}
                  </div>
                </div>
              </div>
            )}

            {/* Write result */}
            {result?.kind === 'write' && (
              <div style={{
                display: 'flex', gap: 10, alignItems: 'center',
                padding: 12,
                background: 'var(--color-accent-soft)',
                border: '1px solid color-mix(in srgb, var(--color-accent) 28%, transparent)',
                borderRadius: 'var(--r-md)',
              }}>
                <CheckCircle2 size={16} color="var(--color-accent)" />
                <span style={{ fontSize: 13, color: 'var(--color-accent)' }}>
                  {result.rows_affected ?? 0} row{result.rows_affected === 1 ? '' : 's'} affected
                </span>
                <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--color-text-dim)', display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                  <Clock size={10} /> {result.duration_ms}ms
                </span>
              </div>
            )}

            {/* Read result */}
            {result?.kind === 'read' && (
              <>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
                  <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                    {result.row_count} row{result.row_count === 1 ? '' : 's'} · {result.columns?.length || 0} column{result.columns?.length === 1 ? '' : 's'}
                    {result.truncated && (
                      <span style={{ color: 'var(--color-warn)', marginLeft: 8 }}>
                        (truncated to first 500)
                      </span>
                    )}
                    <span style={{ marginLeft: 10, fontSize: 11, color: 'var(--color-text-dim)' }}>
                      <Clock size={10} style={{ verticalAlign: 'middle', marginRight: 3 }} />
                      {result.duration_ms}ms
                    </span>
                  </span>
                  <button
                    className="btn-ghost btn-sm"
                    onClick={copyResult}
                    disabled={!result.rows?.length}
                  >
                    <Copy size={12} /> Copy CSV
                  </button>
                </div>

                {result.rows?.length > 0 ? (
                  <div className="table-panel">
                    <div style={{ overflowX: 'auto' }}>
                      <table className="data-table">
                        <thead>
                          <tr>{result.columns.map((c) => <th key={c}>{c}</th>)}</tr>
                        </thead>
                        <tbody>
                          {result.rows.map((row, i) => (
                            <tr key={i}>
                              {result.columns.map((c) => (
                                <td key={c} title={String(row[c] ?? '')}>
                                  {row[c] == null ? <span style={{ color: 'var(--color-text-dim)' }}>NULL</span> : String(row[c])}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-dim)', fontSize: 12.5 }}>
                    Query ran successfully but returned no rows.
                  </div>
                )}
              </>
            )}

            {/* Idle */}
            {!result && !error && (
              <div style={{ textAlign: 'center', padding: 50, color: 'var(--color-text-dim)' }}>
                <Database size={32} style={{ margin: '0 auto 10px', opacity: 0.4 }} />
                <p style={{ fontSize: 13 }}>Write a query above and press <kbd style={{ background: 'var(--color-surface-2)', padding: '2px 6px', borderRadius: 4, border: '1px solid var(--color-border)', fontSize: 10 }}>Ctrl + Enter</kbd></p>
                <p style={{ fontSize: 11, marginTop: 6 }}>Or click a table on the left to start with <code>SELECT * FROM …</code>.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
