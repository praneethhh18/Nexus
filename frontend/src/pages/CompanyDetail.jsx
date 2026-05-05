/**
 * Company detail page — every contact, deal, and invoice tied to one company,
 * plus quick actions to extend the relationship: add a contact, log a deal,
 * draft an invoice.
 */
import { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft, Building2, Globe, Users as UsersIcon, Briefcase, Receipt,
  Edit3, Trash2, Plus, Phone, Mail, AlertCircle, Loader2, MapPin,
} from 'lucide-react';
import {
  getCompany, updateCompany, deleteCompany,
  listContacts, listDeals,
} from '../services/crm';
import { listInvoices } from '../services/invoices';
import { TagPicker, TagChips } from '../components/TagChips';
import { tagsFor } from '../services/tags';


export default function CompanyDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [company, setCompany] = useState(null);
  const [contacts, setContacts] = useState([]);
  const [deals, setDeals] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [tagChips, setTagChips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(false);
  const [edit, setEdit] = useState({});
  const [msg, setMsg] = useState('');

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const reload = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const c = await getCompany(id);
      setCompany(c);
      setEdit(c);
      const [contactList, dealList, invList, tagList] = await Promise.all([
        listContacts({ company_id: id, limit: 200 }).catch(() => []),
        listDeals({ company_id: id, limit: 200 }).catch(() => []),
        listInvoices({ limit: 500 }).catch(() => []),
        tagsFor('company', id).catch(() => []),
      ]);
      setContacts(contactList);
      setDeals(dealList);
      setInvoices((invList || []).filter(v => v.customer_company_id === id));
      setTagChips(tagList);
    } catch (e) { setError(e.message || 'Could not load company.'); }
    setLoading(false);
  }, [id]);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { reload(); }, [reload]);

  const wonValue = useMemo(
    () => deals.filter(d => d.stage === 'won').reduce((s, d) => s + (Number(d.value) || 0), 0),
    [deals],
  );
  const openDealCount = useMemo(
    () => deals.filter(d => !['won', 'lost'].includes(d.stage)).length,
    [deals],
  );
  const totalRevenue = useMemo(
    () => invoices.filter(i => i.status === 'paid').reduce((s, i) => s + (Number(i.total) || 0), 0),
    [invoices],
  );

  const handleSave = async () => {
    try {
      await updateCompany(id, {
        name: edit.name, industry: edit.industry, website: edit.website,
        size: edit.size, notes: edit.notes,
      });
      setEditing(false);
      flash('Saved.');
      reload();
    } catch (e) { flash(`Save failed: ${e.message}`); }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete ${company?.name}? This unlinks it from all contacts and deals (they survive without a company).`)) return;
    try {
      await deleteCompany(id);
      navigate('/crm');
    } catch (e) { flash(`Delete failed: ${e.message}`); }
  };

  if (loading) {
    return <CenterSpinner />;
  }
  if (error || !company) {
    return <NotFound message={error || 'The company may have been deleted.'} backTo="/crm" />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
          <button onClick={() => navigate('/crm')} className="btn-ghost btn-sm">
            <ArrowLeft size={12} /> CRM
          </button>
          <div style={{
            width: 44, height: 44, borderRadius: 'var(--r-md)',
            background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
            boxShadow: 'var(--shadow-1)',
          }}>
            <Building2 size={20} />
          </div>
          <div style={{ minWidth: 0 }}>
            <h1 style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.01em', margin: 0 }}>{company.name}</h1>
            <p style={{ fontSize: 12, color: 'var(--color-text-muted)', margin: 0 }}>
              {company.industry || 'Company'}
              {company.size && <> · {company.size}</>}
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
          {/* Profile */}
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 8px' }}><h2>Profile</h2></div>
            {editing ? (
              <div style={{ display: 'grid', gap: 10 }}>
                <Field label="Name"><input className="field-input" value={edit.name || ''} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /></Field>
                <Field label="Industry"><input className="field-input" value={edit.industry || ''} onChange={(e) => setEdit({ ...edit, industry: e.target.value })} placeholder="e.g. SaaS" /></Field>
                <Field label="Website"><input className="field-input" value={edit.website || ''} onChange={(e) => setEdit({ ...edit, website: e.target.value })} placeholder="https://acme.com" /></Field>
                <Field label="Size"><input className="field-input" value={edit.size || ''} onChange={(e) => setEdit({ ...edit, size: e.target.value })} placeholder="e.g. 50-200" /></Field>
                <Field label="Notes"><textarea className="field-input" rows={3} value={edit.notes || ''} onChange={(e) => setEdit({ ...edit, notes: e.target.value })} /></Field>
                <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 4 }}>
                  <button className="btn-ghost" onClick={() => { setEditing(false); setEdit(company); }}>Cancel</button>
                  <button className="btn-primary" onClick={handleSave}>Save</button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: 10 }}>
                <DetailRow icon={<Globe size={13} />} label="Website">
                  {company.website
                    ? <a href={company.website.startsWith('http') ? company.website : `https://${company.website}`} target="_blank" rel="noreferrer">{company.website}</a>
                    : <span style={{ color: 'var(--color-text-dim)' }}>Not set</span>}
                </DetailRow>
                <DetailRow icon={<MapPin size={13} />} label="Industry">
                  {company.industry || <span style={{ color: 'var(--color-text-dim)' }}>Not set</span>}
                </DetailRow>
                <DetailRow icon={<UsersIcon size={13} />} label="Size">
                  {company.size || <span style={{ color: 'var(--color-text-dim)' }}>Not set</span>}
                </DetailRow>
                {company.notes && (
                  <DetailRow icon={null} label="Notes" multiline>{company.notes}</DetailRow>
                )}
                <DetailRow icon={null} label="Tags">
                  {tagChips.length > 0
                    ? <TagChips tags={tagChips} size="xs" />
                    : <span style={{ color: 'var(--color-text-dim)', fontSize: 12 }}>None</span>}
                </DetailRow>
                <div style={{ marginTop: 6 }}><TagPicker entityType="company" entityId={id} /></div>
              </div>
            )}
          </div>

          {/* Contacts */}
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 10px' }}>
              <h2>People · {contacts.length}</h2>
            </div>
            {contacts.length === 0 ? (
              <div style={{ padding: 16, textAlign: 'center', color: 'var(--color-text-dim)', fontSize: 12 }}>
                No contacts at this company yet.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {contacts.map(c => {
                  const fullName = [c.first_name, c.last_name].filter(Boolean).join(' ') || '—';
                  return (
                    <Link
                      key={c.id} to={`/crm/contacts/${c.id}`}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 10,
                        padding: '10px 12px',
                        background: 'var(--color-surface-1)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--r-md)',
                        textDecoration: 'none', color: 'var(--color-text)',
                      }}
                    >
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 13, fontWeight: 500 }}>{fullName}</div>
                        <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
                          {c.title || '—'}{c.email ? ` · ${c.email}` : ''}
                        </div>
                      </div>
                      {c.email && <Mail size={12} color="var(--color-text-dim)" />}
                      {c.phone && <Phone size={12} color="var(--color-text-dim)" />}
                    </Link>
                  );
                })}
              </div>
            )}
          </div>

          {/* Deals */}
          {deals.length > 0 && (
            <div className="panel">
              <div className="section-h" style={{ margin: '0 0 10px' }}>
                <h2>Deals · {deals.length}</h2>
                <span className="meta">{openDealCount} open · won ${wonValue.toLocaleString()}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {deals.map(d => (
                  <Link
                    key={d.id} to={`/crm/deals/${d.id}`}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '10px 12px',
                      background: 'var(--color-surface-1)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--r-md)',
                      textDecoration: 'none', color: 'var(--color-text)',
                    }}
                  >
                    <Briefcase size={14} color="var(--color-accent)" />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{d.name}</div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-dim)', textTransform: 'capitalize' }}>
                        {d.stage} {d.value ? `· $${Number(d.value).toLocaleString()}` : ''}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Invoices */}
          {invoices.length > 0 && (
            <div className="panel">
              <div className="section-h" style={{ margin: '0 0 10px' }}>
                <h2>Invoices · {invoices.length}</h2>
                <span className="meta">paid: ${totalRevenue.toLocaleString()}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {invoices.slice(0, 10).map(inv => (
                  <Link
                    key={inv.id} to={`/invoices/${inv.id}`}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '10px 12px',
                      background: 'var(--color-surface-1)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--r-md)',
                      textDecoration: 'none', color: 'var(--color-text)',
                    }}
                  >
                    <Receipt size={14} color="var(--color-info)" />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{inv.number}</div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-dim)', textTransform: 'capitalize' }}>
                        {inv.status} · {inv.currency || 'USD'} {Number(inv.total).toLocaleString()}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 10px' }}><h2>Actions</h2></div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <ActionRow icon={<Plus size={13} />} label="Add contact" detail="New person at this company"
                         onClick={() => navigate('/crm', { state: { addContactForCompany: id } })} />
              <ActionRow icon={<Briefcase size={13} />} label="New deal" detail="Add a deal with this company"
                         onClick={() => navigate('/crm', { state: { addDealForCompany: id } })} />
              <ActionRow icon={<Receipt size={13} />} label="New invoice" detail="Draft an invoice for this company"
                         onClick={() => navigate('/invoices', { state: { addInvoiceForCompany: id } })} />
              {company.website && (
                <ActionRow icon={<Globe size={13} />} label="Open website" detail={company.website}
                           onClick={() => window.open(company.website.startsWith('http') ? company.website : `https://${company.website}`, '_blank')} />
              )}
            </div>
          </div>

          <div className="panel" style={{ background: 'var(--color-surface-1)' }}>
            <div className="section-h" style={{ margin: '0 0 6px' }}><h2>Snapshot</h2></div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
              <Snap label="Contacts" value={contacts.length} />
              <Snap label="Open deals" value={openDealCount} />
              <Snap label="Won deals" value={deals.filter(d => d.stage === 'won').length} />
              <Snap label="Won value" value={`$${wonValue.toLocaleString()}`} />
              <Snap label="Invoices" value={invoices.length} />
              <Snap label="Revenue (paid)" value={`$${totalRevenue.toLocaleString()}`} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


// Shared bits used across detail pages — kept inline for now since the
// pages diverge on layout. Could be hoisted to a `components/` later.
function CenterSpinner() {
  return (
    <div className="page-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
      <Loader2 size={20} className="animate-spin" color="var(--color-text-dim)" />
    </div>
  );
}

function NotFound({ message, backTo }) {
  const navigate = useNavigate();
  return (
    <div className="page-body" style={{ maxWidth: 640, margin: '32px auto' }}>
      <div className="panel" style={{
        padding: 20, borderColor: 'color-mix(in srgb, var(--color-err) 28%, transparent)',
        background: 'color-mix(in srgb, var(--color-err) 6%, transparent)',
      }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <AlertCircle size={18} color="var(--color-err)" style={{ marginTop: 2, flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Not found</div>
            <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>{message}</div>
            <button className="btn-ghost btn-sm" style={{ marginTop: 10 }} onClick={() => navigate(backTo)}>
              <ArrowLeft size={11} /> Back
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
        width: 90, fontSize: 11, color: 'var(--color-text-dim)',
        display: 'flex', alignItems: 'center', gap: 5,
        textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600,
        flexShrink: 0,
      }}>
        {icon}{label}
      </div>
      <div style={{
        fontSize: 12.5, color: 'var(--color-text)',
        flex: 1, minWidth: 0,
        whiteSpace: multiline ? 'pre-wrap' : 'normal',
      }}>
        {children}
      </div>
    </div>
  );
}

function ActionRow({ icon, label, detail, disabled, onClick }) {
  return (
    <button
      onClick={onClick} disabled={disabled}
      style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 12px', borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-1)', border: '1px solid var(--color-border)',
        color: 'var(--color-text)',
        cursor: disabled ? 'default' : 'pointer',
        opacity: disabled ? 0.45 : 1,
        textAlign: 'left',
      }}
    >
      <div style={{
        width: 28, height: 28, borderRadius: 'var(--r-md)',
        background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      }}>{icon}</div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12.5, fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{detail}</div>
      </div>
    </button>
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
