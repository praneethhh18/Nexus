import { useState, useEffect, useCallback } from 'react';
import { ShieldCheck, Check, X, AlertTriangle, Clock, ChevronDown, ChevronRight } from 'lucide-react';
import { listApprovals, approveAction, rejectAction } from '../services/agent';
import { listPersonas } from '../services/agents';

// Maps the tool_name on an approval row to the agent_key of the persona that created it.
// For tools invoked from user chat (no owning agent), the value is null and no badge renders.
const TOOL_TO_AGENT = {
  send_invoice_email:     'invoice_reminder',   // Kira
  send_triage_reply:      'email_triage',       // Iris
  draft_reply:            'email_triage',       // Iris
  classify_and_reply:     'email_triage',       // Iris
};

const STATUS_COLORS = {
  pending: 'var(--color-warn)', approved: 'var(--color-info)', rejected: 'var(--color-text-dim)',
  executed: 'var(--color-ok)', failed: 'var(--color-err)', expired: 'var(--color-text-dim)',
};

function formatWhen(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso);
    return d.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch { return iso.substring(0, 16); }
}

function ActionRow({ action, onApprove, onReject, expanded, onToggle, personaByKey }) {
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
              background: `${color}22`, color, textTransform: 'uppercase',
            }}>
              {action.status}
            </span>
            {persona && (
              <span
                title={`Drafted by ${persona.name} — ${persona.description}`}
                style={{
                  fontSize: 9, padding: '2px 8px', borderRadius: 'var(--r-pill)',
                  fontWeight: 600, letterSpacing: 0.3,
                  color: 'var(--color-accent)',
                  background: 'var(--color-accent-soft)',
                  border: '1px solid color-mix(in srgb, var(--color-accent) 22%, transparent)',
                  display: 'inline-flex', alignItems: 'center', gap: 4,
                }}
              >
                <span style={{ fontSize: 10 }}>{persona.emoji}</span>
                by {persona.name} · {persona.role_tag}
              </span>
            )}
          </div>
          <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>
            tool: <code style={{ color: 'var(--color-text-muted)' }}>{action.tool_name}</code> · requested {formatWhen(action.created_at)}
            {action.decided_at && ` · decided ${formatWhen(action.decided_at)}`}
          </div>
        </div>
        {isPending && (
          <div style={{ display: 'flex', gap: 6 }}>
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
        <div style={{ padding: '10px 16px 14px', borderTop: '1px solid var(--color-surface-2)', background: 'var(--color-bg)' }}>
          <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginBottom: 4, textTransform: 'uppercase', letterSpacing: 1 }}>Arguments</div>
          <pre style={{ fontSize: 10, color: 'var(--color-text)', margin: 0, overflow: 'auto', maxHeight: 260, padding: 8, background: 'var(--color-bg)', borderRadius: 6 }}>
{JSON.stringify(action.args || {}, null, 2)}
          </pre>
          {action.error && (
            <div style={{ marginTop: 8, padding: 8, background: 'color-mix(in srgb, var(--color-err) 8%, transparent)', borderRadius: 6, border: '1px solid color-mix(in srgb, var(--color-err) 19%, transparent)' }}>
              <div style={{ fontSize: 10, color: 'var(--color-err)', fontWeight: 600 }}>Error</div>
              <div style={{ fontSize: 11, color: 'var(--color-err)', marginTop: 4 }}>{action.error}</div>
            </div>
          )}
          {action.result && (
            <>
              <div style={{ fontSize: 10, color: 'var(--color-text-dim)', margin: '10px 0 4px', textTransform: 'uppercase', letterSpacing: 1 }}>Result</div>
              <pre style={{ fontSize: 10, color: 'var(--color-ok)', margin: 0, overflow: 'auto', maxHeight: 260, padding: 8, background: 'var(--color-bg)', borderRadius: 6 }}>
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
  const [personaByKey, setPersonaByKey] = useState({});

  useEffect(() => {
    listPersonas().then(list => {
      const map = {};
      for (const p of list) map[p.agent_key] = p;
      setPersonaByKey(map);
    }).catch(() => {});
  }, []);

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
          <ShieldCheck size={16} color="var(--color-ok)" />
          <span style={{ fontSize: 13, color: 'var(--color-text)' }}>{pending} pending</span>
        </div>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      <div style={{ display: 'flex', gap: 6, padding: '0 24px 8px', borderBottom: '1px solid var(--color-surface-2)' }}>
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
          <p style={{ color: 'var(--color-text-dim)', fontSize: 12, textAlign: 'center' }}>Loading...</p>
        ) : actions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 48, color: 'var(--color-text-dim)' }}>
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
              personaByKey={personaByKey}
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
