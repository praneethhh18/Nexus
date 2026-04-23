import { useState, useEffect, useCallback } from 'react';
import { Users, Mail, Plus, Trash2, Clock, Check, X, UserPlus, Activity, Link2, Copy } from 'lucide-react';
import { listInvites, createInvite, revokeInvite, activityFeed } from '../services/team';
import { getBusiness } from '../services/api';
import { getCurrentBusiness } from '../services/auth';

const ROLE_OPTIONS = ['member', 'admin', 'viewer'];

function formatWhen(iso) {
  if (!iso) return '';
  try {
    return new Date(iso).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch { return iso.substring(0, 16); }
}

function Modal({ title, onClose, children }) {
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div onClick={(e) => e.stopPropagation()} style={{
        background: '#0c1222', border: '1px solid #1e293b', borderRadius: 12,
        padding: 20, width: 440, boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
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

export default function Team() {
  const [bizDetail, setBizDetail] = useState(null);
  const [invites, setInvites] = useState([]);
  const [activity, setActivity] = useState([]);
  const [tab, setTab] = useState('members');
  const [showInvite, setShowInvite] = useState(false);
  const [newEmail, setNewEmail] = useState('');
  const [newRole, setNewRole] = useState('member');
  const [msg, setMsg] = useState('');
  const current = getCurrentBusiness();

  const reload = useCallback(async () => {
    if (!current) return;
    try {
      const [b, inv, act] = await Promise.all([
        getBusiness(current.id),
        listInvites(true),
        activityFeed(60),
      ]);
      setBizDetail(b);
      setInvites(inv);
      setActivity(act);
    } catch (e) { setMsg(`Failed: ${e.message}`); }
  }, [current?.id]);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    const h = () => reload();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reload]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  const myRole = bizDetail?.my_role;
  const canManage = myRole === 'owner' || myRole === 'admin';

  const handleInvite = async (e) => {
    e.preventDefault();
    try {
      const inv = await createInvite(newEmail, newRole);
      setShowInvite(false);
      setNewEmail(''); setNewRole('member');
      if (inv.link) {
        try { await navigator.clipboard.writeText(inv.link); } catch {}
        flash('Invite sent. Link copied to clipboard.');
      } else {
        flash('Invite sent.');
      }
      reload();
    } catch (err) { alert(`Failed: ${err.message}`); }
  };

  const members = bizDetail?.members || [];
  const pendingInvites = invites.filter(i => !i.accepted_at && !i.revoked_at);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Team</h1>
          <p>Members, invites, and recent activity for <strong style={{ color: '#e2e8f0' }}>{current?.name}</strong></p>
        </div>
        {canManage && tab !== 'activity' && (
          <button className="btn-primary" onClick={() => setShowInvite(true)}><UserPlus size={13} /> Invite</button>
        )}
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: '#60a5fa' }}>{msg}</div>}

      <div style={{ display: 'flex', gap: 6, padding: '0 24px 8px', borderBottom: '1px solid #1e293b' }}>
        {[
          ['members', `Members (${members.length})`, Users],
          ['invites', `Invites (${pendingInvites.length})`, Mail],
          ['activity', 'Activity', Activity],
        ].map(([k, lbl, Icon]) => (
          <button key={k} onClick={() => setTab(k)} className={tab === k ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 11 }}>
            <Icon size={12} /> {lbl}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
        {tab === 'members' && (
          <div className="table-panel">
            <table className="data-table">
              <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Joined</th></tr></thead>
              <tbody>
                {members.map(m => (
                  <tr key={m.user_id}>
                    <td style={{ fontWeight: 500 }}>{m.name || '—'}</td>
                    <td>{m.email}</td>
                    <td>
                      <span style={{
                        fontSize: 9, fontWeight: 700, textTransform: 'uppercase',
                        padding: '2px 8px', borderRadius: 10,
                        background: m.role === 'owner' ? '#f59e0b22' : m.role === 'admin' ? '#3b82f622' : '#33415522',
                        color: m.role === 'owner' ? '#fbbf24' : m.role === 'admin' ? '#60a5fa' : '#94a3b8',
                      }}>{m.role}</span>
                    </td>
                    <td>{formatWhen(m.joined_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {tab === 'invites' && (
          invites.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 48, color: '#64748b' }}>
              <Mail size={36} style={{ opacity: 0.3, marginBottom: 12 }} />
              <p style={{ fontSize: 13 }}>No invites yet. Click "Invite" to add a teammate.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {invites.map(inv => {
                const status = inv.accepted_at ? 'accepted' : inv.revoked_at ? 'revoked' : 'pending';
                const color = { pending: '#f59e0b', accepted: '#22c55e', revoked: '#64748b' }[status];
                return (
                  <div key={inv.token} className="panel" style={{ padding: 12, display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Mail size={14} style={{ color: '#64748b' }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: '#e2e8f0' }}>{inv.email}</div>
                      <div style={{ fontSize: 10, color: '#64748b' }}>
                        {inv.role} · invited {formatWhen(inv.created_at)}
                        {status === 'pending' && ` · expires ${formatWhen(inv.expires_at)}`}
                        {status === 'accepted' && ` · accepted ${formatWhen(inv.accepted_at)}`}
                      </div>
                    </div>
                    <span style={{
                      fontSize: 9, fontWeight: 700, padding: '2px 8px', borderRadius: 10,
                      background: `${color}22`, color, textTransform: 'uppercase',
                    }}>{status}</span>
                    {status === 'pending' && canManage && (
                      <>
                        <button className="btn-ghost" style={{ padding: 4 }} onClick={async () => {
                          const link = `${window.location.origin}/accept-invite?token=${inv.token}`;
                          await navigator.clipboard.writeText(link);
                          flash('Invite link copied.');
                        }} title="Copy link"><Link2 size={12} /></button>
                        <button className="btn-ghost" style={{ padding: 4, color: '#f87171' }} onClick={async () => {
                          if (!confirm(`Revoke invite for ${inv.email}?`)) return;
                          await revokeInvite(inv.token);
                          flash('Revoked.');
                          reload();
                        }} title="Revoke"><Trash2 size={12} /></button>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          )
        )}

        {tab === 'activity' && (
          activity.length === 0 ? (
            <p style={{ color: '#64748b', fontSize: 12, textAlign: 'center', padding: 48 }}>No activity yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {activity.map((a, i) => {
                const tint = {
                  tool_call: '#60a5fa', approval: '#f59e0b',
                  interaction: '#22c55e', notification: '#a78bfa',
                }[a.kind] || '#64748b';
                return (
                  <div key={a.id || i} style={{
                    padding: '8px 12px', background: '#0f172a', borderRadius: 6, borderLeft: `3px solid ${tint}`,
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                  }}>
                    <span style={{
                      fontSize: 9, fontWeight: 700, textTransform: 'uppercase', color: tint, minWidth: 70,
                    }}>{a.kind.replace('_', ' ')}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 12, color: '#e2e8f0' }}>{a.title}</div>
                      {a.summary && <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.summary}</div>}
                      <div style={{ fontSize: 9, color: '#475569', marginTop: 2 }}>
                        {a.actor_name || 'system'} · {formatWhen(a.ts)}
                      </div>
                    </div>
                    {a.success === false && <span style={{ color: '#f87171', fontSize: 10 }}>failed</span>}
                  </div>
                );
              })}
            </div>
          )
        )}
      </div>

      {showInvite && (
        <Modal title="Invite a teammate" onClose={() => setShowInvite(false)}>
          <form onSubmit={handleInvite}>
            <div style={{ marginBottom: 10 }}>
              <label style={{ display: 'block', fontSize: 10, color: '#94a3b8', marginBottom: 4 }}>Email *</label>
              <input className="field-input" type="email" required autoFocus value={newEmail} onChange={(e) => setNewEmail(e.target.value)} />
            </div>
            <div style={{ marginBottom: 10 }}>
              <label style={{ display: 'block', fontSize: 10, color: '#94a3b8', marginBottom: 4 }}>Role</label>
              <select className="field-select" value={newRole} onChange={(e) => setNewRole(e.target.value)} style={{ width: '100%' }}>
                {ROLE_OPTIONS.map(r => <option key={r}>{r}</option>)}
              </select>
              <p style={{ fontSize: 10, color: '#64748b', marginTop: 4 }}>
                viewer = read-only · member = normal access · admin = can invite others and manage business
              </p>
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 14 }}>
              <button type="button" className="btn-ghost" onClick={() => setShowInvite(false)}>Cancel</button>
              <button type="submit" className="btn-primary">Send invite</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
