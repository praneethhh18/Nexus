import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Users, Building2, Briefcase, Plus, Search, Trash2, Edit3, X, TrendingUp, DollarSign, Phone, Mail, Calendar, MessageSquare, Upload, Activity, ChevronRight, Inbox, Sparkles, Copy, Check, Loader2, AlertCircle, Download } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { listIntakeKeys, createIntakeKey, revokeIntakeKey } from '../services/tags';
import { extractEmail, saveLeadFromEmail, forgeBrainstorm, forgeAccept } from '../services/crm';
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
import { prepareDialForContact } from '../services/voice_calls';
import { useBulkSelection, BulkCheckbox, BulkActionBar, UndoToast } from '../components/BulkActionBar';
import { TagChips, TagPicker } from '../components/TagChips';
import TagFilterBar, { filterItems } from '../components/TagFilterBar';
import { getCached, setCached, keyFor } from '../services/dataCache';
import { useTerm } from '../services/industryTerms';
import { getContactFieldsForIndustry } from '../services/industryContactFields';
import { getCurrentBusiness } from '../services/auth';
import EntityImportWizard from '../components/EntityImportWizard';
import ActivityTimeline from '../components/ActivityTimeline';
import SuggestionPanel from '../components/SuggestionPanel';

const STAGE_COLORS = {
  lead: 'var(--color-info)', qualified: '#a78bfa', proposal: 'var(--color-warn)',
  negotiation: '#ec4899', won: 'var(--color-ok)', lost: 'var(--color-text-dim)',
};

// INR + en-IN by default — NexusAgent is built for Indian SMBs. `cur` arg
// kept for forward-compat if a deal explicitly carries USD/EUR/etc.
const money = (v, cur = 'INR') => new Intl.NumberFormat('en-IN', { style: 'currency', currency: cur || 'INR', maximumFractionDigits: 0 }).format(v || 0);

// ── Quick-action buttons on a contact row (Vox call · WhatsApp · Email) ────
const waLink = (phone) => phone ? `https://wa.me/${phone.replace(/\D/g, '')}` : null;

function ContactQuickActions({ contact, flash, size = 11 }) {
  const wa = waLink(contact.phone);
  const onCall = async (e) => {
    e.stopPropagation();
    if (!contact.phone) return flash?.('No phone number on this contact');
    try {
      const r = await prepareDialForContact({ contact_id: contact.id, purpose: 'a quick check-in' });
      if (r?.precall_url) window.open(r.precall_url, '_blank', 'noopener');
      else flash?.('Could not start call — no precall URL returned');
    } catch (err) {
      flash?.(`Vox call failed: ${err.message}`);
    }
  };
  const stop = (e) => e.stopPropagation();
  const linkBtn = (href, title, Icon, color) => (
    <a href={href} target="_blank" rel="noreferrer" onClick={stop} title={title}
       className="btn-ghost" style={{ padding: 4, display: 'inline-flex', color }}>
      <Icon size={size} />
    </a>
  );
  return (
    <>
      <button
        className="btn-ghost"
        style={{ padding: 4, opacity: contact.phone ? 1 : 0.35 }}
        onClick={onCall}
        title={contact.phone ? `Call ${contact.phone} via Vox` : 'No phone — add one to call'}
        disabled={!contact.phone}
      >
        <Phone size={size} />
      </button>
      {wa && linkBtn(wa, `WhatsApp ${contact.phone}`, MessageSquare, 'var(--color-ok)')}
      {contact.email && linkBtn(`mailto:${contact.email}`, `Email ${contact.email}`, Mail, 'var(--color-info)')}
    </>
  );
}

// ── Reusable modal ──────────────────────────────────────────────────────────
function Modal({ title, onClose, children, wide = false }) {
  // ESC to close; backdrop click does NOT close. An accidental click
  // outside (especially common when a child popover like TagPicker
  // overflows the modal bounds) used to wipe the user's half-written
  // edit — TagPicker dropdowns in particular surfaced this as "the
  // page got cracked" because the modal vanished mid-interaction.
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose?.(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);
  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{
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
function ContactForm({ initial, companies, industry, onSubmit, onCancel }) {
  // Industry-aware schema for extra fields below the standard CRM ones.
  // Empty array for industries without a schema → only base fields show.
  const extraFields = getContactFieldsForIndustry(industry);

  // Parse incoming custom_fields (stored as JSON text in DB) into an object
  // so the inputs can edit individual keys without touching the JSON string.
  const initialExtras = (() => {
    if (!initial?.custom_fields) return {};
    if (typeof initial.custom_fields === 'object') return initial.custom_fields;
    try { return JSON.parse(initial.custom_fields); } catch { return {}; }
  })();

  const [f, setF] = useState({
    first_name: '', last_name: '', email: '', phone: '', title: '',
    company_id: '', notes: '', tags: '', source: '',
    ...(initial || {}),
  });
  const [extras, setExtras] = useState(initialExtras);
  const set = (k, v) => setF((prev) => ({ ...prev, [k]: v }));
  const setExtra = (k, v) => setExtras((prev) => ({ ...prev, [k]: v }));

  const submit = (e) => {
    e.preventDefault();
    // Send custom_fields as an object — backend handles JSON serialisation
    // + normalisation. Skip empties so we don't write '{}' for everyone.
    const cleanExtras = Object.fromEntries(
      Object.entries(extras).filter(([, v]) => v !== '' && v != null)
    );
    onSubmit({
      ...f,
      ...(Object.keys(cleanExtras).length ? { custom_fields: cleanExtras } : {}),
    });
  };

  return (
    <form onSubmit={submit}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="First name">
          <input className="field-input" autoFocus placeholder="e.g. Praneeth"
                 value={f.first_name} onChange={(e) => set('first_name', e.target.value)} maxLength={80} />
        </Field>
        <Field label="Last name">
          <input className="field-input" placeholder="e.g. P K"
                 value={f.last_name} onChange={(e) => set('last_name', e.target.value)} maxLength={80} />
        </Field>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="Email">
          <input className="field-input" type="email" placeholder="praneeth@company.com"
                 value={f.email} onChange={(e) => set('email', e.target.value)} maxLength={200} />
        </Field>
        <Field label="Phone">
          <input className="field-input" type="tel" placeholder="+91 98765 43210"
                 value={f.phone} onChange={(e) => set('phone', e.target.value)} maxLength={40} />
        </Field>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="Role / Title">
          <input className="field-input" list="contact-role-suggestions"
                 placeholder="e.g. VP Engineering"
                 value={f.title} onChange={(e) => set('title', e.target.value)} maxLength={120} />
          <datalist id="contact-role-suggestions">
            <option value="Founder" /><option value="Co-founder" /><option value="CEO" />
            <option value="CTO" /><option value="VP Engineering" />
            <option value="Head of Sales" /><option value="Sales Manager" />
            <option value="Marketing Manager" /><option value="Product Manager" />
            <option value="Customer Success" /><option value="Operations" />
            <option value="Finance / CFO" /><option value="HR" />
          </datalist>
        </Field>
        <Field label="Source">
          <select className="field-select" value={f.source || ''}
                  onChange={(e) => set('source', e.target.value)} style={{ width: '100%' }}>
            <option value="">— manual entry —</option>
            <option value="website">Website / Lead form</option>
            <option value="referral">Referral</option>
            <option value="outbound">Cold outreach</option>
            <option value="event">Event / Conference</option>
            <option value="linkedin">LinkedIn</option>
            <option value="email_paste">Forwarded email</option>
            <option value="import">CSV import</option>
            <option value="other">Other</option>
          </select>
        </Field>
      </div>
      <Field label="Company">
        <select className="field-select" value={f.company_id || ''}
                onChange={(e) => set('company_id', e.target.value)} style={{ width: '100%' }}>
          <option value="">— unlinked —</option>
          {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </Field>

      {/* Industry-specific extras — only renders when the workspace's
          industry has a schema in industryContactFields.js. Falls through
          silently for industries we haven't tuned. */}
      {extraFields.length > 0 && (
        <div style={{
          marginTop: 4, padding: 12,
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--r-md)',
        }}>
          <div style={{
            fontSize: 11, fontWeight: 700, letterSpacing: 0.5, textTransform: 'uppercase',
            color: 'var(--color-text-dim)', marginBottom: 10,
          }}>
            {industry} details
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {extraFields.map((spec) => (
              <Field key={spec.key} label={spec.label}>
                {spec.type === 'select' ? (
                  <select
                    className="field-select"
                    value={extras[spec.key] || ''}
                    onChange={(e) => setExtra(spec.key, e.target.value)}
                  >
                    {(spec.options || []).map((opt) => (
                      <option key={opt} value={opt}>{opt || '— select —'}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    className="field-input"
                    type={spec.type || 'text'}
                    value={extras[spec.key] || ''}
                    onChange={(e) => setExtra(spec.key, e.target.value)}
                    placeholder={spec.placeholder || ''}
                    maxLength={200}
                  />
                )}
                {spec.hint && (
                  <span style={{ fontSize: 10.5, color: 'var(--color-text-dim)', marginTop: 2 }}>
                    {spec.hint}
                  </span>
                )}
              </Field>
            ))}
          </div>
        </div>
      )}

      <Field label="Notes">
        <textarea className="field-input" rows={3} value={f.notes} onChange={(e) => set('notes', e.target.value)} maxLength={2000} />
      </Field>
      {/* Tag editor inline — only when editing an existing contact (need
          an id to link tags). When adding a new contact, the tags can be
          added on the second save (after the row exists). */}
      {initial?.id ? (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 0.4,
                        textTransform: 'uppercase', color: 'var(--color-text-dim)',
                        marginBottom: 6 }}>Tags</div>
          <TagPicker entityType="contact" entityId={initial.id} />
        </div>
      ) : (
        <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', marginTop: -6, marginBottom: 8 }}>
          Save first to enable tags. You can also add tags from the contact&apos;s detail page.
        </div>
      )}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 12 }}>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary">{initial ? 'Save' : 'Add Contact'}</button>
      </div>
    </form>
  );
}

// ── Company form ────────────────────────────────────────────────────────────
// Shared industry + size enum — used by both CompanyForm and the
// filter dropdowns below. Tuned for Indian SMB diversity; "Other"
// captures the long tail without forcing the LLM to invent a new
// category.
const INDUSTRY_OPTIONS = [
  'SaaS / Software', 'E-commerce', 'Retail', 'Manufacturing',
  'Healthcare', 'Education', 'Finance / Banking', 'Real Estate',
  'Consulting', 'Marketing / Advertising', 'Media / Entertainment',
  'Hospitality', 'Logistics / Supply Chain', 'Construction',
  'Legal', 'Non-profit', 'Government', 'Other',
];
const SIZE_OPTIONS = [
  { value: '1-10',     label: 'Solo / Tiny (1–10)' },
  { value: '11-50',    label: 'Small (11–50)' },
  { value: '51-200',   label: 'Growing (51–200)' },
  { value: '201-1000', label: 'Mid-market (201–1,000)' },
  { value: '1000+',    label: 'Enterprise (1,000+)' },
];

function CompanyForm({ initial, onSubmit, onCancel }) {
  const [f, setF] = useState({
    name: '', industry: '', website: '', size: '', notes: '', tags: '',
    phone: '', email: '', country: 'India', ...(initial || {}),
  });
  const set = (k, v) => setF((prev) => ({ ...prev, [k]: v }));
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(f); }}>
      <Field label="Company name *">
        <input className="field-input" required autoFocus
               placeholder="e.g. Nimbus Analytics"
               value={f.name} onChange={(e) => set('name', e.target.value)} maxLength={200} />
      </Field>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="Industry">
          <select className="field-select" value={f.industry}
                  onChange={(e) => set('industry', e.target.value)}
                  style={{ width: '100%' }}>
            <option value="">— pick one —</option>
            {INDUSTRY_OPTIONS.map(i => <option key={i} value={i}>{i}</option>)}
          </select>
        </Field>
        <Field label="Team size">
          <select className="field-select" value={f.size}
                  onChange={(e) => set('size', e.target.value)}
                  style={{ width: '100%' }}>
            <option value="">— pick one —</option>
            {SIZE_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </Field>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="Website">
          <input className="field-input" type="url"
                 placeholder="https://nimbus.example.com"
                 value={f.website} onChange={(e) => set('website', e.target.value)} maxLength={250} />
        </Field>
        <Field label="Country">
          <input className="field-input" value={f.country}
                 onChange={(e) => set('country', e.target.value)} maxLength={80} />
        </Field>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="Main phone">
          <input className="field-input" type="tel"
                 placeholder="+91 98765 43210"
                 value={f.phone} onChange={(e) => set('phone', e.target.value)} maxLength={40} />
        </Field>
        <Field label="Main email">
          <input className="field-input" type="email"
                 placeholder="hello@nimbus.example.com"
                 value={f.email} onChange={(e) => set('email', e.target.value)} maxLength={200} />
        </Field>
      </div>
      <Field label="Notes">
        <textarea className="field-input" rows={3}
                  placeholder="Anything worth remembering — founder background, key contacts, deal history…"
                  value={f.notes} onChange={(e) => set('notes', e.target.value)} maxLength={2000} />
      </Field>
      {initial?.id ? (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: 0.4,
                        textTransform: 'uppercase', color: 'var(--color-text-dim)',
                        marginBottom: 6 }}>Tags</div>
          <TagPicker entityType="company" entityId={initial.id} />
        </div>
      ) : (
        <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', marginBottom: 8 }}>
          Save first to enable tags. You can also add tags from the company&apos;s detail page.
        </div>
      )}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 12 }}>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary">{initial ? 'Save changes' : 'Add company'}</button>
      </div>
    </form>
  );
}

// ── Deal form ────────────────────────────────────────────────────────────────
function DealForm({ initial, contacts, companies, onSubmit, onCancel }) {
  const [f, setF] = useState({
    name: '', value: 0, currency: 'INR', stage: 'lead', probability_pct: 20,
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
// Stale-while-revalidate cache so navigating back to /crm renders the last
// snapshot instantly instead of flashing an empty contacts/companies/deals
// table. Filtered/searched views aren't cached — only the unfiltered base.
const CRM_CACHE_KEY = 'crm:page';


// Pure sorter at module scope — moved out of the component so React
// Compiler can memoize the consuming `reload` callback cleanly. The
// closures inside the component scope used to capture state, which
// confused the compiler's memoization analysis.
function applyCrmSort(rows, key) {
  if (!Array.isArray(rows) || rows.length === 0) return rows;
  const cmp = (a, b, asc = true) => {
    if (a == null && b == null) return 0;
    if (a == null) return 1;
    if (b == null) return -1;
    if (typeof a === 'number' && typeof b === 'number') return (a - b) * (asc ? 1 : -1);
    return String(a).localeCompare(String(b)) * (asc ? 1 : -1);
  };
  const out = [...rows];
  const nameOf = (r) => (r.name || `${r.first_name || ''} ${r.last_name || ''}`).trim().toLowerCase();
  if (key === 'name_asc')  out.sort((a, b) => cmp(nameOf(a), nameOf(b), true));
  else if (key === 'name_desc') out.sort((a, b) => cmp(nameOf(a), nameOf(b), false));
  else if (key === 'created_desc') out.sort((a, b) => cmp(b.created_at, a.created_at, true));
  else if (key === 'created_asc')  out.sort((a, b) => cmp(a.created_at, b.created_at, true));
  else if (key === 'last_contacted_desc') out.sort((a, b) => cmp(
    b.last_contacted_at || b.last_interaction_at,
    a.last_contacted_at || a.last_interaction_at, true));
  else if (key === 'value_desc') out.sort((a, b) => cmp(Number(a.value || 0), Number(b.value || 0), false));
  else if (key === 'value_asc')  out.sort((a, b) => cmp(Number(a.value || 0), Number(b.value || 0), true));
  return out;
}


// ── Smart filter presets ──────────────────────────────────────────────
// Each preset has a key, label, group (for sectioning in the panel),
// and a predicate (row) => bool. Predicates are pure so they can be
// applied during render without re-fetching.
const _now = () => Date.now();
const _daysSince = (iso) => {
  if (!iso) return Infinity;
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return Infinity;
  return (_now() - t) / 86400_000;
};
const SMART_PRESETS = {
  contacts: [
    { key: 'no_email',        label: 'Missing email',          group: 'Data quality',
      pred: (r) => !(r.email || '').trim() },
    { key: 'no_phone',        label: 'Missing phone',          group: 'Data quality',
      pred: (r) => !(r.phone || '').trim() },
    { key: 'no_company',      label: 'No company linked',      group: 'Data quality',
      pred: (r) => !r.company_id && !r.company_name },
    { key: 'stale_30d',       label: 'Stale (>30d no contact)', group: 'Activity',
      pred: (r) => _daysSince(r.last_contacted_at || r.last_interaction_at) > 30 },
    { key: 'never_contacted', label: 'Never contacted',        group: 'Activity',
      pred: (r) => !(r.last_contacted_at || r.last_interaction_at) },
    { key: 'has_open_deals',  label: 'Has open deals',         group: 'Activity',
      pred: (r) => Number(r.open_deals_count || 0) > 0 },
  ],
  companies: [
    { key: 'no_industry',    label: 'Missing industry',         group: 'Data quality',
      pred: (r) => !(r.industry || '').trim() },
    { key: 'no_website',     label: 'Missing website',          group: 'Data quality',
      pred: (r) => !(r.website || '').trim() },
    { key: 'no_size',        label: 'Missing team size',        group: 'Data quality',
      pred: (r) => !(r.size || '').trim() },
    { key: 'has_open_deals', label: 'Has open deals',           group: 'Activity',
      pred: (r) => Number(r.open_deals_count || 0) > 0 },
    { key: 'no_deals',       label: 'No deals attached',        group: 'Activity',
      pred: (r) => Number(r.deals_count || r.open_deals_count || 0) === 0 },
    { key: 'no_contacts',    label: 'No contacts linked',       group: 'Activity',
      pred: (r) => Number(r.contacts_count || 0) === 0 },
  ],
  deals: [
    { key: 'stale_14d',          label: 'Stale (>14d no update)', group: 'Activity',
      pred: (r) => _daysSince(r.updated_at) > 14 },
    { key: 'closing_this_month', label: 'Closing this month',     group: 'Activity',
      pred: (r) => {
        if (!r.close_date && !r.expected_close_date) return false;
        const d = new Date(r.close_date || r.expected_close_date);
        const now = new Date();
        return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
      } },
    { key: 'high_value',         label: 'High value (>₹1L)',       group: 'Value',
      pred: (r) => Number(r.value || 0) >= 100_000 },
    { key: 'low_value',          label: 'Small (<₹50k)',           group: 'Value',
      pred: (r) => Number(r.value || 0) > 0 && Number(r.value || 0) < 50_000 },
    { key: 'open',               label: 'Open (not won/lost)',     group: 'Stage',
      pred: (r) => !['won', 'lost'].includes(r.stage) },
    { key: 'no_contact',         label: 'No contact attached',     group: 'Data quality',
      pred: (r) => !r.contact_id && !r.contact_name },
  ],
};

function SmartFilterBar({
  tab, sourceFilter, setSourceFilter,
  industryFilter, setIndustryFilter,
  stageFilter, setStageFilter,
  smartFilters, setSmartFilters,
}) {
  const [open, setOpen] = useState(false);
  const presets = SMART_PRESETS[tab] || [];
  const groups = useMemo(() => {
    const out = {};
    for (const p of presets) (out[p.group] ||= []).push(p);
    return out;
  }, [presets]);
  // Count active filters (primary + multi)
  const activeCount =
    (sourceFilter ? 1 : 0) +
    (industryFilter ? 1 : 0) +
    (stageFilter ? 1 : 0) +
    smartFilters.size;
  const togglePreset = (key) => {
    setSmartFilters((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  };
  const clearAll = () => {
    setSourceFilter(''); setIndustryFilter(''); setStageFilter('');
    setSmartFilters(new Set());
  };
  // Primary chip: Source / Industry / Stage — single-value, click to clear
  const primary = tab === 'contacts' ? sourceFilter
    : tab === 'companies' ? industryFilter
    : tab === 'deals'     ? stageFilter
    : '';
  const primaryLabel = tab === 'contacts' ? 'Source'
    : tab === 'companies' ? 'Industry'
    : tab === 'deals'     ? 'Stage'
    : '';
  const clearPrimary = () => {
    if (tab === 'contacts')  setSourceFilter('');
    if (tab === 'companies') setIndustryFilter('');
    if (tab === 'deals')     setStageFilter('');
  };
  return (
    <div style={{ padding: '0 24px 8px', display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center', position: 'relative' }}>
      <div style={{ position: 'relative' }}>
        <button
          onClick={() => setOpen(o => !o)}
          className={open || activeCount > 0 ? 'btn-primary' : 'btn-ghost'}
          style={{ fontSize: 11, padding: '4px 10px', display: 'inline-flex', gap: 5, alignItems: 'center' }}
        >
          <Activity size={11} /> Filter
          {activeCount > 0 && (
            <span style={{
              fontSize: 9, fontWeight: 700, padding: '1px 6px', borderRadius: 10,
              background: 'rgba(255,255,255,0.25)', color: 'inherit',
            }}>{activeCount}</span>
          )}
        </button>
        {open && (
          <>
            <div onClick={() => setOpen(false)}
                 style={{ position: 'fixed', inset: 0, zIndex: 50, background: 'transparent' }} />
            <div style={{
              position: 'absolute', top: 'calc(100% + 6px)', left: 0,
              width: 340, maxHeight: 'min(520px, 70vh)', overflow: 'auto',
              background: 'var(--color-bg-elev)',
              border: '1px solid var(--color-border-strong)',
              borderRadius: 12, zIndex: 51,
              boxShadow: '0 18px 48px rgba(0,0,0,0.45)',
              padding: 12,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text)' }}>Filters</span>
                {activeCount > 0 && (
                  <button onClick={clearAll}
                          style={{ fontSize: 10.5, color: 'var(--color-text-muted)', background: 'none', border: 'none', cursor: 'pointer' }}>
                    Clear all
                  </button>
                )}
              </div>
              {/* Primary (single-value) section */}
              {primaryLabel && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 0.6, textTransform: 'uppercase', color: 'var(--color-text-dim)', marginBottom: 6 }}>
                    {primaryLabel}
                  </div>
                  <select
                    value={primary}
                    onChange={(e) => {
                      const v = e.target.value;
                      if (tab === 'contacts')  setSourceFilter(v);
                      if (tab === 'companies') setIndustryFilter(v);
                      if (tab === 'deals')     setStageFilter(v);
                    }}
                    className="field-input"
                    style={{ width: '100%', fontSize: 12 }}
                  >
                    <option value="">— any —</option>
                    {tab === 'contacts' && ['manual', 'website', 'referral', 'outbound', 'event', 'linkedin', 'email_paste', 'import']
                      .map(v => <option key={v} value={v}>{v.replace('_', ' ')}</option>)}
                    {tab === 'companies' && INDUSTRY_OPTIONS
                      .map(v => <option key={v} value={v}>{v}</option>)}
                    {tab === 'deals' && ['lead', 'qualified', 'proposal', 'negotiation', 'won', 'lost']
                      .map(v => <option key={v} value={v}>{v}</option>)}
                  </select>
                </div>
              )}
              {/* Smart preset checkbox sections, grouped */}
              {Object.entries(groups).map(([group, items]) => (
                <div key={group} style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 0.6, textTransform: 'uppercase', color: 'var(--color-text-dim)', marginBottom: 6 }}>
                    {group}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    {items.map(p => {
                      const checked = smartFilters.has(p.key);
                      return (
                        <label key={p.key} style={{
                          display: 'flex', alignItems: 'center', gap: 8, padding: '5px 8px',
                          borderRadius: 6, cursor: 'pointer', fontSize: 12,
                          background: checked ? 'var(--color-accent-soft)' : 'transparent',
                          color: 'var(--color-text)',
                        }}
                        onMouseEnter={(e) => { if (!checked) e.currentTarget.style.background = 'var(--color-surface-1)'; }}
                        onMouseLeave={(e) => { if (!checked) e.currentTarget.style.background = 'transparent'; }}>
                          <input type="checkbox" checked={checked} onChange={() => togglePreset(p.key)}
                                 style={{ cursor: 'pointer' }} />
                          <span>{p.label}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Active filter chips — small dismissable pills for what's
          currently filtering, mirroring Zoho/Linear-style. Lets the
          user clear individual filters without reopening the panel. */}
      {primary && (
        <span style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          padding: '3px 8px', borderRadius: 12, fontSize: 11,
          background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
        }}>
          {primaryLabel}: {String(primary).replace('_', ' ').replace(/ \/.+$/, '')}
          <button onClick={clearPrimary} aria-label="Clear filter"
                  style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0, display: 'flex' }}>
            <X size={11} />
          </button>
        </span>
      )}
      {[...smartFilters].map((k) => {
        const p = presets.find(x => x.key === k);
        if (!p) return null;
        return (
          <span key={k} style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '3px 8px', borderRadius: 12, fontSize: 11,
            background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
          }}>
            {p.label}
            <button onClick={() => setSmartFilters(prev => {
              const next = new Set(prev); next.delete(k); return next;
            })} aria-label="Remove filter"
                    style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 0, display: 'flex' }}>
              <X size={11} />
            </button>
          </span>
        );
      })}
    </div>
  );
}


export default function CRM() {
  const navigate = useNavigate();
  // Industry-aware vocabulary — same product, the user sees "Patients"
  // (Healthcare), "Listings" (Real estate), "Students" (Education), etc.
  // Fallback for businesses with no industry: generic CRM terms.
  const t = useTerm();
  const _cached = getCached(keyFor(CRM_CACHE_KEY)) || {};
  // Persist active tab across navigation so clicking a row → detail
  // page → Back returns to the SAME tab the user came from (Companies
  // or Deals), not always Contacts.
  const [tab, setTab] = useState(() => {
    const saved = sessionStorage.getItem('nexus_crm_tab');
    return saved && ['contacts', 'companies', 'deals', 'leads'].includes(saved) ? saved : 'contacts';
  });
  useEffect(() => { sessionStorage.setItem('nexus_crm_tab', tab); }, [tab]);
  // Per-tab sort key, also persisted. Default values are picked so the
  // first impression of each tab is useful (newest contacts, biggest
  // deals first).
  const [sortKey, setSortKey] = useState(() => {
    const saved = sessionStorage.getItem('nexus_crm_sort');
    return saved || 'name_asc';
  });
  useEffect(() => { sessionStorage.setItem('nexus_crm_sort', sortKey); }, [sortKey]);

  // Primary single-value filters (Source / Industry / Stage) per tab.
  // Reset on tab switch in switchTab().
  const [sourceFilter, setSourceFilter] = useState('');
  const [industryFilter, setIndustryFilter] = useState('');
  const [stageFilter, setStageFilter] = useState('');
  // Multi-criteria smart filter set — held as a flat Set of pre-defined
  // preset keys. Each key maps to a row-level predicate in SMART_PRESETS
  // (defined at module scope). Example keys: "contacts:no_email",
  // "deals:closing_this_month".
  const [smartFilters, setSmartFilters] = useState(() => new Set());
  // Bake tab-switch sort reset into the click handler instead of a
  // separate effect — react-compiler can't memoize an effect that
  // setState's based on a piece of state it doesn't depend on.
  const switchTab = useCallback((next) => {
    setTab(next);
    setSortKey(next === 'deals' ? 'value_desc' : 'name_asc');
    // Reset cross-tab smart filters so they don't bleed (e.g. an
    // industry filter from Companies still active when user switches
    // to Deals).
    setSourceFilter('');
    setIndustryFilter('');
    setStageFilter('');
    setSmartFilters(new Set());
  }, []);

  // ── Export current visible tab as CSV ───────────────────────────────
  const handleExport = () => {
    let rows, headers, filename;
    if (tab === 'contacts') {
      rows = visibleContacts;
      headers = ['First name', 'Last name', 'Email', 'Phone', 'Company', 'Role', 'Created'];
      filename = `nexus_contacts_${new Date().toISOString().slice(0, 10)}.csv`;
      rows = rows.map(r => [
        r.first_name || '', r.last_name || '', r.email || '', r.phone || '',
        r.company_name || '', r.role || r.title || '', r.created_at || '',
      ]);
    } else if (tab === 'companies') {
      rows = visibleCompanies;
      headers = ['Name', 'Industry', 'Size', 'Website', 'Created'];
      filename = `nexus_companies_${new Date().toISOString().slice(0, 10)}.csv`;
      rows = rows.map(r => [
        r.name || '', r.industry || '', r.size || '', r.website || '', r.created_at || '',
      ]);
    } else if (tab === 'deals') {
      rows = visibleDeals;
      headers = ['Name', 'Stage', 'Value (INR)', 'Probability', 'Company', 'Contact', 'Created'];
      filename = `nexus_deals_${new Date().toISOString().slice(0, 10)}.csv`;
      rows = rows.map(r => [
        r.name || r.title || '', r.stage || '', r.value || 0, r.probability || '',
        r.company_name || '', r.contact_name || '', r.created_at || '',
      ]);
    } else {
      return;
    }
    // CSV with proper escaping (quoting cells that contain commas/quotes/newlines)
    const esc = (v) => {
      const s = String(v ?? '');
      return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
    };
    const csv = [headers, ...rows].map(r => r.map(esc).join(',')).join('\n');
    const blob = new Blob(['﻿', csv], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename; a.click();
  };
  const [overview, setOverview] = useState(_cached.overview ?? null);
  const [contacts, setContacts] = useState(_cached.contacts ?? []);
  const [companies, setCompanies] = useState(_cached.companies ?? []);
  const [deals, setDeals] = useState(_cached.deals ?? []);
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

  // eslint-disable-next-line react-hooks/preserve-manual-memoization
  const reload = useCallback(async () => {
    try {
      const [ov, cts, cos, dls] = await Promise.all([
        crmOverview(),
        listContacts({ search: searchStr }),
        listCompanies(searchStr),
        listDeals({ search: searchStr }),
      ]);
      setOverview(ov); setContacts(cts); setCompanies(cos); setDeals(dls);
      // Cache only the unfiltered base view so the next mount paints fast.
      if (!searchStr) {
        setCached(keyFor(CRM_CACHE_KEY), {
          overview: ov, contacts: cts, companies: cos, deals: dls,
        });
      }
      // Batch tag lookup per entity type
      const [ct, co, dt] = await Promise.all([
        cts.length ? bulkTagsFor('contact', cts.map(x => x.id)) : Promise.resolve({}),
        cos.length ? bulkTagsFor('company', cos.map(x => x.id)) : Promise.resolve({}),
        dls.length ? bulkTagsFor('deal',    dls.map(x => x.id)) : Promise.resolve({}),
      ]);
      setTagsByContact(ct); setTagsByCompany(co); setTagsByDeal(dt);
    } catch (e) { setMsg(`Failed to load: ${e.message}`); }
  }, [searchStr]);

  // Compose primary single-value filter + smart preset checkbox
  // predicates. All predicates AND together (every active filter must
  // be true for a row to survive).
  const smartPredicate = (tabKey) => {
    const presets = SMART_PRESETS[tabKey] || [];
    const active = presets.filter(p => smartFilters.has(p.key));
    if (active.length === 0) return () => true;
    return (r) => active.every(p => {
      try { return p.pred(r); } catch { return false; }
    });
  };
  const visibleContacts  = applyCrmSort(
    filterItems(contacts, tagsByContact, selectedTagIds)
      .filter(r => !sourceFilter || (r.source || 'manual') === sourceFilter)
      .filter(smartPredicate('contacts')),
    sortKey,
  );
  const visibleCompanies = applyCrmSort(
    filterItems(companies, tagsByCompany, selectedTagIds)
      .filter(r => !industryFilter || (r.industry || '').toLowerCase().includes(industryFilter.toLowerCase().split(' /')[0]))
      .filter(smartPredicate('companies')),
    sortKey,
  );
  const visibleDeals     = applyCrmSort(
    filterItems(deals, tagsByDeal, selectedTagIds)
      .filter(r => !stageFilter || r.stage === stageFilter)
      .filter(smartPredicate('deals')),
    sortKey,
  );

  // Selection is scoped per tab — easiest: re-bind on the currently visible list
  const selectionContacts  = useBulkSelection(visibleContacts);
  const selectionCompanies = useBulkSelection(visibleCompanies);
  const selectionDeals     = useBulkSelection(visibleDeals);

  // eslint-disable-next-line react-hooks/set-state-in-effect
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
          <p>{t('contacts')}, {t('companies').toLowerCase()}, and your {t('deal_pipeline').toLowerCase()}</p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn-ghost" onClick={() => setShowImport(true)} title="Import CSV / Excel">
            <Upload size={13} /> Import
          </button>
          {tab === 'contacts' && <button className="btn-primary" onClick={() => setModal({ kind: 'contact', record: null })}><Plus size={13} /> {t('contact_add')}</button>}
          {tab === 'companies' && <button className="btn-primary" onClick={() => setModal({ kind: 'company', record: null })}><Plus size={13} /> Add {t('company').toLowerCase()}</button>}
          {tab === 'deals' && <button className="btn-primary" onClick={() => setModal({ kind: 'deal', record: null })}><Plus size={13} /> Add {t('deal').toLowerCase()}</button>}
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
            { label: t('contacts'),  value: overview.contacts,  sub: null, icon: Users, color: 'var(--color-info)' },
            { label: t('companies'), value: overview.companies, sub: null, icon: Building2, color: '#a78bfa' },
            // Open deals: big number = count, sub-line = total value
            // ("4 · ₹24,75,000" used to read as gibberish to first-time
            // users; the split makes the relationship obvious).
            { label: `Open ${t('deals').toLowerCase()}`,
              value: overview.open_deals_count,
              sub: `worth ${money(overview.open_deals_value)}`,
              icon: Briefcase, color: 'var(--color-warn)' },
            // No sub-line — the label "Won this month" already carries
            // the time window. Adding "this month" twice looked sloppy.
            { label: t('kpi_won'), value: money(overview.won_this_month),
              sub: null,
              icon: TrendingUp, color: 'var(--color-ok)' },
          ].map(({ label, value, sub, icon: Icon, color }, i) => (
            <div key={i} className="panel" style={{ padding: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: `${color}22`, color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={16} />
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{label}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)', lineHeight: 1.2 }}>{value}</div>
                {sub && (
                  <div style={{ fontSize: 10, color: 'var(--color-text-muted)', marginTop: 1 }}>{sub}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 6, padding: '0 24px 8px', borderBottom: '1px solid var(--color-surface-2)' }}>
        {[
          ['leads',     t('leads'),         Inbox],
          ['contacts',  t('contacts'),      Users],
          ['companies', t('companies'),     Building2],
          ['deals',     t('deal_pipeline'), Briefcase],
        ].map(([k, lbl, Icon]) => (
          <button key={k} onClick={() => switchTab(k)} className={tab === k ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 11 }}>
            <Icon size={12} /> {lbl}
          </button>
        ))}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Search size={12} color="var(--color-text-dim)" />
          <input className="field-input" placeholder="Search..." value={searchStr} onChange={(e) => setSearchStr(e.target.value)} style={{ fontSize: 11, width: 200 }} />
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value)}
            className="field-input"
            style={{ fontSize: 11, padding: '4px 8px', cursor: 'pointer' }}
            title="Sort by"
          >
            {tab === 'contacts' && (
              <>
                <option value="name_asc">Name A→Z</option>
                <option value="name_desc">Name Z→A</option>
                <option value="created_desc">Newest first</option>
                <option value="created_asc">Oldest first</option>
                <option value="last_contacted_desc">Recently contacted</option>
              </>
            )}
            {tab === 'companies' && (
              <>
                <option value="name_asc">Name A→Z</option>
                <option value="name_desc">Name Z→A</option>
                <option value="created_desc">Newest first</option>
                <option value="created_asc">Oldest first</option>
              </>
            )}
            {tab === 'deals' && (
              <>
                <option value="value_desc">Value (high→low)</option>
                <option value="value_asc">Value (low→high)</option>
                <option value="name_asc">Name A→Z</option>
                <option value="created_desc">Newest first</option>
              </>
            )}
          </select>
          <button
            onClick={handleExport}
            className="btn-ghost"
            style={{ fontSize: 11, padding: '4px 10px' }}
            title="Download current view as CSV"
          >
            <Download size={11} /> Export
          </button>
        </div>
      </div>

      <div style={{ padding: '4px 24px' }}>
        <TagFilterBar selectedIds={selectedTagIds} onChange={setSelectedTagIds} />
      </div>

      {/* Smart filter pills — only render the chip for the ACTIVE
          filter, plus the "Filter" trigger button. Full multi-criteria
          panel lives in SmartFilterPanel below. This replaces the
          earlier flat-chip-row design that became unwieldy. */}
      <SmartFilterBar
        tab={tab}
        sourceFilter={sourceFilter} setSourceFilter={setSourceFilter}
        industryFilter={industryFilter} setIndustryFilter={setIndustryFilter}
        stageFilter={stageFilter} setStageFilter={setStageFilter}
        smartFilters={smartFilters} setSmartFilters={setSmartFilters}
      />

      <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {tab === 'leads' && (
          <>
            <div style={{
              marginBottom: 14, padding: '10px 14px', borderRadius: 8,
              background: 'var(--color-accent-soft)',
              border: '1px solid color-mix(in srgb, var(--color-accent) 22%, transparent)',
              display: 'flex', alignItems: 'center', gap: 10,
            }}>
              <Inbox size={14} color="var(--color-accent)" />
              <div style={{ fontSize: 12, color: 'var(--color-text)', lineHeight: 1.45 }}>
                <strong>{t('leads')}</strong> are contacts captured from outside
                — public lead forms, forwarded emails, the Lead Hunter agent,
                or website signups. Triage them here before they graduate to
                Contacts.
              </div>
            </div>
            <LeadsTab contacts={contacts} navigate={navigate} flash={flash} />
          </>
        )}
        {tab === 'contacts' && (
          visibleContacts.length === 0 ? (
            <EmptyState
              icon={Users}
              title={contacts.length === 0 ? `No ${t('contacts').toLowerCase()} yet` : `No ${t('contacts').toLowerCase()} match this filter`}
              description={contacts.length === 0
                ? `Add your first ${t('primary_record')} manually or import a CSV — Arjun will start tracking your pipeline and Sage will prep meetings.`
                : "Try clearing the tag filter or search to see everyone."}
              primaryLabel={contacts.length === 0 ? t('contact_add') : undefined}
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
                      <th>Name</th>
                      <th className="hide-on-mobile">Title</th>
                      <th className="hide-on-mobile">{t('company')}</th>
                      <th className="hide-on-mobile">Email</th>
                      <th>Phone</th>
                      <th className="hide-on-mobile">Tags</th>
                      <th style={{ width: 110 }}></th>
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
                        <td className="hide-on-mobile">{c.title || '—'}</td>
                        <td className="hide-on-mobile">{c.company_name || '—'}</td>
                        <td className="hide-on-mobile" onClick={(e) => e.stopPropagation()}>
                          {c.email ? <a href={`mailto:${c.email}`} style={{ color: 'var(--color-info)' }}>{c.email}</a> : '—'}
                        </td>
                        <td>{c.phone || '—'}</td>
                        <td className="hide-on-mobile"><TagChips tags={tagsByContact[c.id] || []} size="xs" /></td>
                        <td style={{ display: 'flex', gap: 4 }} onClick={(e) => e.stopPropagation()}>
                          <ContactQuickActions contact={c} flash={flash} />
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
              title={companies.length === 0 ? `No ${t('companies').toLowerCase()} yet` : `No ${t('companies').toLowerCase()} match this filter`}
              description={companies.length === 0
                ? `Add the ${t('companies').toLowerCase()} you work with — ${t('deals').toLowerCase()} and ${t('contacts').toLowerCase()} hang off them.`
                : "Try clearing the tag filter or search."}
              primaryLabel={companies.length === 0 ? `Add ${t('company').toLowerCase()}` : undefined}
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
              title={`No ${t('deals').toLowerCase()} in the pipeline`}
              description={`Create your first ${t('deal').toLowerCase()} — Arjun will flag it as stale if it hasn't moved in 2+ weeks, so the pipeline stays alive.`}
              primaryLabel={`Add ${t('deal').toLowerCase()}`}
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
        <Modal title={modal.record ? `Edit ${t('contact').toLowerCase()}` : t('contact_add')} onClose={() => setModal(null)} wide>
          <ContactForm
            initial={modal.record}
            companies={companies}
            industry={getCurrentBusiness()?.industry || ''}
            onSubmit={(d) => handleSubmit('contact', d)}
            onCancel={() => setModal(null)} />
        </Modal>
      )}
      {modal?.kind === 'company' && (
        <Modal title={modal.record ? `Edit ${t('company').toLowerCase()}` : `Add ${t('company').toLowerCase()}`} onClose={() => setModal(null)} wide>
          <CompanyForm initial={modal.record}
            onSubmit={(d) => handleSubmit('company', d)} onCancel={() => setModal(null)} />
        </Modal>
      )}
      {modal?.kind === 'deal' && (
        <Modal title={modal.record ? `Edit ${t('deal').toLowerCase()}` : `Add ${t('deal').toLowerCase()}`} onClose={() => setModal(null)} wide>
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
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [forgeOpen, setForgeOpen] = useState(false);
  // ── Filter + sort state ─────────────────────────────────────────────
  const [search, setSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');         // '' = all
  const [bucketFilter, setBucketFilter] = useState('all');      // all | high | medium | low | spam | unscored
  const [sortMode, setSortMode] = useState('score_then_recent');// score_then_recent | recent | score_desc | score_asc

  // Inbound = contacts with a non-manual source. The Leads tab is for
  // inbound/qualification work; deliberately filters manual-add contacts out
  // since they belong on the Contacts tab.
  const inboundAll = useMemo(
    () => (contacts || []).filter(c => c.source && c.source !== 'manual'),
    [contacts],
  );

  // Apply filters → sort → take recent.
  const recent = useMemo(() => {
    const s = search.trim().toLowerCase();
    let pool = inboundAll;
    if (sourceFilter) pool = pool.filter(c => c.source === sourceFilter);
    if (bucketFilter !== 'all') {
      pool = pool.filter(c => {
        const b = scoreBucket(c.lead_score);
        if (bucketFilter === 'unscored') return b === null;
        return b === bucketFilter;
      });
    }
    if (s) {
      pool = pool.filter(c => {
        const hay = [
          c.first_name, c.last_name, c.email, c.phone,
          c.company_name, c.title, c.lead_score_reason,
        ].filter(Boolean).join(' ').toLowerCase();
        return hay.includes(s);
      });
    }

    const cmpRecent = (a, b) => (b.created_at || '').localeCompare(a.created_at || '');
    const cmpScoreDesc = (a, b) => {
      const av = a.lead_score == null ? -1 : a.lead_score;
      const bv = b.lead_score == null ? -1 : b.lead_score;
      return bv - av;
    };
    const cmpScoreAsc = (a, b) => {
      const av = a.lead_score == null ?  101 : a.lead_score;  // unscored sinks
      const bv = b.lead_score == null ?  101 : b.lead_score;
      return av - bv;
    };

    if (sortMode === 'recent')      pool = [...pool].sort(cmpRecent);
    else if (sortMode === 'score_desc') pool = [...pool].sort((a, b) => cmpScoreDesc(a, b) || cmpRecent(a, b));
    else if (sortMode === 'score_asc')  pool = [...pool].sort(cmpScoreAsc);
    else /* score_then_recent (default) */ pool = [...pool].sort((a, b) => cmpScoreDesc(a, b) || cmpRecent(a, b));

    return pool.slice(0, 100);
  }, [inboundAll, search, sourceFilter, bucketFilter, sortMode]);

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
        <div className="section-h" style={{ margin: '0 0 10px', flexWrap: 'wrap', gap: 8 }}>
          <h2>Recent inbound · {recent.length}{inboundAll.length !== recent.length ? ` of ${inboundAll.length}` : ''}</h2>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <button
              className="btn-primary btn-sm"
              onClick={() => setEmailModalOpen(true)}
              title="Paste a forwarded email — AI extracts the sender and creates a scored lead"
            >
              <Mail size={11} /> Capture from email
            </button>
            <button
              className="btn-ghost btn-sm"
              onClick={() => setForgeOpen(true)}
              title="AI brainstorms candidate companies for a prospecting brief"
            >
              <Sparkles size={11} /> AI prospect
            </button>
          </div>
        </div>

        {/* Filter + sort bar — only when there's enough data to make filtering useful */}
        {inboundAll.length > 3 && (
          <div style={{
            display: 'flex', flexWrap: 'wrap', gap: 8, alignItems: 'center',
            marginBottom: 10,
            padding: '8px 10px',
            background: 'var(--color-surface-1)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--r-md)',
          }}>
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              flex: 1, minWidth: 200,
              padding: '4px 10px',
              background: 'var(--color-bg)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--r-sm)',
            }}>
              <Search size={11} color="var(--color-text-dim)" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search name, email, company…"
                style={{
                  flex: 1, background: 'transparent', border: 'none', outline: 'none',
                  color: 'var(--color-text)', fontSize: 12,
                }}
              />
            </div>

            <select
              className="field-select"
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              style={{ fontSize: 11.5 }}
            >
              <option value="">All sources</option>
              <option value="public_form">Public form</option>
              <option value="email_paste">Email paste</option>
              <option value="ai_outbound">AI prospecting</option>
              <option value="csv_import">CSV import</option>
              <option value="referral">Referral</option>
              <option value="whatsapp">WhatsApp</option>
            </select>

            <select
              className="field-select"
              value={sortMode}
              onChange={(e) => setSortMode(e.target.value)}
              style={{ fontSize: 11.5 }}
              title="Sort"
            >
              <option value="score_then_recent">Best fit, then newest</option>
              <option value="recent">Newest first</option>
              <option value="score_desc">Score: high → low</option>
              <option value="score_asc">Score: low → high</option>
            </select>

            <div style={{ display: 'flex', gap: 4 }}>
              {[
                { k: 'all',      label: 'All' },
                { k: 'high',     label: 'High' },
                { k: 'medium',   label: 'Med' },
                { k: 'low',      label: 'Low' },
                { k: 'spam',     label: 'Spam' },
                { k: 'unscored', label: '?' },
              ].map(({ k, label }) => (
                <button
                  key={k}
                  className={bucketFilter === k ? 'btn-primary btn-sm' : 'btn-ghost btn-sm'}
                  onClick={() => setBucketFilter(k)}
                  style={{ fontSize: 10.5 }}
                >
                  {label}
                </button>
              ))}
            </div>

            {(search || sourceFilter || bucketFilter !== 'all' || sortMode !== 'score_then_recent') && (
              <button
                className="btn-ghost btn-sm"
                onClick={() => {
                  setSearch(''); setSourceFilter(''); setBucketFilter('all'); setSortMode('score_then_recent');
                }}
                title="Clear all filters"
                style={{ color: 'var(--color-text-dim)' }}
              >
                <X size={10} /> Clear
              </button>
            )}
          </div>
        )}
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

      {emailModalOpen && (
        <CaptureFromEmailModal
          onClose={() => setEmailModalOpen(false)}
          onSaved={(contactId) => {
            setEmailModalOpen(false);
            navigate(`/crm/contacts/${contactId}`);
          }}
          flash={flash}
        />
      )}

      {forgeOpen && (
        <ForgeModal
          onClose={() => setForgeOpen(false)}
          onSaved={(count) => {
            setForgeOpen(false);
            flash?.(`${count} candidate${count === 1 ? '' : 's'} added — verify each in the Leads tab.`);
          }}
          flash={flash}
        />
      )}
    </div>
  );
}


// ── Capture-from-email modal ────────────────────────────────────────────────
// Three-step flow in one modal:
//   1. paste raw email content (textarea)
//   2. click Extract — LLM parses, regex falls back if parsing failed
//   3. user edits the preview fields, clicks Save → contact created + scored
function CaptureFromEmailModal({ onClose, onSaved, flash }) {
  const [step, setStep] = useState('paste');  // 'paste' | 'preview'
  const [rawEmail, setRawEmail] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [extracted, setExtracted] = useState(null);  // { sender_name, sender_email, ... fallback }

  const handleExtract = async () => {
    if (rawEmail.trim().length < 10) {
      setError('Paste the email content first.');
      return;
    }
    setBusy(true); setError('');
    try {
      const r = await extractEmail(rawEmail);
      setExtracted({ ...r });
      setStep('preview');
    } catch (e) {
      setError(e.message || 'Extraction failed.');
    }
    setBusy(false);
  };

  const handleSave = async () => {
    if (!extracted) return;
    if (!extracted.sender_name?.trim() && !extracted.sender_email?.trim()) {
      setError('Add at least a name or email before saving.');
      return;
    }
    setBusy(true); setError('');
    try {
      const r = await saveLeadFromEmail({
        raw_email: rawEmail,
        sender_name: extracted.sender_name || '',
        sender_email: extracted.sender_email || '',
        sender_company: extracted.sender_company || '',
        subject: extracted.subject || '',
        summary: extracted.summary || '',
      });
      flash?.(r.deduped
        ? 'Already in your CRM — logged this email as an interaction.'
        : 'Lead captured + auto-scored against your ICP.');
      onSaved?.(r.contact_id);
    } catch (e) {
      setError(e.message || 'Save failed.');
    }
    setBusy(false);
  };

  const updateField = (k, v) => setExtracted((x) => ({ ...x, [k]: v }));

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 300,
        background: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 640,
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border-strong)',
          borderRadius: 'var(--r-lg)',
          maxHeight: '92vh', display: 'flex', flexDirection: 'column',
          boxShadow: 'var(--shadow-3)',
        }}
      >
        {/* Header */}
        <div style={{
          padding: '14px 18px',
          borderBottom: '1px solid var(--color-border)',
          display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <div style={{
            width: 32, height: 32, borderRadius: 'var(--r-md)',
            background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Mail size={16} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>
              Capture lead from email
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
              {step === 'paste'
                ? 'Paste a forwarded email — AI extracts the sender'
                : 'Review the extracted fields, edit anything, then save'}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 4 }}
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: 18, overflow: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {error && (
            <div style={{
              padding: '8px 10px',
              background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-err) 28%, transparent)',
              borderRadius: 'var(--r-sm)',
              fontSize: 12, color: 'var(--color-err)',
              display: 'flex', alignItems: 'flex-start', gap: 6,
            }}>
              <AlertCircle size={13} style={{ marginTop: 1, flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {step === 'paste' && (
            <>
              <div style={{ fontSize: 11, color: 'var(--color-text-muted)', lineHeight: 1.55 }}>
                Paste anything — a forwarded chain, a raw <code>From: …</code> header,
                or just the body. The AI will pull out who it's from and what they want.
              </div>
              <textarea
                className="field-input"
                rows={14}
                value={rawEmail}
                onChange={(e) => setRawEmail(e.target.value)}
                placeholder={"From: Priya Sharma <priya@acme.com>\nSubject: Interested in your CRM\n\nHi there,\n\nWe're a 200-person SaaS team looking for a privacy-first CRM. Could we hop on a 15-minute call this week?\n\nThanks,\nPriya"}
                style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 12, lineHeight: 1.55 }}
              />
            </>
          )}

          {step === 'preview' && extracted && (
            <>
              {extracted.fallback && (
                <div style={{
                  padding: '8px 10px',
                  background: 'color-mix(in srgb, var(--color-warn) 10%, transparent)',
                  border: '1px solid color-mix(in srgb, var(--color-warn) 28%, transparent)',
                  borderRadius: 'var(--r-sm)',
                  fontSize: 11.5, color: 'var(--color-warn)',
                }}>
                  AI parsing didn't land cleanly — these fields came from a regex fallback.
                  Edit anything that looks off before saving.
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                <FieldInput label="Sender name"
                  value={extracted.sender_name || ''}
                  onChange={(v) => updateField('sender_name', v)} />
                <FieldInput label="Sender email" type="email"
                  value={extracted.sender_email || ''}
                  onChange={(v) => updateField('sender_email', v)} />
              </div>
              <FieldInput label="Company"
                value={extracted.sender_company || ''}
                onChange={(v) => updateField('sender_company', v)} />
              <FieldInput label="Original subject"
                value={extracted.subject || ''}
                onChange={(v) => updateField('subject', v)} />
              <div>
                <label style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 500 }}>
                  Summary
                </label>
                <textarea
                  className="field-input"
                  rows={3}
                  value={extracted.summary || ''}
                  onChange={(e) => updateField('summary', e.target.value)}
                  style={{ marginTop: 4 }}
                />
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '12px 18px',
          borderTop: '1px solid var(--color-border)',
          display: 'flex', gap: 8, alignItems: 'center', justifyContent: 'flex-end',
        }}>
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
          {step === 'paste' ? (
            <button
              className="btn-primary"
              onClick={handleExtract}
              disabled={busy || rawEmail.trim().length < 10}
            >
              {busy
                ? <><Loader2 size={12} className="animate-spin" /> Extracting…</>
                : <><Sparkles size={12} /> Extract</>}
            </button>
          ) : (
            <>
              <button className="btn-ghost btn-sm" onClick={() => setStep('paste')}>
                ← Back
              </button>
              <button
                className="btn-primary"
                onClick={handleSave}
                disabled={busy}
              >
                {busy
                  ? <><Loader2 size={12} className="animate-spin" /> Saving…</>
                  : <><Plus size={12} /> Save as lead</>}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}


// ── Forge AI prospecting modal ──────────────────────────────────────────────
// Three-step flow:
//   1. Brief → user describes the target profile in plain English.
//   2. Brainstorm → AI proposes 8-12 candidate companies, each with a
//      verify-hint and a confidence number. Honestly labelled as
//      suggestions to verify, NOT as confirmed leads.
//   3. Select → user toggles which candidates to keep, hits Save → those
//      become real contacts in CRM tagged source='ai_outbound'.
function ForgeModal({ onClose, onSaved, flash }) {
  const [step, setStep] = useState('brief');         // 'brief' | 'pick'
  const [brief, setBrief] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [candidates, setCandidates] = useState([]);
  const [icpUsed, setIcpUsed] = useState(false);
  const [selected, setSelected] = useState({});      // index → bool

  const handleBrainstorm = async () => {
    if (brief.trim().length < 10) {
      setError('Describe the target profile in at least one sentence.');
      return;
    }
    setBusy(true); setError('');
    try {
      const r = await forgeBrainstorm(brief);
      setCandidates(r.candidates || []);
      setIcpUsed(!!r.icp_used);
      // Pre-select high-confidence ones (≥ 70) so the default action is sensible.
      const initial = {};
      (r.candidates || []).forEach((c, i) => { if ((c.confidence ?? 0) >= 70) initial[i] = true; });
      setSelected(initial);
      setStep('pick');
      if ((r.candidates || []).length === 0) {
        setError('The model came back empty. Try a more specific brief.');
      }
    } catch (e) {
      setError(e.message || 'Brainstorm failed.');
    }
    setBusy(false);
  };

  const handleSave = async () => {
    const toSave = candidates.filter((_, i) => selected[i]);
    if (toSave.length === 0) {
      setError('Pick at least one candidate to save.');
      return;
    }
    setBusy(true); setError('');
    try {
      const r = await forgeAccept(toSave, brief);
      const created = r.created?.length || 0;
      if ((r.skipped?.length || 0) > 0) {
        flash?.(`${created} added · ${r.skipped.length} skipped (already in CRM).`);
      }
      onSaved?.(created);
    } catch (e) {
      setError(e.message || 'Save failed.');
    }
    setBusy(false);
  };

  const totalSelected = Object.values(selected).filter(Boolean).length;

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 300,
        background: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 760,
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border-strong)',
          borderRadius: 'var(--r-lg)',
          maxHeight: '92vh', display: 'flex', flexDirection: 'column',
          boxShadow: 'var(--shadow-3)',
        }}
      >
        <div style={{
          padding: '14px 18px', borderBottom: '1px solid var(--color-border)',
          display: 'flex', alignItems: 'center', gap: 10,
        }}>
          <div style={{
            width: 32, height: 32, borderRadius: 'var(--r-md)',
            background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Sparkles size={16} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>
              AI prospecting · Forge
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
              {step === 'brief'
                ? 'Describe who you want to reach — AI brainstorms candidate companies'
                : 'Review the suggestions, verify them, save the keepers'}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'transparent', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 4 }}
            aria-label="Close"
          >
            <X size={16} />
          </button>
        </div>

        <div style={{ padding: 18, overflow: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {error && (
            <div style={{
              padding: '8px 10px',
              background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-err) 28%, transparent)',
              borderRadius: 'var(--r-sm)',
              fontSize: 12, color: 'var(--color-err)',
              display: 'flex', alignItems: 'flex-start', gap: 6,
            }}>
              <AlertCircle size={13} style={{ marginTop: 1, flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {step === 'brief' && (
            <>
              <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', lineHeight: 1.55 }}>
                Forge suggests candidate companies that <em>might</em> match your brief. These
                are <strong>AI suggestions, not verified leads</strong> — each comes with a Google
                query you can run to confirm. Save the ones that check out, ignore the rest.
              </div>
              <textarea
                className="field-input"
                rows={6}
                value={brief}
                onChange={(e) => setBrief(e.target.value)}
                placeholder={"e.g. D2C brands in Bangalore with 20-100 staff that raised funding in the last 18 months — focus on health & wellness niches."}
                style={{ fontSize: 12.5, lineHeight: 1.55 }}
              />
              {!icpUsed && (
                <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
                  Tip: set an Ideal Customer Profile in Settings — Forge will use it
                  alongside this brief to sharpen the suggestions.
                </div>
              )}
            </>
          )}

          {step === 'pick' && (
            <>
              <div style={{
                padding: '8px 10px',
                background: 'color-mix(in srgb, var(--color-warn) 10%, transparent)',
                border: '1px solid color-mix(in srgb, var(--color-warn) 28%, transparent)',
                borderRadius: 'var(--r-sm)',
                fontSize: 11.5, color: 'var(--color-warn)',
                display: 'flex', alignItems: 'flex-start', gap: 6,
              }}>
                <AlertCircle size={13} style={{ marginTop: 1, flexShrink: 0 }} />
                <span>
                  These are AI suggestions. Run the verify-hint Google search per row to
                  confirm before reaching out. Saved candidates appear in your CRM tagged
                  <code style={{ marginLeft: 4 }}>source: ai_outbound</code>.
                </span>
              </div>

              {candidates.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 30, color: 'var(--color-text-dim)', fontSize: 12.5 }}>
                  The model didn't return any candidates. Try a more specific brief.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {candidates.map((c, i) => (
                    <CandidateCard
                      key={i}
                      candidate={c}
                      checked={!!selected[i]}
                      onToggle={() => setSelected((s) => ({ ...s, [i]: !s[i] }))}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        <div style={{
          padding: '12px 18px', borderTop: '1px solid var(--color-border)',
          display: 'flex', gap: 8, alignItems: 'center', justifyContent: 'flex-end', flexWrap: 'wrap',
        }}>
          {step === 'pick' && (
            <button className="btn-ghost btn-sm" onClick={() => { setStep('brief'); setError(''); }}>
              ← Edit brief
            </button>
          )}
          <button className="btn-ghost" onClick={onClose}>Cancel</button>
          {step === 'brief' ? (
            <button className="btn-primary" onClick={handleBrainstorm} disabled={busy}>
              {busy
                ? <><Loader2 size={12} className="animate-spin" /> Brainstorming…</>
                : <><Sparkles size={12} /> Brainstorm</>}
            </button>
          ) : (
            <button className="btn-primary" onClick={handleSave} disabled={busy || totalSelected === 0}>
              {busy
                ? <><Loader2 size={12} className="animate-spin" /> Saving…</>
                : `Save ${totalSelected || ''} to CRM`}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}


function CandidateCard({ candidate: c, checked, onToggle }) {
  const conf = c.confidence ?? 0;
  const tone = conf >= 70 ? 'var(--color-ok)' : conf >= 40 ? 'var(--color-info)' : 'var(--color-text-dim)';
  return (
    <label style={{
      display: 'flex', gap: 10, alignItems: 'flex-start',
      padding: 10,
      background: checked ? 'color-mix(in srgb, var(--color-accent) 8%, var(--color-surface-1))' : 'var(--color-surface-1)',
      border: `1px solid ${checked ? 'color-mix(in srgb, var(--color-accent) 32%, transparent)' : 'var(--color-border)'}`,
      borderRadius: 'var(--r-md)',
      cursor: 'pointer',
      transition: 'border-color var(--dur-fast) var(--ease-out), background var(--dur-fast) var(--ease-out)',
    }}>
      <input
        type="checkbox"
        checked={checked}
        onChange={onToggle}
        style={{ marginTop: 3, accentColor: 'var(--color-accent)', cursor: 'pointer' }}
      />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
            {c.company_name}
          </span>
          {c.industry && (
            <span className="pill-base pill-muted">{c.industry}</span>
          )}
          {c.size_band && c.size_band !== 'unknown' && (
            <span className="pill-base pill-muted">{c.size_band}</span>
          )}
          <span
            className="pill-base"
            style={{
              marginLeft: 'auto',
              background: `color-mix(in srgb, ${tone} 14%, transparent)`,
              color: tone,
              border: `1px solid color-mix(in srgb, ${tone} 28%, transparent)`,
              fontFeatureSettings: '"tnum"',
            }}
            title="AI confidence (lower = verify harder)"
          >
            {conf}%
          </span>
        </div>
        {c.why_it_fits && (
          <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', marginTop: 4, lineHeight: 1.55 }}>
            {c.why_it_fits}
          </div>
        )}
        {c.suggested_contact_role && (
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 4 }}>
            Likely contact: <strong style={{ color: 'var(--color-text)' }}>{c.suggested_contact_role}</strong>
          </div>
        )}
        {c.verify_hint && (
          <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', marginTop: 4, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
            Verify with: <a
              href={`https://www.google.com/search?q=${encodeURIComponent(c.verify_hint)}`}
              target="_blank" rel="noreferrer"
              style={{ color: 'var(--color-accent)' }}
              onClick={(e) => e.stopPropagation()}
            >
              {c.verify_hint}
            </a>
          </div>
        )}
      </div>
    </label>
  );
}


function FieldInput({ label, value, onChange, type = 'text' }) {
  return (
    <div>
      <label style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 500 }}>
        {label}
      </label>
      <input
        type={type}
        className="field-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{ marginTop: 4 }}
      />
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


// ── Lead-score helpers (mirror the backend bucket logic) ────────────────────
function scoreBucket(score) {
  if (score == null) return null;
  if (score >= 80) return 'high';
  if (score >= 50) return 'medium';
  if (score >= 20) return 'low';
  return 'spam';
}

function ScoreBadge({ score }) {
  const bucket = scoreBucket(score);
  if (bucket === null) {
    return (
      <span className="pill-base pill-muted" title="Not scored yet — open the contact and click Rescore.">
        ?
      </span>
    );
  }
  const TONE = {
    high:   'var(--color-ok)',
    medium: 'var(--color-info)',
    low:    'var(--color-text-dim)',
    spam:   'var(--color-err)',
  };
  const LABEL = { high: 'High', medium: 'Med', low: 'Low', spam: 'Spam' };
  const tone = TONE[bucket];
  return (
    <span
      className="pill-base"
      style={{
        background: `color-mix(in srgb, ${tone} 14%, transparent)`,
        color: tone,
        border: `1px solid color-mix(in srgb, ${tone} 28%, transparent)`,
        fontFeatureSettings: '"tnum"',
      }}
      title={`Lead score: ${score}/100`}
    >
      {LABEL[bucket]} · {score}
    </span>
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
      <ScoreBadge score={c.lead_score} />
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
  // eslint-disable-next-line react-hooks/set-state-in-effect
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
function Stat({ label, value, sub, icon, tone = 'dim' }) {
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
        {sub && (
          <div style={{ fontSize: 10.5, color: 'var(--color-text-muted)', marginTop: 2 }}>{sub}</div>
        )}
      </div>
    </div>
  );
}
