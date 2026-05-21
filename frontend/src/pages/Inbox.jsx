/**
 * Inbox — one page for "what needs me right now".
 *
 * Unifies three streams into a single triage view:
 *   1. Needs your approval  — agent-drafted actions awaiting decision
 *   2. Your overdue items   — tasks past their due date
 *   3. Today                — tasks due today + calendar events today
 *
 * Empty sections hide entirely. Each row links to the full record for
 * deeper editing, so this page stays fast to scan.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Check, X, AlertTriangle, Clock, ChevronDown, ChevronRight, Inbox as InboxIcon,
  CheckSquare, Square, Calendar as CalendarIcon, ArrowRight, Pencil, Sparkles, Mail,
} from 'lucide-react';
import EmptyState from '../components/EmptyState';
import { listApprovals, approveAction, rejectAction, refineAction } from '../services/agent';
import { listPersonas, listNudges, dismissNudge, acceptNudge } from '../services/agents';
import { briefingRun, briefingLatest } from '../services/briefing';
import { listInteractions } from '../services/crm';
import { listTasks, updateTask } from '../services/tasks';
import { calendarStatus, calendarEvents } from '../services/calendar';
import { Loader2, Bot } from 'lucide-react';

const STATUS_COLORS = {
  pending: 'var(--color-warn)', approved: 'var(--color-info)', rejected: 'var(--color-text-dim)',
  executed: 'var(--color-ok)', failed: 'var(--color-err)', expired: 'var(--color-text-dim)',
};

const TOOL_TO_AGENT = {
  send_invoice_email: 'invoice_reminder',
  send_triage_reply:  'email_triage',
  draft_reply:        'email_triage',
  classify_and_reply: 'email_triage',
};

function fmtWhen(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch { return iso.slice(0, 16); }
}
function fmtTimeShort(iso) {
  if (!iso) return '';
  try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); }
  catch { return ''; }
}
function daysOverdue(due) {
  if (!due) return 0;
  const d = new Date(due + 'T00:00:00'); const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.floor((today.getTime() - d.getTime()) / 86400000);
}

// ── Section wrapper ─────────────────────────────────────────────────────────
function Section({ title, count, color, icon: Icon, children }) {
  if (!count) return null;
  return (
    <div style={{ marginBottom: 18 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        marginBottom: 8, padding: '0 4px',
      }}>
        <Icon size={14} color={color} />
        <span style={{
          fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.8,
          color: 'var(--color-text-dim)',
        }}>{title}</span>
        <span style={{
          fontSize: 10, padding: '1px 7px', borderRadius: 'var(--r-pill)',
          background: 'var(--color-surface-3)', color: 'var(--color-text-muted)',
          fontWeight: 600,
        }}>{count}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>{children}</div>
    </div>
  );
}

// ── Approval row ────────────────────────────────────────────────────────────
// Map raw tool args → list of {label, value, multiline?} so the
// expanded panel can render an email/invoice/task draft as a readable
// preview instead of a JSON blob.
function previewFields(toolName, args) {
  const a = args || {};
  if (toolName === 'send_email') {
    return [
      { label: 'To',      value: a.to },
      { label: 'Subject', value: a.subject },
      { label: 'Body',    value: a.body, multiline: true, editable: true, key: 'body' },
    ];
  }
  if (toolName === 'create_task') {
    return [
      { label: 'Title',       value: a.title, editable: true, key: 'title' },
      { label: 'Due',         value: a.due_date },
      { label: 'Priority',    value: a.priority },
      { label: 'Description', value: a.description, multiline: true, editable: true, key: 'description' },
    ].filter(f => f.value);
  }
  if (toolName === 'create_invoice') {
    return [
      { label: 'Customer',  value: a.customer_name || a.customer_email },
      { label: 'Items',     value: Array.isArray(a.line_items)
                                    ? a.line_items.map(li => `${li.description || ''} × ${li.qty || 1} @ ${li.unit_price || 0}`).join('\n')
                                    : a.line_items,
        multiline: true },
      { label: 'Due',       value: a.due_date },
      { label: 'Currency',  value: a.currency || 'INR' },
    ].filter(f => f.value);
  }
  if (toolName === 'create_contact') {
    return [
      { label: 'Name',  value: [a.first_name, a.last_name].filter(Boolean).join(' ') || a.name },
      { label: 'Email', value: a.email },
      { label: 'Phone', value: a.phone },
      { label: 'Company', value: a.company_name },
    ].filter(f => f.value);
  }
  // Fallback: dump every top-level field
  return Object.entries(a).map(([k, v]) => ({
    label: k,
    value: typeof v === 'object' ? JSON.stringify(v, null, 2) : String(v),
    multiline: typeof v === 'object' || (typeof v === 'string' && v.length > 80),
  }));
}


function ApprovalRow({ action, personaByKey, expanded, onToggle,
                       confirmMode, rejectReason, setRejectReason,
                       refineDraft, setRefineDraft, refineMode, setRefineMode,
                       onApprove, onReject, onRefine }) {
  const color = STATUS_COLORS[action.status] || 'var(--color-text-dim)';
  const isPending = action.status === 'pending';
  const agentKey = TOOL_TO_AGENT[action.tool_name];
  const persona = agentKey ? personaByKey[agentKey] : null;
  const fields = previewFields(action.tool_name, action.args);

  return (
    <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
      {/* Collapsed header — clickable area reveals the draft. */}
      <div
        onClick={() => isPending && onToggle()}
        style={{ padding: 12, display: 'flex', alignItems: 'center', gap: 10,
                 cursor: isPending ? 'pointer' : 'default' }}
      >
        <span style={{ color: 'var(--color-text-dim)', display: 'flex', alignItems: 'center' }}>
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {action.summary || action.tool_name}
            </span>
            <span style={{
              fontSize: 9, padding: '2px 8px', borderRadius: 10, fontWeight: 600,
              background: `color-mix(in srgb, ${color} 13%, transparent)`, color, textTransform: 'uppercase',
            }}>{action.status}</span>
            {persona && (
              <span style={{
                fontSize: 9, padding: '2px 8px', borderRadius: 'var(--r-pill)',
                color: 'var(--color-accent)', background: 'var(--color-accent-soft)',
                border: '1px solid color-mix(in srgb, var(--color-accent) 22%, transparent)',
                fontWeight: 600, letterSpacing: 0.3,
                display: 'inline-flex', alignItems: 'center', gap: 4,
              }}>
                <span style={{ fontSize: 10 }}>{persona.emoji}</span>
                by {persona.name} · {persona.role_tag}
              </span>
            )}
          </div>
          <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>
            {fmtWhen(action.created_at)}
          </div>
        </div>
        {isPending && !expanded && (
          <button
            className="btn-primary"
            onClick={(e) => { e.stopPropagation(); onToggle(); }}
            style={{ flexShrink: 0 }}
          >
            View & Approve
          </button>
        )}
      </div>

      {/* Expanded panel: human-readable preview + Approve/Refine/Reject. */}
      {expanded && (
        <div style={{ padding: '12px 16px 16px', borderTop: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
          {fields.length === 0 ? (
            <p style={{ fontSize: 12, color: 'var(--color-text-dim)', margin: 0 }}>
              No preview fields for this action type.
            </p>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: '110px 1fr', gap: '8px 14px', alignItems: 'start', fontSize: 13 }}>
              {fields.map((f, i) => {
                const isEditing = refineMode && f.editable;
                const v = isEditing ? (refineDraft[f.key] ?? f.value ?? '') : f.value;
                return (
                  <React.Fragment key={i}>
                    <div style={{ color: 'var(--color-text-muted)', fontSize: 11, paddingTop: f.multiline ? 6 : 2, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                      {f.label}
                    </div>
                    {isEditing ? (
                      f.multiline ? (
                        <textarea
                          value={v}
                          onChange={(e) => setRefineDraft({ ...refineDraft, [f.key]: e.target.value })}
                          rows={Math.min(12, Math.max(4, (v || '').split('\n').length + 1))}
                          style={{ padding: 8, borderRadius: 6, border: '1px solid var(--color-border-strong)',
                                   background: 'var(--color-surface-2)', color: 'var(--color-text)',
                                   fontSize: 13, fontFamily: 'inherit', resize: 'vertical' }}
                        />
                      ) : (
                        <input
                          type="text"
                          value={v}
                          onChange={(e) => setRefineDraft({ ...refineDraft, [f.key]: e.target.value })}
                          style={{ padding: '6px 10px', borderRadius: 6, border: '1px solid var(--color-border-strong)',
                                   background: 'var(--color-surface-2)', color: 'var(--color-text)',
                                   fontSize: 13, fontFamily: 'inherit' }}
                        />
                      )
                    ) : (
                      <div style={{ color: 'var(--color-text)',
                                    whiteSpace: f.multiline ? 'pre-wrap' : 'normal',
                                    wordBreak: 'break-word',
                                    background: f.multiline ? 'var(--color-surface-2)' : 'transparent',
                                    padding: f.multiline ? 10 : 0,
                                    borderRadius: f.multiline ? 6 : 0,
                                    border: f.multiline ? '1px solid var(--color-border)' : 'none' }}>
                        {v || <span style={{ color: 'var(--color-text-dim)', fontStyle: 'italic' }}>—</span>}
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>
          )}

          {/* Action buttons — only for pending. */}
          {isPending && !confirmMode && !refineMode && (
            <div style={{ marginTop: 14, display: 'flex', gap: 8, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
              <button className="btn-ghost" style={{ color: 'var(--color-err)' }} onClick={() => onReject(action)}>
                <X size={12} /> Reject
              </button>
              <button className="btn-ghost" onClick={() => { setRefineDraft({}); setRefineMode(true); }}>
                <Pencil size={12} /> Refine
              </button>
              <button className="btn-primary" style={{ background: 'var(--color-ok)' }} onClick={() => onApprove(action)}>
                <Check size={12} /> Approve & Send
              </button>
            </div>
          )}

          {/* Confirm reject inline. */}
          {isPending && confirmMode === 'reject' && (
            <div style={{ marginTop: 14, display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
              <input
                type="text"
                value={rejectReason}
                autoFocus
                placeholder="Why are you rejecting? (optional)"
                onChange={(e) => setRejectReason(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') onReject(action, true); if (e.key === 'Escape') onReject(null); }}
                style={{ flex: 1, minWidth: 200, padding: '8px 12px', borderRadius: 6,
                         border: '1px solid var(--color-border-strong)',
                         background: 'var(--color-bg)', color: 'var(--color-text)',
                         fontSize: 13, fontFamily: 'inherit' }}
              />
              <button className="btn-ghost" onClick={() => onReject(null)}>Cancel</button>
              <button className="btn-primary" style={{ background: 'var(--color-err)' }} onClick={() => onReject(action, true)}>
                <X size={12} /> Confirm reject
              </button>
            </div>
          )}

          {/* Refine mode — Save & Approve commits the edits then approves. */}
          {isPending && refineMode && (
            <div style={{ marginTop: 14, display: 'flex', gap: 8, justifyContent: 'flex-end', flexWrap: 'wrap' }}>
              <button className="btn-ghost" onClick={() => { setRefineMode(false); setRefineDraft({}); }}>Cancel edit</button>
              <button className="btn-primary" style={{ background: 'var(--color-ok)' }} onClick={() => onRefine(action)}>
                <Check size={12} /> Save & Approve
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Task row ────────────────────────────────────────────────────────────────
function TaskRow({ task, onToggleDone, onOpen }) {
  const overdue = daysOverdue(task.due_date);
  return (
    <div
      onClick={() => onOpen()}
      style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: '10px 12px', borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border)',
        cursor: 'pointer',
        transition: 'border-color var(--dur-fast) var(--ease-out)',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-border-strong)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; }}
    >
      <button
        onClick={(e) => { e.stopPropagation(); onToggleDone(task); }}
        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 2, display: 'flex', alignItems: 'center' }}
        title="Mark done"
      >
        {task.status === 'done'
          ? <CheckSquare size={15} color="var(--color-ok)" />
          : <Square size={15} color="var(--color-text-dim)" />}
      </button>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 13, color: 'var(--color-text)',
          textDecoration: task.status === 'done' ? 'line-through' : 'none',
          opacity: task.status === 'done' ? 0.6 : 1,
        }}>
          {task.title}
        </div>
        <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 2, display: 'flex', gap: 8, alignItems: 'center' }}>
          {task.priority && task.priority !== 'normal' && (
            <span style={{
              color: task.priority === 'high' || task.priority === 'urgent' ? 'var(--color-warn)' : 'var(--color-text-dim)',
              fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5,
            }}>{task.priority}</span>
          )}
          {overdue > 0 && (
            <span style={{ color: 'var(--color-err)', fontWeight: 600 }}>
              {overdue} day{overdue !== 1 ? 's' : ''} overdue
            </span>
          )}
          {overdue === 0 && task.due_date && <span>Due today</span>}
        </div>
      </div>
      <ArrowRight size={12} color="var(--color-text-dim)" />
    </div>
  );
}

// ── Nudge row ───────────────────────────────────────────────────────────────
function NudgeRow({ nudge, busy, onAccept, onDismiss }) {
  return (
    <div className="panel" style={{
      padding: 12, display: 'flex', alignItems: 'center', gap: 10,
      borderColor: 'color-mix(in srgb, var(--color-accent) 22%, transparent)',
      background: 'color-mix(in srgb, var(--color-accent) 4%, var(--color-surface-2))',
    }}>
      <div style={{
        width: 30, height: 30, borderRadius: 'var(--r-sm)',
        background: 'color-mix(in srgb, var(--color-accent) 16%, transparent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 16, flexShrink: 0,
      }}>
        {nudge.agent_emoji || <Bot size={14} color="var(--color-accent)" />}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{
            fontSize: 9, padding: '2px 7px', borderRadius: 'var(--r-pill)',
            color: 'var(--color-accent)', background: 'var(--color-accent-soft)',
            border: '1px solid color-mix(in srgb, var(--color-accent) 22%, transparent)',
            fontWeight: 600, letterSpacing: 0.3,
          }}>{nudge.agent_name} · {nudge.agent_role_tag}</span>
          <span style={{ fontSize: 13, color: 'var(--color-text)' }}>{nudge.title}</span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 2 }}>{nudge.detail}</div>
      </div>
      <div className="row-actions">
        <button className="btn-primary" disabled={busy} onClick={onAccept}
          style={{ fontSize: 12, padding: '6px 12px' }}>
          {busy
            ? <><Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} /> Working…</>
            : <>{nudge.cta_label} <ChevronRight size={12} /></>}
        </button>
        <button onClick={onDismiss} title="Not now" aria-label="Dismiss nudge"
          className="tap"
          style={{ background: 'transparent', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer' }}>
          <X size={13} />
        </button>
      </div>
    </div>
  );
}

// ── Recently-sent email row ─────────────────────────────────────────────────
function SentRow({ interaction, expanded, onToggle }) {
  const subject = interaction.subject || interaction.title || '(no subject)';
  // The interaction.summary holds the email body the agent sent (first 500
  // chars). Bigger sends have it truncated server-side.
  const body = interaction.summary || interaction.body || '';
  // `to` is in metadata for agent-sent emails; fall back to contact name.
  const meta = interaction.metadata || {};
  const to = meta.to || interaction.contact_name || interaction.recipient || '—';
  return (
    <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
      <div onClick={onToggle}
           style={{ padding: 12, display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
        <span style={{ color: 'var(--color-text-dim)', display: 'flex' }}>
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text)',
                            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {subject}
            </span>
            <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 10,
                            background: 'color-mix(in srgb, var(--color-ok) 12%, transparent)',
                            color: 'var(--color-ok)', fontWeight: 600, textTransform: 'uppercase' }}>
              Sent
            </span>
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 2 }}>
            To {to} · {fmtWhen(interaction.created_at)}
          </div>
        </div>
      </div>
      {expanded && (
        <div style={{ padding: '10px 16px 14px', borderTop: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr', gap: '6px 12px', fontSize: 12 }}>
            <div style={{ color: 'var(--color-text-muted)' }}>To</div>
            <div style={{ color: 'var(--color-text)' }}>{to}</div>
            <div style={{ color: 'var(--color-text-muted)' }}>Subject</div>
            <div style={{ color: 'var(--color-text)' }}>{subject}</div>
            <div style={{ color: 'var(--color-text-muted)' }}>Body</div>
            <div style={{ color: 'var(--color-text)', whiteSpace: 'pre-wrap',
                          background: 'var(--color-surface-2)', padding: 8, borderRadius: 6,
                          maxHeight: 160, overflow: 'auto', fontSize: 12.5 }}>
              {body || <span style={{ color: 'var(--color-text-dim)', fontStyle: 'italic' }}>(no body preview)</span>}
            </div>
          </div>
          <div style={{ marginTop: 8, fontSize: 10.5, color: 'var(--color-text-dim)' }}>
            Read receipts and bounce tracking require a Resend account with a
            verified domain — configure in <strong>Settings → Email</strong>.
          </div>
        </div>
      )}
    </div>
  );
}


// ── Calendar event row ──────────────────────────────────────────────────────
function EventRow({ event }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '10px 12px', borderRadius: 'var(--r-md)',
      background: 'var(--color-surface-2)',
      border: '1px solid var(--color-border)',
    }}>
      <div style={{
        width: 44, fontSize: 11, fontWeight: 600, color: 'var(--color-info)',
        textAlign: 'center', flexShrink: 0,
      }}>
        {fmtTimeShort(event.start)}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, color: 'var(--color-text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {event.summary || 'Untitled event'}
        </div>
        {event.location && (
          <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 2 }}>{event.location}</div>
        )}
      </div>
    </div>
  );
}

// ── Main ────────────────────────────────────────────────────────────────────
export default function Inbox() {
  const [actions, setActions] = useState([]);
  const [overdueTasks, setOverdueTasks] = useState([]);
  const [todayTasks, setTodayTasks] = useState([]);
  const [events, setEvents] = useState([]);
  const [nudges, setNudges] = useState([]);
  const [nudgeBusy, setNudgeBusy] = useState(null);
  const [personaByKey, setPersonaByKey] = useState({});
  const [expanded, setExpanded] = useState({});
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(true);
  // Approval UX state. The row expands to a "review" panel; from there
  // the user can Approve (fires immediately — review was the confirm),
  // Refine (edit the agent's draft inline, then Save & Approve), or
  // Reject (with optional reason inline).
  const [rejectingId, setRejectingId] = useState(null);
  const [rejectReason, setRejectReason] = useState('');
  const [refiningId, setRefiningId] = useState(null);
  const [refineDraft, setRefineDraft] = useState({});
  // Inline briefing surface — set when the user clicks the "Generate
  // briefing" nudge so the result appears IN the Inbox instead of
  // teleporting them to Dashboard.
  const [briefingInline, setBriefingInline] = useState(null);
  // Recently-sent emails / actions: read-only audit trail so the user
  // can see what messages actually went out (vs queued for approval).
  // Sourced from nexus_interactions where type='email'.
  const [sentEmails, setSentEmails] = useState([]);
  const [sentExpanded, setSentExpanded] = useState({});
  const navigate = useNavigate();

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [approvals, overdue, today, cal, n, sent] = await Promise.all([
        listApprovals('pending').catch(() => ({ actions: [] })),
        listTasks({ due_window: 'overdue', status: 'active', limit: 20 }).catch(() => []),
        listTasks({ due_window: 'today',   status: 'active', limit: 20 }).catch(() => []),
        calendarStatus().catch(() => null),
        listNudges().catch(() => []),
        listInteractions({ type: 'email', limit: 15 }).catch(() => []),
      ]);
      setActions(approvals.actions || []);
      setOverdueTasks(overdue || []);
      setTodayTasks(today || []);
      setNudges(n || []);
      setSentEmails(Array.isArray(sent) ? sent : (sent?.interactions || []));
      if (cal?.connected) {
        try { setEvents(await calendarEvents(1, 10)); } catch { setEvents([]); }
      } else { setEvents([]); }
    } catch (e) { setMsg(`Failed: ${e.message}`); }
    setLoading(false);
  }, []);

  const handleAcceptNudge = async (n) => {
    if (nudgeBusy) return;
    setNudgeBusy(n.id);
    try {
      // Special case: the "Generate briefing" nudge. The backend used to
      // accept-then-navigate to /dashboard which felt like a teleport —
      // user clicked a button on Inbox and ended up on a different page
      // wondering what happened. Now we run the briefing here and show
      // it inline at the top of the Inbox.
      const isBriefingNudge = /brief/i.test(n.id || '') ||
                              /brief/i.test(n.cta_label || '') ||
                              /brief/i.test(n.title || '');
      if (isBriefingNudge) {
        try { await briefingRun(); } catch { /* fall through to latest */ }
        const latest = await briefingLatest().catch(() => null);
        if (latest?.id) setBriefingInline(latest);
        // Tell the backend the nudge was actioned, but don't follow its
        // navigate hint.
        try { await acceptNudge(n.id); } catch { /* non-fatal */ }
        setNudges(prev => prev.filter(x => x.id !== n.id));
        reload();
        return;
      }
      const r = await acceptNudge(n.id);
      setNudges(r.next_nudges || []);
      if (r.result?.kind === 'navigate' && r.result.path) {
        navigate(r.result.path);
      } else {
        reload();
      }
    } catch (e) { flash(`Failed: ${e.message}`); }
    finally { setNudgeBusy(null); }
  };
  const handleDismissNudge = async (n) => {
    try { setNudges(await dismissNudge(n.id)); } catch {}
  };

  useEffect(() => {
    listPersonas().then(list => {
      const map = {};
      for (const p of list) map[p.agent_key] = p;
      setPersonaByKey(map);
    }).catch(() => {});
  }, []);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    const h = () => reload();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reload]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  // Approve: review-then-commit. Since the row already expanded showing
  // the full draft, clicking Approve here IS the confirmation — no
  // second dialog. One click is the commit because the user already
  // engaged via "View & Approve".
  const handleApprove = async (a) => {
    try { await approveAction(a.id); flash('Approved — action executed.'); reload(); }
    catch (e) { flash(`Failed: ${e.message}`); }
  };

  // Reject: two states. First call opens the inline reason input.
  // Second call (`commit=true`) fires the API. `handleReject(null)`
  // cancels the input.
  const handleReject = async (a, commit = false) => {
    if (a == null) { setRejectingId(null); setRejectReason(''); return; }
    if (!commit) { setRejectingId(a.id); setRejectReason(''); return; }
    try {
      await rejectAction(a.id, rejectReason);
      flash('Rejected.');
      setRejectingId(null); setRejectReason('');
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  // Refine: write the edited args back to the pending action, then
  // immediately approve so the user doesn't have to click twice.
  const handleRefine = async (a) => {
    try {
      const newArgs = { ...(a.args || {}), ...refineDraft };
      await refineAction(a.id, newArgs);
      await approveAction(a.id);
      flash('Edited & approved.');
      setRefiningId(null); setRefineDraft({});
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };
  const handleToggleDone = async (t) => {
    try {
      await updateTask(t.id, { status: t.status === 'done' ? 'open' : 'done' });
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const totalItems = actions.length + overdueTasks.length + todayTasks.length + events.length + nudges.length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Inbox</h1>
          <p>Everything that wants your attention right now — approvals, overdue items, today's meetings</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <InboxIcon size={16} color="var(--color-accent)" />
          <span style={{ fontSize: 13, color: 'var(--color-text)' }}>{totalItems} item{totalItems !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {/* Inline briefing — shown when the user clicked "Generate
            briefing" from a nudge above. Stays on the Inbox page so the
            click doesn't feel like a teleport. */}
        {briefingInline && briefingInline.data && (
          <div style={{
            marginBottom: 20, padding: 16, borderRadius: 12,
            background: 'color-mix(in srgb, var(--color-accent) 8%, transparent)',
            border: '1px solid color-mix(in srgb, var(--color-accent) 25%, transparent)',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Sparkles size={14} color="var(--color-accent)" />
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
                  Today&apos;s briefing
                </span>
                {briefingInline.data?.date && (
                  <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                    · {briefingInline.data.date}
                  </span>
                )}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn-ghost" onClick={() => navigate('/')}
                        style={{ fontSize: 11 }}>
                  Open on Dashboard
                </button>
                <button onClick={() => setBriefingInline(null)}
                        title="Dismiss"
                        style={{ background: 'none', border: 'none',
                                 color: 'var(--color-text-dim)', cursor: 'pointer', padding: 2 }}>
                  <X size={14} />
                </button>
              </div>
            </div>
            <div style={{ fontSize: 13, color: 'var(--color-text)', lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>
              {(briefingInline.data?.summary || briefingInline.data?.text || '').slice(0, 600)
                || 'Briefing ready — open the Dashboard to read the full version.'}
            </div>
          </div>
        )}

        {loading && totalItems === 0 ? (
          <p style={{ color: 'var(--color-text-dim)', fontSize: 12, textAlign: 'center' }}>Loading…</p>
        ) : totalItems === 0 ? (
          <EmptyState
            icon={InboxIcon}
            title="You're all caught up"
            description="Nothing needs you right now. Your team will drop approvals, nudges, and overdue items here as they come up."
            accent="var(--color-ok)"
            primaryLabel="Go to agents"
            onPrimary={() => navigate('/agents')}
          />
        ) : (
          <>
            <Section title="Your team suggests" count={nudges.length} color="var(--color-accent)" icon={Bot}>
              {nudges.map(n => (
                <NudgeRow
                  key={n.id}
                  nudge={n}
                  busy={nudgeBusy === n.id}
                  onAccept={() => handleAcceptNudge(n)}
                  onDismiss={() => handleDismissNudge(n)}
                />
              ))}
            </Section>

            <Section title="Needs your approval" count={actions.length} color="var(--color-warn)" icon={AlertTriangle}>
              {actions.map(a => (
                <ApprovalRow
                  key={a.id}
                  action={a}
                  personaByKey={personaByKey}
                  expanded={!!expanded[a.id]}
                  onToggle={() => {
                    // Toggling away cancels any in-progress reject/refine on this row.
                    setExpanded(p => ({ ...p, [a.id]: !p[a.id] }));
                    if (rejectingId === a.id) { setRejectingId(null); setRejectReason(''); }
                    if (refiningId === a.id)  { setRefiningId(null);  setRefineDraft({}); }
                  }}
                  confirmMode={rejectingId === a.id ? 'reject' : null}
                  rejectReason={rejectReason}
                  setRejectReason={setRejectReason}
                  refineMode={refiningId === a.id}
                  setRefineMode={(v) => v ? setRefiningId(a.id) : (setRefiningId(null), setRefineDraft({}))}
                  refineDraft={refineDraft}
                  setRefineDraft={setRefineDraft}
                  onApprove={handleApprove}
                  onReject={handleReject}
                  onRefine={handleRefine}
                />
              ))}
            </Section>

            <Section title="Your overdue items" count={overdueTasks.length} color="var(--color-err)" icon={Clock}>
              {overdueTasks.map(t => (
                <TaskRow key={t.id} task={t} onToggleDone={handleToggleDone} onOpen={() => navigate('/tasks')} />
              ))}
            </Section>

            <Section title="Today" count={todayTasks.length + events.length} color="var(--color-info)" icon={CalendarIcon}>
              {todayTasks.map(t => (
                <TaskRow key={t.id} task={t} onToggleDone={handleToggleDone} onOpen={() => navigate('/tasks')} />
              ))}
              {events.map(ev => <EventRow key={ev.id} event={ev} />)}
            </Section>

            {sentEmails.length > 0 && (
              <Section title="Recently sent" count={sentEmails.length} color="var(--color-ok)" icon={Mail}>
                {sentEmails.map(s => (
                  <SentRow
                    key={s.id}
                    interaction={s}
                    expanded={!!sentExpanded[s.id]}
                    onToggle={() => setSentExpanded(p => ({ ...p, [s.id]: !p[s.id] }))}
                  />
                ))}
              </Section>
            )}
          </>
        )}
      </div>

    </div>
  );
}
