import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, MessageSquare, GitBranch, AlertTriangle, Clock, CheckSquare, Users, Briefcase, Receipt, TrendingUp, Plus, Calendar, Zap, ExternalLink } from 'lucide-react';
import { getStats, getHealth, getNotifications, getWorkflows } from '../services/api';
import { crmOverview, pipeline } from '../services/crm';
import { taskSummary, listTasks } from '../services/tasks';
import { invoiceSummary } from '../services/invoices';
import { calendarStatus, calendarEvents } from '../services/calendar';
import { getUser, getCurrentBusiness } from '../services/auth';

const money = (v, cur = 'USD') => new Intl.NumberFormat('en-US', { style: 'currency', currency: cur || 'USD', maximumFractionDigits: 0 }).format(v || 0);

const STAGE_COLORS = {
  lead: '#60a5fa', qualified: '#a78bfa', proposal: '#f59e0b',
  negotiation: '#ec4899', won: '#22c55e', lost: '#6b7280',
};

function KpiCard({ icon: Icon, label, value, sub, color, onClick }) {
  return (
    <div
      onClick={onClick}
      className="panel"
      style={{
        padding: 14, cursor: onClick ? 'pointer' : 'default', display: 'flex', alignItems: 'center', gap: 12,
        transition: 'transform 0.1s',
      }}
      onMouseEnter={(e) => { if (onClick) e.currentTarget.style.transform = 'translateY(-1px)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; }}
    >
      <div style={{
        width: 40, height: 40, borderRadius: 10, flexShrink: 0,
        background: `${color}22`, color,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon size={20} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 10, color: '#64748b' }}>{label}</div>
        <div style={{ fontSize: 18, fontWeight: 700, color: '#e2e8f0' }}>{value}</div>
        {sub && <div style={{ fontSize: 10, color: '#64748b', marginTop: 1 }}>{sub}</div>}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [notifs, setNotifs] = useState([]);
  const [activeWf, setActiveWf] = useState(0);
  const [crm, setCrm] = useState(null);
  const [pipe, setPipe] = useState(null);
  const [tasks, setTasks] = useState(null);
  const [invoices, setInvoices] = useState(null);
  const [todayTasks, setTodayTasks] = useState([]);
  const [stats, setStats] = useState(null);
  const [calConn, setCalConn] = useState(null);
  const [events, setEvents] = useState([]);
  const user = getUser();
  const current = getCurrentBusiness();
  const navigate = useNavigate();

  const reload = useCallback(async () => {
    try {
      const [h, st, ns, wfs, c, p, ts, inv, todayList, cal] = await Promise.all([
        getHealth().catch(() => null),
        getStats().catch(() => null),
        getNotifications().catch(() => ({ notifications: [] })),
        getWorkflows().catch(() => []),
        crmOverview().catch(() => null),
        pipeline().catch(() => null),
        taskSummary(false).catch(() => null),
        invoiceSummary().catch(() => null),
        listTasks({ due_window: 'today', status: 'active', limit: 5 }).catch(() => []),
        calendarStatus().catch(() => null),
      ]);
      setHealth(h); setStats(st);
      setNotifs((ns.notifications || []).slice(0, 5));
      setActiveWf(wfs.filter((w) => w.enabled).length);
      setCrm(c); setPipe(p); setTasks(ts); setInvoices(inv);
      setTodayTasks(todayList);
      setCalConn(cal);
      if (cal?.connected) {
        try {
          const ev = await calendarEvents(14, 8);
          setEvents(ev);
        } catch {}
      } else {
        setEvents([]);
      }
    } catch {}
  }, []);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    const h = () => reload();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reload]);

  // Find top pipeline value stage
  const pipelineTotal = pipe
    ? Object.values(pipe.by_stage).reduce((s, v) => s + (v.total || 0), 0) -
      ((pipe.by_stage?.won?.total || 0) + (pipe.by_stage?.lost?.total || 0))
    : 0;

  const now = new Date();
  const hour = now.getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <h1>{greeting}{user?.name ? `, ${user.name.split(' ')[0]}` : ''}</h1>
        <p>Overview for <strong style={{ color: '#e2e8f0' }}>{current?.name || 'your business'}</strong></p>
      </div>

      <div className="page-body">
        {/* Top KPI row — the numbers that matter */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 14 }}>
          <KpiCard
            icon={Briefcase} label="Open pipeline" color="#f59e0b"
            value={money(pipelineTotal)}
            sub={`${(pipe?.by_stage?.lead?.count || 0) + (pipe?.by_stage?.qualified?.count || 0) + (pipe?.by_stage?.proposal?.count || 0) + (pipe?.by_stage?.negotiation?.count || 0)} deals`}
            onClick={() => navigate('/crm')}
          />
          <KpiCard
            icon={TrendingUp} label="Won this month" color="#22c55e"
            value={money(crm?.won_this_month || 0)}
            sub={`${pipe?.by_stage?.won?.count || 0} closed`}
            onClick={() => navigate('/crm')}
          />
          <KpiCard
            icon={Receipt} label="Outstanding invoices" color="#60a5fa"
            value={money(invoices?.outstanding?.total || 0)}
            sub={`${invoices?.outstanding?.count || 0} unpaid`}
            onClick={() => navigate('/invoices')}
          />
          <KpiCard
            icon={AlertTriangle} label="Overdue" color="#ef4444"
            value={(tasks?.overdue || 0) + (invoices?.overdue?.count || 0)}
            sub={`${tasks?.overdue || 0} tasks · ${invoices?.overdue?.count || 0} invoices`}
            onClick={() => navigate('/tasks')}
          />
        </div>

        {/* Main two-column: left = focus list, right = business snapshot */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: 12 }}>
          {/* LEFT: Today's focus */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="panel">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
                  <CheckSquare size={15} color="#22c55e" /> Today's tasks
                </h3>
                <button className="btn-ghost" style={{ fontSize: 10 }} onClick={() => navigate('/tasks')}>View all</button>
              </div>
              {todayTasks.length === 0 ? (
                <p style={{ fontSize: 12, color: '#64748b', textAlign: 'center', padding: 16 }}>Nothing due today. Clean slate.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {todayTasks.map((t) => (
                    <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8, background: '#0f172a', borderRadius: 6 }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: { urgent: '#ef4444', high: '#f59e0b', normal: '#60a5fa', low: '#64748b' }[t.priority] || '#64748b' }} />
                      <span style={{ fontSize: 12, color: '#e2e8f0', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.title}</span>
                      <span style={{ fontSize: 10, color: '#64748b' }}>{t.priority}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Upcoming calendar events */}
            {calConn?.configured && (
              <div className="panel">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                  <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
                    <Calendar size={15} color="#60a5fa" /> Upcoming meetings
                  </h3>
                  {calConn.connected
                    ? <span style={{ fontSize: 10, color: '#64748b' }}>{calConn.connection?.account_email}</span>
                    : <button className="btn-ghost" style={{ fontSize: 10 }} onClick={() => navigate('/settings')}>Connect</button>
                  }
                </div>
                {!calConn.connected ? (
                  <p style={{ fontSize: 12, color: '#64748b', textAlign: 'center', padding: 12 }}>
                    Connect Google Calendar in Settings to show your next meetings here.
                  </p>
                ) : events.length === 0 ? (
                  <p style={{ fontSize: 12, color: '#64748b', textAlign: 'center', padding: 12 }}>
                    Nothing scheduled in the next 14 days.
                  </p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {events.slice(0, 5).map((e) => {
                      const start = e.start ? new Date(e.start) : null;
                      const label = start
                        ? start.toLocaleString([], { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
                        : 'No date';
                      return (
                        <div key={e.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8, background: '#0f172a', borderRadius: 6 }}>
                          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#60a5fa', flexShrink: 0 }} />
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: 12, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.summary}</div>
                            <div style={{ fontSize: 10, color: '#64748b' }}>{label}{e.location ? ` · ${e.location}` : ''}</div>
                          </div>
                          {e.html_link && (
                            <a href={e.html_link} target="_blank" rel="noreferrer" style={{ color: '#64748b' }}>
                              <ExternalLink size={12} />
                            </a>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {/* Pipeline breakdown */}
            <div className="panel">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
                  <Briefcase size={15} color="#f59e0b" /> Deal pipeline
                </h3>
                <button className="btn-ghost" style={{ fontSize: 10 }} onClick={() => navigate('/crm')}>Open CRM</button>
              </div>
              {pipe ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {['lead', 'qualified', 'proposal', 'negotiation', 'won'].map((stage) => {
                    const s = pipe.by_stage[stage] || { count: 0, total: 0 };
                    const pct = pipelineTotal > 0 ? (s.total / Math.max(pipelineTotal, s.total)) * 100 : 0;
                    return (
                      <div key={stage}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
                          <span style={{ color: '#94a3b8', textTransform: 'capitalize' }}>{stage} · {s.count}</span>
                          <span style={{ color: STAGE_COLORS[stage], fontWeight: 600 }}>{money(s.total)}</span>
                        </div>
                        <div style={{ height: 5, background: '#0f172a', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${Math.min(pct, 100)}%`, height: '100%', background: STAGE_COLORS[stage], transition: 'width 0.3s' }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : <p style={{ fontSize: 12, color: '#64748b' }}>No deals yet.</p>}
            </div>

            {/* Quick actions */}
            <div className="panel">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '0 0 10px' }}>
                <Zap size={15} color="#a78bfa" /> Quick actions
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                {[
                  { icon: Plus, label: 'New task', onClick: () => navigate('/tasks') },
                  { icon: Users, label: 'Add contact', onClick: () => navigate('/crm') },
                  { icon: Receipt, label: 'New invoice', onClick: () => navigate('/invoices') },
                  { icon: MessageSquare, label: 'Ask AI', onClick: () => navigate('/chat') },
                  { icon: GitBranch, label: 'Workflows', onClick: () => navigate('/workflows') },
                  { icon: Calendar, label: 'This week', onClick: () => navigate('/tasks') },
                ].map(({ icon: Icon, label, onClick }, i) => (
                  <button key={i} onClick={onClick} className="btn-ghost" style={{ padding: '10px 8px', flexDirection: 'column', gap: 4, fontSize: 11 }}>
                    <Icon size={14} />
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* RIGHT: CRM snapshot + health + notifications */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="panel">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '0 0 10px' }}>
                <Users size={15} color="#60a5fa" /> Business at a glance
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
                {[
                  { label: 'Contacts', value: crm?.contacts ?? 0 },
                  { label: 'Companies', value: crm?.companies ?? 0 },
                  { label: 'Open tasks', value: tasks?.open_total ?? 0 },
                  { label: 'Active workflows', value: activeWf },
                  { label: 'Done today', value: tasks?.done_today ?? 0 },
                  { label: 'Draft invoices', value: invoices?.draft?.count ?? 0 },
                ].map((row, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: '#0f172a', borderRadius: 6 }}>
                    <span style={{ fontSize: 11, color: '#94a3b8' }}>{row.label}</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: '#e2e8f0' }}>{row.value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '0 0 10px' }}>
                <Activity size={15} color="#22c55e" /> System
              </h3>
              {[
                { label: 'LLM', ok: health?.ollama?.online, detail: health?.model || 'offline' },
                { label: 'Knowledge base', ok: (stats?.knowledge_base?.document_count || 0) > 0, detail: `${stats?.knowledge_base?.document_count || 0} docs` },
                { label: 'Email', ok: health?.features?.email, detail: health?.features?.email ? 'configured' : 'disabled' },
                { label: 'Discord', ok: health?.features?.discord, detail: health?.features?.discord ? 'configured' : 'disabled' },
              ].map((r, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: r.ok ? '#22c55e' : '#64748b' }} />
                  <span style={{ fontSize: 11, color: '#e2e8f0', flex: 1 }}>{r.label}</span>
                  <span style={{ fontSize: 10, color: '#64748b' }}>{r.detail}</span>
                </div>
              ))}
            </div>

            <div className="panel">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
                  <AlertTriangle size={15} color="#f59e0b" /> Recent alerts
                </h3>
              </div>
              {notifs.length === 0 ? (
                <p style={{ fontSize: 11, color: '#64748b', padding: '8px 0' }}>No new alerts.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {notifs.map((n, i) => (
                    <div key={i} style={{
                      padding: '8px 10px', background: '#0f172a', borderRadius: 6,
                      borderLeft: `3px solid ${{ critical: '#ef4444', warning: '#f59e0b', success: '#22c55e', info: '#60a5fa' }[n.severity] || '#64748b'}`,
                    }}>
                      <div style={{ fontSize: 11, fontWeight: 500, color: '#e2e8f0' }}>{n.title}</div>
                      <div style={{ fontSize: 10, color: '#64748b' }}>{n.message}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
