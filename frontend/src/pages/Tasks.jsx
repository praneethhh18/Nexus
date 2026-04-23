import { useState, useEffect, useCallback } from 'react';
import { CheckSquare, Square, Plus, Calendar, AlertTriangle, Clock, Trash2, X, Briefcase } from 'lucide-react';
import { listTasks, createTask, updateTask, deleteTask, taskSummary, STATUSES, PRIORITIES } from '../services/tasks';

const PRIORITY_COLORS = { urgent: '#ef4444', high: '#f59e0b', normal: '#60a5fa', low: '#64748b' };
const STATUS_COLORS = { open: '#64748b', in_progress: '#f59e0b', done: '#22c55e', cancelled: '#475569' };

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
        background: '#0c1222', border: '1px solid #1e293b', borderRadius: 12,
        padding: 20, width: 460, maxHeight: '90vh', overflow: 'auto',
        boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <h3 style={{ fontSize: 15, fontWeight: 600, color: '#e2e8f0', margin: 0 }}>{title}</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}><X size={16} /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

function TaskForm({ initial, onSubmit, onCancel }) {
  const [f, setF] = useState({
    title: '', description: '', priority: 'normal', status: 'open',
    due_date: '', tags: '', ...(initial || {}),
  });
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  return (
    <form onSubmit={(e) => { e.preventDefault(); onSubmit(f); }}>
      <div style={{ marginBottom: 10 }}>
        <label style={{ display: 'block', fontSize: 10, color: '#94a3b8', marginBottom: 4 }}>Title *</label>
        <input className="field-input" required autoFocus value={f.title} onChange={(e) => set('title', e.target.value)} maxLength={200} />
      </div>
      <div style={{ marginBottom: 10 }}>
        <label style={{ display: 'block', fontSize: 10, color: '#94a3b8', marginBottom: 4 }}>Description</label>
        <textarea className="field-input" rows={3} value={f.description} onChange={(e) => set('description', e.target.value)} maxLength={4000} />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
        <div>
          <label style={{ display: 'block', fontSize: 10, color: '#94a3b8', marginBottom: 4 }}>Priority</label>
          <select className="field-select" value={f.priority} onChange={(e) => set('priority', e.target.value)} style={{ width: '100%' }}>
            {PRIORITIES.map((p) => <option key={p}>{p}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 10, color: '#94a3b8', marginBottom: 4 }}>Status</label>
          <select className="field-select" value={f.status} onChange={(e) => set('status', e.target.value)} style={{ width: '100%' }}>
            {STATUSES.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: 10, color: '#94a3b8', marginBottom: 4 }}>Due date</label>
          <input className="field-input" type="date" value={f.due_date || ''} onChange={(e) => set('due_date', e.target.value)} />
        </div>
      </div>
      <div style={{ marginTop: 10 }}>
        <label style={{ display: 'block', fontSize: 10, color: '#94a3b8', marginBottom: 4 }}>Tags</label>
        <input className="field-input" placeholder="comma-separated" value={f.tags} onChange={(e) => set('tags', e.target.value)} />
      </div>
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 16 }}>
        <button type="button" className="btn-ghost" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn-primary">{initial ? 'Save' : 'Add Task'}</button>
      </div>
    </form>
  );
}

function TaskRow({ task, onToggle, onEdit, onDelete }) {
  const done = task.status === 'done';
  const overdue = task.due_date && task.due_date < todayStr() && !done && task.status !== 'cancelled';
  return (
    <div className="panel" style={{
      display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
      opacity: done ? 0.55 : 1,
      borderLeft: `3px solid ${PRIORITY_COLORS[task.priority] || '#475569'}`,
    }}>
      <button onClick={() => onToggle(task)} style={{ background: 'none', border: 'none', color: done ? '#22c55e' : '#64748b', cursor: 'pointer' }}>
        {done ? <CheckSquare size={18} /> : <Square size={18} />}
      </button>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{
          fontSize: 13, fontWeight: 500, color: '#e2e8f0',
          textDecoration: done ? 'line-through' : 'none',
          overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        }}>
          {task.title}
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginTop: 2, fontSize: 10, color: '#64748b' }}>
          <span style={{ color: PRIORITY_COLORS[task.priority], fontWeight: 600 }}>{task.priority}</span>
          <span style={{ color: STATUS_COLORS[task.status] }}>{task.status.replace('_', ' ')}</span>
          {task.due_date && (
            <span style={{ color: overdue ? '#ef4444' : '#64748b', display: 'flex', alignItems: 'center', gap: 3 }}>
              <Calendar size={10} /> {isoToDateLabel(task.due_date)}
            </span>
          )}
          {task.tags && <span>· {task.tags}</span>}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 4 }}>
        <button className="btn-ghost" style={{ padding: 4 }} onClick={() => onEdit(task)}>Edit</button>
        <button className="btn-ghost" style={{ padding: 4, color: '#f87171' }} onClick={() => onDelete(task)}><Trash2 size={12} /></button>
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

  const reload = useCallback(async () => {
    try {
      const opts = {};
      if (filter && filter !== 'all') opts.status = filter;
      if (dueWindow) opts.due_window = dueWindow;
      const [list, s] = await Promise.all([listTasks(opts), taskSummary(false)]);
      setTasks(list);
      setSummary(s);
    } catch (e) { setMsg(`Failed to load: ${e.message}`); }
  }, [filter, dueWindow]);

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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Tasks</h1>
          <p>Your to-dos and priorities for this business</p>
        </div>
        <button className="btn-primary" onClick={() => setModal({ record: null })}><Plus size={13} /> Add task</button>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: '#60a5fa' }}>{msg}</div>}

      {/* Summary cards */}
      {summary && (
        <div style={{ padding: '0 24px', display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 10, marginBottom: 8 }}>
          {[
            { label: 'Open total', value: summary.open_total, icon: Briefcase, color: '#60a5fa' },
            { label: 'Overdue', value: summary.overdue, icon: AlertTriangle, color: '#ef4444' },
            { label: 'Today', value: summary.today, icon: Calendar, color: '#f59e0b' },
            { label: 'Next 7 days', value: summary.upcoming, icon: Clock, color: '#a78bfa' },
            { label: 'Done today', value: summary.done_today, icon: CheckSquare, color: '#22c55e' },
          ].map(({ label, value, icon: Icon, color }, i) => (
            <div key={i} className="panel" style={{ padding: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ width: 32, height: 32, borderRadius: 8, background: `${color}22`, color, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={16} />
              </div>
              <div>
                <div style={{ fontSize: 10, color: '#64748b' }}>{label}</div>
                <div style={{ fontSize: 16, fontWeight: 600, color: '#e2e8f0' }}>{value}</div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 6, padding: '0 24px 8px', borderBottom: '1px solid #1e293b', flexWrap: 'wrap' }}>
        {[['active', 'Active'], ['open', 'Open'], ['in_progress', 'In progress'], ['done', 'Done'], ['all', 'All']].map(([k, lbl]) => (
          <button key={k} onClick={() => setFilter(k)} className={filter === k ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 11 }}>{lbl}</button>
        ))}
        <div style={{ width: 1, background: '#1e293b', margin: '0 4px' }} />
        {[['', 'Any due'], ['overdue', 'Overdue'], ['today', 'Today'], ['this_week', 'This week']].map(([k, lbl]) => (
          <button key={k || 'any'} onClick={() => setDueWindow(k)} className={dueWindow === k ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 11 }}>{lbl}</button>
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {tasks.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48, color: '#64748b' }}>
            <CheckSquare size={36} style={{ opacity: 0.3, marginBottom: 12 }} />
            <p style={{ fontSize: 13 }}>No tasks match this filter.</p>
          </div>
        ) : (
          tasks.map((t) => (
            <TaskRow key={t.id} task={t}
              onToggle={handleToggle}
              onEdit={(t) => setModal({ record: t })}
              onDelete={handleDelete} />
          ))
        )}
      </div>

      {modal && (
        <Modal title={modal.record ? 'Edit task' : 'New task'} onClose={() => setModal(null)}>
          <TaskForm initial={modal.record} onSubmit={handleSubmit} onCancel={() => setModal(null)} />
        </Modal>
      )}
    </div>
  );
}
