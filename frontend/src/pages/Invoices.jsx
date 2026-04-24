import { useState, useEffect, useCallback } from 'react';
import { FileText, Plus, Download, Trash2, Edit3, Send, X, DollarSign, Clock, AlertTriangle, CheckCircle } from 'lucide-react';
import FlowBanner from '../components/FlowBanner';
import EmptyState from '../components/EmptyState';
import SuggestionPanel from '../components/SuggestionPanel';
import {
  listInvoices, createInvoice, updateInvoice, deleteInvoice,
  renderInvoicePdf, invoicePdfUrl, invoiceSummary,
  INVOICE_STATUSES,
} from '../services/invoices';
import { listContacts, listCompanies } from '../services/crm';

const STATUS_COLORS = {
  draft: 'var(--color-text-dim)', sent: 'var(--color-info)', paid: 'var(--color-ok)',
  overdue: 'var(--color-err)', cancelled: 'var(--color-text-dim)',
};

const money = (v, cur = 'USD') => new Intl.NumberFormat('en-US', { style: 'currency', currency: cur || 'USD' }).format(v || 0);

function Modal({ title, onClose, children, wide = false }) {
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 12,
        padding: 20, width: wide ? 720 : 480, maxHeight: '92vh', overflow: 'auto',
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

// ── Invoice form ────────────────────────────────────────────────────────────
function InvoiceForm({ initial, companies, contacts, onSubmit, onCancel }) {
  const [f, setF] = useState({
    customer_name: '', customer_email: '', customer_address: '',
    customer_company_id: '', customer_contact_id: '',
    currency: 'USD', issue_date: new Date().toISOString().substring(0, 10),
    due_date: '', notes: '', tax_pct: 0,
    line_items: [{ description: '', quantity: 1, unit_price: 0 }],
    status: 'draft',
    ...(initial || {}),
  });

  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));

  const setLine = (idx, k, v) => {
    setF((p) => {
      const items = [...p.line_items];
      items[idx] = { ...items[idx], [k]: v };
      return { ...p, line_items: items };
    });
  };
  const addLine = () => setF((p) => ({ ...p, line_items: [...p.line_items, { description: '', quantity: 1, unit_price: 0 }] }));
  const removeLine = (idx) => setF((p) => ({ ...p, line_items: p.line_items.filter((_, i) => i !== idx) }));

  const subtotal = f.line_items.reduce((s, it) => s + (Number(it.quantity) * Number(it.unit_price) || 0), 0);
  const taxAmount = subtotal * (Number(f.tax_pct) / 100);
  const total = subtotal + taxAmount;

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(f); }}>
      {/* Customer */}
      <div style={{ marginBottom: 12, padding: 12, background: 'var(--color-surface-1)', borderRadius: 8 }}>
        <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Customer</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
          <div>
            <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>From CRM Company (optional)</label>
            <select className="field-select" value={f.customer_company_id || ''} onChange={(e) => set('customer_company_id', e.target.value)} style={{ width: '100%' }}>
              <option value="">— none —</option>
              {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>From CRM Contact (optional)</label>
            <select className="field-select" value={f.customer_contact_id || ''} onChange={(e) => set('customer_contact_id', e.target.value)} style={{ width: '100%' }}>
              <option value="">— none —</option>
              {contacts.map((c) => <option key={c.id} value={c.id}>{(c.first_name + ' ' + c.last_name).trim()}</option>)}
            </select>
          </div>
        </div>
        <input className="field-input" placeholder="Customer name *" value={f.customer_name} onChange={(e) => set('customer_name', e.target.value)} maxLength={200} style={{ marginBottom: 6 }} />
        <input className="field-input" placeholder="Customer email" value={f.customer_email} onChange={(e) => set('customer_email', e.target.value)} maxLength={200} style={{ marginBottom: 6 }} />
        <textarea className="field-input" rows={2} placeholder="Billing address" value={f.customer_address} onChange={(e) => set('customer_address', e.target.value)} maxLength={500} />
      </div>

      {/* Dates + Currency */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 8, marginBottom: 12 }}>
        <div>
          <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>Issue date</label>
          <input className="field-input" type="date" value={f.issue_date} onChange={(e) => set('issue_date', e.target.value)} />
        </div>
        <div>
          <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>Due date</label>
          <input className="field-input" type="date" value={f.due_date} onChange={(e) => set('due_date', e.target.value)} />
        </div>
        <div>
          <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>Currency</label>
          <input className="field-input" value={f.currency} onChange={(e) => set('currency', e.target.value.toUpperCase())} maxLength={8} />
        </div>
        <div>
          <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>Status</label>
          <select className="field-select" value={f.status} onChange={(e) => set('status', e.target.value)} style={{ width: '100%' }}>
            {INVOICE_STATUSES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
      </div>

      {/* Line items */}
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>Line items</div>
        {f.line_items.map((it, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: '3fr 1fr 1fr 1fr 30px', gap: 6, marginBottom: 6 }}>
            <input className="field-input" placeholder="Description" value={it.description} onChange={(e) => setLine(i, 'description', e.target.value)} maxLength={400} required />
            <input className="field-input" type="number" step="0.01" min={0} placeholder="Qty" value={it.quantity} onChange={(e) => setLine(i, 'quantity', parseFloat(e.target.value) || 0)} />
            <input className="field-input" type="number" step="0.01" min={0} placeholder="Unit" value={it.unit_price} onChange={(e) => setLine(i, 'unit_price', parseFloat(e.target.value) || 0)} />
            <div style={{ display: 'flex', alignItems: 'center', fontSize: 11, color: 'var(--color-text-muted)', padding: '0 6px' }}>
              {money(Number(it.quantity) * Number(it.unit_price), f.currency)}
            </div>
            <button type="button" onClick={() => removeLine(i)} style={{ background: 'none', border: 'none', color: 'var(--color-err)', cursor: 'pointer' }}>
              <Trash2 size={12} />
            </button>
          </div>
        ))}
        <button type="button" className="btn-ghost" onClick={addLine} style={{ fontSize: 11 }}><Plus size={12} /> Add line</button>
      </div>

      {/* Totals */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 200px', gap: 8, alignItems: 'end', marginBottom: 12 }}>
        <div>
          <label style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>Notes (payment terms, thank-you, etc.)</label>
          <textarea className="field-input" rows={3} value={f.notes} onChange={(e) => set('notes', e.target.value)} maxLength={2000} />
        </div>
        <div style={{ padding: 12, background: 'var(--color-surface-1)', borderRadius: 8, fontSize: 11 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-text-muted)', marginBottom: 4 }}>
            <span>Subtotal</span><span>{money(subtotal, f.currency)}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--color-text-muted)', marginBottom: 4 }}>
            <span>Tax</span>
            <input type="number" step="0.01" min={0} max={100} value={f.tax_pct} onChange={(e) => set('tax_pct', parseFloat(e.target.value) || 0)} style={{ width: 60, fontSize: 11, padding: '2px 4px', background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 4, color: 'var(--color-text)', textAlign: 'right' }} />
            <span>% = {money(taxAmount, f.currency)}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 700, color: 'var(--color-text)', fontSize: 13, paddingTop: 6, borderTop: '1px solid var(--color-surface-2)', marginTop: 6 }}>
            <span>Total</span><span>{money(total, f.currency)}</span>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary">{initial ? 'Save' : 'Create invoice'}</button>
      </div>
    </form>
  );
}

// ── Main page ───────────────────────────────────────────────────────────────
export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [summary, setSummary] = useState(null);
  const [filter, setFilter] = useState('');
  const [contacts, setContacts] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [modal, setModal] = useState(null); // { record: invoice | null }
  const [msg, setMsg] = useState('');

  const reload = useCallback(async () => {
    try {
      const opts = {};
      if (filter) opts.status = filter;
      const [list, s, cts, cos] = await Promise.all([
        listInvoices(opts), invoiceSummary(), listContacts(), listCompanies(),
      ]);
      setInvoices(list); setSummary(s); setContacts(cts); setCompanies(cos);
    } catch (e) { setMsg(`Failed to load: ${e.message}`); }
  }, [filter]);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    const h = () => reload();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reload]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const handleSubmit = async (data) => {
    try {
      if (modal.record) await updateInvoice(modal.record.id, data);
      else await createInvoice(data);
      setModal(null); flash('Saved'); reload();
    } catch (e) { alert(`Failed: ${e.message}`); }
  };

  const handleDelete = async (inv) => {
    if (!confirm(`Delete invoice ${inv.number}?`)) return;
    try { await deleteInvoice(inv.id); flash('Deleted'); reload(); }
    catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleDownload = async (inv) => {
    try {
      const blob = await invoicePdfUrl(inv.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `${inv.number}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { flash(`Download failed: ${e.message}`); }
  };

  const handleMarkStatus = async (inv, status) => {
    try {
      await updateInvoice(inv.id, { status });
      flash(`Marked ${status}`);
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Invoices</h1>
          <p>Create, track, and send invoices to your customers</p>
        </div>
        <button className="btn-primary" onClick={() => setModal({ record: null })}><Plus size={13} /> New invoice</button>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      <div style={{ padding: '8px 24px 0' }}>
        <FlowBanner currentStep="invoice" />
      </div>

      {summary && (
        <div style={{ padding: '0 24px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 8 }}>
          {[
            { label: 'Outstanding', value: money(summary.outstanding.total), sub: `${summary.outstanding.count} invoices`, icon: Clock, color: 'var(--color-info)' },
            { label: 'Overdue', value: money(summary.overdue.total), sub: `${summary.overdue.count} invoices`, icon: AlertTriangle, color: 'var(--color-err)' },
            { label: 'Paid', value: money(summary.paid.total), sub: `${summary.paid.count} invoices`, icon: CheckCircle, color: 'var(--color-ok)' },
            { label: 'Draft', value: money(summary.draft.total), sub: `${summary.draft.count} invoices`, icon: FileText, color: 'var(--color-text-muted)' },
          ].map(({ label, value, sub, icon: Icon, color }, i) => (
            <div key={i} className="panel" style={{ padding: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: `${color}22`, color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={16} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{label}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>{value}</div>
                <div style={{ fontSize: 9, color: 'var(--color-text-dim)' }}>{sub}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'flex', gap: 6, padding: '0 24px 8px', borderBottom: '1px solid var(--color-surface-2)' }}>
        {[['', 'All'], ['draft', 'Draft'], ['sent', 'Sent'], ['paid', 'Paid'], ['overdue', 'Overdue']].map(([k, lbl]) => (
          <button key={k || 'all'} onClick={() => setFilter(k)} className={filter === k ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 11 }}>{lbl}</button>
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {invoices.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No invoices yet"
            description="Draft your first invoice in 30 seconds. Kira will then spot overdue ones and queue reminder emails for your approval."
            primaryLabel="New invoice"
            onPrimary={() => setModal({ record: null })}
          />
        ) : (
          <div className="table-panel">
            <table className="data-table">
              <thead>
                <tr><th>Number</th><th>Customer</th><th>Issued</th><th>Due</th><th style={{ textAlign: 'right' }}>Total</th><th>Status</th><th style={{ width: 160 }}></th></tr>
              </thead>
              <tbody>
                {invoices.map((inv) => (
                  <tr key={inv.id}>
                    <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>{inv.number}</td>
                    <td>
                      <div style={{ fontWeight: 500 }}>{inv.customer_name}</div>
                      {inv.customer_email && <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{inv.customer_email}</div>}
                    </td>
                    <td>{inv.issue_date || '—'}</td>
                    <td>{inv.due_date || '—'}</td>
                    <td style={{ textAlign: 'right', fontWeight: 500 }}>{money(inv.total, inv.currency)}</td>
                    <td>
                      <span style={{ fontSize: 9, padding: '2px 8px', borderRadius: 10, fontWeight: 600, background: `${STATUS_COLORS[inv.status]}22`, color: STATUS_COLORS[inv.status] }}>{inv.status}</span>
                    </td>
                    <td style={{ display: 'flex', gap: 4 }}>
                      <button className="btn-ghost" style={{ padding: 4 }} onClick={() => handleDownload(inv)} title="Download PDF"><Download size={11} /></button>
                      {inv.status === 'draft' && <button className="btn-ghost" style={{ padding: 4, color: 'var(--color-info)' }} onClick={() => handleMarkStatus(inv, 'sent')} title="Mark sent"><Send size={11} /></button>}
                      {inv.status === 'sent' && <button className="btn-ghost" style={{ padding: 4, color: 'var(--color-ok)' }} onClick={() => handleMarkStatus(inv, 'paid')} title="Mark paid"><CheckCircle size={11} /></button>}
                      <button className="btn-ghost" style={{ padding: 4 }} onClick={() => setModal({ record: inv })}><Edit3 size={11} /></button>
                      <button className="btn-ghost" style={{ padding: 4, color: 'var(--color-err)' }} onClick={() => handleDelete(inv)}><Trash2 size={11} /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {modal && (
        <Modal title={modal.record ? `Edit ${modal.record.number}` : 'New invoice'} onClose={() => setModal(null)} wide>
          {modal.record?.id && (
            <div style={{ marginBottom: 12 }}>
              <SuggestionPanel entityType="invoice" entityId={modal.record.id} compact />
            </div>
          )}
          <InvoiceForm initial={modal.record} companies={companies} contacts={contacts}
            onSubmit={handleSubmit} onCancel={() => setModal(null)} />
        </Modal>
      )}
    </div>
  );
}
