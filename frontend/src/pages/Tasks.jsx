import { useState, useEffect, useCallback, useRef } from 'react';
import { CheckSquare, Square, Plus, Calendar, AlertTriangle, Clock, Trash2, X, Briefcase, Repeat, Check, Sparkles, Loader2, RefreshCw } from 'lucide-react';
import { listTasks, createTask, updateTask, deleteTask, taskSummary, extractFromNotes, STATUSES, PRIORITIES } from '../services/tasks';
import { bulkDeleteTasks, bulkTaskStatus, bulkTagsFor } from '../services/tags';
import FlowBanner from '../components/FlowBanner';
import EmptyState from '../components/EmptyState';
import SuggestionPanel from '../components/SuggestionPanel';
import { TagPicker, TagChips } from '../components/TagChips';
import { useBulkSelection, BulkCheckbox, BulkActionBar, UndoToast } from '../components/BulkActionBar';

const RECURRENCES = ['none', 'daily', 'weekly', 'monthly'];

const PRIORITY_COLORS = { urgent: 'var(--color-err)', high: 'var(--color-warn)', normal: 'var(--color-info)', low: 'var(--color-text-dim)' };
const STATUS_COLORS = { open: 'var(--color-text-dim)', in_progress: 'var(--color-warn)', done: 'var(--color-ok)', cancelled: 'var(--color-text-dim)' };

function todayStr() {
  return new Date().toISOString().substring(0, 10);
}

function isoToDateLabel(iso) {
  if (!iso) return '';
  const s = iso.substring(0, 10);
  const today = todayStr();
  if (s === today) return 'Today';
  const d = new Date(s);
  const diff = Math.round((d - new Date(today)) / (1000 * 60 * 60 * 24));
  if (diff === 1) return 'Tomorrow';
  if (diff === -1) return 'Yesterday';
  if (diff < 0 && diff >= -7) return `${-diff}d ago`;
  if (diff > 0 && diff <= 7) return `in ${diff}d`;
  return s;
}

function Modal({ title, onClose, children }) {
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 12,
        padding: 20, width: 460, maxHeight: '90vh', overflow: 'auto',
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

function TaskForm({ initial, onSubmit, onCancel }) {
  const [f, setF] = useState({
    title: '', description: '', priority: 'normal', status: 'open',
    due_date: '', tags: '', recurrence: 'none', ...(initial || {}),
  });
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(f); }}>
      <div style={{ marginBottom: 10 }}>
        <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Title *</label>
        <input className="field-input" required autoFocus value={f.title} onChange={(e) => set('title', e.target.value)} maxLength={200} />
      </div>
      <div style={{ marginBottom: 10 }}>
        <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Description</label>
        <textarea className="field-input" rows={3} value={f.description} onChange={(e) => set('description', e.target.value)} maxLength={4000} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
        <div>
          <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Priority</label>
          <select className="field-select" value={f.priority} onChange={(e) => set('priority', e.target.value)} style={{ width: '100%' }}>
            {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Status</label>
          <select className="field-select" value={f.status} onChange={(e) => set('status', e.target.value)} style={{ width: '100%' }}>
            {STATUSES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Due date</label>
          <input className="field-input" type="date" value={f.due_date || ''} onChange={(e) => set('due_date', e.target.value)} />
        </div>
      </div>
      <div style={{ marginTop: 10, display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 10 }}>
        <div>
          <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Legacy tags (text)</label>
          <input className="field-input" placeholder="comma-separated" value={f.tags} onChange={(e) => set('tags', e.target.value)} />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>
            <Repeat size={10} style={{ display: 'inline', verticalAlign: 'middle', marginRight: 3 }} />
            Repeats
          </label>
          <select className="field-select" value={f.recurrence || 'none'} onChange={(e) => set('recurrence', e.target.value)} style={{ width: '100%' }}>
            {RECURRENCES.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </div>
      {initial?.id && (
        <div style={{ marginTop: 10 }}>
          <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 4 }}>Tags</label>
          <TagPicker entityType="task" entityId={initial.id} />
        </div>
      )}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary">{initial ? 'Save' : 'Add Task'}</button>
      </div>
    </form>
  );
}

function TaskRow({ task, selected, onToggleSelect, tagChips, onToggle, onEdit, onDelete }) {
  const done = task.status === 'done';
  const overdue = task.due_date && task.due_date < todayStr() && !done && task.status !== 'cancelled';
  const isRecurring = task.recurrence && task.recurrence !== 'none';
  return (
    <div
      className="panel row"
      style={{
        display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
        opacity: done ? 0.6 : 1,
        borderLeft: `3px solid ${PRIORITY_COLORS[task.priority] || 'var(--color-text-dim)'}`,
        background: selected ? 'color-mix(in srgb, var(--color-accent) 6%, var(--color-surface-2))' : undefined,
      }}
    >
      {/* Round checkbox — "Mark done." Always visible. Status, not selection. */}
      <button
        type="button"
        onClick={() => onToggle(task)}
        className={`round-check${done ? ' is-done' : ''}`}
        title={done ? 'Mark as not done' : 'Mark as done'}
        aria-label={done ? 'Mark as not done' : 'Mark as done'}
      >
        {done && <Check size={12} strokeWidth={3} />}
      </button>

      {/* Bulk checkbox — "Select." Hidden until hover or bulk mode. Square. */}
      <span
        className="row-bulk"
        title="Select for bulk action"
        aria-label="Select task for bulk actions"
      >
        <BulkCheckbox checked={selected} onChange={() => onToggleSelect(task.id)} />
      </span>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 13, fontWeight: 500, color: 'var(--color-text)',
          textDecoration: done ? 'line-through' : 'none',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          display: 'flex', alignItems: 'center', gap: 6,
        }}>
          {isRecurring && <Repeat size={11} color="var(--color-accent)" title={`Repeats ${task.recurrence}`} />}
          {task.title}
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 2, fontSize: 10, color: 'var(--color-text-dim)', flexWrap: 'wrap' }}>
          <span style={{ color: PRIORITY_COLORS[task.priority], fontWeight: 600 }}>{task.priority}</span>
          <span style={{ color: STATUS_COLORS[task.status] }}>{task.status.replace('_', ' ')}</span>
          {task.due_date && (
            <span style={{ color: overdue ? 'var(--color-err)' : 'var(--color-text-dim)', display: 'flex', alignItems: 'center', gap: 3 }}>
              <Calendar size={10} /> {isoToDateLabel(task.due_date)}
            </span>
          )}
          {tagChips && tagChips.length > 0 && <TagChips tags={tagChips} size="xs" />}
          {task.tags && <span>· {task.tags}</span>}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <button className="btn-ghost btn-sm" onClick={() => onEdit(task)}>Edit</button>
        <button className="btn-ghost btn-sm" style={{ color: 'var(--color-err)' }} onClick={() => onDelete(task)} title="Delete task" aria-label="Delete task"><Trash2 size={12} /></button>
      </div>
    </div>
  );
}

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [summary, setSummary] = useState(null);
  const [filter, setFilter] = useState('active');
  const [dueWindow, setDueWindow] = useState('');
  const [modal, setModal] = useState(null); // { record: task | null }
  const [msg, setMsg] = useState('');
  const [tagsByTask, setTagsByTask] = useState({});
  const [undoToast, setUndoToast] = useState(null);
  const undoTimerRef = useRef(null);
  // "From notes" modal: { notes, busy, error, extracted, summary, picked, creating }
  // — extracted is the items array from the LLM, picked is a Set of indices
  // the user has chosen to commit. Stays null until the user opens the modal.
  const [notesModal, setNotesModal] = useState(null);

  const selection = useBulkSelection(tasks);

  const reload = useCallback(async () => {
    try {
      const opts = {};
      if (filter && filter !== 'all') opts.status = filter;
      if (dueWindow) opts.due_window = dueWindow;
      const [list, s] = await Promise.all([listTasks(opts), taskSummary(false)]);
      setTasks(list);
      setSummary(s);
      // Fetch tag chips for all visible tasks in one batch
      if (list.length > 0) {
        try {
          const map = await bulkTagsFor('task', list.map(t => t.id));
          setTagsByTask(map);
        } catch { setTagsByTask({}); }
      } else {
        setTagsByTask({});
      }
    } catch (e) { setMsg(`Failed to load: ${e.message}`); }
  }, [filter, dueWindow]);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    const h = () => reload();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reload]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const handleToggle = async (t) => {
    try {
      await updateTask(t.id, { status: t.status === 'done' ? 'open' : 'done' });
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleSubmit = async (data) => {
    try {
      if (modal.record) await updateTask(modal.record.id, data);
      else await createTask(data);
      setModal(null);
      flash('Saved');
      reload();
    } catch (e) { alert(`Failed: ${e.message}`); }
  };

  const handleDelete = async (t) => {
    if (!confirm(`Delete "${t.title}"?`)) return;
    try {
      await deleteTask(t.id);
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const doBulkDelete = async () => {
    const ids = Array.from(selection.selected);
    if (ids.length === 0) return;
    if (!confirm(`Delete ${ids.length} task${ids.length === 1 ? '' : 's'}?`)) return;
    // Snapshot for undo
    const snapshot = tasks.filter(t => ids.includes(t.id));
    try {
      await bulkDeleteTasks(ids);
      selection.clear();
      showUndo(
        `${ids.length} task${ids.length === 1 ? '' : 's'} deleted`,
        async () => {
          // Undo = re-create each snapshotted task from its fields
          for (const t of snapshot) {
            try {
              await createTask({
                title: t.title, description: t.description, status: t.status,
                priority: t.priority, due_date: t.due_date, tags: t.tags,
                recurrence: t.recurrence || 'none',
              });
            } catch {}
          }
          reload();
        },
      );
      reload();
    } catch (e) { flash(`Bulk delete failed: ${e.message}`); }
  };

  const doBulkStatus = async (status) => {
    const ids = Array.from(selection.selected);
    if (ids.length === 0) return;
    try {
      await bulkTaskStatus(ids, status);
      selection.clear();
      flash(`Marked ${ids.length} task${ids.length === 1 ? '' : 's'} as ${status}`);
      reload();
    } catch (e) { flash(`Bulk update failed: ${e.message}`); }
  };

  const showUndo = (message, onUndo) => {
    if (undoTimerRef.current) clearTimeout(undoTimerRef.current);
    setUndoToast({ message, onUndo });
    undoTimerRef.current = setTimeout(() => setUndoToast(null), 5000);
  };

  // ── Meeting notes → action items ──────────────────────────────────────
  const runNotesExtract = async () => {
    if (!notesModal || notesModal.notes.trim().length < 20) {
      setNotesModal((m) => ({ ...(m || {}), error: 'Paste at least a couple sentences of notes.' }));
      return;
    }
    setNotesModal((m) => ({ ...m, busy: true, error: '', extracted: null }));
    try {
      const r = await extractFromNotes(notesModal.notes);
      // Pre-pick everything — user unchecks items they don't want.
      const picked = new Set((r.items || []).map((_, i) => i));
      setNotesModal((m) => ({
        ...m, busy: false, error: '',
        extracted: r.items || [], summary: r.summary || '', picked,
      }));
    } catch (e) {
      setNotesModal((m) => ({ ...m, busy: false, error: e.message || 'Extraction failed.', extracted: null }));
    }
  };

  const togglePickedItem = (i) => {
    setNotesModal((m) => {
      if (!m) return m;
      const next = new Set(m.picked);
      if (next.has(i)) next.delete(i); else next.add(i);
      return { ...m, picked: next };
    });
  };

  const editExtractedItem = (i, patch) => {
    setNotesModal((m) => {
      if (!m || !m.extracted) return m;
      const next = m.extracted.map((it, idx) => idx === i ? { ...it, ...patch } : it);
      return { ...m, extracted: next };
    });
  };

  const commitPickedTasks = async () => {
    if (!notesModal?.extracted) return;
    const chosen = notesModal.extracted.filter((_, i) => notesModal.picked.has(i));
    if (chosen.length === 0) {
      setNotesModal((m) => ({ ...m, error: 'Pick at least one item to add.' }));
      return;
    }
    setNotesModal((m) => ({ ...m, creating: true, error: '' }));
    let created = 0;
    let failed = 0;
    for (const it of chosen) {
      try {
        await createTask({
          title: it.title,
          description: [it.description, it.owner_hint && `Owner mentioned: ${it.owner_hint}`, it.due_hint && `Timing mentioned: ${it.due_hint}`].filter(Boolean).join('\n\n'),
          priority: it.priority || 'normal',
        });
        created += 1;
      } catch {
        failed += 1;
      }
    }
    setNotesModal(null);
    flash(`Added ${created} task${created === 1 ? '' : 's'}${failed ? ` (${failed} failed)` : ''}.`);
    reload();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Tasks</h1>
          <p>Your to-dos and priorities for this business</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            className="btn-ghost"
            onClick={() => setNotesModal({ notes: '', busy: false, error: '', extracted: null, summary: '', picked: new Set(), creating: false })}
            title="Paste meeting notes — AI extracts action items"
          >
            <Sparkles size={13} /> From notes
          </button>
          <button className="btn-primary" onClick={() => setModal({ record: null })}><Plus size={13} /> Add task</button>
        </div>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      <div style={{ padding: '8px 24px 0' }}>
        <FlowBanner currentStep="task" />
      </div>

      {/* Summary cards */}
      {summary && (
        <div style={{ padding: '0 24px', display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10, marginBottom: 8 }}>
          {[
            { label: 'Open total', value: summary.open_total, icon: Briefcase, color: 'var(--color-info)' },
            { label: 'Overdue', value: summary.overdue, icon: AlertTriangle, color: 'var(--color-err)' },
            { label: 'Today', value: summary.today, icon: Calendar, color: 'var(--color-warn)' },
            { label: 'Next 7 days', value: summary.upcoming, icon: Clock, color: '#a78bfa' },
            { label: 'Done today', value: summary.done_today, icon: CheckSquare, color: 'var(--color-ok)' },
          ].map(({ label, value, icon: Icon, color }, i) => (
            <div key={i} className="panel" style={{ padding: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: `${color}22`, color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={16} />
              </div>
              <div>
                <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{label}</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text)' }}>{value}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 6, padding: '0 24px 8px', borderBottom: '1px solid var(--color-surface-2)', flexWrap: 'wrap' }}>
        {[['active', 'Active'], ['open', 'Open'], ['in_progress', 'In progress'], ['done', 'Done'], ['all', 'All']].map(([k, lbl]) => (
          <button key={k} onClick={() => setFilter(k)} className={filter === k ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 11 }}>{lbl}</button>
        ))}
        <div style={{ width: 1, background: 'var(--color-surface-2)', margin: '0 4px' }} />
        {[['', 'Any due'], ['overdue', 'Overdue'], ['today', 'Today'], ['this_week', 'This week']].map(([k, lbl]) => (
          <button key={k || 'any'} onClick={() => setDueWindow(k)} className={dueWindow === k ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 11 }}>{lbl}</button>
        ))}
      </div>

      {/* Select-all strip — only appears when bulk mode is active (something
          already selected). Keeps the chrome clean for first-time users who
          don't know about bulk yet. */}
      {tasks.length > 0 && selection.any && (
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '8px 24px', fontSize: 12, color: 'var(--color-text-muted)',
          background: 'var(--color-surface-1)',
          borderTop: '1px solid var(--color-border)',
          borderBottom: '1px solid var(--color-border)',
        }}>
          <BulkCheckbox
            checked={selection.all}
            indeterminate={selection.some}
            onChange={() => selection.toggleAll()}
            title="Select all visible"
          />
          <span>
            {selection.count === tasks.length
              ? `All ${tasks.length} selected`
              : `${selection.count} of ${tasks.length} selected`}
          </span>
          <button
            className="btn-ghost btn-sm"
            style={{ marginLeft: 'auto' }}
            onClick={() => selection.clear()}
          >
            Clear
          </button>
        </div>
      )}

      <div
        data-bulk-active={selection.any || undefined}
        style={{ flex: 1, overflow: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 8 }}
      >
        {tasks.length === 0 ? (
          <EmptyState
            icon={CheckSquare}
            title="No tasks here"
            description="Create a task directly, or ask the AI to generate tasks from a meeting note or a document."
            primaryLabel="Add task"
            onPrimary={() => setModal({ record: null })}
            secondaryLabel="Ask the AI"
            onSecondary={() => window.location.assign('/chat')}
          />
        ) : (
          <>
            {tasks.map((t) => (
              <TaskRow key={t.id} task={t}
                selected={selection.isSelected(t.id)}
                onToggleSelect={selection.toggle}
                tagChips={tagsByTask[t.id] || []}
                onToggle={handleToggle}
                onEdit={(t) => setModal({ record: t })}
                onDelete={handleDelete} />
            ))}

            <BulkActionBar count={selection.count} onCancel={selection.clear}>
              <button onClick={() => doBulkStatus('done')} className="btn-ghost" style={{ fontSize: 11 }}>
                Mark done
              </button>
              <button onClick={() => doBulkStatus('open')} className="btn-ghost" style={{ fontSize: 11 }}>
                Reopen
              </button>
              <button onClick={doBulkDelete} className="btn-ghost" style={{ fontSize: 11, color: 'var(--color-err)' }}>
                <Trash2 size={11} /> Delete
              </button>
            </BulkActionBar>
          </>
        )}
      </div>

      {undoToast && (
        <UndoToast
          message={undoToast.message}
          onUndo={() => { undoToast.onUndo?.(); setUndoToast(null); }}
          onClose={() => setUndoToast(null)}
        />
      )}

      {modal && (
        <Modal title={modal.record ? 'Edit task' : 'New task'} onClose={() => setModal(null)}>
          {modal.record?.id && (
            <div style={{ marginBottom: 12 }}>
              <SuggestionPanel entityType="task" entityId={modal.record.id} compact />
            </div>
          )}
          <TaskForm initial={modal.record} onSubmit={handleSubmit} onCancel={() => setModal(null)} />
        </Modal>
      )}

      {notesModal && (
        <FromNotesModal
          state={notesModal}
          onChangeNotes={(t) => setNotesModal((m) => ({ ...m, notes: t, error: '' }))}
          onRun={runNotesExtract}
          onTogglePicked={togglePickedItem}
          onEditItem={editExtractedItem}
          onCommit={commitPickedTasks}
          onClose={() => setNotesModal(null)}
        />
      )}
    </div>
  );
}


// ── From-notes modal ────────────────────────────────────────────────────────
// Two-step UX in a single modal:
//   1. Paste transcript / notes → click Extract.
//   2. Review/edit the AI's action items, uncheck any junk, click "Add picked".
// We pre-check everything on first extract so the default (one click → all
// items added) is fast for the common case.
function FromNotesModal({ state, onChangeNotes, onRun, onTogglePicked, onEditItem, onCommit, onClose }) {
  const items = state.extracted || [];
  const hasItems = items.length > 0;
  const pickedCount = state.picked ? state.picked.size : 0;

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
              Extract action items from notes
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
              Paste a meeting transcript or rough notes — runs locally on Ollama
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
          {state.error && (
            <div style={{
              padding: '8px 10px',
              background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-err) 28%, transparent)',
              borderRadius: 'var(--r-sm)',
              fontSize: 12, color: 'var(--color-err)',
              display: 'flex', alignItems: 'flex-start', gap: 6,
            }}>
              <AlertTriangle size={13} style={{ marginTop: 1, flexShrink: 0 }} />
              <span>{state.error}</span>
            </div>
          )}

          <textarea
            className="field-input"
            rows={hasItems ? 4 : 12}
            value={state.notes}
            onChange={(e) => onChangeNotes(e.target.value)}
            placeholder="Paste meeting notes or transcript here. Works for sales calls, standups, client check-ins, vendor meetings — anything with concrete next steps."
            style={{ fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 12, lineHeight: 1.55 }}
            disabled={state.busy || state.creating}
          />

          {state.summary && (
            <div style={{
              padding: '8px 10px',
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--r-sm)',
              fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.55,
            }}>
              <span style={{ fontWeight: 600, color: 'var(--color-text)' }}>Recap:</span> {state.summary}
            </div>
          )}

          {hasItems && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ fontSize: 11, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600 }}>
                {items.length} action item{items.length === 1 ? '' : 's'} · uncheck what doesn't fit
              </div>
              {items.map((it, i) => {
                const isPicked = state.picked.has(i);
                const PRI_TONE = { high: 'var(--color-err)', normal: 'var(--color-info)', low: 'var(--color-text-dim)' };
                const tone = PRI_TONE[it.priority] || PRI_TONE.normal;
                return (
                  <div
                    key={i}
                    style={{
                      padding: 10,
                      background: 'var(--color-surface-1)',
                      border: `1px solid ${isPicked ? 'color-mix(in srgb, var(--color-accent) 30%, var(--color-border))' : 'var(--color-border)'}`,
                      borderRadius: 'var(--r-sm)',
                      display: 'flex', gap: 10, alignItems: 'flex-start',
                      opacity: isPicked ? 1 : 0.55,
                    }}
                  >
                    <button
                      onClick={() => onTogglePicked(i)}
                      style={{
                        marginTop: 2,
                        background: 'transparent', border: 'none', cursor: 'pointer',
                        color: isPicked ? 'var(--color-accent)' : 'var(--color-text-dim)',
                        flexShrink: 0,
                      }}
                      aria-label={isPicked ? 'Uncheck' : 'Check'}
                    >
                      {isPicked ? <CheckSquare size={16} /> : <Square size={16} />}
                    </button>
                    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <input
                        className="field-input"
                        value={it.title}
                        onChange={(e) => onEditItem(i, { title: e.target.value })}
                        style={{ fontWeight: 500 }}
                        maxLength={200}
                      />
                      <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
                        <select
                          value={it.priority}
                          onChange={(e) => onEditItem(i, { priority: e.target.value })}
                          className="field-select"
                          style={{ fontSize: 11, padding: '2px 6px', color: tone, fontWeight: 600, textTransform: 'capitalize' }}
                        >
                          <option value="low">low</option>
                          <option value="normal">normal</option>
                          <option value="high">high</option>
                        </select>
                        {it.owner_hint && (
                          <span style={{ fontSize: 10.5, color: 'var(--color-text-dim)' }}>
                            owner: <strong style={{ color: 'var(--color-text-muted)' }}>{it.owner_hint}</strong>
                          </span>
                        )}
                        {it.due_hint && (
                          <span style={{ fontSize: 10.5, color: 'var(--color-text-dim)' }}>
                            due: <strong style={{ color: 'var(--color-text-muted)' }}>{it.due_hint}</strong>
                          </span>
                        )}
                      </div>
                      {it.description && (
                        <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
                          {it.description}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {state.extracted !== null && items.length === 0 && (
            <div style={{
              padding: 14, textAlign: 'center',
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--r-sm)',
              fontSize: 12.5, color: 'var(--color-text-muted)',
            }}>
              No clear action items in those notes. Try fuller text — or maybe this meeting really was just a status update.
            </div>
          )}
        </div>

        <div style={{
          padding: '12px 18px', borderTop: '1px solid var(--color-border)',
          display: 'flex', gap: 8, justifyContent: 'flex-end', flexWrap: 'wrap',
        }}>
          <button className="btn-ghost" onClick={onClose} disabled={state.creating}>Close</button>
          {hasItems && (
            <button className="btn-ghost" onClick={onRun} disabled={state.busy || state.creating} title="Run extraction again on the same notes">
              <RefreshCw size={11} /> Re-extract
            </button>
          )}
          {!hasItems ? (
            <button className="btn-primary" onClick={onRun} disabled={state.busy}>
              {state.busy
                ? <><Loader2 size={12} className="animate-spin" /> Extracting…</>
                : <><Sparkles size={12} /> Extract action items</>}
            </button>
          ) : (
            <button className="btn-primary" onClick={onCommit} disabled={state.creating || pickedCount === 0}>
              {state.creating
                ? <><Loader2 size={12} className="animate-spin" /> Adding…</>
                : <><Plus size={12} /> Add {pickedCount} task{pickedCount === 1 ? '' : 's'}</>}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
