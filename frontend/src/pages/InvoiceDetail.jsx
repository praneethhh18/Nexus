/**
 * Invoice detail page — view, edit, generate PDF, mark sent / paid.
 *
 * The "render PDF" call regenerates the file each time so any edits to
 * line items or notes are reflected. Status changes are one-click and
 * recorded with timestamps so there's a clear paid_at / sent_at trail.
 */
import { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft, Receipt, Edit3, Trash2, Download, Send, FileText,
  Building2, User, Calendar, AlertCircle, Loader2, CheckCircle2, Clock,
  ChevronRight,
} from 'lucide-react';
import {
  getInvoice, updateInvoice, deleteInvoice, renderInvoicePdf, invoicePdfUrl,
  INVOICE_STATUSES,
} from '../services/invoices';
import { getContact, getCompany } from '../services/crm';
import { getToken, getBusinessId } from '../services/auth';

const STATUS_TONE = {
  draft:     'var(--color-text-dim)',
  sent:      'var(--color-info)',
  paid:      'var(--color-ok)',
  overdue:   'var(--color-err)',
  cancelled: 'var(--color-text-dim)',
};


function formatDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso + 'T00:00:00').toLocaleDateString([], {
      month: 'short', day: 'numeric', year: 'numeric',
    });
  } catch { return iso.substring(0, 10); }
}

function formatWhen(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString([], {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso.substring(0, 16); }
}

function moneyOf(currency) {
  return (n) => new Intl.NumberFormat('en-US', {
    style: 'currency', currency: currency || 'USD',
  }).format(n || 0);
}


export default function InvoiceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [invoice, setInvoice] = useState(null);
  const [contact, setContact] = useState(null);
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const [editing, setEditing] = useState(false);
  const [edit, setEdit] = useState({});
  const [msg, setMsg] = useState('');

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const reload = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const inv = await getInvoice(id);
      setInvoice(inv);
      setEdit(inv);
      const [ct, co] = await Promise.all([
        inv.customer_contact_id ? getContact(inv.customer_contact_id).catch(() => null) : Promise.resolve(null),
        inv.customer_company_id ? getCompany(inv.customer_company_id).catch(() => null) : Promise.resolve(null),
      ]);
      setContact(ct);
      setCompany(co);
    } catch (e) { setError(e.message || 'Could not load invoice.'); }
    setLoading(false);
  }, [id]);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { reload(); }, [reload]);

  const money = useMemo(
    () => moneyOf(invoice?.currency || 'USD'),
    [invoice],
  );

  const lineItems = useMemo(() => {
    if (!invoice) return [];
    if (Array.isArray(invoice.line_items)) return invoice.line_items;
    try { return JSON.parse(invoice.line_items || '[]'); }
    catch { return []; }
  }, [invoice]);

  // ── Actions ────────────────────────────────────────────────────────────
  const handleStatus = async (newStatus) => {
    if (newStatus === invoice.status) return;
    setBusy('status');
    try {
      const patch = { status: newStatus };
      if (newStatus === 'paid') patch.paid_at = new Date().toISOString();
      await updateInvoice(id, patch);
      flash(`Marked as ${newStatus}.`);
      reload();
    } catch (e) { flash(`Update failed: ${e.message}`); }
    setBusy('');
  };

  const handleRender = async () => {
    setBusy('render');
    try {
      const r = await renderInvoicePdf(id);
      flash('PDF regenerated.');
      // Open the PDF in a new tab.
      const url = invoicePdfUrl(id);
      const t = getToken();
      const b = getBusinessId();
      const h = {};
      if (t) h.Authorization = `Bearer ${t}`;
      if (b) h['X-Business-Id'] = b;
      const res = await fetch(url, { headers: h });
      if (res.ok) {
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        window.open(blobUrl, '_blank');
        setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
      }
      void r;
    } catch (e) { flash(`PDF render failed: ${e.message}`); }
    setBusy('');
  };

  const handleEmailDraft = () => {
    const to = invoice.customer_email;
    if (!to) {
      flash('No customer email on file.');
      return;
    }
    const subject = `Invoice ${invoice.number} from ${company?.name || ''}`.trim();
    const body =
      `Hi,\n\n` +
      `Please find invoice ${invoice.number} attached, due ${formatDate(invoice.due_date)}.\n\n` +
      `Total: ${money(invoice.total)}.\n\n` +
      `Thanks!`;
    window.open(
      `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`,
      '_blank',
    );
  };

  const handleSave = async () => {
    try {
      await updateInvoice(id, {
        customer_name: edit.customer_name,
        customer_email: edit.customer_email,
        customer_address: edit.customer_address,
        currency: edit.currency,
        due_date: edit.due_date,
        notes: edit.notes,
        tax_pct: edit.tax_pct,
      });
      setEditing(false);
      flash('Saved.');
      reload();
    } catch (e) { flash(`Save failed: ${e.message}`); }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete invoice ${invoice?.number}? This can't be undone.`)) return;
    try {
      await deleteInvoice(id);
      navigate('/invoices');
    } catch (e) { flash(`Delete failed: ${e.message}`); }
  };

  if (loading) return <CenterSpinner />;
  if (error || !invoice) return <NotFound message={error || 'Invoice may have been deleted.'} />;

  const statusTone = STATUS_TONE[invoice.status] || 'var(--color-text-dim)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
          <button onClick={() => navigate('/invoices')} className="btn-ghost btn-sm">
            <ArrowLeft size={12} /> Invoices
          </button>
          <div style={{
            width: 44, height: 44, borderRadius: 'var(--r-md)',
            background: `color-mix(in srgb, ${statusTone} 14%, transparent)`,
            color: statusTone,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <Receipt size={20} />
          </div>
          <div style={{ minWidth: 0 }}>
            <h1 style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.01em', margin: 0 }}>{invoice.number}</h1>
            <p style={{ fontSize: 12, color: 'var(--color-text-muted)', margin: 0, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ textTransform: 'capitalize', color: statusTone, fontWeight: 600 }}>{invoice.status}</span>
              <span>· {money(invoice.total)}</span>
              <span>· {invoice.customer_name || 'Unknown customer'}</span>
            </p>
          </div>
        </div>
        <div className="row-actions">
          <button className="btn-ghost btn-sm" onClick={() => setEditing(v => !v)}>
            <Edit3 size={11} /> {editing ? 'Cancel' : 'Edit'}
          </button>
          <button className="btn-ghost btn-sm" style={{ color: 'var(--color-err)' }} onClick={handleDelete}>
            <Trash2 size={11} /> Delete
          </button>
        </div>
      </div>

      {msg && <div style={{ padding: '6px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      <div className="page-body" style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(280px, 380px)', gap: 16 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Status flow */}
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 10px' }}>
              <h2>Status</h2>
              <span className="meta">click to change</span>
            </div>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {INVOICE_STATUSES.map(s => {
                const isActive = s === invoice.status;
                const tone = STATUS_TONE[s];
                return (
                  <button
                    key={s}
                    onClick={() => handleStatus(s)}
                    disabled={busy === 'status' || isActive}
                    style={{
                      flex: '1 1 0', minWidth: 90,
                      padding: '8px 10px',
                      border: `1px solid ${isActive ? tone : 'var(--color-border)'}`,
                      borderRadius: 'var(--r-md)',
                      background: isActive
                        ? `color-mix(in srgb, ${tone} 14%, transparent)`
                        : 'var(--color-surface-1)',
                      color: isActive ? tone : 'var(--color-text-dim)',
                      cursor: isActive ? 'default' : 'pointer',
                      fontSize: 12, fontWeight: 600, textTransform: 'capitalize',
                    }}
                  >
                    {s}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Customer + dates */}
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 8px' }}><h2>Bill to</h2></div>
            {editing ? (
              <div style={{ display: 'grid', gap: 10 }}>
                <Field label="Customer name"><input className="field-input" value={edit.customer_name || ''} onChange={(e) => setEdit({ ...edit, customer_name: e.target.value })} /></Field>
                <Field label="Email"><input className="field-input" type="email" value={edit.customer_email || ''} onChange={(e) => setEdit({ ...edit, customer_email: e.target.value })} /></Field>
                <Field label="Address"><textarea className="field-input" rows={3} value={edit.customer_address || ''} onChange={(e) => setEdit({ ...edit, customer_address: e.target.value })} /></Field>
                <Field label="Currency"><input className="field-input" value={edit.currency || ''} onChange={(e) => setEdit({ ...edit, currency: e.target.value.toUpperCase() })} maxLength={8} /></Field>
                <Field label="Due date"><input className="field-input" type="date" value={edit.due_date || ''} onChange={(e) => setEdit({ ...edit, due_date: e.target.value })} /></Field>
                <Field label="Tax %"><input className="field-input" type="number" min={0} max={100} step="0.01" value={edit.tax_pct || 0} onChange={(e) => setEdit({ ...edit, tax_pct: parseFloat(e.target.value) || 0 })} /></Field>
                <Field label="Notes"><textarea className="field-input" rows={3} value={edit.notes || ''} onChange={(e) => setEdit({ ...edit, notes: e.target.value })} /></Field>
                <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                  <button className="btn-ghost" onClick={() => { setEditing(false); setEdit(invoice); }}>Cancel</button>
                  <button className="btn-primary" onClick={handleSave}>Save</button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: 10 }}>
                <DetailRow icon={<User size={13} />} label="Customer">
                  {invoice.customer_name}
                  {contact && (
                    <Link to={`/crm/contacts/${contact.id}`} style={{ marginLeft: 8, fontSize: 11, color: 'var(--color-accent)' }}>(open)</Link>
                  )}
                </DetailRow>
                {invoice.customer_email && (
                  <DetailRow icon={null} label="Email">
                    <a href={`mailto:${invoice.customer_email}`}>{invoice.customer_email}</a>
                  </DetailRow>
                )}
                {company && (
                  <DetailRow icon={<Building2 size={13} />} label="Company">
                    <Link to={`/crm/companies/${company.id}`} style={{ color: 'var(--color-accent)' }}>{company.name}</Link>
                  </DetailRow>
                )}
                {invoice.customer_address && (
                  <DetailRow icon={null} label="Address" multiline>{invoice.customer_address}</DetailRow>
                )}
                <DetailRow icon={<Calendar size={13} />} label="Issued">{formatDate(invoice.issue_date)}</DetailRow>
                <DetailRow icon={<Calendar size={13} />} label="Due">{formatDate(invoice.due_date)}</DetailRow>
                {invoice.notes && <DetailRow icon={null} label="Notes" multiline>{invoice.notes}</DetailRow>}
              </div>
            )}
          </div>

          {/* Line items + totals */}
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 10px' }}><h2>Line items</h2></div>
            {lineItems.length === 0 ? (
              <div style={{ padding: 16, textAlign: 'center', color: 'var(--color-text-dim)', fontSize: 12 }}>No line items.</div>
            ) : (
              <div className="table-panel" style={{ marginBottom: 12 }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Description</th>
                      <th style={{ width: 60, textAlign: 'right' }}>Qty</th>
                      <th style={{ width: 100, textAlign: 'right' }}>Unit</th>
                      <th style={{ width: 110, textAlign: 'right' }}>Subtotal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lineItems.map((it, i) => (
                      <tr key={i}>
                        <td>{it.description}</td>
                        <td style={{ textAlign: 'right', fontFeatureSettings: '"tnum"' }}>{Number(it.quantity || 0)}</td>
                        <td style={{ textAlign: 'right', fontFeatureSettings: '"tnum"' }}>{money(it.unit_price)}</td>
                        <td style={{ textAlign: 'right', fontFeatureSettings: '"tnum"', fontWeight: 600 }}>
                          {money(Number(it.quantity || 0) * Number(it.unit_price || 0))}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div style={{
              padding: 14,
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--r-md)',
              fontFeatureSettings: '"tnum"',
              maxWidth: 320, marginLeft: 'auto',
            }}>
              <Row label="Subtotal" value={money(invoice.subtotal)} />
              {invoice.tax_pct > 0 && (
                <Row label={`Tax (${invoice.tax_pct}%)`} value={money(invoice.tax_amount)} />
              )}
              <div style={{
                display: 'flex', justifyContent: 'space-between',
                paddingTop: 8, marginTop: 6,
                borderTop: '1px solid var(--color-border)',
                fontSize: 14, fontWeight: 700, color: 'var(--color-text)',
              }}>
                <span>Total</span><span>{money(invoice.total)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 10px' }}><h2>Actions</h2></div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <ActionRow
                icon={busy === 'render' ? <Loader2 size={13} className="animate-spin" /> : <FileText size={13} />}
                label="View / regenerate PDF"
                detail="Renders fresh from current data"
                disabled={busy === 'render'}
                onClick={handleRender}
              />
              <ActionRow
                icon={<Download size={13} />}
                label="Download PDF"
                detail={invoice.pdf_path ? 'Last rendered version' : 'Generate first to download'}
                disabled={!invoice.pdf_path}
                onClick={async () => {
                  const url = invoicePdfUrl(id);
                  const t = getToken(); const b = getBusinessId();
                  const h = {}; if (t) h.Authorization = `Bearer ${t}`; if (b) h['X-Business-Id'] = b;
                  const res = await fetch(url, { headers: h });
                  if (!res.ok) return flash('No PDF yet — render first.');
                  const blob = await res.blob();
                  const a = document.createElement('a');
                  a.href = URL.createObjectURL(blob);
                  a.download = `${invoice.number}.pdf`;
                  a.click();
                  URL.revokeObjectURL(a.href);
                }}
              />
              <ActionRow
                icon={<Send size={13} />}
                label="Email customer"
                detail={invoice.customer_email || 'No email on file'}
                disabled={!invoice.customer_email}
                onClick={handleEmailDraft}
              />
              {invoice.status !== 'paid' && (
                <ActionRow
                  icon={<CheckCircle2 size={13} />}
                  label="Mark as paid"
                  detail="Records paid_at = now"
                  onClick={() => handleStatus('paid')}
                />
              )}
              {invoice.status === 'draft' && (
                <ActionRow
                  icon={<Send size={13} />}
                  label="Mark as sent"
                  detail="Status: draft → sent"
                  onClick={() => handleStatus('sent')}
                />
              )}
            </div>
          </div>

          <div className="panel" style={{ background: 'var(--color-surface-1)' }}>
            <div className="section-h" style={{ margin: '0 0 6px' }}><h2>Snapshot</h2></div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
              <Snap label="Status" value={<span style={{ textTransform: 'capitalize', color: statusTone }}>{invoice.status}</span>} />
              <Snap label="Total" value={money(invoice.total)} />
              <Snap label="Items" value={lineItems.length} />
              <Snap label="Issued" value={formatDate(invoice.issue_date)} />
              <Snap label="Due" value={formatDate(invoice.due_date)} />
              {invoice.paid_at && <Snap label="Paid" value={formatWhen(invoice.paid_at)} />}
              <Snap label="Created" value={formatWhen(invoice.created_at)} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


// ── Bits (intentionally duplicated across detail pages — see DealDetail) ────
function CenterSpinner() {
  return (
    <div className="page-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
      <Loader2 size={20} className="animate-spin" color="var(--color-text-dim)" />
    </div>
  );
}

function NotFound({ message }) {
  const navigate = useNavigate();
  return (
    <div className="page-body" style={{ maxWidth: 640, margin: '32px auto' }}>
      <div className="panel" style={{
        padding: 20,
        borderColor: 'color-mix(in srgb, var(--color-err) 28%, transparent)',
        background: 'color-mix(in srgb, var(--color-err) 6%, transparent)',
      }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <AlertCircle size={18} color="var(--color-err)" style={{ marginTop: 2, flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Invoice not found</div>
            <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>{message}</div>
            <button className="btn-ghost btn-sm" style={{ marginTop: 10 }} onClick={() => navigate('/invoices')}>
              <ArrowLeft size={11} /> Back to invoices
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <label style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 500 }}>{label}</label>
      {children}
    </div>
  );
}

function DetailRow({ icon, label, multiline, children }) {
  return (
    <div style={{ display: 'flex', gap: 12, alignItems: multiline ? 'flex-start' : 'center' }}>
      <div style={{
        width: 100, fontSize: 11, color: 'var(--color-text-dim)',
        display: 'flex', alignItems: 'center', gap: 5,
        textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600,
        flexShrink: 0,
      }}>
        {icon}{label}
      </div>
      <div style={{
        fontSize: 12.5, color: 'var(--color-text)',
        flex: 1, minWidth: 0, whiteSpace: multiline ? 'pre-wrap' : 'normal',
      }}>{children}</div>
    </div>
  );
}

function ActionRow({ icon, label, detail, disabled, onClick }) {
  return (
    <button onClick={onClick} disabled={disabled}
      style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 12px', borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-1)', border: '1px solid var(--color-border)',
        color: 'var(--color-text)', cursor: disabled ? 'default' : 'pointer',
        opacity: disabled ? 0.45 : 1, textAlign: 'left',
      }}>
      <div style={{
        width: 28, height: 28, borderRadius: 'var(--r-md)',
        background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      }}>{icon}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12.5, fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{detail}</div>
      </div>
      <ChevronRight size={12} color="var(--color-text-dim)" />
    </button>
  );
}

function Row({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, color: 'var(--color-text-muted)', marginBottom: 6 }}>
      <span>{label}</span><span style={{ color: 'var(--color-text)' }}>{value}</span>
    </div>
  );
}

function Snap({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
      <span style={{ color: 'var(--color-text-dim)' }}>{label}</span>
      <span style={{ fontWeight: 600, color: 'var(--color-text)', fontFeatureSettings: '"tnum"' }}>{value}</span>
    </div>
  );
}
