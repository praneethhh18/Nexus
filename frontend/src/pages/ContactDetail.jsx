/**
 * Contact detail page — the single source of truth for one person.
 *
 * Shows: identity (name/email/phone/title), the company relationship, notes,
 * tags, recent interactions, open deals where they're the primary contact,
 * and invoices addressed to them. Plus first-class action buttons that
 * actually do things — log a call, send an email, create a task, draft an
 * invoice for this person — instead of forcing the user to leave for
 * another page and re-enter the same context.
 */
import { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft, Mail, Phone, Building2, Briefcase, Calendar, MessageSquare,
  Edit3, Trash2, Plus, Receipt, CheckSquare, Send, AlertCircle, Loader2,
} from 'lucide-react';
import {
  getContact, updateContact, deleteContact,
  listInteractions, createInteraction, listDeals,
} from '../services/crm';
import { listInvoices } from '../services/invoices';
import { createTask } from '../services/tasks';
import { TagPicker, TagChips } from '../components/TagChips';
import { tagsFor } from '../services/tags';

const INTERACTION_ICONS = {
  call:    Phone, email: Mail, meeting: Calendar, note: MessageSquare,
};

const INTERACTION_TONES = {
  call:    'var(--color-info)',
  email:   'var(--color-accent)',
  meeting: 'var(--color-warn)',
  note:    'var(--color-text-muted)',
};


function formatWhen(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString([], {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso.substring(0, 16); }
}


export default function ContactDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [contact, setContact] = useState(null);
  const [interactions, setInteractions] = useState([]);
  const [deals, setDeals] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [tagChips, setTagChips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(false);
  const [edit, setEdit] = useState({});
  const [logging, setLogging] = useState(false);
  const [newInter, setNewInter] = useState({ type: 'call', subject: '', summary: '' });
  const [msg, setMsg] = useState('');

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const reload = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const c = await getContact(id);
      setContact(c);
      setEdit(c);
      const [ints, dealList, invList, tagList] = await Promise.all([
        listInteractions({ contact_id: id, limit: 30 }).catch(() => []),
        listDeals({ contact_id: id, limit: 50 }).catch(() => []),
        listInvoices({ limit: 200 }).catch(() => []),
        tagsFor('contact', id).catch(() => []),
      ]);
      setInteractions(ints);
      setDeals(dealList);
      setInvoices((invList || []).filter(
        v => v.customer_contact_id === id || v.customer_email === c.email,
      ));
      setTagChips(tagList);
    } catch (e) {
      setError(e.message || 'Could not load contact.');
    }
    setLoading(false);
  }, [id]);

  useEffect(() => { reload(); }, [reload]);

  const fullName = useMemo(() => {
    if (!contact) return '';
    return [contact.first_name, contact.last_name].filter(Boolean).join(' ') || '—';
  }, [contact]);

  const openDeals = useMemo(
    () => deals.filter(d => !['won', 'lost'].includes(d.stage)),
    [deals],
  );

  const wonValue = useMemo(
    () => deals
      .filter(d => d.stage === 'won')
      .reduce((s, d) => s + (Number(d.value) || 0), 0),
    [deals],
  );

  // ── Actions ────────────────────────────────────────────────────────────
  const handleSave = async () => {
    try {
      await updateContact(id, {
        first_name: edit.first_name, last_name: edit.last_name,
        email: edit.email, phone: edit.phone, title: edit.title,
        notes: edit.notes,
      });
      setEditing(false);
      flash('Saved.');
      reload();
    } catch (e) { flash(`Save failed: ${e.message}`); }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete ${fullName}? This will also unlink them from any open deals.`)) return;
    try {
      await deleteContact(id);
      navigate('/crm');
    } catch (e) { flash(`Delete failed: ${e.message}`); }
  };

  const handleLogInteraction = async () => {
    if (!newInter.subject.trim() && !newInter.summary.trim()) return;
    setLogging(true);
    try {
      await createInteraction({
        ...newInter,
        contact_id: id,
        company_id: contact?.company_id || null,
      });
      setNewInter({ type: 'call', subject: '', summary: '' });
      flash('Interaction logged.');
      reload();
    } catch (e) { flash(`Log failed: ${e.message}`); }
    setLogging(false);
  };

  const handleCreateTask = async () => {
    const title = prompt(`New task for ${fullName}:`);
    if (!title) return;
    try {
      await createTask({
        title,
        description: `Related to contact: ${fullName}${contact?.email ? ` (${contact.email})` : ''}`,
        priority: 'normal',
      });
      flash('Task created.');
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleEmailDraft = () => {
    if (!contact?.email) {
      flash('No email on file for this contact.');
      return;
    }
    // Open the user's mail client. Using mailto: keeps it simple — the
    // alternative is to route through the agent's send_email tool, but
    // that requires SMTP config which not every workspace has.
    window.open(`mailto:${contact.email}`, '_blank');
  };

  // ── Render ─────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="page-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <Loader2 size={20} className="animate-spin" color="var(--color-text-dim)" />
      </div>
    );
  }
  if (error || !contact) {
    return (
      <div className="page-body" style={{ maxWidth: 640, margin: '32px auto' }}>
        <div className="panel" style={{
          padding: 20, borderColor: 'color-mix(in srgb, var(--color-err) 28%, transparent)',
          background: 'color-mix(in srgb, var(--color-err) 6%, transparent)',
        }}>
          <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
            <AlertCircle size={18} color="var(--color-err)" style={{ marginTop: 2, flexShrink: 0 }} />
            <div>
              <div style={{ fontWeight: 600, marginBottom: 4 }}>Contact not found</div>
              <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>
                {error || 'The contact may have been deleted.'}
              </div>
              <button
                className="btn-ghost btn-sm"
                style={{ marginTop: 10 }}
                onClick={() => navigate('/crm')}
              >
                <ArrowLeft size={11} /> Back to CRM
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
          <button
            onClick={() => navigate('/crm')}
            className="btn-ghost btn-sm"
            title="Back to CRM"
          >
            <ArrowLeft size={12} /> CRM
          </button>
          <Avatar name={fullName} />
          <div style={{ minWidth: 0 }}>
            <h1 style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.01em', color: 'var(--color-text)', margin: 0 }}>
              {fullName}
            </h1>
            <p style={{ fontSize: 12, color: 'var(--color-text-muted)', margin: 0 }}>
              {contact.title || 'Contact'}
              {contact.company_name && (
                <> · <Link to={`/crm/companies/${contact.company_id}`} style={{ color: 'var(--color-accent)' }}>
                  <Building2 size={11} style={{ verticalAlign: 'middle', marginRight: 3 }} />
                  {contact.company_name}
                </Link></>
              )}
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

      <div className="page-body" style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0, 1fr) minmax(280px, 380px)',
        gap: 16,
      }}>
        {/* ── Left column ──────────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>

          {/* Identity / edit */}
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 8px' }}>
              <h2>Profile</h2>
            </div>
            {editing ? (
              <div style={{ display: 'grid', gap: 10 }}>
                <Field label="First name">
                  <input className="field-input" value={edit.first_name || ''} onChange={(e) => setEdit({ ...edit, first_name: e.target.value })} />
                </Field>
                <Field label="Last name">
                  <input className="field-input" value={edit.last_name || ''} onChange={(e) => setEdit({ ...edit, last_name: e.target.value })} />
                </Field>
                <Field label="Email">
                  <input className="field-input" type="email" value={edit.email || ''} onChange={(e) => setEdit({ ...edit, email: e.target.value })} />
                </Field>
                <Field label="Phone">
                  <input className="field-input" value={edit.phone || ''} onChange={(e) => setEdit({ ...edit, phone: e.target.value })} />
                </Field>
                <Field label="Title">
                  <input className="field-input" value={edit.title || ''} onChange={(e) => setEdit({ ...edit, title: e.target.value })} placeholder="e.g. Head of Sales" />
                </Field>
                <Field label="Notes">
                  <textarea className="field-input" rows={3} value={edit.notes || ''} onChange={(e) => setEdit({ ...edit, notes: e.target.value })} />
                </Field>
                <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 4 }}>
                  <button className="btn-ghost" onClick={() => { setEditing(false); setEdit(contact); }}>Cancel</button>
                  <button className="btn-primary" onClick={handleSave}>Save</button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: 10 }}>
                <Detail icon={<Mail size={13} />} label="Email">
                  {contact.email
                    ? <a href={`mailto:${contact.email}`}>{contact.email}</a>
                    : <span style={{ color: 'var(--color-text-dim)' }}>Not set</span>}
                </Detail>
                <Detail icon={<Phone size={13} />} label="Phone">
                  {contact.phone
                    ? <a href={`tel:${contact.phone}`}>{contact.phone}</a>
                    : <span style={{ color: 'var(--color-text-dim)' }}>Not set</span>}
                </Detail>
                {contact.notes && (
                  <Detail icon={<MessageSquare size={13} />} label="Notes" multiline>
                    {contact.notes}
                  </Detail>
                )}
                <Detail icon={null} label="Tags">
                  {tagChips.length > 0
                    ? <TagChips tags={tagChips} size="xs" />
                    : <span style={{ color: 'var(--color-text-dim)', fontSize: 12 }}>None</span>}
                </Detail>
                <div style={{ marginTop: 6 }}>
                  <TagPicker entityType="contact" entityId={id} />
                </div>
              </div>
            )}
          </div>

          {/* Open deals */}
          {openDeals.length > 0 && (
            <div className="panel">
              <div className="section-h" style={{ margin: '0 0 10px' }}>
                <h2>Open deals · {openDeals.length}</h2>
                <span className="meta">Won: ${wonValue.toLocaleString()}</span>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {openDeals.map(d => (
                  <Link
                    key={d.id}
                    to={`/crm/deals/${d.id}`}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '10px 12px',
                      background: 'var(--color-surface-1)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--r-md)',
                      textDecoration: 'none',
                      color: 'var(--color-text)',
                      transition: 'border-color var(--dur-fast) var(--ease-out)',
                    }}
                  >
                    <Briefcase size={14} color="var(--color-accent)" style={{ flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {d.name}
                      </div>
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
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {invoices.slice(0, 5).map(inv => (
                  <Link
                    key={inv.id}
                    to={`/invoices/${inv.id}`}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '10px 12px',
                      background: 'var(--color-surface-1)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--r-md)',
                      textDecoration: 'none',
                      color: 'var(--color-text)',
                    }}
                  >
                    <Receipt size={14} color="var(--color-info)" style={{ flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 500 }}>{inv.number}</div>
                      <div style={{ fontSize: 11, color: 'var(--color-text-dim)', textTransform: 'capitalize' }}>
                        {inv.status} · {inv.currency || 'USD'} {Number(inv.total).toLocaleString()}
                      </div>
                    </div>
                  </Link>
                ))}
                {invoices.length > 5 && (
                  <Link to="/invoices" style={{ fontSize: 11, color: 'var(--color-accent)', alignSelf: 'flex-end' }}>
                    View all {invoices.length} →
                  </Link>
                )}
              </div>
            </div>
          )}

          {/* Interaction history + new */}
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 10px' }}>
              <h2>Recent interactions · {interactions.length}</h2>
            </div>

            {/* Quick log */}
            <div style={{
              padding: 10, marginBottom: 12,
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--r-md)',
              display: 'flex', flexDirection: 'column', gap: 8,
            }}>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                {['call', 'email', 'meeting', 'note'].map(t => {
                  const Icon = INTERACTION_ICONS[t];
                  const active = newInter.type === t;
                  return (
                    <button
                      key={t}
                      onClick={() => setNewInter({ ...newInter, type: t })}
                      className={active ? 'btn-primary btn-sm' : 'btn-ghost btn-sm'}
                      style={{ textTransform: 'capitalize' }}
                    >
                      <Icon size={11} /> {t}
                    </button>
                  );
                })}
              </div>
              <input
                className="field-input"
                placeholder='Subject (e.g. "Follow-up call about Q1 proposal")'
                value={newInter.subject}
                onChange={(e) => setNewInter({ ...newInter, subject: e.target.value })}
                maxLength={200}
              />
              <textarea
                className="field-input"
                rows={2}
                placeholder="Summary — what got discussed?"
                value={newInter.summary}
                onChange={(e) => setNewInter({ ...newInter, summary: e.target.value })}
                maxLength={2000}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  className="btn-primary btn-sm"
                  disabled={logging || (!newInter.subject.trim() && !newInter.summary.trim())}
                  onClick={handleLogInteraction}
                >
                  {logging ? <Loader2 size={11} className="animate-spin" /> : <Plus size={11} />}
                  Log
                </button>
              </div>
            </div>

            {/* History */}
            {interactions.length === 0 ? (
              <div style={{ padding: 16, textAlign: 'center', color: 'var(--color-text-dim)', fontSize: 12 }}>
                No interactions logged yet.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {interactions.map(it => {
                  const Icon = INTERACTION_ICONS[it.type] || MessageSquare;
                  const tone = INTERACTION_TONES[it.type] || 'var(--color-text-muted)';
                  return (
                    <div key={it.id} style={{
                      display: 'flex', gap: 10, alignItems: 'flex-start',
                      padding: '10px 12px',
                      background: 'var(--color-surface-1)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--r-md)',
                    }}>
                      <div style={{
                        width: 28, height: 28, borderRadius: 'var(--r-md)',
                        background: `color-mix(in srgb, ${tone} 14%, transparent)`,
                        color: tone,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        flexShrink: 0,
                      }}>
                        <Icon size={13} />
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--color-text)' }}>
                          {it.subject || <em style={{ color: 'var(--color-text-dim)' }}>(no subject)</em>}
                        </div>
                        {it.summary && (
                          <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2, lineHeight: 1.5 }}>
                            {it.summary}
                          </div>
                        )}
                        <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', marginTop: 4, display: 'flex', gap: 8 }}>
                          <span style={{ textTransform: 'capitalize' }}>{it.type}</span>
                          <span>{formatWhen(it.occurred_at || it.created_at)}</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* ── Right column — Actions ────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 10px' }}>
              <h2>Actions</h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <ActionButton
                icon={<Send size={13} />}
                label="Send email"
                detail={contact.email || 'No email on file'}
                disabled={!contact.email}
                onClick={handleEmailDraft}
              />
              <ActionButton
                icon={<Phone size={13} />}
                label="Call"
                detail={contact.phone || 'No phone on file'}
                disabled={!contact.phone}
                onClick={() => contact.phone && window.open(`tel:${contact.phone}`)}
              />
              <ActionButton
                icon={<CheckSquare size={13} />}
                label="Create task"
                detail="Quick reminder for this contact"
                onClick={handleCreateTask}
              />
              <ActionButton
                icon={<Briefcase size={13} />}
                label="New deal"
                detail="Add a deal with this contact"
                onClick={() => navigate('/crm', { state: { addDealForContact: id } })}
              />
              <ActionButton
                icon={<Receipt size={13} />}
                label="New invoice"
                detail="Draft an invoice for this contact"
                onClick={() => navigate('/invoices', { state: { addInvoiceForContact: id } })}
              />
            </div>
          </div>

          <div className="panel" style={{ background: 'var(--color-surface-1)' }}>
            <div className="section-h" style={{ margin: '0 0 6px' }}>
              <h2>Snapshot</h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
              <Snap label="Open deals" value={openDeals.length} />
              <Snap label="Won deals" value={deals.filter(d => d.stage === 'won').length} />
              <Snap label="Won value" value={`$${wonValue.toLocaleString()}`} />
              <Snap label="Interactions" value={interactions.length} />
              <Snap label="Invoices" value={invoices.length} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


// ── Bits ─────────────────────────────────────────────────────────────────────
function Avatar({ name }) {
  const initials = (name || '?').split(/\s+/).filter(Boolean).slice(0, 2).map(s => s[0]).join('').toUpperCase() || '?';
  // Stable hue from the name so two users with similar names don't collide.
  const hue = [...(name || '')].reduce((h, c) => (h * 31 + c.charCodeAt(0)) % 360, 0);
  return (
    <div style={{
      width: 44, height: 44, borderRadius: '50%',
      background: `linear-gradient(135deg, hsl(${hue}, 60%, 36%), hsl(${(hue + 40) % 360}, 60%, 28%))`,
      color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontWeight: 700, fontSize: 15, flexShrink: 0,
      boxShadow: 'var(--shadow-1)',
    }}>
      {initials}
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


function Detail({ icon, label, multiline, children }) {
  return (
    <div style={{
      display: 'flex', gap: 12,
      alignItems: multiline ? 'flex-start' : 'center',
    }}>
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


function ActionButton({ icon, label, detail, disabled, onClick }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 12px', borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        color: 'var(--color-text)',
        cursor: disabled ? 'default' : 'pointer',
        opacity: disabled ? 0.45 : 1,
        textAlign: 'left',
        transition: 'border-color var(--dur-fast) var(--ease-out)',
      }}
      onMouseEnter={(e) => { if (!disabled) e.currentTarget.style.borderColor = 'color-mix(in srgb, var(--color-accent) 35%, transparent)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
    >
      <div style={{
        width: 28, height: 28, borderRadius: 'var(--r-md)',
        background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      }}>
        {icon}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 12.5, fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {detail}
        </div>
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
