import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Users, Building2, Briefcase, Plus, Search, Trash2, Edit3, X, TrendingUp, DollarSign, Phone, Mail, Calendar, MessageSquare, Upload, Activity, ChevronRight, Inbox, Sparkles, Copy, Check } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { listIntakeKeys, createIntakeKey, revokeIntakeKey } from '../services/tags';
import FlowBanner from '../components/FlowBanner';
import EmptyState from '../components/EmptyState';
import {
  crmOverview, pipeline,
  listCompanies, createCompany, updateCompany, deleteCompany,
  listContacts, createContact, updateContact, deleteContact,
  listDeals, createDeal, updateDeal, deleteDeal,
  listInteractions, createInteraction,
  DEAL_STAGES, INTERACTION_TYPES,
} from '../services/crm';
import { bulkDeleteContacts, bulkDeleteCompanies, bulkDeleteDeals, bulkDealStage, bulkTagsFor } from '../services/tags';
import { useBulkSelection, BulkCheckbox, BulkActionBar, UndoToast } from '../components/BulkActionBar';
import { TagChips, TagPicker } from '../components/TagChips';
import TagFilterBar, { filterItems } from '../components/TagFilterBar';
import EntityImportWizard from '../components/EntityImportWizard';
import ActivityTimeline from '../components/ActivityTimeline';
import SuggestionPanel from '../components/SuggestionPanel';

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
function DealColumn({ stage, deals, onEdit, onDelete, onMove, onOpen }) {
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
          onClick={() => onOpen?.(d)}
          style={{ padding: 10, background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 8, cursor: 'pointer' }}
          title="Open deal"
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text)', flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis' }}>{d.name}</span>
            <div style={{ display: 'flex', gap: 4 }} onClick={(e) => e.stopPropagation()}>
              <button onClick={() => onEdit(d)} style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer' }} title="Edit"><Edit3 size={11} /></button>
              <button onClick={() => onDelete(d)} style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer' }} title="Delete"><Trash2 size={11} /></button>
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
  const navigate = useNavigate();
  const [tab, setTab] = useState('contacts');
  const [overview, setOverview] = useState(null);
  const [contacts, setContacts] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [deals, setDeals] = useState([]);
  const [searchStr, setSearchStr] = useState('');
  const [msg, setMsg] = useState('');

  const [modal, setModal] = useState(null); // { kind: 'contact'|'company'|'deal', record: {} | null }
  const [showImport, setShowImport] = useState(false);
  const [activityFor, setActivityFor] = useState(null); // { kind, record }

  // Tag chips + filter (per tab)
  const [tagsByContact, setTagsByContact] = useState({});
  const [tagsByCompany, setTagsByCompany] = useState({});
  const [tagsByDeal, setTagsByDeal] = useState({});
  const [selectedTagIds, setSelectedTagIds] = useState([]);

  const [undoToast, setUndoToast] = useState(null);
  const undoTimerRef = useRef(null);
  const showUndo = (message, onUndo) => {
    if (undoTimerRef.current) clearTimeout(undoTimerRef.current);
    setUndoToast({ message, onUndo });
    undoTimerRef.current = setTimeout(() => setUndoToast(null), 5000);
  };

  const reload = useCallback(async () => {
    try {
      const [ov, cts, cos, dls] = await Promise.all([
        crmOverview(),
        listContacts({ search: searchStr }),
        listCompanies(searchStr),
        listDeals({ search: searchStr }),
      ]);
      setOverview(ov); setContacts(cts); setCompanies(cos); setDeals(dls);
      // Batch tag lookup per entity type
      const [ct, co, dt] = await Promise.all([
        cts.length ? bulkTagsFor('contact', cts.map(x => x.id)) : Promise.resolve({}),
        cos.length ? bulkTagsFor('company', cos.map(x => x.id)) : Promise.resolve({}),
        dls.length ? bulkTagsFor('deal',    dls.map(x => x.id)) : Promise.resolve({}),
      ]);
      setTagsByContact(ct); setTagsByCompany(co); setTagsByDeal(dt);
    } catch (e) { setMsg(`Failed to load: ${e.message}`); }
  }, [searchStr]);

  // Filtered views — apply selected-tag filter per tab
  const visibleContacts  = filterItems(contacts,  tagsByContact, selectedTagIds);
  const visibleCompanies = filterItems(companies, tagsByCompany, selectedTagIds);
  const visibleDeals     = filterItems(deals,     tagsByDeal,    selectedTagIds);

  // Selection is scoped per tab — easiest: re-bind on the currently visible list
  const selectionContacts  = useBulkSelection(visibleContacts);
  const selectionCompanies = useBulkSelection(visibleCompanies);
  const selectionDeals     = useBulkSelection(visibleDeals);

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
          <button className="btn-ghost" onClick={() => setShowImport(true)} title="Import CSV / Excel">
            <Upload size={13} /> Import
          </button>
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
        {[
          ['leads', 'Leads', Inbox],
          ['contacts', 'Contacts', Users],
          ['companies', 'Companies', Building2],
          ['deals', 'Deals Pipeline', Briefcase],
        ].map(([k, lbl, Icon]) => (
          <button key={k} onClick={() => setTab(k)} className={tab === k ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 11 }}>
            <Icon size={12} /> {lbl}
          </button>
        ))}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Search size={12} color="var(--color-text-dim)" />
          <input className="field-input" placeholder="Search..." value={searchStr} onChange={(e) => setSearchStr(e.target.value)} style={{ fontSize: 11, width: 200 }} />
        </div>
      </div>

      <div style={{ padding: '4px 24px' }}>
        <TagFilterBar selectedIds={selectedTagIds} onChange={setSelectedTagIds} />
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {tab === 'leads' && <LeadsTab contacts={contacts} navigate={navigate} flash={flash} />}
        {tab === 'contacts' && (
          visibleContacts.length === 0 ? (
            <EmptyState
              icon={Users}
              title={contacts.length === 0 ? "No contacts yet" : "No contacts match this filter"}
              description={contacts.length === 0
                ? "Add your first lead manually or import a CSV of contacts to let Arjun track your pipeline and Sage prep meetings."
                : "Try clearing the tag filter or search to see everyone."}
              primaryLabel={contacts.length === 0 ? "Add contact" : undefined}
              onPrimary={contacts.length === 0 ? () => setModal({ kind: 'contact', record: null }) : undefined}
              secondaryLabel={contacts.length === 0 ? "Import CSV" : undefined}
              onSecondary={contacts.length === 0 ? () => setShowImport(true) : undefined}
            />
          ) : (
            <>
              <div className="table-panel">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{ width: 24 }}>
                        <BulkCheckbox
                          checked={selectionContacts.all}
                          indeterminate={selectionContacts.some}
                          onChange={() => selectionContacts.toggleAll()}
                          title="Select all visible"
                        />
                      </th>
                      <th>Name</th><th>Title</th><th>Company</th><th>Email</th><th>Phone</th><th>Tags</th><th style={{ width: 110 }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleContacts.map((c) => (
                      <tr
                        key={c.id}
                        onClick={() => navigate(`/crm/contacts/${c.id}`)}
                        style={{
                          background: selectionContacts.isSelected(c.id) ? 'color-mix(in srgb, var(--color-accent) 6%, transparent)' : undefined,
                          cursor: 'pointer',
                        }}
                        title="Open contact"
                      >
                        <td onClick={(e) => e.stopPropagation()}>
                          <BulkCheckbox checked={selectionContacts.isSelected(c.id)} onChange={() => selectionContacts.toggle(c.id)} />
                        </td>
                        <td style={{ fontWeight: 500, color: 'var(--color-text)' }}>
                          {(c.first_name + ' ' + c.last_name).trim() || '—'}
                        </td>
                        <td>{c.title || '—'}</td>
                        <td>{c.company_name || '—'}</td>
                        <td onClick={(e) => e.stopPropagation()}>
                          {c.email ? <a href={`mailto:${c.email}`} style={{ color: 'var(--color-info)' }}>{c.email}</a> : '—'}
                        </td>
                        <td>{c.phone || '—'}</td>
                        <td><TagChips tags={tagsByContact[c.id] || []} size="xs" /></td>
                        <td style={{ display: 'flex', gap: 4 }} onClick={(e) => e.stopPropagation()}>
                          <button className="btn-ghost" style={{ padding: 4 }} onClick={() => navigate(`/crm/contacts/${c.id}`)} title="Open"><ChevronRight size={11} /></button>
                          <button className="btn-ghost" style={{ padding: 4 }} onClick={() => setActivityFor({ kind: 'contact', record: c })} title="Activity"><Activity size={11} /></button>
                          <button className="btn-ghost" style={{ padding: 4 }} onClick={() => setModal({ kind: 'contact', record: c })}><Edit3 size={11} /></button>
                          <button className="btn-ghost" style={{ padding: 4, color: 'var(--color-err)' }} onClick={() => handleDelete('contact', c)}><Trash2 size={11} /></button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <BulkActionBar count={selectionContacts.count} onCancel={selectionContacts.clear}>
                <button
                  onClick={async () => {
                    const ids = Array.from(selectionContacts.selected);
                    if (!confirm(`Delete ${ids.length} contact${ids.length === 1 ? '' : 's'}?`)) return;
                    try {
                      await bulkDeleteContacts(ids);
                      selectionContacts.clear();
                      showUndo(`${ids.length} contact${ids.length === 1 ? '' : 's'} deleted`, null);
                      reload();
                    } catch (e) { flash(`Bulk delete failed: ${e.message}`); }
                  }}
                  className="btn-ghost" style={{ fontSize: 11, color: 'var(--color-err)' }}
                ><Trash2 size={11} /> Delete</button>
              </BulkActionBar>
            </>
          )
        )}

        {tab === 'companies' && (
          visibleCompanies.length === 0 ? (
            <EmptyState
              icon={Building2}
              title={companies.length === 0 ? "No companies yet" : "No companies match this filter"}
              description={companies.length === 0
                ? "Add the companies you sell to or work with — deals and contacts hang off them."
                : "Try clearing the tag filter or search."}
              primaryLabel={companies.length === 0 ? "Add company" : undefined}
              onPrimary={companies.length === 0 ? () => setModal({ kind: 'company', record: null }) : undefined}
            />
          ) : (
            <div className="table-panel">
              <table className="data-table">
                <thead><tr><th>Name</th><th>Industry</th><th>Size</th><th>Website</th><th>Tags</th><th style={{ width: 110 }}></th></tr></thead>
                <tbody>
                  {visibleCompanies.map((c) => (
                    <tr
                      key={c.id}
                      onClick={() => navigate(`/crm/companies/${c.id}`)}
                      style={{ cursor: 'pointer' }}
                      title="Open company"
                    >
                      <td style={{ fontWeight: 500, color: 'var(--color-text)' }}>{c.name}</td>
                      <td>{c.industry || '—'}</td>
                      <td>{c.size || '—'}</td>
                      <td onClick={(e) => e.stopPropagation()}>
                        {c.website ? <a href={c.website.startsWith('http') ? c.website : `https://${c.website}`} target="_blank" rel="noreferrer" style={{ color: 'var(--color-info)' }}>{c.website}</a> : '—'}
                      </td>
                      <td><TagChips tags={tagsByCompany[c.id] || []} size="xs" /></td>
                      <td style={{ display: 'flex', gap: 4 }} onClick={(e) => e.stopPropagation()}>
                        <button className="btn-ghost" style={{ padding: 4 }} onClick={() => navigate(`/crm/companies/${c.id}`)} title="Open"><ChevronRight size={11} /></button>
                        <button className="btn-ghost" style={{ padding: 4 }} onClick={() => setActivityFor({ kind: 'company', record: c })} title="Activity"><Activity size={11} /></button>
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
            <EmptyState
              icon={Briefcase}
              title="No deals in the pipeline"
              description="Create your first deal — Arjun will flag it as stale if it hasn't moved in 2+ weeks, so the pipeline stays alive."
              primaryLabel="Add deal"
              onPrimary={() => setModal({ kind: 'deal', record: null })}
            />
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
                  onOpen={(d) => navigate(`/crm/deals/${d.id}`)}
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

      {showImport && (
        <EntityImportWizard
          defaultEntityType={tab === 'contacts' ? 'contact' : 'contact'}
          onClose={() => setShowImport(false)}
          onDone={() => { setShowImport(false); reload(); }}
        />
      )}

      {activityFor && (
        <Modal
          title={`Activity · ${activityFor.record.name || (activityFor.record.first_name || '') + ' ' + (activityFor.record.last_name || '')}`}
          onClose={() => setActivityFor(null)}
          wide
        >
          <div style={{ marginBottom: 12 }}>
            <TagPicker entityType={activityFor.kind} entityId={activityFor.record.id} onChange={reload} />
          </div>
          {(activityFor.kind === 'contact' || activityFor.kind === 'deal') && (
            <div style={{ marginBottom: 14 }}>
              <SuggestionPanel entityType={activityFor.kind} entityId={activityFor.record.id} />
            </div>
          )}
          <ActivityTimeline entityType={activityFor.kind} entityId={activityFor.record.id} />
        </Modal>
      )}

      {undoToast && (
        <UndoToast
          message={undoToast.message}
          onUndo={undoToast.onUndo ? () => { undoToast.onUndo?.(); setUndoToast(null); } : null}
          onClose={() => setUndoToast(null)}
        />
      )}
    </div>
  );
}


// ── Leads tab — inbound lead-gen home ───────────────────────────────────────
// Surfaces every contact whose `source` isn't 'manual' (i.e. came from the
// public form, email forwarder, WhatsApp, AI prospecting, etc.) plus the
// public-form key management UI that used to live in Settings.
//
// Two reasons this tab exists:
//   1. People doing lead-gen work shouldn't have to bounce between Settings
//      and CRM. Everything lead-related is now one click away.
//   2. The source breakdown band makes attribution legible — "30% from the
//      website form, 50% from email forwards, 20% from referrals."
function LeadsTab({ contacts, navigate, flash }) {
  // Recent inbound = contacts with a non-manual source. Sorted newest first.
  const recent = useMemo(() => {
    return (contacts || [])
      .filter(c => c.source && c.source !== 'manual')
      .sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''))
      .slice(0, 50);
  }, [contacts]);

  // Source breakdown across all leads (manual + others).
  const sourceCounts = useMemo(() => {
    const out = {};
    for (const c of contacts || []) {
      const s = c.source || 'manual';
      out[s] = (out[s] || 0) + 1;
    }
    return Object.entries(out).sort((a, b) => b[1] - a[1]);
  }, [contacts]);

  const last24h = useMemo(() => {
    const cutoff = Date.now() - 86400_000;
    return recent.filter(c => {
      try { return new Date(c.created_at).getTime() >= cutoff; }
      catch { return false; }
    }).length;
  }, [recent]);

  const totalLeads = recent.length;
  const totalContacts = (contacts || []).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Stats band */}
      <div className="card-grid card-grid--sm">
        <Stat label="Inbound leads"   value={totalLeads.toLocaleString()} icon={<Inbox size={14} />} tone="accent" />
        <Stat label="Last 24 hours"   value={last24h.toLocaleString()}    icon={<Sparkles size={14} />} tone="info" />
        <Stat label="All contacts"    value={totalContacts.toLocaleString()} icon={<Users size={14} />} tone="muted" />
        <Stat label="Sources active"  value={sourceCounts.length}          icon={<TrendingUp size={14} />} tone="warn" />
      </div>

      {/* Source breakdown */}
      {sourceCounts.length > 0 && (
        <div className="panel">
          <div className="section-h" style={{ margin: '0 0 10px' }}>
            <h2>Where leads come from</h2>
            <span className="meta">all-time, this workspace</span>
          </div>
          <SourceBars counts={sourceCounts} total={totalContacts} />
        </div>
      )}

      {/* Recent inbound leads list */}
      <div className="panel">
        <div className="section-h" style={{ margin: '0 0 10px' }}>
          <h2>Recent inbound · {recent.length}</h2>
          <span className="meta">contacts captured automatically</span>
        </div>
        {recent.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="No inbound leads yet"
            description="Once you set up a public lead form, email forwarder, or AI prospecting, captured leads will land here. Generate a public-form key below to get started in 2 minutes."
            size="sm"
            minHeight={140}
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {recent.slice(0, 12).map(c => (
              <LeadRow key={c.id} contact={c} onClick={() => navigate(`/crm/contacts/${c.id}`)} />
            ))}
            {recent.length > 12 && (
              <div style={{ fontSize: 11, color: 'var(--color-text-dim)', textAlign: 'center', padding: '6px 0' }}>
                + {recent.length - 12} more inbound leads — switch to the Contacts tab to see them all.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Public form key management */}
      <IntakeKeyCard flash={flash} />

      {/* Future channels — placeholders that link to the doc */}
      <div className="panel" style={{ background: 'var(--color-surface-1)' }}>
        <div className="section-h" style={{ margin: '0 0 10px' }}>
          <h2>Other lead channels</h2>
          <span className="meta">on the roadmap</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 10 }}>
          <ChannelTile
            icon={<Mail size={14} />} title="Email forwarder"
            description="Forward inbound emails to a magic inbox; Iris parses senders into leads."
            status="planned"
          />
          <ChannelTile
            icon={<MessageSquare size={14} />} title="WhatsApp"
            description="Strangers messaging your WhatsApp number become leads automatically."
            status="extends bridge"
          />
          <ChannelTile
            icon={<Sparkles size={14} />} title="AI prospecting"
            description='"Find me 30 D2C brands in Bangalore with 20-100 staff" → ranked candidate list.'
            status="next"
          />
        </div>
      </div>
    </div>
  );
}


// ── Source breakdown bars ────────────────────────────────────────────────────
function SourceBars({ counts, total }) {
  const SOURCE_TONE = {
    public_form: 'var(--color-accent)',
    email:       'var(--color-info)',
    whatsapp:    '#22c55e',
    csv_import:  'var(--color-warn)',
    manual:      'var(--color-text-dim)',
    ai_outbound: '#a78bfa',
    referral:    '#ec4899',
  };
  const SOURCE_LABEL = {
    public_form: 'Public form',
    email:       'Email forward',
    whatsapp:    'WhatsApp',
    csv_import:  'CSV import',
    manual:      'Added manually',
    ai_outbound: 'AI prospecting',
    referral:    'Referral',
  };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {counts.map(([source, count]) => {
        const tone = SOURCE_TONE[source] || 'var(--color-text-muted)';
        const label = SOURCE_LABEL[source] || source;
        const pct = total > 0 ? Math.round((count / total) * 100) : 0;
        return (
          <div key={source}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 3 }}>
              <span style={{ fontSize: 12, color: 'var(--color-text)' }}>{label}</span>
              <span style={{ fontSize: 11, color: 'var(--color-text-dim)', fontFeatureSettings: '"tnum"' }}>
                {count} <span style={{ marginLeft: 4 }}>· {pct}%</span>
              </span>
            </div>
            <div style={{ height: 6, background: 'var(--color-surface-1)', borderRadius: 'var(--r-pill)', overflow: 'hidden' }}>
              <div style={{
                width: `${Math.max(2, pct)}%`, height: '100%', background: tone,
                transition: 'width var(--dur-base) var(--ease-out)',
              }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}


// ── Single inbound-lead row ──────────────────────────────────────────────────
function LeadRow({ contact: c, onClick }) {
  const fullName = `${c.first_name || ''} ${c.last_name || ''}`.trim() || 'Unnamed';
  const SOURCE_TONE = {
    public_form: 'var(--color-accent)', email: 'var(--color-info)',
    whatsapp: '#22c55e', ai_outbound: '#a78bfa', referral: '#ec4899',
    csv_import: 'var(--color-warn)',
  };
  const tone = SOURCE_TONE[c.source] || 'var(--color-text-muted)';
  const ago = (() => {
    if (!c.created_at) return '';
    try {
      const d = new Date(c.created_at);
      const diff = Date.now() - d.getTime();
      if (diff < 3600_000) return `${Math.max(1, Math.floor(diff / 60_000))}m ago`;
      if (diff < 86400_000) return `${Math.floor(diff / 3600_000)}h ago`;
      return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    } catch { return ''; }
  })();
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 12px',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--r-md)',
        cursor: 'pointer', textAlign: 'left',
        color: 'var(--color-text)',
      }}
    >
      <div style={{
        width: 30, height: 30, borderRadius: 'var(--r-pill)',
        background: 'var(--color-surface-3)',
        color: 'var(--color-text-muted)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 11, fontWeight: 700, flexShrink: 0,
      }}>
        {(fullName.split(/\s+/).filter(Boolean).slice(0, 2).map(s => s[0]).join('') || '?').toUpperCase()}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 500 }}>{fullName}</div>
        <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
          {c.email || c.phone || '—'}{c.company_name ? ` · ${c.company_name}` : ''}
        </div>
      </div>
      <span className="pill-base" style={{
        background: `color-mix(in srgb, ${tone} 14%, transparent)`,
        color: tone,
        border: `1px solid color-mix(in srgb, ${tone} 28%, transparent)`,
      }}>{c.source}</span>
      <span style={{ fontSize: 10.5, color: 'var(--color-text-dim)', minWidth: 60, textAlign: 'right' }}>{ago}</span>
      <ChevronRight size={12} color="var(--color-text-dim)" />
    </button>
  );
}


// ── Future-channel tile ──────────────────────────────────────────────────────
function ChannelTile({ icon, title, description, status }) {
  return (
    <div style={{
      padding: 12,
      background: 'var(--color-surface-2)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--r-md)',
      opacity: 0.85,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
        <span style={{ color: 'var(--color-text-muted)' }}>{icon}</span>
        <span style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--color-text)' }}>{title}</span>
        <span className="pill-base pill-muted" style={{ marginLeft: 'auto', fontSize: 10 }}>{status}</span>
      </div>
      <p style={{ fontSize: 11, color: 'var(--color-text-muted)', margin: 0, lineHeight: 1.5 }}>
        {description}
      </p>
    </div>
  );
}


// ── Public-form key management (moved from Settings) ────────────────────────
function IntakeKeyCard({ flash }) {
  const [keys, setKeys] = useState([]);
  const [busy, setBusy] = useState(false);
  const [label, setLabel] = useState('');
  const [justCreated, setJustCreated] = useState(null);
  const [showSnippet, setShowSnippet] = useState(false);

  const reload = async () => {
    try { setKeys(await listIntakeKeys()); }
    catch (e) { flash?.(`Could not load keys: ${e.message || e}`); }
  };
  useEffect(() => { reload(); }, []);  // eslint-disable-line react-hooks/exhaustive-deps

  const handleCreate = async () => {
    setBusy(true);
    try {
      const r = await createIntakeKey(label.trim() || 'New key');
      setJustCreated(r);
      setLabel('');
      reload();
    } catch (e) { flash?.(`Create failed: ${e.message || e}`); }
    setBusy(false);
  };

  const handleRevoke = async (id) => {
    if (!confirm('Revoke this key? Any forms still using it will start failing immediately.')) return;
    try {
      await revokeIntakeKey(id);
      flash?.('Key revoked.');
      reload();
    } catch (e) { flash?.(`Revoke failed: ${e.message || e}`); }
  };

  const copyText = (txt) => {
    try { navigator.clipboard.writeText(txt); flash?.('Copied.'); }
    catch { flash?.('Copy failed — select manually.'); }
  };

  const activeKey = justCreated || keys.find(k => !k.revoked_at);
  const sampleSnippet = activeKey ? buildSnippet(activeKey.key || activeKey.key_prefix) : '';

  return (
    <div className="panel">
      <div className="section-h" style={{ margin: '0 0 10px' }}>
        <h2>Public form keys</h2>
        <span className="meta">drop a 5-line snippet on any website</span>
      </div>

      {/* Just-created banner */}
      {justCreated && (
        <div style={{
          padding: '10px 12px', marginBottom: 12,
          background: 'var(--color-accent-soft)',
          border: '1px solid color-mix(in srgb, var(--color-accent) 32%, transparent)',
          borderRadius: 'var(--r-md)',
        }}>
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6,
            fontSize: 11, fontWeight: 600, color: 'var(--color-accent)',
            letterSpacing: 0.5, textTransform: 'uppercase',
          }}>
            <Check size={11} /> New key — copy it now
          </div>
          <div style={{
            display: 'flex', gap: 6, alignItems: 'center',
            background: 'var(--color-bg)',
            padding: '6px 10px', borderRadius: 'var(--r-sm)',
            border: '1px solid var(--color-border)',
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
            fontSize: 11, wordBreak: 'break-all',
          }}>
            <span style={{ flex: 1, color: 'var(--color-text)' }}>{justCreated.key}</span>
            <button className="btn-ghost btn-sm" onClick={() => copyText(justCreated.key)}>
              <Copy size={11} /> Copy
            </button>
          </div>
          <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', marginTop: 6 }}>
            We don't store the raw key — only its hash. Save it somewhere safe.
          </div>
          <button className="btn-ghost btn-sm" style={{ marginTop: 8 }} onClick={() => setJustCreated(null)}>
            Got it
          </button>
        </div>
      )}

      {/* Existing keys */}
      {keys.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 12 }}>
          {keys.map(k => (
            <div key={k.id} style={{
              display: 'flex', alignItems: 'center', gap: 8,
              padding: '8px 10px',
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--r-sm)',
              fontSize: 11.5,
              opacity: k.revoked_at ? 0.5 : 1,
            }}>
              <code style={{ fontSize: 10.5, color: 'var(--color-text)' }}>{k.key_prefix}</code>
              <span style={{ color: 'var(--color-text-muted)' }}>{k.label || '(unlabelled)'}</span>
              <span style={{ color: 'var(--color-text-dim)', marginLeft: 'auto', fontSize: 10 }}>
                {k.use_count || 0} uses
                {k.last_used_at && ` · last ${new Date(k.last_used_at).toLocaleDateString()}`}
              </span>
              {k.revoked_at ? (
                <span style={{ fontSize: 10, color: 'var(--color-err)', fontWeight: 600 }}>REVOKED</span>
              ) : (
                <button className="btn-ghost btn-sm" style={{ color: 'var(--color-err)' }}
                  onClick={() => handleRevoke(k.id)} title="Revoke key">
                  <Trash2 size={10} />
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
        <input
          className="field-input"
          placeholder='Label (e.g. "homepage form", "footer signup")'
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          maxLength={80}
          style={{ fontSize: 12, flex: 1 }}
        />
        <button className="btn-primary" onClick={handleCreate} disabled={busy} style={{ fontSize: 12 }}>
          {busy ? 'Creating…' : <><Plus size={12} /> Generate key</>}
        </button>
      </div>

      {/* Embed snippet */}
      {activeKey && (
        <>
          <button className="btn-ghost btn-sm" onClick={() => setShowSnippet(v => !v)}>
            {showSnippet ? 'Hide' : 'Show'} embed snippet
          </button>
          {showSnippet && (
            <pre style={{
              marginTop: 6, padding: 10,
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--r-sm)',
              fontSize: 11, lineHeight: 1.5,
              fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
              color: 'var(--color-text)',
              whiteSpace: 'pre-wrap', wordBreak: 'break-all',
              overflowX: 'auto',
            }}>
              {sampleSnippet}
            </pre>
          )}
          {showSnippet && (
            <button className="btn-ghost btn-sm" style={{ marginTop: 6 }}
              onClick={() => copyText(sampleSnippet)}>
              <Copy size={11} /> Copy snippet
            </button>
          )}
        </>
      )}
    </div>
  );
}


function buildSnippet(keyOrPlaceholder) {
  const looksRaw = keyOrPlaceholder && keyOrPlaceholder.startsWith('nx_pub_') && !keyOrPlaceholder.endsWith('…');
  const keyToken = looksRaw ? keyOrPlaceholder : 'YOUR_KEY_HERE';
  return `<!-- Drop on any website to capture leads into NexusAgent. -->
<form id="lead-form">
  <input name="name" placeholder="Your name" required />
  <input name="email" placeholder="Email" required />
  <input name="company" placeholder="Company (optional)" />
  <textarea name="message" placeholder="What can we help with?"></textarea>
  <button type="submit">Send</button>
</form>
<script>
document.getElementById('lead-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target));
  data.intake_key = '${keyToken}';
  const r = await fetch('https://YOUR-NEXUS-HOST/api/public/leads', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  alert(r.ok ? 'Thanks — we\\'ll be in touch.' : 'Send failed, please email us.');
  e.target.reset();
});
</script>`;
}


// ── Stat card (mirrors the History page's pattern) ──────────────────────────
function Stat({ label, value, icon, tone = 'dim' }) {
  const toneColor = {
    accent: 'var(--color-accent)',
    info:   'var(--color-info)',
    ok:     'var(--color-ok)',
    warn:   'var(--color-warn)',
    err:    'var(--color-err)',
    dim:    'var(--color-text-dim)',
    muted:  'var(--color-text-muted)',
  }[tone];
  return (
    <div className="kpi">
      <div className="kpi-icon" style={{ background: `color-mix(in srgb, ${toneColor} 14%, transparent)`, color: toneColor }}>
        {icon}
      </div>
      <div className="kpi-body">
        <div className="kpi-label">{label}</div>
        <div className="kpi-value">{value}</div>
      </div>
    </div>
  );
}
