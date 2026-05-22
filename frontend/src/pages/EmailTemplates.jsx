/**
 * Email Templates, manage reusable subject/body presets with {{variable}}
 * substitution. Pairs with the send_email_from_template agent tool so the
 * same templates work whether you compose by chat or by hand.
 */
import { useState, useEffect, useCallback } from 'react';
import { Mail, Plus, Trash2, Edit3, X, Eye, Code, Save, Sparkles, AlertCircle } from 'lucide-react';
import {
  listEmailTemplates, createEmailTemplate, updateEmailTemplate,
  deleteEmailTemplate, renderEmailTemplate,
} from '../services/email_templates';
import EmptyState from '../components/EmptyState';

const VAR_RE = /\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}/g;

function extractVars(subject, body) {
  const seen = new Set();
  const out = [];
  for (const text of [subject || '', body || '']) {
    for (const m of text.matchAll(VAR_RE)) {
      if (!seen.has(m[1])) { seen.add(m[1]); out.push(m[1]); }
    }
  }
  return out;
}

export default function EmailTemplates() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editor, setEditor]   = useState(null);          // template being edited (or 'new')
  const [preview, setPreview] = useState(null);          // template being previewed
  const [msg, setMsg]         = useState('');

  const flash = (t) => { setMsg(t); setTimeout(() => setMsg(''), 2500); };

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setTemplates(await listEmailTemplates());
    } catch (e) {
      flash(`Failed to load: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { reload(); }, [reload]);

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 12,
          background: 'color-mix(in srgb, var(--color-info) 14%, transparent)',
          color: 'var(--color-info)', display: 'flex',
          alignItems: 'center', justifyContent: 'center',
        }}>
          <Mail size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h1 style={{ fontSize: 22, color: 'var(--color-text)', margin: 0 }}>
            Email Templates
          </h1>
          <p style={{ fontSize: 13, color: 'var(--color-text-dim)', margin: '4px 0 0' }}>
            Reusable subject + body presets with{' '}
            <code style={{ background: 'var(--color-surface-2)', padding: '1px 5px', borderRadius: 3, fontSize: 11 }}>
              {'{{variable}}'}
            </code>{' '}
            substitution. Used by the agent's <code>send_email_from_template</code> tool.
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setEditor({ id: null, name: '', subject: '', body: '' })}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
        >
          <Plus size={14} /> New template
        </button>
      </header>

      {msg && (
        <div style={{
          padding: '8px 14px', marginBottom: 16, borderRadius: 8,
          background: 'color-mix(in srgb, var(--color-info) 10%, transparent)',
          color: 'var(--color-info)', fontSize: 13,
          display: 'inline-flex', alignItems: 'center', gap: 8,
        }}>
          <AlertCircle size={14} /> {msg}
        </div>
      )}

      {loading ? (
        <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-dim)' }}>
          Loading templates…
        </div>
      ) : templates.length === 0 ? (
        <EmptyState
          icon={Mail}
          title="No email templates yet"
          description="Templates let your agents send polished emails without redrafting copy each time. Use {{first_name}}, {{amount}}, etc. as placeholders."
          primaryLabel="Create your first template"
          onPrimary={() => setEditor({ id: null, name: '', subject: '', body: '' })}
        />
      ) : (
        <div style={{
          display: 'grid', gap: 12,
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        }}>
          {templates.map((t) => (
            <TemplateCard
              key={t.id} template={t}
              onEdit={() => setEditor(t)}
              onPreview={() => setPreview(t)}
              onDelete={async () => {
                if (!window.confirm(`Delete template "${t.name}"?`)) return;
                try {
                  await deleteEmailTemplate(t.id);
                  flash('Deleted');
                  reload();
                } catch (e) { flash(`Delete failed: ${e.message}`); }
              }}
            />
          ))}
        </div>
      )}

      {editor && (
        <EditorModal
          initial={editor}
          onClose={() => setEditor(null)}
          onSave={async (data) => {
            try {
              if (editor.id) {
                await updateEmailTemplate(editor.id, data);
                flash(`Updated "${data.name}"`);
              } else {
                await createEmailTemplate(data);
                flash(`Created "${data.name}"`);
              }
              setEditor(null);
              reload();
            } catch (e) { flash(`Save failed: ${e.message}`); }
          }}
        />
      )}

      {preview && (
        <PreviewModal
          template={preview}
          onClose={() => setPreview(null)}
        />
      )}
    </div>
  );
}

// ── Template card ──────────────────────────────────────────────────────────
function TemplateCard({ template, onEdit, onPreview, onDelete }) {
  const vars = template.variables || [];
  return (
    <div style={{
      background: 'var(--color-surface-1)',
      border: '1px solid var(--color-border-strong)',
      borderRadius: 12, padding: 16,
      display: 'flex', flexDirection: 'column', gap: 8,
      transition: 'border-color 0.15s ease',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: 14, fontWeight: 600, color: 'var(--color-text)',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>{template.name}</div>
          <div style={{
            fontSize: 11, color: 'var(--color-text-dim)', marginTop: 2,
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>{template.subject}</div>
        </div>
        <button className="btn-ghost" onClick={onPreview} title="Preview" style={{ padding: 6 }}>
          <Eye size={13} />
        </button>
        <button className="btn-ghost" onClick={onEdit} title="Edit" style={{ padding: 6 }}>
          <Edit3 size={13} />
        </button>
        <button className="btn-ghost" onClick={onDelete} title="Delete"
                style={{ padding: 6, color: 'var(--color-err)' }}>
          <Trash2 size={13} />
        </button>
      </div>
      <div style={{
        fontSize: 11, color: 'var(--color-text-dim)',
        display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical',
        overflow: 'hidden', lineHeight: 1.5,
      }}>
        {(template.preview || '').slice(0, 200)}
      </div>
      {vars.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
          {vars.map(v => (
            <span key={v} style={{
              fontSize: 10, padding: '2px 7px', borderRadius: 999,
              background: 'color-mix(in srgb, var(--color-warn) 12%, transparent)',
              color: 'var(--color-warn)', fontFamily: 'var(--font-mono, monospace)',
            }}>{`{{${v}}}`}</span>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Editor modal ───────────────────────────────────────────────────────────
function EditorModal({ initial, onClose, onSave }) {
  const [name, setName]     = useState(initial.name || '');
  const [subject, setSubj]  = useState(initial.subject || '');
  const [body, setBody]     = useState(initial.body || '');
  const [saving, setSaving] = useState(false);

  const detected = extractVars(subject, body);

  const submit = async (e) => {
    e.preventDefault();
    if (!name.trim() || !subject.trim() || !body.trim()) return;
    setSaving(true);
    try {
      await onSave({ name: name.trim(), subject: subject.trim(), body: body.trim() });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title={initial.id ? 'Edit template' : 'New email template'} onClose={onClose} wide>
      <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <Field label="Name (internal, what you'll search by)">
          <input
            className="field-input" value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. invoice_reminder, welcome_email, monsoon_promo"
            maxLength={80} autoFocus
          />
        </Field>
        <Field label={<>Subject <span style={{ color: 'var(--color-text-dim)', fontSize: 11 }}>{'(supports {{variable}} placeholders)'}</span></>}>
          <input
            className="field-input" value={subject}
            onChange={(e) => setSubj(e.target.value)}
            placeholder="e.g. Invoice {{invoice_id}} overdue, Rs.{{amount}}"
            maxLength={200}
          />
        </Field>
        <Field label="Body">
          <textarea
            className="field-input" value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder={`e.g.\nHi {{first_name}},\n\nINV-{{invoice_id}} for Rs.{{amount}} was due {{due_date}}. Could you confirm payment status?\n\nThanks!`}
            rows={10} maxLength={10000}
            style={{ fontFamily: 'var(--font-mono, monospace)', fontSize: 13, resize: 'vertical' }}
          />
        </Field>
        {detected.length > 0 && (
          <div style={{
            padding: '8px 12px', borderRadius: 8,
            background: 'color-mix(in srgb, var(--color-warn) 10%, transparent)',
            border: '1px solid color-mix(in srgb, var(--color-warn) 25%, transparent)',
            fontSize: 12, color: 'var(--color-text)',
          }}>
            <Code size={12} style={{ verticalAlign: -2, marginRight: 4 }} />
            <strong>Variables detected:</strong>{' '}
            {detected.map((v, i) => (
              <span key={v}>
                <code style={{ background: 'var(--color-surface-2)', padding: '1px 5px', borderRadius: 3 }}>
                  {`{{${v}}}`}
                </code>
                {i < detected.length - 1 ? ', ' : ''}
              </span>
            ))}
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 4 }}>
              The agent will be told these need values at send time.
            </div>
          </div>
        )}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button type="button" className="btn-ghost" onClick={onClose}>Cancel</button>
          <button
            type="submit" className="btn btn-primary"
            disabled={saving || !name.trim() || !subject.trim() || !body.trim()}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
          >
            <Save size={13} /> {saving ? 'Saving…' : (initial.id ? 'Save changes' : 'Create template')}
          </button>
        </div>
      </form>
    </Modal>
  );
}

// ── Preview modal (variable filling + render) ──────────────────────────────
function PreviewModal({ template, onClose }) {
  const [vars, setVars]       = useState({});
  const [rendered, setRendered] = useState(null);
  const [loading, setLoading]   = useState(false);
  const [err, setErr]           = useState('');

  const tplVars = template.variables || [];

  const updateVar = (k, v) => setVars(p => ({ ...p, [k]: v }));

  const doRender = async () => {
    setLoading(true); setErr('');
    try {
      setRendered(await renderEmailTemplate(template.id, vars));
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  };

  return (
    <Modal title={`Preview · ${template.name}`} onClose={onClose} wide>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {tplVars.length > 0 && (
          <div>
            <div style={{ fontSize: 12, color: 'var(--color-text-dim)', marginBottom: 8 }}>
              Fill in the variables to preview how the email will look:
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: 10 }}>
              {tplVars.map(v => (
                <div key={v}>
                  <label style={{ fontSize: 11, color: 'var(--color-text-dim)', display: 'block', marginBottom: 4 }}>
                    <code style={{ background: 'var(--color-surface-2)', padding: '1px 5px', borderRadius: 3 }}>
                      {`{{${v}}}`}
                    </code>
                  </label>
                  <input
                    className="field-input"
                    value={vars[v] || ''}
                    onChange={(e) => updateVar(v, e.target.value)}
                    placeholder={`Value for ${v}`}
                  />
                </div>
              ))}
            </div>
            <button
              type="button" className="btn btn-primary"
              onClick={doRender} disabled={loading}
              style={{ marginTop: 10, display: 'inline-flex', alignItems: 'center', gap: 6 }}
            >
              <Sparkles size={13} /> {loading ? 'Rendering…' : 'Render preview'}
            </button>
          </div>
        )}

        {err && (
          <div style={{
            padding: '8px 12px', borderRadius: 8,
            background: 'color-mix(in srgb, var(--color-err) 10%, transparent)',
            color: 'var(--color-err)', fontSize: 12,
          }}>{err}</div>
        )}

        <div style={{
          background: 'var(--color-surface-2)', borderRadius: 8, padding: 14,
          border: '1px solid var(--color-border-strong)',
        }}>
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginBottom: 4 }}>SUBJECT</div>
          <div style={{
            fontSize: 14, fontWeight: 600, color: 'var(--color-text)', marginBottom: 12,
            fontFamily: rendered ? 'inherit' : 'var(--font-mono, monospace)',
          }}>
            {rendered ? rendered.subject : template.subject}
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginBottom: 4 }}>BODY</div>
          <div style={{
            fontSize: 13, color: 'var(--color-text)', whiteSpace: 'pre-wrap',
            fontFamily: rendered ? 'inherit' : 'var(--font-mono, monospace)', lineHeight: 1.6,
          }}>
            {rendered ? rendered.body : template.preview || '(body)'}
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button type="button" className="btn-ghost" onClick={onClose}>Close</button>
        </div>
      </div>
    </Modal>
  );
}

// ── Lightweight modal + field primitives (matches the rest of the app) ────
function Modal({ title, onClose, wide = false, children }) {
  return (
    <div onClick={onClose} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)',
      zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center',
      padding: 20,
    }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: 'var(--color-bg)', border: '1px solid var(--color-border-strong)',
        borderRadius: 14, width: wide ? 720 : 480, maxWidth: '95vw', maxHeight: '90vh',
        overflow: 'auto', padding: 22,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 18 }}>
          <h2 style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text)', margin: 0, flex: 1 }}>
            {title}
          </h2>
          <button onClick={onClose} className="btn-ghost" style={{ padding: 4 }}>
            <X size={16} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div>
      <label style={{ fontSize: 11, color: 'var(--color-text-dim)', display: 'block', marginBottom: 5 }}>
        {label}
      </label>
      {children}
    </div>
  );
}
