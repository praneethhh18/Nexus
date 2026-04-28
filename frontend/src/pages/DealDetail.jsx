/**
 * Deal detail page — pipeline-stage management plus full context.
 *
 * The most useful thing this page does is the stage-advance bar at the top:
 * one click moves a deal forward without opening a modal. Combined with
 * inline interaction logging and the "create invoice on close" shortcut,
 * a sales rep can run a whole follow-up sequence without leaving the page.
 */
import { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft, Briefcase, Edit3, Trash2, Plus, Building2, User,
  Calendar, DollarSign, Receipt, Phone, Mail, MessageSquare,
  AlertCircle, Loader2, CheckCircle2, XCircle, ChevronRight,
} from 'lucide-react';
import {
  getDeal, updateDeal, deleteDeal,
  getContact, getCompany, listInteractions, createInteraction,
} from '../services/crm';
import { createTask } from '../services/tasks';

const STAGES = ['lead', 'qualified', 'proposal', 'negotiation', 'won', 'lost'];

const STAGE_TONE = {
  lead:        'var(--color-info)',
  qualified:   '#a78bfa',
  proposal:    'var(--color-warn)',
  negotiation: '#ec4899',
  won:         'var(--color-ok)',
  lost:        'var(--color-text-dim)',
};

const INTERACTION_ICONS = { call: Phone, email: Mail, meeting: Calendar, note: MessageSquare };

function formatWhen(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString([], {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso.substring(0, 16); }
}

function formatDate(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso + 'T00:00:00').toLocaleDateString([], {
      month: 'short', day: 'numeric', year: 'numeric',
    });
  } catch { return iso.substring(0, 10); }
}


export default function DealDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [deal, setDeal] = useState(null);
  const [contact, setContact] = useState(null);
  const [company, setCompany] = useState(null);
  const [interactions, setInteractions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(false);
  const [edit, setEdit] = useState({});
  const [newInter, setNewInter] = useState({ type: 'note', subject: '', summary: '' });
  const [logging, setLogging] = useState(false);
  const [advancing, setAdvancing] = useState(false);
  const [msg, setMsg] = useState('');

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const reload = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const d = await getDeal(id);
      setDeal(d);
      setEdit(d);

      const [contactRes, companyRes, ints] = await Promise.all([
        d.contact_id ? getContact(d.contact_id).catch(() => null) : Promise.resolve(null),
        d.company_id ? getCompany(d.company_id).catch(() => null) : Promise.resolve(null),
        listInteractions({ deal_id: id, limit: 30 }).catch(() => []),
      ]);
      setContact(contactRes);
      setCompany(companyRes);
      setInteractions(ints);
    } catch (e) { setError(e.message || 'Could not load deal.'); }
    setLoading(false);
  }, [id]);

  useEffect(() => { reload(); }, [reload]);

  const stageIndex = useMemo(
    () => STAGES.indexOf(deal?.stage || 'lead'),
    [deal],
  );

  const handleSave = async () => {
    try {
      await updateDeal(id, {
        name: edit.name, stage: edit.stage, value: edit.value,
        expected_close: edit.expected_close, notes: edit.notes,
      });
      setEditing(false);
      flash('Saved.');
      reload();
    } catch (e) { flash(`Save failed: ${e.message}`); }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete deal "${deal?.name}"?`)) return;
    try {
      await deleteDeal(id);
      navigate('/crm');
    } catch (e) { flash(`Delete failed: ${e.message}`); }
  };

  const handleStage = async (newStage) => {
    if (newStage === deal.stage) return;
    setAdvancing(true);
    try {
      await updateDeal(id, { stage: newStage });
      flash(`Moved to ${newStage}.`);
      reload();
    } catch (e) { flash(`Stage update failed: ${e.message}`); }
    setAdvancing(false);
  };

  const handleLogInteraction = async () => {
    if (!newInter.subject.trim() && !newInter.summary.trim()) return;
    setLogging(true);
    try {
      await createInteraction({
        ...newInter,
        deal_id: id,
        contact_id: deal?.contact_id || null,
        company_id: deal?.company_id || null,
      });
      setNewInter({ type: 'note', subject: '', summary: '' });
      flash('Interaction logged.');
      reload();
    } catch (e) { flash(`Log failed: ${e.message}`); }
    setLogging(false);
  };

  const handleFollowUpTask = async () => {
    const title = prompt(`Follow-up task for "${deal?.name}":`, 'Follow up');
    if (!title) return;
    try {
      await createTask({
        title,
        description: `Related to deal: ${deal.name}` +
                     (deal.value ? ` ($${Number(deal.value).toLocaleString()})` : ''),
        priority: 'normal',
      });
      flash('Task created.');
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleInvoiceOnClose = () => {
    navigate('/invoices', { state: { addInvoiceForDeal: id } });
  };

  if (loading) return <CenterSpinner />;
  if (error || !deal) return <NotFound message={error || 'The deal may have been deleted.'} />;

  const stageTone = STAGE_TONE[deal.stage] || 'var(--color-text-dim)';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
          <button onClick={() => navigate('/crm')} className="btn-ghost btn-sm">
            <ArrowLeft size={12} /> CRM
          </button>
          <div style={{
            width: 44, height: 44, borderRadius: 'var(--r-md)',
            background: `color-mix(in srgb, ${stageTone} 14%, transparent)`,
            color: stageTone,
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <Briefcase size={20} />
          </div>
          <div style={{ minWidth: 0 }}>
            <h1 style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.01em', margin: 0 }}>{deal.name}</h1>
            <p style={{ fontSize: 12, color: 'var(--color-text-muted)', margin: 0, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <span style={{ textTransform: 'capitalize', color: stageTone, fontWeight: 600 }}>{deal.stage}</span>
              {deal.value > 0 && <span>· ${Number(deal.value).toLocaleString()}</span>}
              {deal.expected_close && <span>· closes {formatDate(deal.expected_close)}</span>}
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

          {/* Stage advancer */}
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 10px' }}>
              <h2>Pipeline stage</h2>
              <span className="meta">click to move</span>
            </div>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {STAGES.map((s, i) => {
                const isActive = s === deal.stage;
                const isPast = i < stageIndex;
                const tone = STAGE_TONE[s];
                return (
                  <button
                    key={s}
                    onClick={() => handleStage(s)}
                    disabled={advancing || isActive}
                    style={{
                      flex: '1 1 0',
                      minWidth: 90,
                      padding: '8px 10px',
                      border: `1px solid ${isActive ? tone : 'var(--color-border)'}`,
                      borderRadius: 'var(--r-md)',
                      background: isActive
                        ? `color-mix(in srgb, ${tone} 14%, transparent)`
                        : isPast
                          ? `color-mix(in srgb, ${tone} 6%, var(--color-surface-1))`
                          : 'var(--color-surface-1)',
                      color: isActive ? tone : isPast ? 'var(--color-text-muted)' : 'var(--color-text-dim)',
                      cursor: isActive || advancing ? 'default' : 'pointer',
                      fontSize: 12, fontWeight: 600, textTransform: 'capitalize',
                      transition: 'all var(--dur-fast) var(--ease-out)',
                      display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 4,
                    }}
                  >
                    {isPast && s !== 'lost' && <CheckCircle2 size={11} />}
                    {s === 'lost' && deal.stage === 'lost' && <XCircle size={11} />}
                    {s}
                  </button>
                );
              })}
            </div>
            {deal.stage === 'won' && (
              <div style={{
                marginTop: 12, padding: 10,
                background: 'var(--color-accent-soft)',
                border: '1px solid color-mix(in srgb, var(--color-accent) 28%, transparent)',
                borderRadius: 'var(--r-md)',
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10,
              }}>
                <div style={{ fontSize: 12.5, color: 'var(--color-accent)' }}>
                  <strong>Deal won.</strong> Ready to invoice the customer?
                </div>
                <button className="btn-primary btn-sm" onClick={handleInvoiceOnClose}>
                  <Receipt size={11} /> Draft invoice
                </button>
              </div>
            )}
          </div>

          {/* Identity / edit */}
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 8px' }}><h2>Details</h2></div>
            {editing ? (
              <div style={{ display: 'grid', gap: 10 }}>
                <Field label="Name"><input className="field-input" value={edit.name || ''} onChange={(e) => setEdit({ ...edit, name: e.target.value })} /></Field>
                <Field label="Stage">
                  <select className="field-select" value={edit.stage} onChange={(e) => setEdit({ ...edit, stage: e.target.value })} style={{ width: '100%' }}>
                    {STAGES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </Field>
                <Field label="Value (USD)"><input className="field-input" type="number" min={0} step="0.01" value={edit.value || 0} onChange={(e) => setEdit({ ...edit, value: parseFloat(e.target.value) || 0 })} /></Field>
                <Field label="Expected close"><input className="field-input" type="date" value={edit.expected_close || ''} onChange={(e) => setEdit({ ...edit, expected_close: e.target.value })} /></Field>
                <Field label="Notes"><textarea className="field-input" rows={3} value={edit.notes || ''} onChange={(e) => setEdit({ ...edit, notes: e.target.value })} /></Field>
                <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 4 }}>
                  <button className="btn-ghost" onClick={() => { setEditing(false); setEdit(deal); }}>Cancel</button>
                  <button className="btn-primary" onClick={handleSave}>Save</button>
                </div>
              </div>
            ) : (
              <div style={{ display: 'grid', gap: 10 }}>
                {contact && (
                  <DetailRow icon={<User size={13} />} label="Contact">
                    <Link to={`/crm/contacts/${contact.id}`} style={{ color: 'var(--color-accent)' }}>
                      {[contact.first_name, contact.last_name].filter(Boolean).join(' ') || '—'}
                    </Link>
                    {contact.email && <span style={{ color: 'var(--color-text-dim)', marginLeft: 8 }}>· {contact.email}</span>}
                  </DetailRow>
                )}
                {company && (
                  <DetailRow icon={<Building2 size={13} />} label="Company">
                    <Link to={`/crm/companies/${company.id}`} style={{ color: 'var(--color-accent)' }}>{company.name}</Link>
                  </DetailRow>
                )}
                <DetailRow icon={<DollarSign size={13} />} label="Value">
                  {deal.value ? `$${Number(deal.value).toLocaleString()}` : <span style={{ color: 'var(--color-text-dim)' }}>Not set</span>}
                </DetailRow>
                <DetailRow icon={<Calendar size={13} />} label="Expected close">
                  {deal.expected_close ? formatDate(deal.expected_close) : <span style={{ color: 'var(--color-text-dim)' }}>Not set</span>}
                </DetailRow>
                {deal.notes && <DetailRow icon={null} label="Notes" multiline>{deal.notes}</DetailRow>}
              </div>
            )}
          </div>

          {/* Interaction log */}
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 10px' }}>
              <h2>Activity · {interactions.length}</h2>
            </div>

            <div style={{
              padding: 10, marginBottom: 12,
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--r-md)',
              display: 'flex', flexDirection: 'column', gap: 8,
            }}>
              <div style={{ display: 'flex', gap: 6 }}>
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
                className="field-input" placeholder='Subject (e.g. "Pricing discussion")'
                value={newInter.subject} onChange={(e) => setNewInter({ ...newInter, subject: e.target.value })}
                maxLength={200}
              />
              <textarea
                className="field-input" rows={2} placeholder="Summary"
                value={newInter.summary} onChange={(e) => setNewInter({ ...newInter, summary: e.target.value })}
                maxLength={2000}
              />
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button
                  className="btn-primary btn-sm" disabled={logging}
                  onClick={handleLogInteraction}
                >
                  {logging ? <Loader2 size={11} className="animate-spin" /> : <Plus size={11} />} Log
                </button>
              </div>
            </div>

            {interactions.length === 0 ? (
              <div style={{ padding: 16, textAlign: 'center', color: 'var(--color-text-dim)', fontSize: 12 }}>
                No activity logged yet.
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {interactions.map(it => {
                  const Icon = INTERACTION_ICONS[it.type] || MessageSquare;
                  return (
                    <div key={it.id} style={{
                      display: 'flex', gap: 10, alignItems: 'flex-start',
                      padding: '10px 12px',
                      background: 'var(--color-surface-1)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--r-md)',
                    }}>
                      <Icon size={13} style={{ marginTop: 2, color: 'var(--color-text-muted)', flexShrink: 0 }} />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 12.5, fontWeight: 500 }}>
                          {it.subject || <em style={{ color: 'var(--color-text-dim)' }}>(no subject)</em>}
                        </div>
                        {it.summary && <div style={{ fontSize: 12, color: 'var(--color-text-muted)', marginTop: 2 }}>{it.summary}</div>}
                        <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)', marginTop: 4 }}>
                          {it.type} · {formatWhen(it.occurred_at || it.created_at)}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right: actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div className="panel">
            <div className="section-h" style={{ margin: '0 0 10px' }}><h2>Actions</h2></div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <ActionRow icon={<Plus size={13} />} label="Follow-up task" detail="Reminder to chase this deal" onClick={handleFollowUpTask} />
              {contact && (
                <ActionRow icon={<User size={13} />} label="View contact" detail={[contact.first_name, contact.last_name].filter(Boolean).join(' ')}
                           onClick={() => navigate(`/crm/contacts/${contact.id}`)} />
              )}
              {company && (
                <ActionRow icon={<Building2 size={13} />} label="View company" detail={company.name}
                           onClick={() => navigate(`/crm/companies/${company.id}`)} />
              )}
              {deal.stage === 'won' && (
                <ActionRow icon={<Receipt size={13} />} label="Create invoice" detail="Bill the customer for this deal"
                           onClick={handleInvoiceOnClose} />
              )}
            </div>
          </div>

          <div className="panel" style={{ background: 'var(--color-surface-1)' }}>
            <div className="section-h" style={{ margin: '0 0 6px' }}><h2>Snapshot</h2></div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 12 }}>
              <Snap label="Stage" value={<span style={{ textTransform: 'capitalize', color: stageTone }}>{deal.stage}</span>} />
              <Snap label="Value" value={`$${Number(deal.value || 0).toLocaleString()}`} />
              <Snap label="Activity" value={interactions.length} />
              <Snap label="Created" value={formatDate(deal.created_at?.substring(0, 10))} />
              <Snap label="Updated" value={formatWhen(deal.updated_at)} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


// Shared bits (intentional dupe across detail pages — keeps each file
// self-contained for now; promote to components/ once the pattern stabilises).
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
        padding: 20, borderColor: 'color-mix(in srgb, var(--color-err) 28%, transparent)',
        background: 'color-mix(in srgb, var(--color-err) 6%, transparent)',
      }}>
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <AlertCircle size={18} color="var(--color-err)" style={{ marginTop: 2, flexShrink: 0 }} />
          <div>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>Not found</div>
            <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)' }}>{message}</div>
            <button className="btn-ghost btn-sm" style={{ marginTop: 10 }} onClick={() => navigate('/crm')}>
              <ArrowLeft size={11} /> Back to CRM
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
        width: 110, fontSize: 11, color: 'var(--color-text-dim)',
        display: 'flex', alignItems: 'center', gap: 5,
        textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600,
        flexShrink: 0,
      }}>
        {icon}{label}
      </div>
      <div style={{ fontSize: 12.5, color: 'var(--color-text)', flex: 1, minWidth: 0, whiteSpace: multiline ? 'pre-wrap' : 'normal' }}>
        {children}
      </div>
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

function Snap({ label, value }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
      <span style={{ color: 'var(--color-text-dim)' }}>{label}</span>
      <span style={{ fontWeight: 600, color: 'var(--color-text)', fontFeatureSettings: '"tnum"' }}>{value}</span>
    </div>
  );
}
