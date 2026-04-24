/**
 * CSV/Excel import wizard for contacts / tasks / invoices.
 *
 *  Upload → Preview + column mapping → Commit
 *
 * Backend does two round trips:
 *  - POST /api/entity-import/preview   (file + entity_type) → suggested mapping
 *  - POST /api/entity-import/commit    (session_id + final mapping) → stats
 *
 * The file is stashed server-side with a 15-min TTL; the frontend never needs
 * to re-upload once the session_id is in hand.
 */
import { useState, useRef } from 'react';
import { Upload, X, ArrowRight, CheckCircle2, AlertTriangle, Loader2 } from 'lucide-react';
import { getToken, getBusinessId } from '../services/auth';

function headers() {
  const h = {};
  const t = getToken();
  if (t) h['Authorization'] = `Bearer ${t}`;
  const b = getBusinessId();
  if (b) h['X-Business-Id'] = b;
  return h;
}

const ENTITY_LABELS = {
  contact: 'Contacts',
  task:    'Tasks',
  invoice: 'Invoices',
};

export default function EntityImportWizard({ defaultEntityType = 'contact', onClose, onDone }) {
  const [entityType, setEntityType] = useState(defaultEntityType);
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [mapping, setMapping] = useState({});
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const fileRef = useRef(null);

  const doPreview = async () => {
    if (!file) return;
    setBusy(true); setErr('');
    try {
      const fd = new FormData();
      fd.append('file', file);
      const res = await fetch(
        `/api/entity-import/preview?entity_type=${encodeURIComponent(entityType)}`,
        { method: 'POST', headers: headers(), body: fd },
      );
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setPreview(data);
      setMapping(data.suggested_mapping || {});
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const doCommit = async () => {
    if (!preview) return;
    setBusy(true); setErr('');
    try {
      const res = await fetch('/api/entity-import/commit', {
        method: 'POST',
        headers: { ...headers(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: preview.session_id,
          entity_type: entityType,
          mapping,
        }),
      });
      if (!res.ok) throw new Error(await res.text());
      const r = await res.json();
      setResult(r);
      onDone?.(r);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  };

  const step = result ? 3 : preview ? 2 : 1;

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
        zIndex: 400, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 24,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)',
          borderRadius: 'var(--r-lg)', padding: 22,
          width: 'min(640px, 96vw)', maxHeight: '88vh',
          overflow: 'auto', boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <h3 style={{ margin: 0, fontSize: 16, color: 'var(--color-text)' }}>
            Import CSV / Excel
          </h3>
          <button onClick={onClose} className="btn-ghost"><X size={14} /></button>
        </div>

        {/* Step indicator */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 18 }}>
          {[1, 2, 3].map(s => (
            <div key={s} style={{
              flex: 1, height: 3, borderRadius: 2,
              background: s <= step ? 'var(--color-accent)' : 'var(--color-surface-2)',
            }} />
          ))}
        </div>

        {err && (
          <div style={{
            padding: 10, marginBottom: 12, borderRadius: 'var(--r-sm)',
            background: 'color-mix(in srgb, var(--color-err) 10%, transparent)',
            color: 'var(--color-err)', fontSize: 12,
          }}>
            <AlertTriangle size={12} style={{ verticalAlign: 'middle' }} /> {err}
          </div>
        )}

        {/* STEP 1: pick file + entity */}
        {!preview && !result && (
          <>
            <label style={{ display: 'block', fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 6 }}>
              What are you importing?
            </label>
            <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
              {Object.entries(ENTITY_LABELS).map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setEntityType(key)}
                  className={entityType === key ? 'btn-primary' : 'btn-ghost'}
                  style={{ fontSize: 12 }}
                >
                  {label}
                </button>
              ))}
            </div>

            <div
              onClick={() => fileRef.current?.click()}
              style={{
                padding: 28, border: '2px dashed var(--color-surface-2)',
                borderRadius: 'var(--r-md)', textAlign: 'center', cursor: 'pointer',
                color: 'var(--color-text-dim)',
              }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                const f = e.dataTransfer.files?.[0];
                if (f) setFile(f);
              }}
            >
              <Upload size={22} style={{ marginBottom: 6 }} />
              <div style={{ fontSize: 13, color: 'var(--color-text)' }}>
                {file ? file.name : 'Click or drop a CSV / XLSX file'}
              </div>
              <div style={{ fontSize: 10 }}>Max 20 MB</div>
              <input
                ref={fileRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                style={{ display: 'none' }}
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>

            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
              <button onClick={onClose} className="btn-ghost">Cancel</button>
              <button
                onClick={doPreview}
                disabled={!file || busy}
                className="btn-primary"
              >
                {busy ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <ArrowRight size={12} />}
                Preview
              </button>
            </div>
          </>
        )}

        {/* STEP 2: mapping */}
        {preview && !result && (
          <>
            <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginBottom: 10 }}>
              Detected <strong>{preview.total_rows}</strong> row{preview.total_rows === 1 ? '' : 's'} across
              {' '}<strong>{preview.source_columns.length}</strong> columns. Map each target field to a column in your file — we pre-filled best guesses.
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 14 }}>
              {Object.entries(preview.target_fields).map(([target, meta]) => (
                <div key={target} style={{
                  display: 'grid', gridTemplateColumns: '1fr 1fr',
                  gap: 10, alignItems: 'center',
                  padding: '6px 10px', borderRadius: 'var(--r-sm)',
                  background: 'var(--color-surface-1)',
                }}>
                  <div>
                    <div style={{ fontSize: 12, color: 'var(--color-text)' }}>
                      {meta.label || target}
                      {meta.required && <span style={{ color: 'var(--color-err)', marginLeft: 4 }}>*</span>}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>
                      <code>{target}</code>
                    </div>
                  </div>
                  <select
                    className="field-select"
                    value={mapping[target] || ''}
                    onChange={(e) => setMapping(m => ({ ...m, [target]: e.target.value }))}
                    style={{ fontSize: 11 }}
                  >
                    <option value="">— skip —</option>
                    {preview.source_columns.map(c => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              ))}
            </div>

            {preview.sample_rows?.length > 0 && (
              <details style={{ marginBottom: 14, fontSize: 11, color: 'var(--color-text-dim)' }}>
                <summary style={{ cursor: 'pointer' }}>Peek at first rows</summary>
                <div style={{ marginTop: 6, overflowX: 'auto' }}>
                  <table className="data-table" style={{ fontSize: 10 }}>
                    <thead><tr>{preview.source_columns.map(c => <th key={c}>{c}</th>)}</tr></thead>
                    <tbody>
                      {preview.sample_rows.map((r, i) => (
                        <tr key={i}>
                          {preview.source_columns.map(c => <td key={c}>{String(r[c] ?? '')}</td>)}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            )}

            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button onClick={() => { setPreview(null); setFile(null); }} className="btn-ghost">
                Start over
              </button>
              <button onClick={doCommit} disabled={busy} className="btn-primary">
                {busy
                  ? <><Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> Importing…</>
                  : <>Import {preview.total_rows} row{preview.total_rows === 1 ? '' : 's'} <ArrowRight size={12} /></>}
              </button>
            </div>
          </>
        )}

        {/* STEP 3: result */}
        {result && (
          <>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14,
              color: result.inserted > 0 ? 'var(--color-ok)' : 'var(--color-warn)',
            }}>
              <CheckCircle2 size={20} />
              <div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>
                  Imported {result.inserted} of {result.total}
                </div>
                {result.skipped > 0 && (
                  <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
                    {result.skipped} row{result.skipped === 1 ? '' : 's'} skipped
                  </div>
                )}
              </div>
            </div>

            {result.errors?.length > 0 && (
              <details style={{ marginBottom: 14 }}>
                <summary style={{ fontSize: 11, color: 'var(--color-err)', cursor: 'pointer' }}>
                  {result.errors.length} error{result.errors.length === 1 ? '' : 's'} (click to expand)
                </summary>
                <ul style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 4, paddingLeft: 18 }}>
                  {result.errors.map((e, i) => <li key={i}>{e}</li>)}
                </ul>
              </details>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={onClose} className="btn-primary">Done</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
