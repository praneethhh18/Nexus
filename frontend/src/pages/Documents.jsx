import { useState, useEffect, useCallback } from 'react';
import { FileText, Download, Trash2, Plus, X, FileType2, Sparkles } from 'lucide-react';
import { listDocTemplates, listDocuments, generateDocument, deleteDocument, downloadDocument } from '../services/documents';

function Modal({ title, onClose, children }) {
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 12,
        padding: 20, width: 560, maxHeight: '92vh', overflow: 'auto',
        boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--color-text)', margin: 0 }}>{title}</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer' }}><X size={16} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

// Convert a variable name to a readable label
function varLabel(v) {
  return v.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function varIsLong(v) {
  return /(summary|objectives|scope|deliverables|milestones|description|acceptance|payment_terms|compensation)/i.test(v);
}

function GenerateForm({ template, onSubmit, onCancel }) {
  const [title, setTitle] = useState('');
  const [fmt, setFmt] = useState('docx');
  const [vars, setVars] = useState(() => Object.fromEntries(template.variables.map((v) => [v, ''])));
  const [busy, setBusy] = useState(false);

  const update = (k, v) => setVars((p) => ({ ...p, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setBusy(true);
    try {
      await onSubmit({ template_key: template.key, title, variables: vars, format: fmt });
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit}>
      <p style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 10 }}>{template.description}</p>
      <div style={{ marginBottom: 10 }}>
        <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Document title *</label>
        <input className="field-input" autoFocus required value={title} onChange={(e) => setTitle(e.target.value)} placeholder="e.g. Acme Proposal — Q2 engagement" maxLength={200} />
      </div>
      <div style={{ marginBottom: 10 }}>
        <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Format</label>
        <select className="field-select" value={fmt} onChange={(e) => setFmt(e.target.value)} style={{ width: '100%' }}>
          <option value="docx">Word (.docx)</option>
          <option value="pdf">PDF</option>
        </select>
      </div>
      <div style={{ paddingTop: 10, marginTop: 10, borderTop: '1px solid var(--color-surface-2)' }}>
        <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
          Template variables
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          {template.variables.map((v) => (
            <div key={v} style={{ gridColumn: varIsLong(v) ? '1 / -1' : 'auto' }}>
              <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-dim)', marginBottom: 4 }}>{varLabel(v)}</label>
              {varIsLong(v) ? (
                <textarea className="field-input" rows={3} value={vars[v] || ''} onChange={(e) => update(v, e.target.value)} maxLength={4000} placeholder={v.includes('bullets') || v.includes('deliverables') || v.includes('milestones') ? 'One item per line' : ''} />
              ) : (
                <input className="field-input" value={vars[v] || ''} onChange={(e) => update(v, e.target.value)} maxLength={400} />
              )}
            </div>
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 14 }}>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary" disabled={busy}>{busy ? 'Generating...' : 'Generate'}</button>
      </div>
    </form>
  );
}

export default function Documents() {
  const [templates, setTemplates] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [modal, setModal] = useState(null);
  const [msg, setMsg] = useState('');

  const reload = useCallback(async () => {
    try {
      const [t, d] = await Promise.all([listDocTemplates(), listDocuments()]);
      setTemplates(t.map((x) => ({ ...x })));
      setDocuments(d);
    } catch (e) { setMsg(`Failed to load: ${e.message}`); }
  }, []);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    const h = () => reload();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reload]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const handleGenerate = async (body) => {
    try {
      const doc = await generateDocument(body);
      setModal(null);
      flash(`Generated ${doc.filename}`);
      reload();
      // Auto-download for convenience
      try { await downloadDocument(doc.id, doc.filename); } catch {}
    } catch (e) { alert(`Failed: ${e.message}`); }
  };

  const handleDelete = async (d) => {
    if (!confirm(`Delete "${d.title}"?`)) return;
    try { await deleteDocument(d.id); flash('Deleted'); reload(); }
    catch (e) { flash(`Failed: ${e.message}`); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <h1>Documents</h1>
        <p>Generate proposals, SOWs, contracts, and offer letters from templates</p>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      <div className="page-body">
        {/* Templates */}
        <div>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '0 0 10px' }}>
            <Sparkles size={15} color="#a78bfa" /> Templates
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 10 }}>
            {templates.map((t) => (
              <div key={t.key} className="panel" style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <FileType2 size={18} color="var(--color-info)" />
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>{t.name}</span>
                </div>
                <p style={{ fontSize: 11, color: 'var(--color-text-muted)', margin: 0, minHeight: 32 }}>{t.description}</p>
                <div style={{ fontSize: 9, color: 'var(--color-text-dim)' }}>{t.variables.length} fields</div>
                <button className="btn-primary" style={{ marginTop: 'auto' }} onClick={() => setModal({ template: t })}>
                  <Plus size={12} /> Generate
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Generated documents */}
        <div style={{ marginTop: 20 }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '0 0 10px' }}>
            <FileText size={15} color="var(--color-ok)" /> Recent documents
          </h3>
          {documents.length === 0 ? (
            <p style={{ fontSize: 12, color: 'var(--color-text-dim)', textAlign: 'center', padding: 32 }}>
              No documents generated yet. Pick a template above to create your first one.
            </p>
          ) : (
            <div className="table-panel">
              <table className="data-table">
                <thead>
                  <tr><th>Title</th><th>Template</th><th>Format</th><th>Created</th><th style={{ width: 120 }}></th></tr>
                </thead>
                <tbody>
                  {documents.map((d) => (
                    <tr key={d.id}>
                      <td style={{ fontWeight: 500 }}>{d.title}</td>
                      <td style={{ textTransform: 'capitalize' }}>{d.template_key.replace('_', ' ')}</td>
                      <td><span style={{ fontSize: 9, padding: '2px 8px', borderRadius: 10, background: 'var(--color-surface-1)', color: 'var(--color-text-muted)', textTransform: 'uppercase' }}>{d.format}</span></td>
                      <td>{d.created_at?.substring(0, 16)}</td>
                      <td style={{ display: 'flex', gap: 4 }}>
                        <button className="btn-ghost" style={{ padding: 4 }} onClick={() => downloadDocument(d.id, d.filename).catch((e) => flash(e.message))} title="Download"><Download size={11} /></button>
                        <button className="btn-ghost" style={{ padding: 4, color: 'var(--color-err)' }} onClick={() => handleDelete(d)}><Trash2 size={11} /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {modal?.template && (
        <Modal title={`New ${modal.template.name}`} onClose={() => setModal(null)}>
          <GenerateForm template={modal.template} onSubmit={handleGenerate} onCancel={() => setModal(null)} />
        </Modal>
      )}
    </div>
  );
}
