import { useState, useEffect, useCallback } from 'react';
import { ShieldCheck, Check, X, AlertTriangle, Clock, ChevronDown, ChevronRight } from 'lucide-react';
import { listApprovals, approveAction, rejectAction } from '../services/agent';

const STATUS_COLORS = {
  pending: '#f59e0b', approved: '#60a5fa', rejected: '#6b7280',
  executed: '#22c55e', failed: '#ef4444', expired: '#475569',
};

function formatWhen(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch { return iso.substring(0, 16); }
}

function ActionRow({ action, onApprove, onReject, expanded, onToggle }) {
  const color = STATUS_COLORS[action.status] || '#64748b';
  const isPending = action.status === 'pending';
  return (
    <div className="panel" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{ padding: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
        <button onClick={onToggle} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 2 }}>
          {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
            <span style={{ fontSize: 13, fontWeight: 500, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {action.summary || action.tool_name}
            </span>
            <span style={{
              fontSize: 9, padding: '2px 8px', borderRadius: 10, fontWeight: 600,
              background: `${color}22`, color, textTransform: 'uppercase',
            }}>
              {action.status}
            </span>
          </div>
          <div style={{ fontSize: 10, color: '#64748b' }}>
            tool: <code style={{ color: '#94a3b8' }}>{action.tool_name}</code> · requested {formatWhen(action.created_at)}
            {action.decided_at && ` · decided ${formatWhen(action.decided_at)}`}
          </div>
        </div>
        {isPending && (
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="btn-ghost" style={{ color: '#f87171' }} onClick={() => onReject(action)}>
              <X size={12} /> Reject
            </button>
            <button className="btn-primary" onClick={() => onApprove(action)}>
              <Check size={12} /> Approve
            </button>
          </div>
        )}
      </div>
      {expanded && (
        <div style={{ padding: '10px 16px 14px', borderTop: '1px solid #1e293b', background: '#0a0f1c' }}>
          <div style={{ fontSize: 10, color: '#64748b', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Arguments</div>
          <pre style={{ fontSize: 10, color: '#cbd5e1', margin: 0, overflow: 'auto', maxHeight: 260, padding: 8, background: '#060a14', borderRadius: 6 }}>
{JSON.stringify(action.args || {}, null, 2)}
          </pre>
          {action.error && (
            <div style={{ marginTop: 8, padding: 8, background: '#ef444415', borderRadius: 6, border: '1px solid #ef444430' }}>
              <div style={{ fontSize: 10, color: '#f87171', fontWeight: 600 }}>Error</div>
              <div style={{ fontSize: 11, color: '#fca5a5', marginTop: 4 }}>{action.error}</div>
            </div>
          )}
          {action.result && (
            <>
              <div style={{ fontSize: 10, color: '#64748b', margin: '10px 0 4px', textTransform: 'uppercase', letterSpacing: 1 }}>Result</div>
              <pre style={{ fontSize: 10, color: '#86efac', margin: 0, overflow: 'auto', maxHeight: 260, padding: 8, background: '#060a14', borderRadius: 6 }}>
{JSON.stringify(action.result, null, 2)}
              </pre>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function Approvals() {
  const [actions, setActions] = useState([]);
  const [pending, setPending] = useState(0);
  const [filter, setFilter] = useState('pending');
  const [expanded, setExpanded] = useState({});
  const [msg, setMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    try {
      const data = await listApprovals(filter === 'all' ? '' : filter);
      setActions(data.actions || []);
      setPending(data.pending_count || 0);
    } catch (e) { setMsg(`Failed: ${e.message}`); }
    setLoading(false);
  }, [filter]);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    const h = () => reload();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reload]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const handleApprove = async (a) => {
    if (!confirm(`Approve and execute?\n\n${a.summary}`)) return;
    try {
      await approveAction(a.id);
      flash('Approved and executed.');
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  const handleReject = async (a) => {
    const reason = prompt('Why are you rejecting? (optional)', '');
    if (reason === null) return;
    try {
      await rejectAction(a.id, reason);
      flash('Rejected.');
      reload();
    } catch (e) { flash(`Failed: ${e.message}`); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Approvals</h1>
          <p>Review and approve agent actions before they run</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ShieldCheck size={16} color="#22c55e" />
          <span style={{ fontSize: 13, color: '#e2e8f0' }}>{pending} pending</span>
        </div>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: '#60a5fa' }}>{msg}</div>}

      <div style={{ display: 'flex', gap: 6, padding: '0 24px 8px', borderBottom: '1px solid #1e293b' }}>
        {[
          ['pending', 'Pending', AlertTriangle],
          ['executed', 'Executed', Check],
          ['rejected', 'Rejected', X],
          ['expired', 'Expired', Clock],
          ['all', 'All', null],
        ].map(([k, lbl, Icon]) => (
          <button key={k} onClick={() => setFilter(k)} className={filter === k ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 11 }}>
            {Icon && <Icon size={12} />} {lbl}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {loading && actions.length === 0 ? (
          <p style={{ color: '#64748b', fontSize: 12, textAlign: 'center' }}>Loading...</p>
        ) : actions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48, color: '#64748b' }}>
            <ShieldCheck size={36} style={{ opacity: 0.3, marginBottom: 12 }} />
            <p style={{ fontSize: 13 }}>
              {filter === 'pending' ? 'Nothing is waiting for your approval. You\'re all clear.' : 'Nothing matches this filter.'}
            </p>
          </div>
        ) : (
          actions.map((a) => (
            <ActionRow
              key={a.id}
              action={a}
              expanded={!!expanded[a.id]}
              onToggle={() => setExpanded((p) => ({ ...p, [a.id]: !p[a.id] }))}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          ))
        )}
      </div>
    </div>
  );
}
