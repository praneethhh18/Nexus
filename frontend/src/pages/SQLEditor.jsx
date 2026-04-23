import { useState, useEffect } from 'react';
import { Play, Copy, Download, Database } from 'lucide-react';
import { getTables, getTableDetail } from '../services/api';

export default function SQLEditor() {
  const [sql, setSQL] = useState('SELECT * FROM sales_metrics LIMIT 20;');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [tables, setTables] = useState([]);
  const [history, setHistory] = useState([]);

  useEffect(() => { getTables().then(setTables).catch(() => {}); }, []);

  const runQuery = async () => {
    if (!sql.trim()) return;
    setLoading(true); setError(''); setResult(null);
    try {
      // Use the table detail endpoint with a raw query approach
      // We'll send through the chat API as a workaround
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: `Run this SQL: ${sql}` }),
      });
      const data = await res.json();

      if (data.state?.sql_results?.data) {
        setResult(data.state.sql_results);
        setHistory(h => [{ sql, rows: data.state.sql_results.row_count, time: new Date().toLocaleTimeString() }, ...h.slice(0, 19)]);
      } else {
        setResult({ data: [], columns: [], row_count: 0, explanation: data.message?.content || 'No data returned' });
      }
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  const copyResult = () => {
    if (!result?.data?.length) return;
    const csv = [result.columns.join(','), ...result.data.map(r => result.columns.map(c => String(r[c] ?? '')).join(','))].join('\n');
    navigator.clipboard.writeText(csv);
  };

  const EXAMPLES = [
    "SELECT region, ROUND(SUM(revenue), 2) as total FROM sales_metrics GROUP BY region ORDER BY total DESC;",
    "SELECT c.name, COUNT(o.id) as orders FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id ORDER BY orders DESC LIMIT 10;",
    "SELECT strftime('%Y-%m', order_date) as month, ROUND(SUM(total_amount), 2) as revenue FROM orders GROUP BY month ORDER BY month;",
    "SELECT p.name, SUM(oi.quantity) as sold FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id ORDER BY sold DESC LIMIT 5;",
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header"><h1>SQL Editor</h1><p>Write and execute SQL queries directly against your database</p></div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar — tables + history */}
        <div style={{ width: 200, borderRight: '1px solid var(--color-surface-2)', overflow: 'auto', padding: 8, flexShrink: 0 }}>
          <div className="conv-label">Tables</div>
          {tables.filter(t => !t.is_system).map(t => (
            <div key={t.name} className="conv-item" onClick={() => setSQL(`SELECT * FROM ${t.name} LIMIT 20;`)} style={{ fontSize: 11 }}>
              <Database size={11} style={{ opacity: 0.4, flexShrink: 0 }} />
              <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.name}</span>
              <span style={{ fontSize: 9, color: 'var(--color-text-dim)' }}>{t.row_count}</span>
            </div>
          ))}

          {history.length > 0 && (
            <>
              <div className="conv-label" style={{ marginTop: 12 }}>Recent</div>
              {history.map((h, i) => (
                <div key={i} className="conv-item" onClick={() => setSQL(h.sql)} style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>
                  {h.sql.substring(0, 30)}...
                </div>
              ))}
            </>
          )}
        </div>

        {/* Main */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Editor */}
          <div style={{ padding: 12, borderBottom: '1px solid var(--color-surface-2)' }}>
            <textarea value={sql} onChange={e => setSQL(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); runQuery(); } }}
              style={{
                width: '100%', minHeight: 100, background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 8,
                padding: 12, color: 'var(--color-text)', fontFamily: 'monospace', fontSize: 13, lineHeight: 1.5,
                resize: 'vertical', outline: 'none',
              }}
              placeholder="Write SQL here... Press Ctrl+Enter to run" />
            <div style={{ display: 'flex', gap: 6, marginTop: 8, alignItems: 'center' }}>
              <button className="btn-primary" onClick={runQuery} disabled={loading || !sql.trim()}>
                <Play size={14} /> {loading ? 'Running...' : 'Run Query'}
              </button>
              <span style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>Ctrl+Enter to run</span>
              <div style={{ marginLeft: 'auto', display: 'flex', gap: 4 }}>
                {EXAMPLES.map((ex, i) => (
                  <button key={i} className="btn-ghost" onClick={() => setSQL(ex)} style={{ fontSize: 9, padding: '3px 8px' }}>
                    Example {i + 1}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Results */}
          <div style={{ flex: 1, overflow: 'auto', padding: 12 }}>
            {error && <div className="panel" style={{ color: 'var(--color-err)', borderColor: 'color-mix(in srgb, var(--color-err) 13%, transparent)' }}>{error}</div>}

            {result && (
              <>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                  <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                    {result.row_count} rows &middot; {result.columns?.length || 0} columns
                  </span>
                  <div style={{ display: 'flex', gap: 4 }}>
                    <button className="btn-ghost" onClick={copyResult} style={{ fontSize: 10 }}><Copy size={12} /> Copy CSV</button>
                  </div>
                </div>

                {result.explanation && (
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', padding: '8px 12px', background: 'var(--color-surface-1)', borderRadius: 8, marginBottom: 8, borderLeft: '2px solid color-mix(in srgb, var(--color-accent) 25%, transparent)' }}>
                    {result.explanation}
                  </div>
                )}

                {result.data?.length > 0 ? (
                  <div className="table-panel">
                    <div style={{ overflowX: 'auto' }}>
                      <table className="data-table">
                        <thead><tr>{result.columns.map(c => <th key={c}>{c}</th>)}</tr></thead>
                        <tbody>{result.data.slice(0, 100).map((row, i) => (
                          <tr key={i}>{result.columns.map(c => <td key={c}>{String(row[c] ?? '')}</td>)}</tr>
                        ))}</tbody>
                      </table>
                    </div>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-dim)', fontSize: 13 }}>Query returned no rows</div>
                )}
              </>
            )}

            {!result && !error && (
              <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-border-strong)' }}>
                <Database size={32} style={{ margin: '0 auto 8px' }} />
                <p style={{ fontSize: 13 }}>Write a query above and press Run or Ctrl+Enter</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
