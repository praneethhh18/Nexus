/**
 * Public lead-capture form rendered at /f/:slug.
 *
 * Loads the form schema from /api/public/forms/:slug (no auth), renders the
 * fields the workspace chose, and posts back to /api/public/leads with the
 * slug + an optional ?via=<channel> attribution tag.
 *
 * Standalone — no app chrome, no auth, no business context. Anyone with the
 * URL can submit.
 */
import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { getPublicForm, submitPublicForm, FORM_FIELD_CATALOGUE } from '../services/leadForms';


function fieldCatalogue(key) {
  return FORM_FIELD_CATALOGUE.find(f => f.key === key) || {
    key, label: key, placeholder: '', inputType: 'text',
  };
}


export default function PublicLeadForm() {
  const { slug } = useParams();
  const [params] = useSearchParams();
  const via = (params.get('via') || '').slice(0, 40);

  const [schema, setSchema]     = useState(null);
  const [loadErr, setLoadErr]   = useState('');
  const [values, setValues]     = useState({});
  const [busy, setBusy]         = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [err, setErr]           = useState('');

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const s = await getPublicForm(slug);
        if (alive) setSchema(s);
      } catch (e) {
        if (alive) setLoadErr(e.message || 'Form not found');
      }
    })();
    return () => { alive = false; };
  }, [slug]);

  const set = (k, v) => setValues((prev) => ({ ...prev, [k]: v }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr('');
    try {
      // Public endpoint requires `name` — synthesize from first available
      // human-name field if the form didn't include one explicitly.
      const payload = { ...values };
      if (!payload.name) payload.name = (payload.email || payload.phone || 'Anonymous').slice(0, 200);
      await submitPublicForm(slug, payload, via);
      setSubmitted(true);
    } catch (e2) {
      setErr(e2.message || 'Submission failed — please try again.');
    } finally {
      setBusy(false);
    }
  };

  const accent = schema?.accent_color || '#8b5cf6';

  // ── Theme — light, minimal, single-color accent ─────────────────────────
  const page = {
    minHeight: '100vh',
    background: `radial-gradient(1200px 600px at 20% -10%, ${accent}18, transparent 60%), #fafaff`,
    display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
    padding: '40px 16px',
    fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, sans-serif',
    color: '#1a1a2e',
  };
  const card = {
    background: '#fff',
    borderRadius: 14,
    padding: 28,
    width: '100%', maxWidth: 480,
    boxShadow: '0 20px 60px rgba(15, 15, 60, 0.08), 0 1px 2px rgba(15, 15, 60, 0.04)',
    border: '1px solid #eeeaff',
  };
  const labelStyle = { fontSize: 12, fontWeight: 600, color: '#444', marginBottom: 6, display: 'block' };
  const inputStyle = {
    width: '100%', padding: '10px 12px', fontSize: 14,
    border: '1px solid #e3def7', borderRadius: 8, background: '#fff',
    color: '#1a1a2e', outline: 'none',
    fontFamily: 'inherit',
  };

  // ── Loading ──────────────────────────────────────────────────────────────
  if (!schema && !loadErr) {
    return (
      <div style={page}>
        <div style={card}>
          <Loader2 size={20} className="spin" style={{ color: accent }} />
          <div style={{ marginTop: 8, color: '#666', fontSize: 13 }}>Loading form…</div>
        </div>
      </div>
    );
  }

  // ── Not found / broken slug ──────────────────────────────────────────────
  if (loadErr) {
    return (
      <div style={page}>
        <div style={card}>
          <AlertCircle size={28} style={{ color: '#e0524d' }} />
          <h2 style={{ fontSize: 18, fontWeight: 700, margin: '12px 0 6px' }}>Form unavailable</h2>
          <p style={{ fontSize: 13, color: '#666', lineHeight: 1.5, margin: 0 }}>
            This form link may have been removed or is incorrect. Please check with whoever shared it with you.
          </p>
        </div>
      </div>
    );
  }

  // ── Success state ────────────────────────────────────────────────────────
  if (submitted) {
    return (
      <div style={page}>
        <div style={card}>
          <CheckCircle2 size={32} style={{ color: accent }} />
          <h2 style={{ fontSize: 20, fontWeight: 700, margin: '12px 0 8px' }}>Thank you</h2>
          <p style={{ fontSize: 14, color: '#444', lineHeight: 1.5, margin: 0 }}>
            {schema.thank_you || 'We received your details — we’ll be in touch soon.'}
          </p>
        </div>
      </div>
    );
  }

  // ── Form ─────────────────────────────────────────────────────────────────
  return (
    <div style={page}>
      <div style={card}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: '0 0 6px', letterSpacing: -0.3 }}>
          {schema.title}
        </h1>
        {schema.description && (
          <p style={{ fontSize: 13.5, color: '#555', lineHeight: 1.55, margin: '0 0 18px' }}>
            {schema.description}
          </p>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {(schema.fields || []).map((f) => {
            const cat = fieldCatalogue(f.key);
            return (
              <div key={f.key}>
                <label style={labelStyle}>
                  {f.label || cat.label}
                  {f.required && <span style={{ color: '#e0524d', marginLeft: 4 }}>*</span>}
                </label>
                {cat.inputType === 'textarea' ? (
                  <textarea
                    rows={4}
                    required={f.required}
                    placeholder={cat.placeholder}
                    value={values[f.key] || ''}
                    onChange={(e) => set(f.key, e.target.value)}
                    style={{ ...inputStyle, resize: 'vertical', minHeight: 90 }}
                    maxLength={2000}
                  />
                ) : (
                  <input
                    type={cat.inputType}
                    required={f.required}
                    placeholder={cat.placeholder}
                    value={values[f.key] || ''}
                    onChange={(e) => set(f.key, e.target.value)}
                    style={inputStyle}
                    maxLength={200}
                  />
                )}
              </div>
            );
          })}

          {err && (
            <div style={{
              padding: '10px 12px', background: '#fdeceb', color: '#9b2c27',
              borderRadius: 8, fontSize: 12.5, border: '1px solid #f8c3bf',
            }}>{err}</div>
          )}

          <button
            type="submit"
            disabled={busy}
            style={{
              padding: '11px 16px', fontSize: 14, fontWeight: 600,
              background: accent, color: '#fff', border: 'none',
              borderRadius: 9, cursor: busy ? 'wait' : 'pointer',
              opacity: busy ? 0.7 : 1, marginTop: 4,
              transition: 'transform 0.05s ease',
            }}
          >
            {busy ? 'Sending…' : 'Send'}
          </button>

          {via && (
            <div style={{ fontSize: 10.5, color: '#999', textAlign: 'center', marginTop: -4 }}>
              via {via}
            </div>
          )}
        </form>

        <div style={{
          marginTop: 24, paddingTop: 16, borderTop: '1px solid #eeeaff',
          fontSize: 10.5, color: '#a0a0b0', textAlign: 'center',
        }}>
          Powered by <b style={{ color: '#666' }}>NexusAgent</b>
        </div>
      </div>
    </div>
  );
}
