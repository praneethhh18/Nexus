import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, MessageSquare, GitBranch, AlertTriangle, Clock, CheckSquare, Users, Briefcase, Receipt, TrendingUp, Plus, Calendar, Zap, ExternalLink } from 'lucide-react';
import { getStats, getHealth, getNotifications, getWorkflows } from '../services/api';
import { crmOverview, pipeline } from '../services/crm';
import { taskSummary, listTasks } from '../services/tasks';
import { invoiceSummary } from '../services/invoices';
import { calendarStatus, calendarEvents } from '../services/calendar';
import { getUser, getCurrentBusiness } from '../services/auth';
import { seedSampleData } from '../services/seed';
import { briefingLatest, briefingRun, eveningLatest, eveningRun } from '../services/briefing';
import { listPersonas } from '../services/agents';
import ReactMarkdown from 'react-markdown';
import { Sparkles, Loader2, Sun, Moon, Lock } from 'lucide-react';
import OnboardingChecklist from '../components/OnboardingChecklist';

const money = (v, cur = 'USD') => new Intl.NumberFormat('en-US', { style: 'currency', currency: cur || 'USD', maximumFractionDigits: 0 }).format(v || 0);

const STAGE_COLORS = {
  lead: 'var(--color-info)', qualified: '#a78bfa', proposal: 'var(--color-warn)',
  negotiation: '#ec4899', won: 'var(--color-ok)', lost: 'var(--color-text-dim)',
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
        <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{label}</div>
        <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text)' }}>{value}</div>
        {sub && <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 1 }}>{sub}</div>}
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
  const [seeding, setSeeding] = useState(false);
  const [seedError, setSeedError] = useState('');
  const [briefing, setBriefing] = useState(null);
  const [briefingBusy, setBriefingBusy] = useState(false);
  const [briefingError, setBriefingError] = useState('');
  const [briefingAgent, setBriefingAgent] = useState(null);
  const [evening, setEvening] = useState(null);
  const [eveningBusy, setEveningBusy] = useState(false);
  const [eveningError, setEveningError] = useState('');
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

  const loadBriefing = useCallback(async () => {
    try {
      const b = await briefingLatest();
      const todayIso = new Date().toISOString().slice(0, 10);
      const isToday = b?.data?.date === todayIso;
      if (b?.id && isToday) {
        setBriefing(b);
      } else {
        // No briefing for today yet — generate one silently so the user
        // never lands on a stale dashboard. We mark the previous briefing
        // as stale so it stays visible while the new one is being built.
        if (b?.id) setBriefing({ ...b, _stale: true });
        else setBriefing(null);
        setBriefingBusy(true);
        try {
          const fresh = await briefingRun();
          if (fresh?.id) setBriefing(fresh);
        } catch {
          // Auto-generation failures stay silent — manual "Run now" still works
        } finally {
          setBriefingBusy(false);
        }
      }
    } catch { /* ignore — non-critical */ }
    try {
      const all = await listPersonas();
      setBriefingAgent(all.find(p => p.agent_key === 'morning_briefing') || null);
    } catch { /* ignore */ }
  }, []);
  useEffect(() => { loadBriefing(); }, [loadBriefing]);


  // Evening digest — surfaces only after 4 PM local. Auto-generates on first
  // afternoon load if today's doesn't exist yet, mirroring the morning briefing.
  const loadEvening = useCallback(async () => {
    if (new Date().getHours() < 16) return;
    try {
      const e = await eveningLatest();
      const todayIso = new Date().toISOString().slice(0, 10);
      const isToday = e?.data?.date === todayIso;
      if (e?.id && isToday) {
        setEvening(e);
      } else {
        setEvening(null);
        setEveningBusy(true);
        try {
          const fresh = await eveningRun();
          if (fresh?.id) setEvening(fresh);
        } catch { /* silent — manual button still works */ }
        finally { setEveningBusy(false); }
      }
    } catch { /* ignore */ }
  }, []);
  useEffect(() => { loadEvening(); }, [loadEvening]);


  const handleRunEvening = async () => {
    if (eveningBusy) return;
    setEveningBusy(true); setEveningError('');
    try {
      const e = await eveningRun();
      setEvening(e);
    } catch (e) {
      setEveningError(e.message || 'Digest failed.');
    } finally {
      setEveningBusy(false);
    }
  };


  const handleRunBriefing = async () => {
    if (briefingBusy) return;
    setBriefingBusy(true); setBriefingError('');
    try {
      const b = await briefingRun();
      setBriefing(b);
    } catch (e) {
      setBriefingError(e.message || 'Briefing failed.');
    } finally {
      setBriefingBusy(false);
    }
  };

  // Find top pipeline value stage
  const pipelineTotal = pipe
    ? Object.values(pipe.by_stage).reduce((s, v) => s + (v.total || 0), 0) -
      ((pipe.by_stage?.won?.total || 0) + (pipe.by_stage?.lost?.total || 0))
    : 0;

  // Detect "fresh business" — nothing created yet
  const isEmptyBusiness =
    crm && tasks && invoices &&
    (crm.contacts || 0) === 0 &&
    (tasks.open_total || 0) === 0 &&
    (invoices.outstanding?.count || 0) === 0 &&
    (invoices.paid?.count || 0) === 0 &&
    (invoices.draft?.count || 0) === 0;

  const handleSeed = async () => {
    if (seeding) return;
    setSeeding(true); setSeedError('');
    try {
      const r = await seedSampleData();
      if (!r.seeded) setSeedError(r.reason || 'Could not seed.');
      await reload();
    } catch (e) {
      setSeedError(e.message || 'Seed failed.');
    } finally {
      setSeeding(false);
    }
  };

  const now = new Date();
  const hour = now.getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <h1>{greeting}{user?.name ? `, ${user.name.split(' ')[0]}` : ''}</h1>
        <p>Overview for <strong style={{ color: 'var(--color-text)' }}>{current?.name || 'your business'}</strong></p>
      </div>

      <div className="page-body">
        {/* Onboarding checklist — self-hides when complete or skipped */}
        <div style={{ marginBottom: 14 }}>
          <OnboardingChecklist />
        </div>

        {/* Morning briefing card — the daily-use moment */}
        {!isEmptyBusiness && (
          <div className="panel" style={{
            marginBottom: 14,
            borderColor: briefing ? 'color-mix(in srgb, var(--color-accent) 28%, transparent)' : 'var(--color-border)',
            background: briefing
              ? 'linear-gradient(135deg, color-mix(in srgb, var(--color-accent) 6%, var(--color-surface-2)), var(--color-surface-2))'
              : 'var(--color-surface-2)',
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: briefing ? 12 : 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 'var(--r-md)',
                  background: 'color-mix(in srgb, var(--color-accent) 16%, transparent)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Sun size={18} color="var(--color-accent)" />
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    Morning briefing
                    {briefingAgent && (
                      <span style={{
                        fontSize: 10, padding: '2px 8px', borderRadius: 'var(--r-pill)',
                        background: 'var(--color-accent-soft)',
                        color: 'var(--color-accent)',
                        fontWeight: 600, letterSpacing: 0.3,
                        border: '1px solid color-mix(in srgb, var(--color-accent) 25%, transparent)',
                        cursor: 'pointer',
                      }}
                      title="View all agents"
                      onClick={() => navigate('/agents')}>
                        by {briefingAgent.name} · {briefingAgent.role_tag}
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--color-text-dim)', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    {briefing
                      ? <>Generated {new Date(briefing.created_at + 'Z').toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })} · <span style={{ color: briefing.narrative_mode === 'cloud' ? 'var(--color-info)' : 'var(--color-text-dim)' }}>{briefing.narrative_mode === 'cloud' ? 'cloud narrative' : 'local'}</span></>
                      : briefingBusy
                        ? 'Generating today\'s briefing…'
                        : 'Not generated yet today — runs automatically each morning at 08:00 UTC.'}
                    {briefing?._stale && (
                      <span style={{
                        padding: '1px 6px', borderRadius: 'var(--r-pill)',
                        background: 'color-mix(in srgb, var(--color-warn) 12%, transparent)',
                        border: '1px solid color-mix(in srgb, var(--color-warn) 30%, transparent)',
                        color: 'var(--color-warn)', fontSize: 10, fontWeight: 600,
                      }}>
                        from {briefing.data?.date} · refreshing
                      </span>
                    )}
                    {briefing && !briefing._stale && <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}><Lock size={10} /> aggregates only</span>}
                  </div>
                </div>
              </div>
              <button className="btn-ghost" onClick={handleRunBriefing} disabled={briefingBusy}
                style={{ flexShrink: 0 }}>
                {briefingBusy
                  ? <><Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> Generating…</>
                  : (briefing ? <><Sparkles size={12} /> Re-run</> : <><Sparkles size={12} /> Run now</>)}
              </button>
            </div>

            {briefingError && (
              <div style={{ fontSize: 11, color: 'var(--color-err)', marginTop: 6 }}>{briefingError}</div>
            )}

            {briefing && (
              <div className="chat-markdown" style={{
                fontSize: 13, color: 'var(--color-text)', lineHeight: 1.65,
                borderTop: '1px solid var(--color-border)', paddingTop: 12,
              }}>
                <ReactMarkdown>{briefing.narrative}</ReactMarkdown>
              </div>
            )}
          </div>
        )}

        {/* Evening digest — shown after 4 PM local; auto-generates on first afternoon load */}
        {!isEmptyBusiness && (evening || eveningBusy || new Date().getHours() >= 16) && (
          <div className="panel" style={{
            marginBottom: 14,
            borderColor: evening ? 'color-mix(in srgb, var(--color-info) 28%, transparent)' : 'var(--color-border)',
            background: evening
              ? 'linear-gradient(135deg, color-mix(in srgb, var(--color-info) 6%, var(--color-surface-2)), var(--color-surface-2))'
              : 'var(--color-surface-2)',
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12, marginBottom: evening ? 12 : 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{
                  width: 36, height: 36, borderRadius: 'var(--r-md)',
                  background: 'color-mix(in srgb, var(--color-info) 16%, transparent)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Moon size={18} color="var(--color-info)" />
                </div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
                    Today's wrap
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--color-text-dim)', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    {evening
                      ? <>Generated {new Date(evening.created_at + 'Z').toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })} · <span style={{ color: evening.narrative_mode === 'cloud' ? 'var(--color-info)' : 'var(--color-text-dim)' }}>{evening.narrative_mode === 'cloud' ? 'cloud narrative' : 'local'}</span></>
                      : eveningBusy
                        ? 'Generating today\'s wrap…'
                        : 'Backward-looking digest of what got done today.'}
                    {evening && <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3 }}><Lock size={10} /> aggregates only</span>}
                  </div>
                </div>
              </div>
              <button className="btn-ghost" onClick={handleRunEvening} disabled={eveningBusy}
                style={{ flexShrink: 0 }}>
                {eveningBusy
                  ? <><Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> Generating…</>
                  : (evening ? <><Sparkles size={12} /> Re-run</> : <><Sparkles size={12} /> Run now</>)}
              </button>
            </div>

            {eveningError && (
              <div style={{ fontSize: 11, color: 'var(--color-err)', marginTop: 6 }}>{eveningError}</div>
            )}

            {evening && (
              <div className="chat-markdown" style={{
                fontSize: 13, color: 'var(--color-text)', lineHeight: 1.65,
                borderTop: '1px solid var(--color-border)', paddingTop: 12,
              }}>
                <ReactMarkdown>{evening.narrative}</ReactMarkdown>
              </div>
            )}
          </div>
        )}

        {/* Empty-state banner — gives a one-click path to a working demo */}
        {isEmptyBusiness && (
          <div style={{
            padding: '18px 20px', marginBottom: 14,
            borderRadius: 'var(--r-lg)',
            background: 'linear-gradient(135deg, color-mix(in srgb, var(--color-accent) 12%, transparent), color-mix(in srgb, var(--color-info) 10%, transparent))',
            border: '1px solid color-mix(in srgb, var(--color-accent) 28%, transparent)',
            display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap',
          }}>
            <div style={{
              width: 44, height: 44, borderRadius: 'var(--r-md)',
              background: 'color-mix(in srgb, var(--color-accent) 18%, transparent)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0,
            }}>
              <Sparkles size={22} color="var(--color-accent)" />
            </div>
            <div style={{ flex: 1, minWidth: 260 }}>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)', marginBottom: 2 }}>
                Your workspace is empty
              </div>
              <div style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
                Load sample data to see NexusAgent in action — 4 companies, 5 deals across the pipeline,
                6 tasks, and 4 invoices. You can delete it anytime. Nothing leaves your machine.
              </div>
              {seedError && (
                <div style={{ fontSize: 11, color: 'var(--color-err)', marginTop: 6 }}>{seedError}</div>
              )}
            </div>
            <button className="btn-primary" onClick={handleSeed} disabled={seeding}
              style={{ flexShrink: 0 }}>
              {seeding
                ? <><Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Loading…</>
                : <><Sparkles size={13} /> Load sample data</>}
            </button>
          </div>
        )}

        {/* Top KPI row — the numbers that matter */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 14 }}>
          <KpiCard
            icon={Briefcase} label="Open pipeline" color="var(--color-warn)"
            value={money(pipelineTotal)}
            sub={`${(pipe?.by_stage?.lead?.count || 0) + (pipe?.by_stage?.qualified?.count || 0) + (pipe?.by_stage?.proposal?.count || 0) + (pipe?.by_stage?.negotiation?.count || 0)} deals`}
            onClick={() => navigate('/crm')}
          />
          <KpiCard
            icon={TrendingUp} label="Won this month" color="var(--color-ok)"
            value={money(crm?.won_this_month || 0)}
            sub={`${pipe?.by_stage?.won?.count || 0} closed`}
            onClick={() => navigate('/crm')}
          />
          <KpiCard
            icon={Receipt} label="Outstanding invoices" color="var(--color-info)"
            value={money(invoices?.outstanding?.total || 0)}
            sub={`${invoices?.outstanding?.count || 0} unpaid`}
            onClick={() => navigate('/invoices')}
          />
          <KpiCard
            icon={AlertTriangle} label="Overdue" color="var(--color-err)"
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
                  <CheckSquare size={15} color="var(--color-ok)" /> Today's tasks
                </h3>
                <button className="btn-ghost" style={{ fontSize: 10 }} onClick={() => navigate('/tasks')}>View all</button>
              </div>
              {todayTasks.length === 0 ? (
                <p style={{ fontSize: 12, color: 'var(--color-text-dim)', textAlign: 'center', padding: 16 }}>Nothing due today. Clean slate.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {todayTasks.map((t) => (
                    <div key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8, background: 'var(--color-surface-1)', borderRadius: 6 }}>
                      <span style={{ width: 6, height: 6, borderRadius: '50%', background: { urgent: 'var(--color-err)', high: 'var(--color-warn)', normal: 'var(--color-info)', low: 'var(--color-text-dim)' }[t.priority] || 'var(--color-text-dim)' }} />
                      <span style={{ fontSize: 12, color: 'var(--color-text)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{t.title}</span>
                      <span style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{t.priority}</span>
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
                    <Calendar size={15} color="var(--color-info)" /> Upcoming meetings
                  </h3>
                  {calConn.connected
                    ? <span style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{calConn.connection?.account_email}</span>
                    : <button className="btn-ghost" style={{ fontSize: 10 }} onClick={() => navigate('/settings')}>Connect</button>
                  }
                </div>
                {!calConn.connected ? (
                  <p style={{ fontSize: 12, color: 'var(--color-text-dim)', textAlign: 'center', padding: 12 }}>
                    Connect Google Calendar in Settings to show your next meetings here.
                  </p>
                ) : events.length === 0 ? (
                  <p style={{ fontSize: 12, color: 'var(--color-text-dim)', textAlign: 'center', padding: 12 }}>
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
                        <div key={e.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8, background: 'var(--color-surface-1)', borderRadius: 6 }}>
                          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-info)', flexShrink: 0 }} />
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ fontSize: 12, color: 'var(--color-text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.summary}</div>
                            <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{label}{e.location ? ` · ${e.location}` : ''}</div>
                          </div>
                          {e.html_link && (
                            <a href={e.html_link} target="_blank" rel="noreferrer" style={{ color: 'var(--color-text-dim)' }}>
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
                  <Briefcase size={15} color="var(--color-warn)" /> Deal pipeline
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
                          <span style={{ color: 'var(--color-text-muted)', textTransform: 'capitalize' }}>{stage} · {s.count}</span>
                          <span style={{ color: STAGE_COLORS[stage], fontWeight: 600 }}>{money(s.total)}</span>
                        </div>
                        <div style={{ height: 5, background: 'var(--color-surface-1)', borderRadius: 3, overflow: 'hidden' }}>
                          <div style={{ width: `${Math.min(pct, 100)}%`, height: '100%', background: STAGE_COLORS[stage], transition: 'width 0.3s' }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : <p style={{ fontSize: 12, color: 'var(--color-text-dim)' }}>No deals yet.</p>}
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
                <Users size={15} color="var(--color-info)" /> Business at a glance
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
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 10px', background: 'var(--color-surface-1)', borderRadius: 6 }}>
                    <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{row.label}</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text)' }}>{row.value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel">
              <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: '0 0 10px' }}>
                <Activity size={15} color="var(--color-ok)" /> System
              </h3>
              {[
                { label: 'LLM', ok: health?.ollama?.online, detail: health?.model || 'offline' },
                { label: 'Knowledge base', ok: (stats?.knowledge_base?.document_count || 0) > 0, detail: `${stats?.knowledge_base?.document_count || 0} docs` },
                { label: 'Email', ok: health?.features?.email, detail: health?.features?.email ? 'configured' : 'disabled' },
                { label: 'Discord', ok: health?.features?.discord, detail: health?.features?.discord ? 'configured' : 'disabled' },
              ].map((r, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: r.ok ? 'var(--color-ok)' : 'var(--color-text-dim)' }} />
                  <span style={{ fontSize: 11, color: 'var(--color-text)', flex: 1 }}>{r.label}</span>
                  <span style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{r.detail}</span>
                </div>
              ))}
            </div>

            <div className="panel">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
                  <AlertTriangle size={15} color="var(--color-warn)" /> Recent alerts
                </h3>
              </div>
              {notifs.length === 0 ? (
                <p style={{ fontSize: 11, color: 'var(--color-text-dim)', padding: '8px 0' }}>No new alerts.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {notifs.map((n, i) => (
                    <div key={i} style={{
                      padding: '8px 10px', background: 'var(--color-surface-1)', borderRadius: 6,
                      borderLeft: `3px solid ${{ critical: 'var(--color-err)', warning: 'var(--color-warn)', success: 'var(--color-ok)', info: 'var(--color-info)' }[n.severity] || 'var(--color-text-dim)'}`,
                    }}>
                      <div style={{ fontSize: 11, fontWeight: 500, color: 'var(--color-text)' }}>{n.title}</div>
                      <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{n.message}</div>
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
