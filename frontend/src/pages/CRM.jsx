import { useState, useEffect, useCallback } from 'react';
import { Users, Building2, Briefcase, Plus, Search, Trash2, Edit3, X, TrendingUp, DollarSign, Phone, Mail, Calendar, MessageSquare } from 'lucide-react';
import FlowBanner from '../components/FlowBanner';
import {
  crmOverview, pipeline,
  listCompanies, createCompany, updateCompany, deleteCompany,
  listContacts, createContact, updateContact, deleteContact,
  listDeals, createDeal, updateDeal, deleteDeal,
  listInteractions, createInteraction,
  DEAL_STAGES, INTERACTION_TYPES,
} from '../services/crm';

const STAGE_COLORS = {
  lead: 'var(--color-info)', qualified: '#a78bfa', proposal: 'var(--color-warn)',
  negotiation: '#ec4899', won: 'var(--color-ok)', lost: 'var(--color-text-dim)',
};

const money = (v, cur = 'USD') => new Intl.NumberFormat('en-US', { style: 'currency', currency: cur || 'USD', maximumFractionDigits: 0 }).format(v || 0);

// ── Reusable modal ──────────────────────────────────────────────────────────
function Modal({ title, onClose, children, wide = false }) {
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 12,
        padding: 20, width: wide ? 560 : 420, maxHeight: '90vh', overflow: 'auto',
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

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 10 }}>
      <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>{label}</label>
      {children}
    </div>
  );
}

// ── Contact form ────────────────────────────────────────────────────────────
function ContactForm({ initial, companies, onSubmit, onCancel }) {
  const [f, setF] = useState({
    first_name: '', last_name: '', email: '', phone: '', title: '',
    company_id: '', notes: '', tags: '', ...(initial || {}),
  });
  const set = (k, v) => setF((prev) => ({ ...prev, [k]: v }));
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(f); }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="First name">
          <input className="field-input" value={f.first_name} onChange={(e) => set('first_name', e.target.value)} maxLength={80} />
        </Field>
        <Field label="Last name">
          <input className="field-input" value={f.last_name} onChange={(e) => set('last_name', e.target.value)} maxLength={80} />
        </Field>
      </div>
      <Field label="Email">
        <input className="field-input" type="email" value={f.email} onChange={(e) => set('email', e.target.value)} maxLength={200} />
      </Field>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="Phone">
          <input className="field-input" value={f.phone} onChange={(e) => set('phone', e.target.value)} maxLength={40} />
        </Field>
        <Field label="Title">
          <input className="field-input" value={f.title} onChange={(e) => set('title', e.target.value)} maxLength={120} />
        </Field>
      </div>
      <Field label="Company">
        <select className="field-select" value={f.company_id || ''} onChange={(e) => set('company_id', e.target.value)} style={{ width: '100%' }}>
          <option value="">— none —</option>
          {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </Field>
      <Field label="Tags (comma-separated)">
        <input className="field-input" value={f.tags} onChange={(e) => set('tags', e.target.value)} maxLength={300} />
      </Field>
      <Field label="Notes">
        <textarea className="field-input" rows={3} value={f.notes} onChange={(e) => set('notes', e.target.value)} maxLength={2000} />
      </Field>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 12 }}>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary">{initial ? 'Save' : 'Add Contact'}</button>
      </div>
    </form>
  );
}

// ── Company form ────────────────────────────────────────────────────────────
function CompanyForm({ initial, onSubmit, onCancel }) {
  const [f, setF] = useState({ name: '', industry: '', website: '', size: '', notes: '', tags: '', ...(initial || {}) });
  const set = (k, v) => setF((prev) => ({ ...prev, [k]: v }));
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(f); }}>
      <Field label="Name *">
        <input className="field-input" required value={f.name} onChange={(e) => set('name', e.target.value)} maxLength={200} />
      </Field>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="Industry">
          <input className="field-input" value={f.industry} onChange={(e) => set('industry', e.target.value)} maxLength={80} />
        </Field>
        <Field label="Size">
          <input className="field-input" placeholder="e.g. 1-10, 50-200" value={f.size} onChange={(e) => set('size', e.target.value)} maxLength={40} />
        </Field>
      </div>
      <Field label="Website">
        <input className="field-input" value={f.website} onChange={(e) => set('website', e.target.value)} maxLength={250} />
      </Field>
      <Field label="Tags"><input className="field-input" value={f.tags} onChange={(e) => set('tags', e.target.value)} /></Field>
      <Field label="Notes">
        <textarea className="field-input" rows={3} value={f.notes} onChange={(e) => set('notes', e.target.value)} maxLength={2000} />
      </Field>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 12 }}>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary">{initial ? 'Save' : 'Add Company'}</button>
      </div>
    </form>
  );
}

// ── Deal form ────────────────────────────────────────────────────────────────
function DealForm({ initial, contacts, companies, onSubmit, onCancel }) {
  const [f, setF] = useState({
    name: '', value: 0, currency: 'USD', stage: 'lead', probability_pct: 20,
    contact_id: '', company_id: '', notes: '', expected_close: '', ...(initial || {}),
  });
  const set = (k, v) => setF((prev) => ({ ...prev, [k]: v }));
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(f); }}>
      <Field label="Deal name *">
        <input className="field-input" required value={f.name} onChange={(e) => set('name', e.target.value)} maxLength={200} />
      </Field>
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 10 }}>
        <Field label="Value">
          <input className="field-input" type="number" min={0} step="0.01" value={f.value} onChange={(e) => set('value', parseFloat(e.target.value) || 0)} />
        </Field>
        <Field label="Currency">
          <input className="field-input" value={f.currency} onChange={(e) => set('currency', e.target.value.toUpperCase())} maxLength={8} />
        </Field>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="Stage">
          <select className="field-select" value={f.stage} onChange={(e) => set('stage', e.target.value)} style={{ width: '100%' }}>
            {DEAL_STAGES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </Field>
        <Field label={`Probability (${f.probability_pct}%)`}>
          <input type="range" min={0} max={100} value={f.probability_pct} onChange={(e) => set('probability_pct', parseInt(e.target.value))} style={{ width: '100%' }} />
        </Field>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="Company">
          <select className="field-select" value={f.company_id || ''} onChange={(e) => set('company_id', e.target.value)} style={{ width: '100%' }}>
            <option value="">— none —</option>
            {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </Field>
        <Field label="Primary contact">
          <select className="field-select" value={f.contact_id || ''} onChange={(e) => set('contact_id', e.target.value)} style={{ width: '100%' }}>
            <option value="">— none —</option>
            {contacts.map((c) => <option key={c.id} value={c.id}>{(c.first_name + ' ' + c.last_name).trim()}</option>)}
          </select>
        </Field>
      </div>
      <Field label="Expected close date (YYYY-MM-DD)">
        <input className="field-input" value={f.expected_close || ''} onChange={(e) => set('expected_close', e.target.value)} maxLength={30} />
      </Field>
      <Field label="Notes">
        <textarea className="field-input" rows={2} value={f.notes} onChange={(e) => set('notes', e.target.value)} maxLength={2000} />
      </Field>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 12 }}>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary">{initial ? 'Save' : 'Add Deal'}</button>
      </div>
    </form>
  );
}

// ── Kanban-style deal column ────────────────────────────────────────────────
function DealColumn({ stage, deals, onEdit, onDelete, onMove }) {
  const [dragOver, setDragOver] = useState(false);
  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        const id = e.dataTransfer.getData('deal_id');
        const currentStage = e.dataTransfer.getData('stage');
        if (id && currentStage !== stage) onMove(id, stage);
      }}
      style={{
        minWidth: 240, flex: 1, background: dragOver ? 'var(--color-surface-2)' : 'var(--color-bg)',
        border: `1px solid ${dragOver ? STAGE_COLORS[stage] : 'var(--color-surface-2)'}`, borderRadius: 10,
        padding: 10, display: 'flex', flexDirection: 'column', gap: 8, transition: 'all 0.1s',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, paddingBottom: 6, borderBottom: `2px solid ${STAGE_COLORS[stage]}` }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: STAGE_COLORS[stage] }} />
        <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text)', textTransform: 'capitalize' }}>{stage}</span>
        <span style={{ fontSize: 10, color: 'var(--color-text-dim)', marginLeft: 'auto' }}>{deals.length}</span>
      </div>
      <div style={{ fontSize: 9, color: 'var(--color-text-dim)' }}>
        Total: {money(deals.reduce((s, d) => s + (d.value || 0), 0), deals[0]?.currency)}
      </div>
      {deals.map((d) => (
        <div
          key={d.id}
          draggable
          onDragStart={(e) => { e.dataTransfer.setData('deal_id', d.id); e.dataTransfer.setData('stage', d.stage); }}
          style={{ padding: 10, background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 8, cursor: 'grab' }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text)', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis' }}>{d.name}</span>
            <div style={{ display: 'flex', gap: 4 }}>
              <button onClick={() => onEdit(d)} style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer' }}><Edit3 size={11} /></button>
              <button onClick={() => onDelete(d)} style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer' }}><Trash2 size={11} /></button>
            </div>
          </div>
          <div style={{ fontSize: 11, fontWeight: 500, color: STAGE_COLORS[stage], marginTop: 4 }}>{money(d.value, d.currency)}</div>
          {d.company_name && <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginTop: 2 }}>{d.company_name}</div>}
          {d.contact_name && d.contact_name.trim() && <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{d.contact_name}</div>}
          <div style={{ fontSize: 9, color: 'var(--color-text-dim)', marginTop: 4 }}>{d.probability_pct}% · {d.expected_close || 'no close date'}</div>
        </div>
      ))}
    </div>
  );
}

// ── Main CRM page ───────────────────────────────────────────────────────────
export default function CRM() {
  const [tab, setTab] = useState('contacts');
  const [overview, setOverview] = useState(null);
  const [contacts, setContacts] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [deals, setDeals] = useState([]);
  const [searchStr, setSearchStr] = useState('');
  const [msg, setMsg] = useState('');

  const [modal, setModal] = useState(null); // { kind: 'contact'|'company'|'deal', record: {} | null }

  const reload = useCallback(async () => {
    try {
      const [ov, cts, cos, dls] = await Promise.all([
        crmOverview(),
        listContacts({ search: searchStr }),
        listCompanies(searchStr),
        listDeals({ search: searchStr }),
      ]);
      setOverview(ov); setContacts(cts); setCompanies(cos); setDeals(dls);
    } catch (e) { setMsg(`Failed to load: ${e.message}`); }
  }, [searchStr]);

  useEffect(() => { reload(); }, [reload]);

  // Reload when business context changes
  useEffect(() => {
    const h = () => reload();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reload]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const handleSubmit = async (kind, data) => {
    try {
      const isEdit = !!modal.record;
      if (kind === 'contact') isEdit ? await updateContact(modal.record.id, data) : await createContact(data);
      if (kind === 'company') isEdit ? await updateCompany(modal.record.id, data) : await createCompany(data);
      if (kind === 'deal') isEdit ? await updateDeal(modal.record.id, data) : await createDeal(data);
      setModal(null);
      flash(isEdit ? 'Saved' : 'Added');
      reload();
    } catch (e) { alert(`Failed: ${e.message}`); }
  };

  const handleDelete = async (kind, record) => {
    if (!confirm(`Delete ${kind} "${record.name || record.first_name + ' ' + record.last_name}"?`)) return;
    try {
      if (kind === 'contact') await deleteContact(record.id);
      if (kind === 'company') await deleteCompany(record.id);
      if (kind === 'deal') await deleteDeal(record.id);
      flash('Deleted');
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleMoveDeal = async (dealId, stage) => {
    try {
      const prob = { lead: 20, qualified: 40, proposal: 60, negotiation: 80, won: 100, lost: 0 }[stage];
      await updateDeal(dealId, { stage, probability_pct: prob });
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>CRM</h1>
          <p>Contacts, companies, and your deal pipeline</p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {tab === 'contacts' && <button className="btn-primary" onClick={() => setModal({ kind: 'contact', record: null })}><Plus size={13} /> Add contact</button>}
          {tab === 'companies' && <button className="btn-primary" onClick={() => setModal({ kind: 'company', record: null })}><Plus size={13} /> Add company</button>}
          {tab === 'deals' && <button className="btn-primary" onClick={() => setModal({ kind: 'deal', record: null })}><Plus size={13} /> Add deal</button>}
        </div>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      <div style={{ padding: '8px 24px 0' }}>
        <FlowBanner currentStep={tab === 'deals' ? 'deal' : 'lead'} />
      </div>

      {/* Overview cards */}
      {overview && (
        <div style={{ padding: '0 24px', display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 8 }}>
          {[
            { label: 'Contacts', value: overview.contacts, icon: Users, color: 'var(--color-info)' },
            { label: 'Companies', value: overview.companies, icon: Building2, color: '#a78bfa' },
            { label: 'Open deals', value: `${overview.open_deals_count} · ${money(overview.open_deals_value)}`, icon: Briefcase, color: 'var(--color-warn)' },
            { label: 'Won this month', value: money(overview.won_this_month), icon: TrendingUp, color: 'var(--color-ok)' },
          ].map(({ label, value, icon: Icon, color }, i) => (
            <div key={i} className="panel" style={{ padding: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: `${color}22`, color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={16} />
              </div>
              <div>
                <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{label}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>{value}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 6, padding: '0 24px 8px', borderBottom: '1px solid var(--color-surface-2)' }}>
        {[['contacts', 'Contacts', Users], ['companies', 'Companies', Building2], ['deals', 'Deals Pipeline', Briefcase]].map(([k, lbl, Icon]) => (
          <button key={k} onClick={() => setTab(k)} className={tab === k ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 11 }}>
            <Icon size={12} /> {lbl}
          </button>
        ))}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Search size={12} color="var(--color-text-dim)" />
          <input className="field-input" placeholder="Search..." value={searchStr} onChange={(e) => setSearchStr(e.target.value)} style={{ fontSize: 11, width: 200 }} />
        </div>
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {tab === 'contacts' && (
          contacts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 48, color: 'var(--color-text-dim)' }}>
              <Users size={36} style={{ opacity: 0.3, marginBottom: 12 }} />
              <p style={{ fontSize: 13 }}>No contacts yet. Click "Add contact" to create one.</p>
            </div>
          ) : (
            <div className="table-panel">
              <table className="data-table">
                <thead><tr><th>Name</th><th>Title</th><th>Company</th><th>Email</th><th>Phone</th><th style={{ width: 80 }}></th></tr></thead>
                <tbody>
                  {contacts.map((c) => (
                    <tr key={c.id}>
                      <td style={{ fontWeight: 500 }}>{(c.first_name + ' ' + c.last_name).trim() || '—'}</td>
                      <td>{c.title || '—'}</td>
                      <td>{c.company_name || '—'}</td>
                      <td>{c.email ? <a href={`mailto:${c.email}`} style={{ color: 'var(--color-info)' }}>{c.email}</a> : '—'}</td>
                      <td>{c.phone || '—'}</td>
                      <td style={{ display: 'flex', gap: 4 }}>
                        <button className="btn-ghost" style={{ padding: 4 }} onClick={() => setModal({ kind: 'contact', record: c })}><Edit3 size={11} /></button>
                        <button className="btn-ghost" style={{ padding: 4, color: 'var(--color-err)' }} onClick={() => handleDelete('contact', c)}><Trash2 size={11} /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}

        {tab === 'companies' && (
          companies.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 48, color: 'var(--color-text-dim)' }}>
              <Building2 size={36} style={{ opacity: 0.3, marginBottom: 12 }} />
              <p style={{ fontSize: 13 }}>No companies yet. Click "Add company".</p>
            </div>
          ) : (
            <div className="table-panel">
              <table className="data-table">
                <thead><tr><th>Name</th><th>Industry</th><th>Size</th><th>Website</th><th>Tags</th><th style={{ width: 80 }}></th></tr></thead>
                <tbody>
                  {companies.map((c) => (
                    <tr key={c.id}>
                      <td style={{ fontWeight: 500 }}>{c.name}</td>
                      <td>{c.industry || '—'}</td>
                      <td>{c.size || '—'}</td>
                      <td>{c.website ? <a href={c.website.startsWith('http') ? c.website : `https://${c.website}`} target="_blank" rel="noreferrer" style={{ color: 'var(--color-info)' }}>{c.website}</a> : '—'}</td>
                      <td>{c.tags || '—'}</td>
                      <td style={{ display: 'flex', gap: 4 }}>
                        <button className="btn-ghost" style={{ padding: 4 }} onClick={() => setModal({ kind: 'company', record: c })}><Edit3 size={11} /></button>
                        <button className="btn-ghost" style={{ padding: 4, color: 'var(--color-err)' }} onClick={() => handleDelete('company', c)}><Trash2 size={11} /></button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        )}

        {tab === 'deals' && (
          deals.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 48, color: 'var(--color-text-dim)' }}>
              <Briefcase size={36} style={{ opacity: 0.3, marginBottom: 12 }} />
              <p style={{ fontSize: 13 }}>No deals yet. Click "Add deal" — you can drag deals between stages.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: 10, minHeight: 400 }}>
              {DEAL_STAGES.map((s) => (
                <DealColumn
                  key={s}
                  stage={s}
                  deals={deals.filter((d) => d.stage === s)}
                  onEdit={(d) => setModal({ kind: 'deal', record: d })}
                  onDelete={(d) => handleDelete('deal', d)}
                  onMove={handleMoveDeal}
                />
              ))}
            </div>
          )
        )}
      </div>

      {modal?.kind === 'contact' && (
        <Modal title={modal.record ? 'Edit contact' : 'Add contact'} onClose={() => setModal(null)} wide>
          <ContactForm initial={modal.record} companies={companies}
            onSubmit={(d) => handleSubmit('contact', d)} onCancel={() => setModal(null)} />
        </Modal>
      )}
      {modal?.kind === 'company' && (
        <Modal title={modal.record ? 'Edit company' : 'Add company'} onClose={() => setModal(null)} wide>
          <CompanyForm initial={modal.record}
            onSubmit={(d) => handleSubmit('company', d)} onCancel={() => setModal(null)} />
        </Modal>
      )}
      {modal?.kind === 'deal' && (
        <Modal title={modal.record ? 'Edit deal' : 'Add deal'} onClose={() => setModal(null)} wide>
          <DealForm initial={modal.record} contacts={contacts} companies={companies}
            onSubmit={(d) => handleSubmit('deal', d)} onCancel={() => setModal(null)} />
        </Modal>
      )}
    </div>
  );
}
