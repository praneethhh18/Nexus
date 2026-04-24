import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Edit3, Check, X, RotateCcw, Clock, ExternalLink, Loader2, Bot, Activity, Play,
         Pause, PlayCircle, AlertTriangle, ShieldCheck, History } from 'lucide-react';
import { listPersonas, renamePersona, togglePersonaEnabled, listActivity, runAgent, listRuns } from '../services/agents';

function formatWhen(iso) {
  if (!iso) return null;
  try {
    const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z');
    const mins = Math.floor((Date.now() - d.getTime()) / 60000);
    if (mins < 1)    return 'just now';
    if (mins < 60)   return `${mins}m ago`;
    if (mins < 1440) return `${Math.floor(mins / 60)}h ago`;
    return `${Math.floor(mins / 1440)}d ago`;
  } catch { return iso.slice(0, 16); }
}

function formatNextRun(iso) {
  if (!iso) return null;
  try {
    const d = new Date(iso);
    return d.toLocaleString([], { weekday: 'short', hour: '2-digit', minute: '2-digit' });
  } catch { return iso.slice(0, 16); }
}

function LastRunChip({ lastRun, stats24h }) {
  if (!lastRun) {
    return <span style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>No runs yet</span>;
  }
  const st = lastRun.status;
  const color = st === 'success' ? 'var(--color-ok)'
              : st === 'error'   ? 'var(--color-err)'
              : st === 'skipped' ? 'var(--color-text-dim)'
              :                    'var(--color-warn)';
  const bg = `color-mix(in srgb, ${color} 12%, transparent)`;
  const when = lastRun.finished_at || lastRun.started_at;
  return (
    <span
      title={lastRun.error || `Last run ${st} · ${lastRun.items_produced || 0} item(s)`}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 4,
        fontSize: 10, fontWeight: 600, padding: '2px 7px',
        borderRadius: 'var(--r-pill)', color, background: bg,
        border: `1px solid color-mix(in srgb, ${color} 28%, transparent)`,
      }}
    >
      {st === 'error' ? <AlertTriangle size={9} /> : <ShieldCheck size={9} />}
      {st === 'success' && `${lastRun.items_produced || 0} produced`}
      {st === 'error'   && 'Last run failed'}
      {st === 'skipped' && 'Paused'}
      {st === 'running' && 'Running…'}
      {stats24h?.error > 0 && st !== 'error' && (
        <span style={{ marginLeft: 4, color: 'var(--color-err)' }}>· {stats24h.error} err 24h</span>
      )}
    </span>
  );
}

function PersonaCard({ persona, onRenamed, onEnabledChanged, onOpenSurface, onRanAgent, onOpenRuns }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(persona.name);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [running, setRunning] = useState(false);
  const [runMsg, setRunMsg] = useState('');
  const [togglingEnabled, setTogglingEnabled] = useState(false);

  const enabled = persona.enabled !== false;

  const togglePause = async () => {
    if (togglingEnabled) return;
    setTogglingEnabled(true); setErr('');
    try {
      const updated = await togglePersonaEnabled(persona.agent_key, !enabled);
      onEnabledChanged(updated);
    } catch (e) { setErr(e.message || 'Toggle failed'); }
    finally { setTogglingEnabled(false); }
  };

  useEffect(() => { setValue(persona.name); }, [persona.name]);

  const save = async (newVal) => {
    if (busy) return;
    setBusy(true); setErr('');
    try {
      const updated = await renamePersona(persona.agent_key, newVal);
      onRenamed(updated);
      setEditing(false);
    } catch (e) { setErr(e.message); }
    finally { setBusy(false); }
  };

  const reset = () => save('');  // empty name → backend clears override

  const run = async () => {
    if (running) return;
    setRunning(true); setRunMsg(''); setErr('');
    try {
      const r = await runAgent(persona.agent_key);
      const d = r.detail || {};
      // Compose a short human-readable result line per agent
      const parts = [];
      if (d.queued !== undefined)           parts.push(`${d.queued} drafted`);
      if (d.candidates !== undefined)       parts.push(`${d.candidates} invoice${d.candidates === 1 ? '' : 's'} checked`);
      if (d.stale_deals !== undefined)      parts.push(`${d.stale_deals} stale`);
      if (d.created !== undefined && d.created > 0) parts.push(`${d.created} follow-up task${d.created === 1 ? '' : 's'}`);
      if (d.processed !== undefined)        parts.push(`${d.processed} email${d.processed === 1 ? '' : 's'} triaged`);
      if (d.narrative_mode)                 parts.push(`briefing ${d.narrative_mode}`);
      if (d.meetings !== undefined)         parts.push(`${d.meetings} meeting${d.meetings === 1 ? '' : 's'}`);
      if (d.consolidated !== undefined)     parts.push(`memory updated`);
      setRunMsg(parts.length ? `Done — ${parts.join(' · ')}` : 'Done.');
      onRanAgent?.();
    } catch (e) {
      setErr(e.message || 'Run failed');
    } finally {
      setRunning(false);
      setTimeout(() => setRunMsg(''), 6000);
    }
  };

  return (
    <div className="panel" style={{
      padding: 18,
      display: 'flex', flexDirection: 'column', gap: 12,
      transition: 'border-color var(--dur-fast) var(--ease-out), transform var(--dur-fast) var(--ease-out), opacity var(--dur-fast)',
      opacity: enabled ? 1 : 0.7,
      borderStyle: enabled ? 'solid' : 'dashed',
    }}>
      {/* Header — avatar + name + role */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 'var(--r-md)',
          background: 'linear-gradient(135deg, color-mix(in srgb, var(--color-accent) 22%, transparent), color-mix(in srgb, var(--color-info) 18%, transparent))',
          border: '1px solid color-mix(in srgb, var(--color-accent) 28%, transparent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 22, flexShrink: 0,
        }}>
          {persona.emoji || <Bot size={20} color="var(--color-accent)" />}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          {editing ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <input
                autoFocus
                className="field-input"
                style={{ fontSize: 16, fontWeight: 600, padding: '5px 10px', maxWidth: 200 }}
                value={value}
                maxLength={40}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') save(value);
                  if (e.key === 'Escape') { setEditing(false); setValue(persona.name); }
                }}
                disabled={busy}
              />
              <button className="btn-ghost" onClick={() => save(value)} disabled={busy} title="Save">
                {busy ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> : <Check size={13} color="var(--color-ok)" />}
              </button>
              <button className="btn-ghost" onClick={() => { setEditing(false); setValue(persona.name); }} title="Cancel">
                <X size={13} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 17, fontWeight: 600, color: 'var(--color-text)', letterSpacing: '-0.01em' }}>
                {persona.name}
              </span>
              <span style={{
                fontSize: 10, padding: '2px 8px', borderRadius: 'var(--r-pill)',
                background: 'var(--color-accent-soft)',
                color: 'var(--color-accent)',
                fontWeight: 600, letterSpacing: 0.3,
                border: '1px solid color-mix(in srgb, var(--color-accent) 25%, transparent)',
              }}>
                {persona.role_tag}
              </span>
              <button
                onClick={() => setEditing(true)}
                title="Rename"
                style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 2, display: 'flex' }}
              >
                <Edit3 size={12} />
              </button>
              {persona.is_custom && (
                <button
                  onClick={reset}
                  title={`Reset to default name "${persona.default_name}"`}
                  style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 2, display: 'flex' }}
                >
                  <RotateCcw size={12} />
                </button>
              )}
            </div>
          )}
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 2 }}>
            {persona.is_custom && <>You renamed — default is <em>{persona.default_name}</em> · </>}
            <code style={{ fontSize: 10 }}>{persona.agent_key}</code>
          </div>
          {err && <div style={{ fontSize: 11, color: 'var(--color-err)', marginTop: 4 }}>{err}</div>}
        </div>
      </div>

      {/* Description */}
      <p style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.55, margin: 0 }}>
        {persona.description}
      </p>

      {/* Run Now + Pause/Resume + last-run chip */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <button
          onClick={run}
          disabled={running || !enabled}
          className="btn-primary"
          style={{ fontSize: 12, padding: '6px 14px', opacity: enabled ? 1 : 0.5 }}
          title={enabled ? `Run ${persona.name} right now` : 'Resume the agent to run it'}
        >
          {running
            ? <><Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} /> Working…</>
            : <><Play size={11} /> Run now</>}
        </button>
        <button
          onClick={togglePause}
          disabled={togglingEnabled}
          className="btn-ghost"
          style={{ fontSize: 11, padding: '6px 10px' }}
          title={enabled ? 'Pause the scheduled run' : 'Resume the scheduled run'}
        >
          {togglingEnabled
            ? <Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} />
            : (enabled ? <><Pause size={11} /> Pause</> : <><PlayCircle size={11} /> Resume</>)}
        </button>
        <button
          onClick={() => onOpenRuns(persona)}
          className="btn-ghost"
          style={{ fontSize: 11, padding: '6px 10px' }}
          title="See recent runs"
        >
          <History size={11} /> History
        </button>
        <LastRunChip lastRun={persona.last_run} stats24h={persona.run_stats_24h} />
        {runMsg && <span style={{ fontSize: 11, color: 'var(--color-ok)' }}>{runMsg}</span>}
      </div>

      {/* Activity strip */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        paddingTop: 10, borderTop: '1px solid var(--color-border)',
        fontSize: 11, color: 'var(--color-text-dim)', flexWrap: 'wrap',
      }}>
        {persona.last_activity?.last_ran && (
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            <Clock size={11} /> Last ran {formatWhen(persona.last_activity.last_ran)}
          </span>
        )}
        {persona.last_activity?.last_24h_count > 0 && (
          <span style={{ color: 'var(--color-accent)' }}>
            {persona.last_activity.last_24h_count} in the last 24h
          </span>
        )}
        {persona.next_run && (
          <span>Next run · {formatNextRun(persona.next_run)}</span>
        )}
        {!persona.last_activity?.last_ran && !persona.next_run && (
          <span>No activity yet</span>
        )}
        {persona.last_activity?.surface && (
          <button
            onClick={() => onOpenSurface(persona.last_activity.surface)}
            className="btn-ghost"
            style={{ marginLeft: 'auto', fontSize: 11 }}
          >
            Open <ExternalLink size={11} />
          </button>
        )}
      </div>
    </div>
  );
}

function groupByDay(events) {
  const groups = new Map();
  for (const e of events) {
    const d = e.ts ? new Date(e.ts.endsWith('Z') ? e.ts : e.ts + 'Z') : null;
    const key = d ? d.toDateString() : 'Unknown';
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(e);
  }
  return [...groups.entries()];
}

function dayLabel(dateStr) {
  if (!dateStr || dateStr === 'Unknown') return 'Earlier';
  const d = new Date(dateStr);
  const today = new Date();
  const yday = new Date(Date.now() - 86400000);
  if (d.toDateString() === today.toDateString()) return 'Today';
  if (d.toDateString() === yday.toDateString()) return 'Yesterday';
  return d.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric' });
}

function ActivityRow({ event, onOpen }) {
  const time = event.ts
    ? new Date(event.ts.endsWith('Z') ? event.ts : event.ts + 'Z')
        .toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';
  const statusColor = {
    pending:  'var(--color-warn)',
    approved: 'var(--color-ok)',
    denied:   'var(--color-err)',
    expired:  'var(--color-text-dim)',
    done:     'var(--color-accent)',
  }[event.status] || 'var(--color-text-dim)';

  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 12,
      padding: '10px 12px',
      borderRadius: 'var(--r-md)',
      transition: 'background var(--dur-fast) var(--ease-out)',
      cursor: event.surface ? 'pointer' : 'default',
    }}
      onClick={() => event.surface && onOpen(event.surface)}
      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--color-surface-3)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
    >
      <div style={{
        width: 32, height: 32, borderRadius: 'var(--r-sm)',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 15, flexShrink: 0,
      }}>
        {event.agent_emoji || <Bot size={14} color="var(--color-text-dim)" />}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 2 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text)' }}>
            {event.agent_name}
          </span>
          <span style={{
            fontSize: 9, padding: '1px 7px', borderRadius: 'var(--r-pill)',
            color: 'var(--color-accent)',
            background: 'var(--color-accent-soft)',
            border: '1px solid color-mix(in srgb, var(--color-accent) 22%, transparent)',
            letterSpacing: 0.3,
          }}>
            {event.agent_role_tag}
          </span>
          <span style={{ fontSize: 10, color: statusColor, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            {event.status}
          </span>
          <span style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--color-text-dim)', whiteSpace: 'nowrap' }}>
            {time}
          </span>
        </div>
        <div style={{ fontSize: 12, color: 'var(--color-text)' }}>{event.title}</div>
        {event.summary && (
          <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 2, lineHeight: 1.5 }}>
            {event.summary}
          </div>
        )}
      </div>
      {event.surface && <ExternalLink size={12} color="var(--color-text-dim)" style={{ flexShrink: 0, alignSelf: 'center' }} />}
    </div>
  );
}

function RunsDrawer({ persona, onClose }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let cancelled = false;
    listRuns({ agentKey: persona.agent_key, limit: 50 })
      .then((r) => { if (!cancelled) setRuns(r.runs || []); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [persona.agent_key]);

  const fmt = (iso) => iso ? new Date(iso.endsWith('Z') ? iso : iso + 'Z').toLocaleString() : '—';
  const dur = (r) => {
    if (!r.started_at || !r.finished_at) return '';
    const ms = new Date(r.finished_at + (r.finished_at.endsWith('Z') ? '' : 'Z')) -
               new Date(r.started_at  + (r.started_at.endsWith('Z')  ? '' : 'Z'));
    return ms > 0 ? `${(ms / 1000).toFixed(1)}s` : '';
  };
  const statusColor = (s) => ({
    success: 'var(--color-ok)',
    error:   'var(--color-err)',
    skipped: 'var(--color-text-dim)',
    running: 'var(--color-warn)',
  }[s] || 'var(--color-text-dim)');

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.45)',
        zIndex: 100, display: 'flex', justifyContent: 'flex-end',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="panel"
        style={{
          width: 'min(520px, 94vw)', height: '100%', overflowY: 'auto',
          borderRadius: 0, padding: 20,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
          <div>
            <h3 style={{ margin: 0, fontSize: 15, color: 'var(--color-text)' }}>
              {persona.name} — run history
            </h3>
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 2 }}>
              Last 50 runs, newest first
            </div>
          </div>
          <button className="btn-ghost" onClick={onClose}><X size={14} /></button>
        </div>
        {loading && <div style={{ fontSize: 12, color: 'var(--color-text-dim)' }}>Loading…</div>}
        {!loading && runs.length === 0 && (
          <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
            No runs recorded yet. The agent will log here the next time it runs.
          </div>
        )}
        {runs.map((r) => (
          <div key={r.id} style={{
            padding: '10px 0', borderBottom: '1px solid var(--color-border)',
            display: 'flex', flexDirection: 'column', gap: 4,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span style={{
                fontSize: 10, fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: 0.4, color: statusColor(r.status),
              }}>{r.status}</span>
              <span style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>
                {r.trigger === 'manual' ? 'Run now' : 'Scheduled'}
              </span>
              <span style={{ fontSize: 10, color: 'var(--color-text-dim)', marginLeft: 'auto' }}>
                {fmt(r.started_at)} · {dur(r)}
              </span>
            </div>
            {r.items_produced > 0 && (
              <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                {r.items_produced} item{r.items_produced === 1 ? '' : 's'} produced
              </div>
            )}
            {r.error && (
              <div style={{
                fontSize: 11, color: 'var(--color-err)',
                background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
                padding: '6px 8px', borderRadius: 'var(--r-sm)',
                fontFamily: 'var(--font-mono)', wordBreak: 'break-word',
              }}>
                {r.error}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Agents() {
  const [personas, setPersonas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [activity, setActivity] = useState([]);
  const [activityLoading, setActivityLoading] = useState(true);
  const [runsDrawer, setRunsDrawer] = useState(null);
  const navigate = useNavigate();

  const load = useCallback(async () => {
    setLoading(true); setErr('');
    try { setPersonas(await listPersonas()); }
    catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }, []);

  const loadActivity = useCallback(async () => {
    setActivityLoading(true);
    try { setActivity(await listActivity({ hours: 48, limit: 50 })); }
    catch { /* non-critical */ }
    finally { setActivityLoading(false); }
  }, []);

  useEffect(() => { load(); loadActivity(); }, [load, loadActivity]);

  const onRenamed = (updated) => {
    setPersonas(prev => prev.map(p => p.agent_key === updated.agent_key ? { ...p, ...updated } : p));
  };
  const onEnabledChanged = (updated) => {
    setPersonas(prev => prev.map(p => p.agent_key === updated.agent_key ? { ...p, ...updated } : p));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <h1>Agents</h1>
        <p>Your autonomous team — each agent has a name, a role, and a shift. Rename them anything you like.</p>
      </div>

      <div className="page-body">
        {loading && (
          <div style={{ color: 'var(--color-text-dim)', fontSize: 12, padding: 20 }}>Loading…</div>
        )}
        {err && (
          <div className="panel" style={{ color: 'var(--color-err)', fontSize: 12 }}>{err}</div>
        )}

        {!loading && !err && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 12 }}>
            {personas.map(p => (
              <PersonaCard
                key={p.agent_key}
                persona={p}
                onRenamed={onRenamed}
                onEnabledChanged={onEnabledChanged}
                onOpenSurface={(path) => navigate(path)}
                onRanAgent={() => { loadActivity(); load(); }}
                onOpenRuns={(persona) => setRunsDrawer(persona)}
              />
            ))}
          </div>
        )}

        {/* Activity timeline */}
        <div style={{ marginTop: 22 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, margin: 0, fontSize: 14, color: 'var(--color-text)' }}>
              <Activity size={16} color="var(--color-accent)" />
              Recent activity
              <span style={{ fontSize: 11, color: 'var(--color-text-dim)', fontWeight: 400 }}>
                last 48 hours
              </span>
            </h3>
            <button className="btn-ghost" onClick={loadActivity} disabled={activityLoading}>
              <RotateCcw size={11} style={{ animation: activityLoading ? 'spin 1s linear infinite' : 'none' }} />
              Refresh
            </button>
          </div>

          {activityLoading && activity.length === 0 && (
            <div style={{ color: 'var(--color-text-dim)', fontSize: 12, padding: 12 }}>Loading…</div>
          )}

          {!activityLoading && activity.length === 0 && (
            <div className="panel" style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.55 }}>
              No activity in the last 48 hours. Agents will appear here as they run — Atlas writes the
              briefing each morning, Iris triages email every 15 minutes, Kira and Arjun run daily.
            </div>
          )}

          {activity.length > 0 && (
            <div className="panel" style={{ padding: 12 }}>
              {groupByDay(activity).map(([day, events]) => (
                <div key={day} style={{ marginBottom: 8 }}>
                  <div style={{
                    fontSize: 10, fontWeight: 600, textTransform: 'uppercase',
                    letterSpacing: 0.8, color: 'var(--color-text-dim)',
                    padding: '6px 12px 4px',
                  }}>
                    {dayLabel(day)}
                  </div>
                  {events.map(e => (
                    <ActivityRow key={e.id} event={e} onOpen={(path) => navigate(path)} />
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>

        <div style={{
          marginTop: 18, padding: 14,
          borderRadius: 'var(--r-lg)',
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
          fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.6,
        }}>
          <strong style={{ color: 'var(--color-text)' }}>How this works.</strong>{' '}
          Each agent runs on its own schedule in the background. Anywhere in NexusAgent where
          you see "<span style={{ color: 'var(--color-accent)' }}>Atlas · Chief of staff</span>" or
          similar, it means that specific agent took the action. Rename any of them to match your
          team's vocabulary — they'll keep their role and behaviour, just wear the new name.
        </div>
      </div>

      {runsDrawer && (
        <RunsDrawer persona={runsDrawer} onClose={() => setRunsDrawer(null)} />
      )}
    </div>
  );
}
