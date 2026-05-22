import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Calendar, AlertTriangle, Check, Trash2, Send,
  CheckSquare, UserPlus, UserMinus, ArrowRightLeft, Flag, MessageSquare,
  CircleDot, History, Plus,
} from 'lucide-react';

import {
  getTask, updateTask, deleteTask,
  getTaskThread, addTaskComment, deleteTaskComment,
  STATUSES, PRIORITIES,
} from '../services/tasks';
import { listMembers } from '../services/businesses';
import { getCurrentBusiness, getUser } from '../services/auth';

// ── Shared formatters ─────────────────────────────────────────────────────
function relativeTime(iso) {
  if (!iso) return '';
  const then = new Date(iso);
  const now = new Date();
  const diff = (now - then) / 1000;
  if (diff < 60)          return 'just now';
  if (diff < 3600)        return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400)       return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 86400 * 7)   return `${Math.floor(diff / 86400)}d ago`;
  return then.toISOString().substring(0, 10);
}

// User-id -> friendly label using the loaded members list. Falls back
// to "Someone" for unknown ids (system actions, deleted users).
function actorLabel(userId, membersById, meId) {
  if (!userId)              return 'System';
  if (userId === meId)      return 'You';
  const m = membersById[userId];
  if (m?.name?.trim())      return m.name.trim();
  if (m?.email)             return m.email.split('@')[0];
  if (userId === 'vox')     return 'Vox (voice agent)';
  return 'Someone';
}


// ── Activity verb rendering ───────────────────────────────────────────────
// Each thread row's `kind` maps to (icon, sentence-fragment). Keeps the
// pane reading like a human conversation: "Praneeth assigned this to
// Anuj" rather than "kind: assigned, payload: {...}".
const ACTIVITY_VERB = {
  created: {
    icon: Plus, color: 'var(--color-ok)',
    text: (p) => `created this task`,
  },
  assigned: {
    icon: UserPlus, color: 'var(--color-accent)',
    text: (p, label) => `assigned this to ${label(p.to)}`,
  },
  reassigned: {
    icon: ArrowRightLeft, color: 'var(--color-accent)',
    text: (p, label) => `reassigned from ${label(p.from)} to ${label(p.to)}`,
  },
  unassigned: {
    icon: UserMinus, color: 'var(--color-text-dim)',
    text: (p, label) => `removed ${label(p.from)} as assignee`,
  },
  status_changed: {
    icon: CircleDot, color: 'var(--color-warn)',
    text: (p) => `moved status from ${p.from?.replace('_', ' ')} to ${p.to?.replace('_', ' ')}`,
  },
  completed: {
    icon: Check, color: 'var(--color-ok)',
    text: () => `marked this done`,
  },
  reopened: {
    icon: CircleDot, color: 'var(--color-warn)',
    text: () => `reopened this task`,
  },
  priority_changed: {
    icon: Flag, color: 'var(--color-warn)',
    text: (p) => `changed priority from ${p.from} to ${p.to}`,
  },
  due_changed: {
    icon: Calendar, color: 'var(--color-info)',
    text: (p) => `${p.to ? `set due date to ${p.to}` : 'cleared the due date'}`,
  },
};


// ── Activity row component ────────────────────────────────────────────────
function ActivityRow({ event, members, meId, onDeleteComment }) {
  const label = (uid) => actorLabel(uid, members, meId);
  const actor = label(event.actor_id);
  const when = relativeTime(event.created_at);

  if (event.kind === 'commented') {
    return (
      <div style={{
        display: 'flex', gap: 10, alignItems: 'flex-start',
        padding: '10px 12px',
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border)',
        borderRadius: 8,
      }}>
        <MessageSquare size={14} style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: 2 }} />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text)' }}>{actor}</span>
            <span style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{when}</span>
          </div>
          <div style={{
            fontSize: 12, color: 'var(--color-text)', lineHeight: 1.5,
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
          }}>{event.body}</div>
        </div>
        {onDeleteComment && (
          <button
            className="btn-ghost btn-sm"
            style={{ color: 'var(--color-err)', flexShrink: 0 }}
            onClick={() => onDeleteComment(event)}
            title="Delete this comment"
            aria-label="Delete comment"
          >
            <Trash2 size={11} />
          </button>
        )}
      </div>
    );
  }

  // Structured activity row (assignment, status change, etc.)
  const def = ACTIVITY_VERB[event.kind];
  if (!def) {
    return null; // unknown kind, fail silently
  }
  const Icon = def.icon;
  return (
    <div style={{
      display: 'flex', gap: 10, alignItems: 'center',
      padding: '6px 12px',
      fontSize: 11, color: 'var(--color-text-muted)',
    }}>
      <span style={{
        width: 22, height: 22, borderRadius: '50%',
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border)',
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
        color: def.color, flexShrink: 0,
      }}>
        <Icon size={11} />
      </span>
      <span style={{ flex: 1 }}>
        <strong style={{ color: 'var(--color-text)', fontWeight: 600 }}>{actor}</strong>
        {' '}
        {def.text(event.payload || {}, label)}
      </span>
      <span style={{ fontSize: 10, color: 'var(--color-text-dim)', flexShrink: 0 }}>
        {when}
      </span>
    </div>
  );
}


// ── Main page ─────────────────────────────────────────────────────────────
export default function TaskDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [task, setTask] = useState(null);
  const [thread, setThread] = useState([]);
  const [members, setMembers] = useState([]);
  const [meId, setMeId] = useState(null);
  const [msg, setMsg] = useState('');
  const [err, setErr] = useState('');
  const [savingField, setSavingField] = useState('');
  const [commentDraft, setCommentDraft] = useState('');
  const [posting, setPosting] = useState(false);
  const composerRef = useRef(null);

  // Initial load.
  useEffect(() => {
    const u = getUser();
    if (u) setMeId(u.id || u.user_id || null);
    const biz = getCurrentBusiness();
    if (biz?.id) {
      listMembers(biz.id)
        .then((d) => setMembers(Array.isArray(d) ? d : []))
        .catch(() => setMembers([]));
    }
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [t, th] = await Promise.all([getTask(id), getTaskThread(id)]);
      setTask(t);
      setThread(th);
      setErr('');
    } catch (e) {
      setErr(e.message || 'Failed to load task');
    }
  }, [id]);

  useEffect(() => { refresh(); }, [refresh]);

  const membersById = useMemo(
    () => members.reduce((acc, m) => {
      if (m?.user_id) acc[m.user_id] = m;
      return acc;
    }, {}),
    [members],
  );

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  // Optimistic field update — set local state then reconcile via refresh.
  const saveField = async (field, value) => {
    if (!task) return;
    if (task[field] === value) return;
    setSavingField(field);
    try {
      const updated = await updateTask(id, { [field]: value });
      setTask(updated);
      const th = await getTaskThread(id);
      setThread(th);
    } catch (e) {
      flash(`Failed: ${e.message}`);
    } finally {
      setSavingField('');
    }
  };

  const handleAddComment = async (e) => {
    e?.preventDefault?.();
    const body = commentDraft.trim();
    if (!body || posting) return;
    setPosting(true);
    try {
      await addTaskComment(id, body);
      setCommentDraft('');
      const th = await getTaskThread(id);
      setThread(th);
    } catch (e) {
      flash(`Failed: ${e.message}`);
    } finally {
      setPosting(false);
    }
  };

  const handleDeleteComment = async (event) => {
    if (!confirm('Delete this comment?')) return;
    try {
      await deleteTaskComment(id, event.id);
      const th = await getTaskThread(id);
      setThread(th);
    } catch (e) {
      flash(`Failed: ${e.message}`);
    }
  };

  const handleDeleteTask = async () => {
    if (!task) return;
    if (!confirm(`Delete "${task.title}"?\n\nThis can't be undone.`)) return;
    try {
      await deleteTask(id);
      navigate('/tasks');
    } catch (e) {
      flash(`Failed: ${e.message}`);
    }
  };

  if (err && !task) {
    return (
      <div style={{ padding: 32 }}>
        <Link to="/tasks" className="btn-ghost"><ArrowLeft size={14} /> Back to Tasks</Link>
        <div style={{ marginTop: 24, color: 'var(--color-err)' }}>{err}</div>
      </div>
    );
  }
  if (!task) {
    return (
      <div style={{ padding: 32, color: 'var(--color-text-dim)' }}>Loading…</div>
    );
  }

  const overdue = task.due_date && task.due_date < new Date().toISOString().slice(0, 10)
    && task.status !== 'done' && task.status !== 'cancelled';
  const assignee = membersById[task.assignee_id];
  const creator = membersById[task.created_by];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header: breadcrumb + actions */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <Link to="/tasks" className="btn-ghost btn-sm" style={{ marginBottom: 8 }}>
            <ArrowLeft size={12} /> Back to Tasks
          </Link>
          <h1 style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <input
              className="field-input"
              value={task.title}
              onChange={(e) => setTask({ ...task, title: e.target.value })}
              onBlur={(e) => saveField('title', e.target.value)}
              style={{
                fontSize: 22, fontWeight: 600, color: 'var(--color-text)',
                padding: '4px 8px', minWidth: 360, flex: 1,
                background: 'transparent', border: '1px solid transparent',
              }}
              onFocus={(e) => { e.target.style.borderColor = 'var(--color-border)'; }}
              onMouseOut={(e) => { if (document.activeElement !== e.target) e.target.style.borderColor = 'transparent'; }}
            />
            {overdue && (
              <span style={{
                fontSize: 11, fontWeight: 600,
                padding: '2px 10px', borderRadius: 999,
                background: 'color-mix(in srgb, var(--color-err) 12%, transparent)',
                color: 'var(--color-err)',
                display: 'inline-flex', alignItems: 'center', gap: 4,
              }}>
                <AlertTriangle size={11} /> Overdue
              </span>
            )}
          </h1>
          <p style={{ marginTop: 4 }}>
            Created by {actorLabel(task.created_by, membersById, meId)} · {relativeTime(task.created_at)}
            {task.completed_at && ` · Completed ${relativeTime(task.completed_at)}`}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn-ghost" style={{ color: 'var(--color-err)' }} onClick={handleDeleteTask}>
            <Trash2 size={13} /> Delete
          </button>
        </div>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      {/* Body: 2-column layout — left = facts, right = thread */}
      <div style={{
        flex: 1, overflow: 'auto', padding: 24,
        display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1.4fr)', gap: 20,
      }}>
        {/* LEFT: status / assignee / dates / description */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Status + priority + due in a compact 3-col row */}
          <div className="panel" style={{ padding: 16 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
              <div>
                <div className="conv-label" style={{ marginBottom: 4 }}>Status</div>
                <select
                  className="field-select"
                  value={task.status}
                  onChange={(e) => saveField('status', e.target.value)}
                  style={{ width: '100%' }}
                  disabled={savingField === 'status'}
                >
                  {STATUSES.map((s) => <option key={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <div className="conv-label" style={{ marginBottom: 4 }}>Priority</div>
                <select
                  className="field-select"
                  value={task.priority}
                  onChange={(e) => saveField('priority', e.target.value)}
                  style={{ width: '100%' }}
                  disabled={savingField === 'priority'}
                >
                  {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <div className="conv-label" style={{ marginBottom: 4 }}>Due date</div>
                <input
                  type="date"
                  className="field-input"
                  value={task.due_date || ''}
                  onChange={(e) => saveField('due_date', e.target.value || null)}
                  disabled={savingField === 'due_date'}
                />
              </div>
            </div>
          </div>

          {/* Assignee picker */}
          <div className="panel" style={{ padding: 16 }}>
            <div className="conv-label" style={{ marginBottom: 6 }}>Assigned to</div>
            <select
              className="field-select"
              value={task.assignee_id || ''}
              onChange={(e) => saveField('assignee_id', e.target.value || null)}
              style={{ width: '100%' }}
              disabled={savingField === 'assignee_id'}
            >
              <option value="">Unassigned</option>
              {members.map((m) => (
                <option key={m.user_id} value={m.user_id}>
                  {(m.name || m.email || m.user_id) + (m.role ? ` (${m.role})` : '')}
                </option>
              ))}
            </select>
            {assignee && (
              <p style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 6 }}>
                {assignee.user_id === meId
                  ? "This is on your list."
                  : `${actorLabel(task.assignee_id, membersById, meId)} sees this in their 'Assigned to me'.`}
              </p>
            )}
          </div>

          {/* Description */}
          <div className="panel" style={{ padding: 16 }}>
            <div className="conv-label" style={{ marginBottom: 6 }}>Description</div>
            <textarea
              className="field-input"
              value={task.description || ''}
              onChange={(e) => setTask({ ...task, description: e.target.value })}
              onBlur={(e) => saveField('description', e.target.value)}
              rows={8}
              placeholder="Context, links, what 'done' looks like. Future-you will thank present-you."
              style={{ width: '100%', resize: 'vertical', fontSize: 12, lineHeight: 1.55 }}
            />
            <p style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 4 }}>
              Saved when you click outside. {savingField === 'description' && '— saving…'}
            </p>
          </div>
        </div>

        {/* RIGHT: thread (activity + comments) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <History size={14} color="var(--color-text-muted)" />
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
              Activity & comments
            </span>
            <span style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>({thread.length})</span>
          </div>

          {/* Comment composer */}
          <form
            onSubmit={handleAddComment}
            className="panel"
            style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}
          >
            <textarea
              ref={composerRef}
              className="field-input"
              value={commentDraft}
              onChange={(e) => setCommentDraft(e.target.value)}
              placeholder="Leave a note for the team…"
              rows={3}
              style={{ width: '100%', resize: 'vertical', fontSize: 12, lineHeight: 1.55 }}
              onKeyDown={(e) => {
                if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                  e.preventDefault();
                  handleAddComment();
                }
              }}
            />
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ fontSize: 10, color: 'var(--color-text-dim)', flex: 1 }}>
                Cmd/Ctrl + Enter to post.
                {task.assignee_id && task.assignee_id !== meId &&
                  ` ${actorLabel(task.assignee_id, membersById, meId)} will be notified.`}
              </span>
              <button
                type="submit"
                className="btn-primary btn-sm"
                disabled={!commentDraft.trim() || posting}
              >
                <Send size={11} /> {posting ? 'Posting…' : 'Post comment'}
              </button>
            </div>
          </form>

          {/* Thread feed */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {thread.length === 0 ? (
              <div style={{
                padding: 24, textAlign: 'center', fontSize: 12,
                color: 'var(--color-text-dim)',
                background: 'var(--color-surface-1)', borderRadius: 8,
              }}>
                No activity yet. Comments and changes show up here.
              </div>
            ) : (
              thread.map((event) => (
                <ActivityRow
                  key={event.id}
                  event={event}
                  members={membersById}
                  meId={meId}
                  onDeleteComment={event.kind === 'commented' && event.actor_id === meId
                    ? handleDeleteComment : null}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
