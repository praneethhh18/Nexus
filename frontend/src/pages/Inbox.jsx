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
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Check, X, AlertTriangle, Clock, ChevronDown, ChevronRight, Inbox as InboxIcon,
  CheckSquare, Square, Calendar as CalendarIcon, ArrowRight,
} from 'lucide-react';
import EmptyState from '../components/EmptyState';
import { listApprovals, approveAction, rejectAction } from '../services/agent';
import { listPersonas, listNudges, dismissNudge, acceptNudge } from '../services/agents';
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
function ApprovalRow({ action, personaByKey, expanded, onToggle, onApprove, onReject }) {
  const color = STATUS_COLORS[action.status] || 'var(--color-text-dim)';
  const isPending = action.status === 'pending';
  const agentKey = TOOL_TO_AGENT[action.tool_name];
  const persona = agentKey ? personaByKey[agentKey] : null;
  return (
    <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{ padding: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
        <button onClick={onToggle} style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 2 }}>
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
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
        {isPending && (
          <div className="row-actions">
            <button className="btn-ghost" style={{ color: 'var(--color-err)' }} onClick={() => onReject(action)}>
              <X size={12} /> Reject
            </button>
            <button className="btn-primary" onClick={() => onApprove(action)}>
              <Check size={12} /> Approve
            </button>
          </div>
        )}
      </div>
      {expanded && (
        <div style={{ padding: '10px 16px 14px', borderTop: '1px solid var(--color-border)', background: 'var(--color-bg)' }}>
          <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Arguments</div>
          <pre style={{ fontSize: 10, color: 'var(--color-text)', margin: 0, overflow: 'auto', maxHeight: 260, padding: 8, background: 'var(--color-bg)', borderRadius: 6 }}>
{JSON.stringify(action.args || {}, null, 2)}
          </pre>
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
  const navigate = useNavigate();

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const [approvals, overdue, today, cal, n] = await Promise.all([
        listApprovals('pending').catch(() => ({ actions: [] })),
        listTasks({ due_window: 'overdue', status: 'active', limit: 20 }).catch(() => []),
        listTasks({ due_window: 'today',   status: 'active', limit: 20 }).catch(() => []),
        calendarStatus().catch(() => null),
        listNudges().catch(() => []),
      ]);
      setActions(approvals.actions || []);
      setOverdueTasks(overdue || []);
      setTodayTasks(today || []);
      setNudges(n || []);
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

  const handleApprove = async (a) => {
    if (!confirm(`Approve and execute?\n\n${a.summary}`)) return;
    try { await approveAction(a.id); flash('Approved.'); reload(); }
    catch (e) { flash(`Failed: ${e.message}`); }
  };
  const handleReject = async (a) => {
    const reason = prompt('Why are you rejecting? (optional)', '');
    if (reason === null) return;
    try { await rejectAction(a.id, reason); flash('Rejected.'); reload(); }
    catch (e) { flash(`Failed: ${e.message}`); }
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
                  onToggle={() => setExpanded(p => ({ ...p, [a.id]: !p[a.id] }))}
                  onApprove={handleApprove}
                  onReject={handleReject}
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
          </>
        )}
      </div>
    </div>
  );
}
