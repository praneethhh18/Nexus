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
  Sparkles, Copy, RefreshCw, X,
} from 'lucide-react';
import {
  getContact, updateContact, deleteContact,
  listInteractions, createInteraction, listDeals, draftOutreach,
  scoreContactFit, extractBant, updateDeal, draftReply,
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
  const [draftModal, setDraftModal] = useState(null);  // { variants: [...], busy, error }
  const [scoring, setScoring] = useState(false);
  const [bantModal, setBantModal] = useState(null);  // { busy, error, result, replyText }
  const [replyModal, setReplyModal] = useState(null);  // { busy, error, draft, incoming }

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

  // ── BANT extraction ─────────────────────────────────────────────────
  const openBantModal = () =>
    setBantModal({ replyText: '', busy: false, error: '', result: null });

  const runBantExtract = async () => {
    if (!bantModal?.replyText || bantModal.replyText.trim().length < 10) {
      setBantModal((m) => ({ ...(m || {}), error: 'Paste the prospect\'s reply first.' }));
      return;
    }
    setBantModal((m) => ({ ...m, busy: true, error: '', result: null }));
    try {
      const r = await extractBant(id, bantModal.replyText);
      setBantModal((m) => ({ ...m, busy: false, error: '', result: r }));
      // Reload contact so the BANT card surfaces in the related panel.
      reload();
    } catch (e) {
      setBantModal((m) => ({ ...m, busy: false, error: e.message || 'Extraction failed.', result: null }));
    }
  };

  const openReplyDraftFor = async (incomingText) => {
    if (!incomingText || incomingText.trim().length < 10) return;
    setReplyModal({ busy: true, error: '', draft: null, incoming: incomingText });
    try {
      const r = await draftReply(id, incomingText);
      setReplyModal({ busy: false, error: '', draft: r, incoming: incomingText });
    } catch (e) {
      setReplyModal({ busy: false, error: e.message || 'Draft failed.', draft: null, incoming: incomingText });
    }
  };

  const advanceDealStage = async (stage) => {
    // The first open deal on this contact gets advanced. If they have
    // multiple, we surface a friendly note pointing them to the deal page.
    const target = openDeals[0];
    if (!target) {
      flash('No open deal on this contact yet — create one from the Actions panel.');
      return;
    }
    if (openDeals.length > 1) {
      flash(`Advanced "${target.name}" to ${stage}. (You have ${openDeals.length} open deals — use the Deal pages for the others.)`);
    }
    try {
      await updateDeal(target.id, { stage });
      flash(`Deal "${target.name}" → ${stage}.`);
      setBantModal(null);
      reload();
    } catch (e) {
      flash(`Stage advance failed: ${e.message || e}`);
    }
  };

  // ── AI lead scoring ─────────────────────────────────────────────────
  const handleScoreFit = async () => {
    setScoring(true);
    try {
      const r = await scoreContactFit(id);
      // Reload the contact so the badge updates with the new score.
      reload();
      if (!r.icp_set) {
        flash('No Ideal Customer Profile set yet — head to Settings to define one.');
      } else if (r.score == null) {
        flash(r.reason || 'Scoring did not return a usable result.');
      } else {
        flash(`Scored ${r.score}/100 · ${r.bucket}.`);
      }
    } catch (e) {
      flash(`Scoring failed: ${e.message || e}`);
    }
    setScoring(false);
  };

  // ── AI-drafted outreach ─────────────────────────────────────────────
  const openDraftModal = async () => {
    setDraftModal({ variants: null, busy: true, error: '' });
    try {
      const r = await draftOutreach(id);
      setDraftModal({ variants: r.variants || [], busy: false, error: '' });
    } catch (e) {
      setDraftModal({ variants: null, busy: false, error: e.message || 'Draft failed.' });
    }
  };
  const regenerateDraft = async () => {
    setDraftModal((m) => ({ ...(m || {}), busy: true, error: '' }));
    try {
      const r = await draftOutreach(id);
      setDraftModal({ variants: r.variants || [], busy: false, error: '' });
    } catch (e) {
      setDraftModal({ variants: null, busy: false, error: e.message || 'Draft failed.' });
    }
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
            <h1 style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.01em', color: 'var(--color-text)', margin: 0, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              {fullName}
              <LeadScoreChip score={contact.lead_score} reason={contact.lead_score_reason} scoredAt={contact.lead_scored_at} />
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

          {/* Unified timeline — the conversation-stitch view. Combines
              interactions + stage transitions (best-effort) + invoices into
              one chronological feed. Below it, the structured per-type
              panels still render so users can drill into a specific deal
              or invoice without scrolling the whole timeline. */}
          <TimelineFeed
            interactions={interactions}
            deals={deals}
            invoices={invoices}
          />

          {/* BANT card — only when extracted */}
          {contact.bant_signals && (() => {
            try {
              const b = typeof contact.bant_signals === 'string'
                ? JSON.parse(contact.bant_signals) : contact.bant_signals;
              if (!b || !b.budget) return null;
              return (
                <BantCard
                  bant={b}
                  extractedAt={contact.bant_extracted_at}
                  hasOpenDeal={openDeals.length > 0}
                  onAdvance={(stage) => advanceDealStage(stage)}
                />
              );
            } catch { return null; }
          })()}

          {/* AI fit reasoning — only when scored */}
          {contact.lead_score != null && contact.lead_score_reason && (
            <div className="panel" style={{
              borderColor: 'color-mix(in srgb, var(--color-accent) 22%, var(--color-border))',
              background: 'color-mix(in srgb, var(--color-accent) 4%, var(--color-surface-2))',
            }}>
              <div className="section-h" style={{ margin: '0 0 6px' }}>
                <h2>AI fit assessment</h2>
                <span className="meta">vs your ICP</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <LeadScoreChip
                  score={contact.lead_score}
                  reason={contact.lead_score_reason}
                  scoredAt={contact.lead_scored_at}
                />
                {contact.lead_scored_at && (
                  <span style={{ fontSize: 10.5, color: 'var(--color-text-dim)' }}>
                    {new Date(contact.lead_scored_at).toLocaleString()}
                  </span>
                )}
              </div>
              <p style={{ fontSize: 12.5, color: 'var(--color-text-muted)', margin: 0, lineHeight: 1.55 }}>
                {contact.lead_score_reason}
              </p>
            </div>
          )}

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
                icon={scoring ? <Loader2 size={13} className="animate-spin" /> : <Sparkles size={13} />}
                label={contact.lead_score == null ? 'Score this lead' : 'Rescore lead'}
                detail={
                  contact.lead_score == null
                    ? 'AI compares to your ICP'
                    : `Currently ${contact.lead_score}/100`
                }
                disabled={scoring}
                onClick={handleScoreFit}
              />
              <ActionButton
                icon={<Sparkles size={13} />}
                label="AI draft outreach"
                detail="Three personalised email variants"
                disabled={!contact.email}
                onClick={openDraftModal}
              />
              <ActionButton
                icon={<Sparkles size={13} />}
                label="Qualify their reply"
                detail="Paste a reply → BANT signals"
                onClick={openBantModal}
              />
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

      {/* AI Outreach modal */}
      {draftModal && (
        <DraftOutreachModal
          state={draftModal}
          contact={contact}
          onRegenerate={regenerateDraft}
          onClose={() => setDraftModal(null)}
          onCopied={() => flash('Copied to clipboard.')}
          onSent={() => flash('Opened in your mail client.')}
        />
      )}

      {/* BANT extraction modal */}
      {bantModal && (
        <BantModal
          state={bantModal}
          contact={contact}
          openDealsCount={openDeals.length}
          onChangeReply={(t) => setBantModal((m) => ({ ...m, replyText: t }))}
          onRun={runBantExtract}
          onClose={() => setBantModal(null)}
          onAdvance={advanceDealStage}
          onDraftReply={() => openReplyDraftFor(bantModal.replyText)}
        />
      )}

      {/* AI reply drafter modal */}
      {replyModal && (
        <ReplyDraftModal
          state={replyModal}
          contact={contact}
          onClose={() => setReplyModal(null)}
          onCopied={() => flash('Copied to clipboard.')}
          onSent={() => flash('Opened in your mail client.')}
          onRegenerate={() => openReplyDraftFor(replyModal.incoming)}
          onChangeDraft={(d) => setReplyModal((m) => ({ ...m, draft: d }))}
        />
      )}
    </div>
  );
}


// ── AI Outreach modal ───────────────────────────────────────────────────────
// Renders the three variants returned by /api/crm/contacts/{id}/draft-outreach
// in a tabbed view. Each variant is editable in place; the user can copy
// to clipboard or open in their mail client (mailto:) without sending
// through the agent — keeps the privacy story simple (no SMTP needed).
function DraftOutreachModal({ state, contact, onRegenerate, onClose, onCopied, onSent }) {
  const [active, setActive] = useState(0);
  const [edits, setEdits] = useState({});  // tone -> {subject, body}

  const variants = state.variants || [];
  const current = variants[active];
  const currentEdits = current ? (edits[current.tone] || current) : null;

  const setSubject = (val) => {
    if (!current) return;
    setEdits((e) => ({ ...e, [current.tone]: { ...currentEdits, subject: val } }));
  };
  const setBody = (val) => {
    if (!current) return;
    setEdits((e) => ({ ...e, [current.tone]: { ...currentEdits, body: val } }));
  };

  const copyToClipboard = async () => {
    if (!currentEdits) return;
    const text = `Subject: ${currentEdits.subject}\n\n${currentEdits.body}`;
    try { await navigator.clipboard.writeText(text); onCopied?.(); }
    catch { /* no clipboard permission, user can select manually */ }
  };

  const openInMail = () => {
    if (!currentEdits || !contact?.email) return;
    const url = `mailto:${encodeURIComponent(contact.email)}?subject=${encodeURIComponent(currentEdits.subject)}&body=${encodeURIComponent(currentEdits.body)}`;
    window.open(url, '_blank');
    onSent?.();
  };

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
          width: '100%', maxWidth: 720,
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
            <Sparkles size={16} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>
              AI-drafted outreach
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
              Personalised for {[contact?.first_name, contact?.last_name].filter(Boolean).join(' ') || 'this contact'} · runs locally on Ollama
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
        {state.busy ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-dim)' }}>
            <Loader2 size={18} className="animate-spin" style={{ marginBottom: 8 }} />
            <div style={{ fontSize: 12.5 }}>Drafting three personalised variants…</div>
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 4 }}>
              Pulling signals from this contact + recent interactions + linked deals.
            </div>
          </div>
        ) : state.error ? (
          <div style={{ padding: 24 }}>
            <div style={{
              padding: 12,
              background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-err) 28%, transparent)',
              borderRadius: 'var(--r-md)',
              display: 'flex', gap: 10, alignItems: 'flex-start',
            }}>
              <AlertCircle size={16} color="var(--color-err)" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--color-err)', marginBottom: 4 }}>
                  Couldn't draft
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.55 }}>
                  {state.error}
                </div>
                <button className="btn-ghost btn-sm" style={{ marginTop: 8 }} onClick={onRegenerate}>
                  <RefreshCw size={11} /> Try again
                </button>
              </div>
            </div>
          </div>
        ) : variants.length === 0 ? (
          <div style={{ padding: 30, textAlign: 'center', color: 'var(--color-text-dim)', fontSize: 12 }}>
            No variants returned.
          </div>
        ) : (
          <>
            {/* Tabs */}
            <div style={{
              display: 'flex', gap: 2,
              padding: '0 18px',
              borderBottom: '1px solid var(--color-border)',
            }}>
              {variants.map((v, i) => {
                const isActive = i === active;
                return (
                  <button
                    key={v.tone}
                    onClick={() => setActive(i)}
                    style={{
                      padding: '10px 14px',
                      border: 'none', cursor: 'pointer',
                      background: 'transparent',
                      color: isActive ? 'var(--color-accent)' : 'var(--color-text-muted)',
                      fontSize: 12, fontWeight: 600, textTransform: 'capitalize',
                      borderBottom: isActive
                        ? '2px solid var(--color-accent)'
                        : '2px solid transparent',
                      marginBottom: -1,
                    }}
                  >
                    {v.tone}
                  </button>
                );
              })}
            </div>

            {/* Editable preview */}
            <div style={{ padding: 18, overflow: 'auto', flex: 1 }}>
              <label style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 500, letterSpacing: 0.4, textTransform: 'uppercase' }}>
                Subject
              </label>
              <input
                className="field-input"
                value={currentEdits?.subject || ''}
                onChange={(e) => setSubject(e.target.value)}
                style={{ marginTop: 4, marginBottom: 12 }}
              />
              <label style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 500, letterSpacing: 0.4, textTransform: 'uppercase' }}>
                Body
              </label>
              <textarea
                className="field-input"
                rows={10}
                value={currentEdits?.body || ''}
                onChange={(e) => setBody(e.target.value)}
                style={{ marginTop: 4, fontFamily: 'inherit', lineHeight: 1.55 }}
              />
            </div>

            {/* Footer actions */}
            <div style={{
              padding: '12px 18px',
              borderTop: '1px solid var(--color-border)',
              display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap',
            }}>
              <button className="btn-ghost btn-sm" onClick={onRegenerate}>
                <RefreshCw size={11} /> Regenerate
              </button>
              <span style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
                <button className="btn-ghost btn-sm" onClick={copyToClipboard}>
                  <Copy size={11} /> Copy
                </button>
                <button
                  className="btn-primary btn-sm"
                  onClick={openInMail}
                  disabled={!contact?.email}
                  title={contact?.email ? 'Open in your mail client' : 'No email on file for this contact'}
                >
                  <Send size={11} /> Open in mail
                </button>
              </span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}


// ── Conversation-stitch timeline ────────────────────────────────────────────
// Merge interactions + invoices + (currently just open) deals into a single
// chronological feed. Each entry is icon + tinted left rail + title + summary
// + when. Keeps the structured per-type panels below for drill-in.
function TimelineFeed({ interactions = [], deals = [], invoices = [] }) {
  const items = useMemo(() => {
    const out = [];
    for (const it of interactions || []) {
      const when = it.occurred_at || it.created_at || '';
      out.push({
        kind: 'interaction', subkind: it.type || 'note',
        when, title: it.subject || `(no subject)`,
        body: it.summary || '',
      });
    }
    for (const d of deals || []) {
      out.push({
        kind: 'deal', subkind: d.stage,
        when: d.updated_at || d.created_at || '',
        title: `Deal "${d.name}"`,
        body: `Stage: ${d.stage}` + (d.value ? ` · $${Number(d.value).toLocaleString()}` : ''),
      });
    }
    for (const inv of invoices || []) {
      out.push({
        kind: 'invoice', subkind: inv.status,
        when: inv.issue_date || inv.created_at || '',
        title: `Invoice ${inv.number}`,
        body: `${inv.status} · ${inv.currency || 'USD'} ${Number(inv.total || 0).toLocaleString()}`,
      });
    }
    out.sort((a, b) => (b.when || '').localeCompare(a.when || ''));
    return out;
  }, [interactions, deals, invoices]);

  if (items.length === 0) {
    return null;  // Don't show an empty timeline; the per-type panels handle "no data" copy.
  }

  const TYPE_TONE = {
    interaction: 'var(--color-info)',
    deal:        'var(--color-warn)',
    invoice:     '#a78bfa',
  };
  const TYPE_LABEL = {
    interaction: 'Interaction',
    deal:        'Deal',
    invoice:     'Invoice',
  };

  const formatWhenShort = (iso) => {
    if (!iso) return '';
    try {
      const d = new Date(iso);
      const now = new Date();
      const sameDay = d.toDateString() === now.toDateString();
      if (sameDay) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: d.getFullYear() === now.getFullYear() ? undefined : '2-digit' });
    } catch { return iso.substring(0, 10); }
  };

  return (
    <div className="panel">
      <div className="section-h" style={{ margin: '0 0 10px' }}>
        <h2>Timeline · {items.length}</h2>
        <span className="meta">all touches with this contact, newest first</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {items.slice(0, 25).map((it, i) => {
          const tone = TYPE_TONE[it.kind] || 'var(--color-text-dim)';
          return (
            <div key={i} style={{
              display: 'flex', gap: 12,
              padding: '10px 4px',
              borderBottom: i < Math.min(items.length, 25) - 1 ? '1px solid var(--color-border)' : 'none',
            }}>
              <div style={{
                width: 6, alignSelf: 'stretch', borderRadius: 'var(--r-pill)',
                background: `color-mix(in srgb, ${tone} 60%, transparent)`,
                flexShrink: 0,
              }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span style={{
                    fontSize: 9.5, fontWeight: 700, letterSpacing: 0.5, textTransform: 'uppercase',
                    padding: '2px 7px', borderRadius: 'var(--r-pill)',
                    background: `color-mix(in srgb, ${tone} 14%, transparent)`,
                    color: tone,
                  }}>
                    {TYPE_LABEL[it.kind]} · {it.subkind}
                  </span>
                  <span style={{ fontSize: 12.5, color: 'var(--color-text)', fontWeight: 500 }}>
                    {it.title}
                  </span>
                  <span style={{ fontSize: 10.5, color: 'var(--color-text-dim)', marginLeft: 'auto', fontFeatureSettings: '"tnum"' }}>
                    {formatWhenShort(it.when)}
                  </span>
                </div>
                {it.body && (
                  <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 3, lineHeight: 1.55 }}>
                    {it.body.length > 200 ? `${it.body.substring(0, 200)}…` : it.body}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {items.length > 25 && (
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)', padding: '8px 0 0', textAlign: 'center' }}>
            + {items.length - 25} earlier touches
          </div>
        )}
      </div>
    </div>
  );
}


// ── BANT panel + modal ──────────────────────────────────────────────────────
function BantCard({ bant, extractedAt, hasOpenDeal, onAdvance }) {
  const dims = [
    { key: 'budget',    label: 'Budget',    icon: '💰' },
    { key: 'authority', label: 'Authority', icon: '👑' },
    { key: 'need',      label: 'Need',      icon: '🎯' },
    { key: 'timing',    label: 'Timing',    icon: '⏱' },
  ];
  const TONE = {
    yes:     'var(--color-ok)',
    no:      'var(--color-err)',
    unknown: 'var(--color-text-dim)',
  };
  return (
    <div className="panel" style={{
      borderColor: 'color-mix(in srgb, var(--color-info) 22%, var(--color-border))',
      background: 'color-mix(in srgb, var(--color-info) 4%, var(--color-surface-2))',
    }}>
      <div className="section-h" style={{ margin: '0 0 8px' }}>
        <h2>BANT signals</h2>
        <span className="meta">
          confidence {bant.confidence ?? 0}%
          {extractedAt && ` · ${new Date(extractedAt).toLocaleDateString()}`}
        </span>
      </div>
      {bant.summary && (
        <p style={{ fontSize: 12.5, color: 'var(--color-text-muted)', margin: '0 0 10px', lineHeight: 1.55 }}>
          {bant.summary}
        </p>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 8 }}>
        {dims.map(({ key, label, icon }) => {
          const v = bant[key] || { signal: 'unknown', evidence: '' };
          const tone = TONE[v.signal] || TONE.unknown;
          return (
            <div key={key} style={{
              padding: '8px 10px',
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--r-sm)',
              display: 'flex', flexDirection: 'column', gap: 3,
            }}>
              <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600 }}>
                {icon} {label}
              </div>
              <div style={{
                fontSize: 12, fontWeight: 600, color: tone, textTransform: 'capitalize',
              }}>
                {v.signal}
              </div>
              {v.evidence && v.evidence !== 'none' && (
                <div style={{ fontSize: 10.5, color: 'var(--color-text-muted)', lineHeight: 1.5, fontStyle: 'italic' }}>
                  "{v.evidence}"
                </div>
              )}
            </div>
          );
        })}
      </div>
      {bant.suggested_stage && hasOpenDeal && (
        <div style={{
          marginTop: 10, padding: '8px 10px',
          background: 'var(--color-accent-soft)',
          border: '1px solid color-mix(in srgb, var(--color-accent) 30%, transparent)',
          borderRadius: 'var(--r-sm)',
          display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
        }}>
          <span style={{ fontSize: 12, color: 'var(--color-text)' }}>
            Suggested next stage: <strong style={{ color: 'var(--color-accent)' }}>{bant.suggested_stage}</strong>
          </span>
          <button
            className="btn-primary btn-sm"
            style={{ marginLeft: 'auto' }}
            onClick={() => onAdvance(bant.suggested_stage)}
          >
            <Check size={11} /> Advance
          </button>
        </div>
      )}
    </div>
  );
}


function BantModal({ state, contact, openDealsCount, onChangeReply, onRun, onClose, onAdvance, onDraftReply }) {
  const r = state.result;
  const fullName = [contact?.first_name, contact?.last_name].filter(Boolean).join(' ') || 'this contact';
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
          width: '100%', maxWidth: 720,
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
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>
              Qualify {fullName}'s reply
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
              Paste their reply — AI extracts Budget · Authority · Need · Timing
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 4 }} aria-label="Close">
            <X size={16} />
          </button>
        </div>

        <div style={{ padding: 18, overflow: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
          {state.error && (
            <div style={{
              padding: '8px 10px',
              background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-err) 28%, transparent)',
              borderRadius: 'var(--r-sm)',
              fontSize: 12, color: 'var(--color-err)',
              display: 'flex', alignItems: 'flex-start', gap: 6,
            }}>
              <AlertCircle size={13} style={{ marginTop: 1, flexShrink: 0 }} />
              <span>{state.error}</span>
            </div>
          )}

          <textarea
            className="field-input"
            rows={r ? 4 : 12}
            value={state.replyText}
            onChange={(e) => onChangeReply(e.target.value)}
            placeholder="Paste their reply here. The fuller the better — full email or just the body, both work."
            style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 12, lineHeight: 1.55 }}
          />

          {r && (
            <BantCard
              bant={r}
              extractedAt={null}
              hasOpenDeal={openDealsCount > 0}
              onAdvance={onAdvance}
            />
          )}
        </div>

        <div style={{
          padding: '12px 18px', borderTop: '1px solid var(--color-border)',
          display: 'flex', gap: 8, justifyContent: 'flex-end', flexWrap: 'wrap',
        }}>
          <button className="btn-ghost" onClick={onClose}>Close</button>
          {r && onDraftReply && (
            <button
              className="btn-ghost"
              onClick={onDraftReply}
              title="Draft an AI response to this exact reply"
            >
              <Send size={12} /> Draft response
            </button>
          )}
          <button className="btn-primary" onClick={onRun} disabled={state.busy}>
            {state.busy
              ? <><Loader2 size={12} className="animate-spin" /> Extracting…</>
              : r ? 'Re-run' : <><Sparkles size={12} /> Extract BANT</>}
          </button>
        </div>
      </div>
    </div>
  );
}


// ── AI reply drafter modal ──────────────────────────────────────────────────
// Shown after BANT extraction (or anywhere we want to draft a contextual
// response). Editable subject + body, copy or open in mail client. Same
// privacy posture as the rest — backend forces sensitive=True.
function ReplyDraftModal({ state, contact, onClose, onCopied, onSent, onRegenerate, onChangeDraft }) {
  const draft = state.draft;
  const fullName = [contact?.first_name, contact?.last_name].filter(Boolean).join(' ') || 'this contact';

  const copy = async () => {
    if (!draft) return;
    try {
      await navigator.clipboard.writeText(`Subject: ${draft.subject}\n\n${draft.body}`);
      onCopied?.();
    } catch { /* clipboard unavailable */ }
  };
  const openMail = () => {
    if (!draft || !contact?.email) return;
    const url = `mailto:${encodeURIComponent(contact.email)}?subject=${encodeURIComponent(draft.subject)}&body=${encodeURIComponent(draft.body)}`;
    window.open(url, '_blank');
    onSent?.();
  };

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, zIndex: 310,
        background: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%', maxWidth: 720,
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
            <Send size={16} />
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>
              AI-drafted reply
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
              Contextual response to {fullName} · runs locally on Ollama
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

        {state.busy ? (
          <div style={{ padding: 36, textAlign: 'center', color: 'var(--color-text-dim)' }}>
            <Loader2 size={18} className="animate-spin" style={{ marginBottom: 6 }} />
            <div style={{ fontSize: 12.5 }}>Reading their reply, drafting a response…</div>
          </div>
        ) : state.error ? (
          <div style={{ padding: 24 }}>
            <div style={{
              padding: 12,
              background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-err) 28%, transparent)',
              borderRadius: 'var(--r-md)',
              display: 'flex', gap: 10, alignItems: 'flex-start',
            }}>
              <AlertCircle size={16} color="var(--color-err)" style={{ flexShrink: 0, marginTop: 2 }} />
              <div>
                <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--color-err)', marginBottom: 4 }}>
                  Couldn't draft a reply
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.55 }}>
                  {state.error}
                </div>
                <button className="btn-ghost btn-sm" style={{ marginTop: 8 }} onClick={onRegenerate}>
                  <RefreshCw size={11} /> Try again
                </button>
              </div>
            </div>
          </div>
        ) : draft ? (
          <div style={{ padding: 18, overflow: 'auto', flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div>
              <label style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 500, letterSpacing: 0.4, textTransform: 'uppercase' }}>
                Subject
              </label>
              <input
                className="field-input"
                value={draft.subject}
                onChange={(e) => onChangeDraft({ ...draft, subject: e.target.value })}
                style={{ marginTop: 4 }}
              />
            </div>
            <div>
              <label style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 500, letterSpacing: 0.4, textTransform: 'uppercase' }}>
                Body
              </label>
              <textarea
                className="field-input"
                rows={12}
                value={draft.body}
                onChange={(e) => onChangeDraft({ ...draft, body: e.target.value })}
                style={{ marginTop: 4, fontFamily: 'inherit', lineHeight: 1.55 }}
              />
            </div>
          </div>
        ) : null}

        <div style={{
          padding: '12px 18px', borderTop: '1px solid var(--color-border)',
          display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap',
        }}>
          {draft && (
            <button className="btn-ghost btn-sm" onClick={onRegenerate}>
              <RefreshCw size={11} /> Regenerate
            </button>
          )}
          <span style={{ marginLeft: 'auto', display: 'flex', gap: 8 }}>
            <button className="btn-ghost btn-sm" onClick={copy} disabled={!draft}>
              <Copy size={11} /> Copy
            </button>
            <button
              className="btn-primary btn-sm"
              onClick={openMail}
              disabled={!draft || !contact?.email}
              title={contact?.email ? 'Open in mail client' : 'No email on file'}
            >
              <Send size={11} /> Open in mail
            </button>
          </span>
        </div>
      </div>
    </div>
  );
}


// ── Lead-score chip + bucket helpers (mirror backend) ───────────────────────
function _bucketOf(score) {
  if (score == null) return null;
  if (score >= 80) return 'high';
  if (score >= 50) return 'medium';
  if (score >= 20) return 'low';
  return 'spam';
}

function LeadScoreChip({ score, reason, scoredAt }) {
  const bucket = _bucketOf(score);
  if (bucket === null) return null;
  const TONE = {
    high:   'var(--color-ok)',
    medium: 'var(--color-info)',
    low:    'var(--color-text-dim)',
    spam:   'var(--color-err)',
  };
  const LABEL = { high: 'High fit', medium: 'Medium fit', low: 'Low fit', spam: 'Spam / not a lead' };
  const tone = TONE[bucket];
  const tip = [reason, scoredAt && `Scored ${new Date(scoredAt).toLocaleString()}`]
    .filter(Boolean).join('\n');
  return (
    <span
      title={tip}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 4,
        padding: '2px 10px', borderRadius: 'var(--r-pill)',
        fontSize: 11, fontWeight: 600,
        background: `color-mix(in srgb, ${tone} 14%, transparent)`,
        color: tone,
        border: `1px solid color-mix(in srgb, ${tone} 28%, transparent)`,
        fontFeatureSettings: '"tnum"',
      }}
    >
      {LABEL[bucket]} · {score}/100
    </span>
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
