import { useState, useEffect } from 'react';
import { FileText, Download, Loader } from 'lucide-react';
import { generateReport, getReports, downloadReport } from '../services/api';
import EmptyState from '../components/EmptyState';

export default function Reports() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [reports, setReports] = useState([]);
  const [msg, setMsg] = useState('');

  useEffect(() => { getReports().then(setReports).catch(() => {}); }, []);

  const generate = async () => {
    if (!query.trim()) return;
    setLoading(true); setMsg('');
    try { const r = await generateReport(query); setMsg(`Report generated: ${r.filename}`); getReports().then(setReports); }
    catch (e) { setMsg(`Error: ${e.message}`); }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header"><h1>Reports</h1><p>Generate professional PDF reports from your data</p></div>
      <div className="page-body">
        <div className="panel">
          <h3>Generate New Report</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            <input className="field-input" value={query} onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && generate()} placeholder="e.g. Regional sales performance for Q3 2025" />
            <button className="btn-primary" onClick={generate} disabled={loading || !query.trim()}>
              {loading ? <Loader size={14} className="animate-spin" /> : <FileText size={14} />}
              {loading ? 'Generating...' : 'Generate'}
            </button>
          </div>
          {msg && <p style={{ fontSize: 12, color: 'var(--color-info)', marginTop: 8 }}>{msg}</p>}
        </div>

        <h3 style={{ fontSize: 13, fontWeight: 600, color: 'white', marginBottom: 10 }}>Recent Reports</h3>
        {reports.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No reports yet"
            description="Type a natural-language request above — totals, trends, comparisons — and a narrated PDF will appear here."
            size="sm"
            minHeight={180}
          />
        ) : reports.map((r, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: 12, marginBottom: 6 }} className="panel">
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 36, height: 36, borderRadius: 8, background: '#581c8720', border: '1px solid #581c8730', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <FileText size={16} color="#a78bfa" />
              </div>
              <div>
                <p style={{ fontSize: 13, color: 'white', fontWeight: 500 }}>{r.name}</p>
                <p style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>{r.size_kb} KB &middot; {r.modified}</p>
              </div>
            </div>
            <button
              className="btn-ghost"
              onClick={async () => {
                try { await downloadReport(r.name); }
                catch (err) { alert(`Download failed: ${err.message}`); }
              }}
            >
              <Download size={13} /> Download
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
