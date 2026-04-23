import { useState, useEffect, useCallback } from 'react';
import { Activity, Search, Download, Check, X } from 'lucide-react';
import { auditList } from '../services/security';
import { getToken, getBusinessId } from '../services/auth';

function formatWhen(iso) {
  if (!iso) return '—';
  try { return new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' }); }
  catch { return iso.substring(0, 19); }
}

export default function AuditLog() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({ tool: '', search: '', success: '' });
  const [msg, setMsg] = useState('');

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.tool) params.tool = filters.tool;
      if (filters.search) params.search = filters.search;
      if (filters.success !== '') params.success = filters.success;
      params.limit = 200;
      const data = await auditList(params);
      setRows(data || []);
    } catch (e) { setMsg(`Failed: ${e.message}`); }
    setLoading(false);
  }, [filters]);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    const h = () => reload();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reload]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const downloadCsv = async () => {
    const t = getToken(); const b = getBusinessId();
    const h = {}; if (t) h['Authorization'] = `Bearer ${t}`; if (b) h['X-Business-Id'] = b;
    try {
      const r = await fetch('/api/audit/export?limit=10000', { headers: h });
      if (!r.ok) throw new Error(await r.text());
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = `audit_log_${Date.now()}.csv`; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { flash(`Export failed: ${e.message}`); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Audit log</h1>
          <p>Every action the agent or a user took in this business</p>
        </div>
        <button className="btn-ghost" onClick={downloadCsv}>
          <Download size={12} /> Export CSV
        </button>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: '#60a5fa' }}>{msg}</div>}

      <div style={{ display: 'flex', gap: 8, padding: '0 24px 8px', borderBottom: '1px solid #1e293b', alignItems: 'center', flexWrap: 'wrap' }}>
        <Search size={12} color="#64748b" />
        <input className="field-input" placeholder="Search input/output..." value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })} style={{ fontSize: 11, width: 220 }} />
        <input className="field-input" placeholder="Filter by tool (e.g. agent.send_email)" value={filters.tool}
          onChange={(e) => setFilters({ ...filters, tool: e.target.value })} style={{ fontSize: 11, width: 220 }} />
        <select className="field-select" value={filters.success}
          onChange={(e) => setFilters({ ...filters, success: e.target.value })} style={{ fontSize: 11 }}>
          <option value="">All outcomes</option>
          <option value="true">Success only</option>
          <option value="false">Failures only</option>
        </select>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {loading && rows.length === 0 ? (
          <p style={{ color: '#64748b', fontSize: 12, textAlign: 'center' }}>Loading…</p>
        ) : rows.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48, color: '#64748b' }}>
            <Activity size={36} style={{ opacity: 0.3, marginBottom: 12 }} />
            <p style={{ fontSize: 13 }}>No events match these filters.</p>
          </div>
        ) : (
          <div className="table-panel">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 150 }}>Time</th>
                  <th style={{ width: 160 }}>Tool</th>
                  <th style={{ width: 120 }}>Actor</th>
                  <th>Input</th>
                  <th>Output</th>
                  <th style={{ width: 70, textAlign: 'right' }}>Duration</th>
                  <th style={{ width: 50 }}>OK</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(r => (
                  <tr key={r.event_id}>
                    <td style={{ fontSize: 10, color: '#94a3b8' }}>{formatWhen(r.timestamp)}</td>
                    <td><code style={{ fontSize: 10 }}>{r.tool_name}</code></td>
                    <td style={{ fontSize: 11 }}>{r.actor_name || '—'}</td>
                    <td style={{ fontSize: 11, maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.input_summary}>
                      {r.input_summary}
                    </td>
                    <td style={{ fontSize: 11, maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.output_summary}>
                      {r.output_summary}
                    </td>
                    <td style={{ textAlign: 'right', fontSize: 10, color: '#64748b' }}>{r.duration_ms || 0}ms</td>
                    <td style={{ textAlign: 'center' }}>
                      {r.success ? <Check size={12} color="#22c55e" /> : <X size={12} color="#ef4444" />}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
