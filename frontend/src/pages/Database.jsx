import { useState, useEffect } from 'react';
import { Database as DbIcon, Upload, Table } from 'lucide-react';
import { getTables, getTableDetail, importData, previewImport } from '../services/api';

export default function Database() {
  const [tables, setTables] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [tab, setTab] = useState('browse');
  const [importFile, setImportFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [importName, setImportName] = useState('');
  const [importing, setImporting] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => { getTables().then(setTables).catch(() => {}); }, []);

  const loadDetail = async (name) => { setSelected(name); setDetail(await getTableDetail(name)); };

  const handleFile = async (e) => {
    const f = e.target.files[0]; if (!f) return;
    setImportFile(f);
    try { const p = await previewImport(f); setPreview(p); setImportName(p.suggested_table_name || ''); }
    catch (err) { setMsg(`Error: ${err.message}`); }
  };

  const handleImport = async () => {
    if (!importFile || !importName) return;
    setImporting(true);
    try { const res = await importData(importFile, importName); setMsg(`Imported ${res.rows_imported} rows into ${res.table_name}`); getTables().then(setTables); setPreview(null); }
    catch (err) { setMsg(`Failed: ${err.message}`); }
    setImporting(false);
  };

  const dataTables = tables.filter(t => !t.is_system);
  const sysTables = tables.filter(t => t.is_system);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header"><h1>Database Explorer</h1><p>Browse tables, view data, and import datasets</p></div>

      <div className="page-body">
        <div className="stat-grid">
          {[{ l: 'Data Tables', v: dataTables.length }, { l: 'System Tables', v: sysTables.length },
            { l: 'Total Rows', v: dataTables.reduce((s, t) => s + t.row_count, 0).toLocaleString() },
            { l: 'Columns', v: dataTables.reduce((s, t) => s + t.column_count, 0) }
          ].map((s, i) => <div key={i} className="stat-card"><div className="value">{s.v}</div><div className="label">{s.l}</div></div>)}
        </div>

        <div style={{ display: 'flex', gap: 6, marginBottom: 12 }}>
          {['browse', 'import'].map(t => (
            <button key={t} onClick={() => setTab(t)} className={tab === t ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 12 }}>
              {t === 'browse' ? 'Browse Tables' : 'Import Data'}
            </button>
          ))}
        </div>

        {tab === 'browse' ? (
          <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: 16, height: 'calc(100vh - 280px)' }}>
            <div style={{ overflowY: 'auto' }}>
              <div className="conv-label">Data Tables</div>
              {dataTables.map(t => (
                <div key={t.name} onClick={() => loadDetail(t.name)}
                  className={`conv-item ${selected === t.name ? 'active' : ''}`}
                  style={selected === t.name ? { background: 'color-mix(in srgb, var(--color-accent) 8%, transparent)', color: 'var(--color-info)' } : {}}>
                  <Table size={14} /><span style={{ flex: 1 }}>{t.name}</span><span style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{t.row_count}</span>
                </div>
              ))}
              {sysTables.length > 0 && <>
                <div className="conv-label" style={{ marginTop: 12 }}>System</div>
                {sysTables.map(t => (
                  <div key={t.name} onClick={() => loadDetail(t.name)} className="conv-item" style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.name}</span>
                    <span style={{ fontSize: 10 }}>{t.row_count}</span>
                  </div>
                ))}
              </>}
            </div>
            <div style={{ overflowY: 'auto' }}>
              {detail ? (<>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                  <h3 style={{ fontSize: 14, fontWeight: 600, color: 'white' }}>{detail.name}</h3>
                  <span style={{ fontSize: 12, color: 'var(--color-text-dim)' }}>{detail.row_count.toLocaleString()} rows</span>
                </div>
                <div className="table-panel">
                  <div className="table-panel-header">Schema</div>
                  <table className="data-table">
                    <thead><tr><th>Column</th><th>Type</th><th>PK</th></tr></thead>
                    <tbody>{detail.columns.map((c, i) => (
                      <tr key={i}><td style={{ fontWeight: 500 }}>{c.name}</td><td>{c.type || 'TEXT'}</td><td style={{ color: 'var(--color-info)' }}>{c.pk > 0 ? 'PK' : ''}</td></tr>
                    ))}</tbody>
                  </table>
                </div>
                {detail.data?.length > 0 && (
                  <div className="table-panel">
                    <div className="table-panel-header">Data Preview ({detail.data.length} rows)</div>
                    <div style={{ overflowX: 'auto' }}>
                      <table className="data-table">
                        <thead><tr>{Object.keys(detail.data[0]).map(k => <th key={k}>{k}</th>)}</tr></thead>
                        <tbody>{detail.data.slice(0, 30).map((row, i) => (
                          <tr key={i}>{Object.values(row).map((v, j) => <td key={j}>{String(v ?? '')}</td>)}</tr>
                        ))}</tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--color-text-dim)', fontSize: 13 }}>
                  <DbIcon size={18} style={{ marginRight: 8 }} /> Select a table to explore
                </div>
              )}
            </div>
          </div>
        ) : (
          <div style={{ maxWidth: 520, margin: '0 auto' }}>
            <div className="upload-zone">
              <Upload size={28} color="var(--color-text-dim)" style={{ margin: '0 auto 10px' }} />
              <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginBottom: 10 }}>Drop a CSV or Excel file, or click to browse</p>
              <input type="file" accept=".csv,.xlsx,.xls" onChange={handleFile} style={{ fontSize: 12, color: 'var(--color-text-muted)' }} />
            </div>
            {preview && (
              <div style={{ marginTop: 16 }}>
                <div className="panel"><p style={{ fontSize: 13, color: 'white', fontWeight: 500 }}>{importFile?.name}</p><p style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>{preview.total_rows?.toLocaleString()} rows, {preview.total_columns} columns</p></div>
                <div style={{ marginBottom: 10 }}>
                  <label style={{ fontSize: 11, color: 'var(--color-text-dim)', display: 'block', marginBottom: 4 }}>Table Name</label>
                  <input className="field-input" value={importName} onChange={e => setImportName(e.target.value)} />
                </div>
                <button className="btn-primary" onClick={handleImport} disabled={importing} style={{ width: '100%', justifyContent: 'center' }}>
                  {importing ? 'Importing...' : 'Import to Database'}
                </button>
              </div>
            )}
            {msg && <div className="panel" style={{ marginTop: 12, color: 'var(--color-info)', fontSize: 13 }}>{msg}</div>}
          </div>
        )}
      </div>
    </div>
  );
}
