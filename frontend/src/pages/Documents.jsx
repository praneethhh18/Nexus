import { useState, useEffect, useCallback } from 'react';
import { FileText, Download, Trash2, Plus, X, FileType2, Sparkles } from 'lucide-react';
import { listDocTemplates, listDocuments, generateDocument, deleteDocument, downloadDocument } from '../services/documents';
import EmptyState from '../components/EmptyState';

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

// ── Variable hint dictionary ────────────────────────────────────────────────
// Maps known template variable names (or substring matches) to:
//   - placeholder: example value
//   - helper:      one-line guidance shown below the input
//   - type:        "text" | "long" | "email" | "date" | "number" | "money"
//   - required:    boolean
// Anything not listed falls back to the auto-derived label and a sensible
// default. Adding a new template variable here = no backend change needed.
const VAR_HINTS = {
  // Identity / parties
  client_name:        { placeholder: 'Acme Inc.',                  helper: 'The company you are sending this to.',                          required: true },
  client_company:     { placeholder: 'Acme Inc.',                  helper: 'Legal name of the client company.',                              required: true },
  client_contact:     { placeholder: 'Priya Sharma',               helper: 'Person at the client side this document is addressed to.' },
  recipient_name:     { placeholder: 'Priya Sharma',               helper: 'Person being addressed.',                                       required: true },
  candidate_name:     { placeholder: 'Aarav Mehta',                helper: 'Full legal name of the candidate.',                              required: true },
  vendor_name:        { placeholder: 'Acme Pvt Ltd',               helper: 'Your company name (the one selling).' },
  company_name:       { placeholder: 'NexusAgent Pvt Ltd',         helper: 'Your company name as it should appear on the document.',         required: true },
  // Roles / titles
  role:               { placeholder: 'Senior Software Engineer',   helper: 'Job title.',                                                    required: true },
  position:           { placeholder: 'Senior Software Engineer',   helper: 'Job title for the role.' },
  job_title:          { placeholder: 'Senior Software Engineer' },
  // Dates
  start_date:         { type: 'date',                              helper: 'When work / engagement begins.',                                 required: true },
  end_date:           { type: 'date',                              helper: 'Optional. Leave blank for open-ended.' },
  effective_date:     { type: 'date',                              helper: 'When this document takes effect.',                               required: true },
  expiry_date:        { type: 'date',                              helper: 'Optional. Leave blank for no expiry.' },
  date:               { type: 'date',                              helper: 'Document date.' },
  // Money
  amount:             { type: 'money',  placeholder: '50000',      helper: 'Amount in the contract currency. Numbers only.',                 required: true },
  fee:                { type: 'money',  placeholder: '50000',      helper: 'Total fee. Numbers only.' },
  budget:             { type: 'money',  placeholder: '500000',     helper: 'Total project budget. Numbers only.' },
  salary:             { type: 'money',  placeholder: '1800000',    helper: 'Annual CTC. Numbers only.',                                      required: true },
  hourly_rate:        { type: 'money',  placeholder: '4500',       helper: 'Per-hour rate. Numbers only.' },
  // Email
  client_email:       { type: 'email',  placeholder: 'priya@acme.com', helper: 'Used in the document header. Optional.' },
  recipient_email:    { type: 'email',  placeholder: 'priya@acme.com' },
  // Long-form
  summary:            { type: 'long',   placeholder: 'Two or three sentences describing the engagement.',                           required: true },
  scope:              { type: 'long',   placeholder: 'What is in scope. Be specific — vague scope causes scope creep.',             required: true },
  out_of_scope:       { type: 'long',   placeholder: 'What is explicitly NOT included. Equally important to write.' },
  objectives:         { type: 'long',   placeholder: 'One per line.\n• Cut response time by 30%\n• Cover top 5 use cases' },
  deliverables:       { type: 'long',   placeholder: 'One per line.\n• Discovery report\n• Working prototype\n• Final handoff doc' },
  milestones:         { type: 'long',   placeholder: 'One per line. Include rough dates.\n• Kickoff — Mon 5 May\n• Mid-review — Mon 19 May' },
  acceptance:         { type: 'long',   placeholder: 'How the client decides the work is complete.' },
  acceptance_criteria:{ type: 'long',   placeholder: 'How the client decides the work is complete.' },
  payment_terms:      { type: 'long',   placeholder: 'e.g. 50% on signing, 50% on delivery. Net-30. Bank: HDFC ··· 1234.',           required: true },
  compensation:       { type: 'long',   placeholder: 'Annual CTC, breakdown by component, bonus structure if any.',                  required: true },
  benefits:           { type: 'long',   placeholder: 'Health insurance, leave policy, equipment, etc. One per line.' },
  description:        { type: 'long',   placeholder: 'Free-form description.' },
  notes:              { type: 'long',   placeholder: 'Anything else worth recording on this document.' },
  background:         { type: 'long',   placeholder: 'Why is this document needed? What problem does it solve?' },
  // Numbers
  duration_weeks:     { type: 'number', placeholder: '8',           helper: 'Project duration in weeks. Numbers only.' },
  notice_period:      { type: 'number', placeholder: '60',          helper: 'Notice period in days.' },
};

const LONG_FALLBACK = /(summary|objectives|scope|deliverables|milestones|description|acceptance|payment_terms|compensation|benefits|background|notes)/i;

function varLabel(v) {
  return v.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function hintFor(varName) {
  const exact = VAR_HINTS[varName];
  if (exact) return exact;
  // Fuzzy match — find the first key that's a substring of the variable.
  const lower = varName.toLowerCase();
  for (const k of Object.keys(VAR_HINTS)) {
    if (lower.includes(k)) return VAR_HINTS[k];
  }
  return {};
}

function inputTypeFor(hint, varName) {
  if (hint.type) return hint.type;
  if (LONG_FALLBACK.test(varName)) return 'long';
  return 'text';
}


function GenerateForm({ template, onSubmit, onCancel }) {
  const [title, setTitle] = useState('');
  const [fmt, setFmt] = useState('docx');
  const [vars, setVars] = useState(() => Object.fromEntries(template.variables.map((v) => [v, ''])));
  const [busy, setBusy] = useState(false);
  const [showAll, setShowAll] = useState(false);

  const update = (k, v) => setVars((p) => ({ ...p, [k]: v }));

  // Categorise variables: required vs. optional (per the hint dictionary).
  const requiredVars = template.variables.filter((v) => hintFor(v).required);
  const optionalVars = template.variables.filter((v) => !hintFor(v).required);
  const visibleVars = showAll ? template.variables : [...requiredVars, ...optionalVars];

  const isFormValid = () => {
    if (!title.trim()) return false;
    return requiredVars.every((v) => (vars[v] || '').trim().length > 0);
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!isFormValid()) return;
    setBusy(true);
    try {
      await onSubmit({ template_key: template.key, title, variables: vars, format: fmt });
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit}>
      {/* Description block — explains what this template does. */}
      <div style={{
        padding: '10px 12px', marginBottom: 14,
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--r-md)',
        fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.55,
      }}>
        {template.description}
        <div style={{ marginTop: 6, fontSize: 11, color: 'var(--color-text-dim)' }}>
          {template.variables.length} field{template.variables.length === 1 ? '' : 's'}
          {requiredVars.length > 0 && <> · <strong style={{ color: 'var(--color-err)' }}>{requiredVars.length} required</strong></>}
        </div>
      </div>

      {/* Document title + format */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 10, marginBottom: 14 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 500 }}>
            Document title <span style={{ color: 'var(--color-err)' }}>*</span>
          </label>
          <input className="field-input" autoFocus required value={title} onChange={(e) => setTitle(e.target.value)} placeholder={`e.g. Acme — ${template.name}`} maxLength={200} />
          <span style={{ fontSize: 10.5, color: 'var(--color-text-dim)' }}>Used as the file name.</span>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          <label style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 500 }}>Format</label>
          <select className="field-select" value={fmt} onChange={(e) => setFmt(e.target.value)} style={{ width: '100%' }}>
            <option value="docx">Word (.docx)</option>
            <option value="pdf">PDF</option>
          </select>
          <span style={{ fontSize: 10.5, color: 'var(--color-text-dim)' }}>Word stays editable; PDF is final.</span>
        </div>
      </div>

      {/* Template variables — grouped by required first, then optional */}
      <div className="divider-h">Fill in the template</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        {visibleVars.map((v) => {
          const hint = hintFor(v);
          const type = inputTypeFor(hint, v);
          const label = hint.label || varLabel(v);
          const placeholder = hint.placeholder || '';
          const helper = hint.helper || '';
          const isLong = type === 'long';
          const value = vars[v] || '';

          return (
            <div key={v} style={{
              gridColumn: isLong ? '1 / -1' : 'auto',
              display: 'flex', flexDirection: 'column', gap: 4,
            }}>
              <label style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 500 }}>
                {label}
                {hint.required && <span style={{ color: 'var(--color-err)', marginLeft: 4 }}>*</span>}
              </label>
              {isLong ? (
                <textarea
                  className="field-input"
                  rows={3}
                  value={value}
                  onChange={(e) => update(v, e.target.value)}
                  maxLength={4000}
                  placeholder={placeholder}
                  required={hint.required}
                />
              ) : (
                <input
                  className="field-input"
                  type={type === 'email' ? 'email' : type === 'date' ? 'date' : (type === 'money' || type === 'number') ? 'number' : 'text'}
                  step={type === 'money' ? '0.01' : type === 'number' ? '1' : undefined}
                  min={type === 'money' || type === 'number' ? 0 : undefined}
                  value={value}
                  onChange={(e) => update(v, e.target.value)}
                  maxLength={400}
                  placeholder={placeholder}
                  required={hint.required}
                />
              )}
              {helper && <span style={{ fontSize: 10.5, color: 'var(--color-text-dim)', lineHeight: 1.45 }}>{helper}</span>}
            </div>
          );
        })}
      </div>

      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary" disabled={busy || !isFormValid()}>
          {busy ? 'Generating…' : 'Generate'}
        </button>
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
            <EmptyState
              icon={FileType2}
              title="No documents yet"
              description="Pick a template above to generate your first document, or upload a PDF to the knowledge base to start asking questions about it."
              size="sm"
              minHeight={180}
            />
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
