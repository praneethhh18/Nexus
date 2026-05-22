import { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useNavigate } from 'react-router-dom';
import { Edit3, Check, X, RotateCcw, Clock, ExternalLink, Loader2, Bot, Activity, Play,
         Pause, PlayCircle, AlertTriangle, ShieldCheck, History, Plus, Sparkles, Settings2 } from 'lucide-react';
import { listPersonas, renamePersona, togglePersonaEnabled, listActivity, runAgent, listRuns } from '../services/agents';
import {
  listCustomAgents, runCustomAgent, getAgentSchedule, setAgentInterval, resetAgentInterval,
} from '../services/customAgents';
import IntervalPicker from '../components/IntervalPicker';
import CustomAgentBuilder from '../components/CustomAgentBuilder';
import CustomAgentGallery from '../components/CustomAgentGallery';

// Per-agent profiles shown in the IDLE state of the run-result modal , 
// so a new user on an empty workspace sees concretely what the agent WILL
// do once there's data, instead of a vague "nothing happened" feeling.
const IDLE_PROFILES = {
  morning_briefing: {
    watches: 'overnight changes in tasks, deals, invoices, and triaged emails.',
    produces: 'a one-page morning briefing delivered to your Inbox at 08:00.',
    example: 'On a busy day: "3 invoices went overdue, Acme moved to negotiation, 2 leads need follow-up."',
  },
  evening_digest: {
    watches: "what closed, sent, or advanced today across CRM, tasks, and billing.",
    produces: "an end-of-day recap delivered to your Inbox at 18:00.",
    example: '"₹2.1L collected today · 1 deal won (Nimbus) · 4 follow-ups completed."',
  },
  invoice_reminder: {
    watches: 'invoices that are past their due date and still unpaid.',
    produces: 'a polite reminder email draft queued for your approval (never auto-sent).',
    example: 'Invoice INV-2026-0007 is 8 days overdue → drafts a "friendly check-in" email to the contact.',
  },
  stale_deal_watcher: {
    watches: 'open deals that haven\'t moved a stage in 14+ days.',
    produces: 'a follow-up task on the contact, tagged "stale-deal", with a suggested next action.',
    example: 'Deal "Acme Q3 Pilot" stuck in "proposal" for 18 days → task: "Nudge Priya on the proposal."',
  },
  meeting_prep: {
    watches: 'meetings on your connected calendar starting in the next 30 minutes.',
    produces: 'a briefing on the contact: recent interactions, open deals, suggested talking points.',
    example: 'Meeting with Priya at 3pm → brief: "Last spoke 6 days ago, 2 open deals worth ₹4.5L, blocker = pricing."',
  },
  email_triage: {
    watches: 'every new email landing in your connected inbox.',
    produces: 'a classification (lead / customer / supplier / spam) + a reply draft for the important ones.',
    example: '"New inquiry from a Bangalore D2C brand asking about pricing" → classified as lead, reply drafted.',
  },
  memory_consolidate: {
    watches: 'your conversation history with the AI and notes added across the workspace.',
    produces: 'a refined long-term memory the AI uses for future context.',
    example: 'After a week: distils dozens of chats into "User runs a SaaS analytics firm, key clients are X/Y/Z, prefers WhatsApp."',
  },
  outbound_caller: {
    watches: 'manual queue of contacts you want Vox to call (or a workflow trigger).',
    produces: 'a real phone call following your script + a structured summary filed on the contact.',
    example: 'Queue a "follow up on quote" call → Vox dials, has a short conversation, logs outcome.',
  },
};


// Per-agent result formatter, turns the raw `detail` from the backend into
// a structured object the card can render clearly. Returns:
//   { tone: 'success' | 'skip' | 'idle' | 'info',
//     summary: 'one-line human result',
//     details: 'optional second line',
//     hint:    'optional fix hint (e.g. connect inbox in Settings)',
//     link:    { label, href } | null }
//
// The previous implementation looked for fields that didn't exist on half
// the agents, so the user just saw "Done." with no idea what happened.
function formatAgentResult(agentKey, d) {
  d = d || {};
  // Vox has a dedicated case below, let it own its skip story.
  if (agentKey === 'outbound_caller') {
    return {
      tone: 'info',
      summary: 'Vox makes real outbound calls.',
      hint: 'Add a contact with a phone number, then queue a call from the Vox console.',
      link: { label: 'Open Vox', href: '/agents/vox' },
    };
  }
  // Common "skipped because X isn't connected" pattern, surface the
  // reason + a hint pointing the user at where to set it up.
  if (d.skipped) {
    const skipMap = {
      'no_account':    { msg: "No email account connected yet.",
                         hint: "Connect a Gmail/Outlook inbox in Integrations to enable email triage." },
      'not connected': { msg: "Calendar not connected yet.",
                         hint: "Connect Google Calendar in Integrations to enable meeting prep." },
    };
    const k = skipMap[d.skipped];
    return {
      tone: 'skip',
      summary: k ? k.msg : `Skipped: ${d.skipped}`,
      hint: k ? k.hint : undefined,
      link: k ? { label: 'Open Integrations', href: '/integrations' } : null,
    };
  }

  switch (agentKey) {
    case 'morning_briefing': {
      const ch = (d.delivered || []).filter(Boolean);
      return {
        tone: 'success',
        summary: `Briefing ready${d.narrative_mode ? ` (${d.narrative_mode})` : ''}`,
        details: ch.length ? `Delivered: ${ch.join(', ')}` : undefined,
        link: { label: 'Open Inbox', href: '/inbox' },
      };
    }
    case 'evening_digest': {
      const ch = (d.delivered || []).filter(Boolean);
      return {
        tone: 'success',
        summary: `Evening recap ready${d.narrative_mode ? ` (${d.narrative_mode})` : ''}`,
        details: ch.length ? `Delivered: ${ch.join(', ')}` : undefined,
        link: { label: 'Open Inbox', href: '/inbox' },
      };
    }
    case 'invoice_reminder': {
      const cand = Number(d.candidates || 0);
      const queued = Number(d.queued || 0);
      if (cand === 0 && queued === 0) {
        return { tone: 'idle', summary: 'No invoices need chasing right now.' };
      }
      return {
        tone: 'success',
        summary: `Checked ${cand} invoice${cand === 1 ? '' : 's'} · drafted ${queued} reminder${queued === 1 ? '' : 's'}`,
        link: queued > 0 ? { label: 'Review in Inbox', href: '/inbox' } : null,
      };
    }
    case 'stale_deal_watcher': {
      const stale = Number(d.stale_deals || 0);
      const created = Number(d.created || 0);
      if (stale === 0) {
        return { tone: 'idle', summary: 'No stale deals, pipeline is healthy.' };
      }
      return {
        tone: 'success',
        summary: `Found ${stale} stale deal${stale === 1 ? '' : 's'}`,
        details: created > 0 ? `Created ${created} follow-up task${created === 1 ? '' : 's'}` : undefined,
        link: created > 0 ? { label: 'Open Tasks', href: '/tasks' } : null,
      };
    }
    case 'meeting_prep': {
      const pushed = Number(d.pushed || 0);
      if (pushed === 0) {
        return { tone: 'idle', summary: 'No upcoming meetings need prep right now.' };
      }
      return {
        tone: 'success',
        summary: `Prepped ${pushed} meeting${pushed === 1 ? '' : 's'}`,
        link: { label: 'Open Inbox', href: '/inbox' },
      };
    }
    case 'email_triage': {
      const proc = Number(d.processed || 0);
      if (proc === 0) {
        return { tone: 'idle', summary: 'Inbox already clean, nothing new to triage.' };
      }
      return {
        tone: 'success',
        summary: `Triaged ${proc} email${proc === 1 ? '' : 's'}`,
        link: { label: 'Open Inbox', href: '/inbox' },
      };
    }
    case 'memory_consolidate': {
      if (d.applied === false) {
        return {
          tone: 'idle',
          summary: 'Nothing to consolidate yet.',
          details: d.reason || 'Comes alive after a few days of conversation history.',
        };
      }
      return {
        tone: 'success',
        summary: 'Business memory updated.',
        details: d.entries_consolidated ? `${d.entries_consolidated} entries merged` : undefined,
        link: { label: 'View Memory', href: '/memory' },
      };
    }
    case 'outbound_caller': {
      return {
        tone: 'info',
        summary: 'Vox makes real outbound calls.',
        hint: 'Add a contact with a phone number, then queue a call from the Vox console.',
        link: { label: 'Open Vox', href: '/agents/vox' },
      };
    }
    default:
      return { tone: 'success', summary: 'Done.' };
  }
}


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

function PersonaCard({ persona, schedule, onRenamed, onEnabledChanged, onIntervalChanged, onOpenSurface, onRanAgent, onOpenRuns }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(persona.name);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [running, setRunning] = useState(false);
  // Structured run result: { summary, tone, details, hint, link } | null
  const [runResult, setRunResult] = useState(null);
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

  // eslint-disable-next-line react-hooks/set-state-in-effect
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
    setRunning(true); setRunResult(null); setErr('');
    try {
      const r = await runAgent(persona.agent_key);
      // Stash the raw detail too, the modal renders the actual artifact
      // (briefing text, list of stale deals, etc.) so the user sees proof
      // of work instead of guessing what happened.
      const formatted = formatAgentResult(persona.agent_key, r.detail || {});
      setRunResult({ ...formatted, detail: r.detail || {} });
      onRanAgent?.();
    } catch (e) {
      console.error(`[Agents] ${persona.agent_key} failed:`, e);
      // Show the error as a result modal too, so the user always gets a
      // visible response, never just a silent flash-and-disappear.
      setRunResult({
        tone: 'skip',
        summary: 'Run failed',
        details: e.message || 'The agent could not complete. See console for details.',
        hint: 'If this keeps happening, the backend may be down or your session expired, try logging out and back in.',
        detail: {},
      });
      setErr(e.message || 'Run failed');
    } finally {
      setRunning(false);
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
      {/* Header, avatar + name + role */}
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
            {persona.is_custom && <>You renamed, default is <em>{persona.default_name}</em> · </>}
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
        {persona.agent_key === 'outbound_caller' && (
          <button
            onClick={() => onOpenSurface('/agents/vox')}
            className="btn-ghost"
            style={{ fontSize: 11, padding: '6px 10px' }}
            title="Open Vox console, pending dials, usage, recent calls"
          >
            <ExternalLink size={11} /> View
          </button>
        )}
        <LastRunChip lastRun={persona.last_run} stats24h={persona.run_stats_24h} />
        {schedule && (
          <IntervalPicker
            value={schedule.interval_minutes}
            defaultValue={schedule.default_minutes}
            onChange={(n) => onIntervalChanged?.(persona.agent_key, n)}
            onReset={() => onIntervalChanged?.(persona.agent_key, null)}
          />
        )}
      </div>

      {runResult && (
        <AgentResultModal
          agentKey={persona.agent_key}
          agentName={persona.name}
          emoji={persona.emoji}
          result={runResult}
          onClose={() => setRunResult(null)}
          onOpenSurface={onOpenSurface}
        />
      )}

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

// Parse a backend ISO timestamp robustly. Backend sends a mix of:
//   "2026-05-03T19:23:45.123456"        (naive, assume UTC, append Z)
//   "2026-05-03T19:23:45.123456+00:00"  (explicit offset, leave alone)
//   "2026-05-03T19:23:45Z"              (Zulu, leave alone)
// Old code blindly appended Z to the second form which produced the
// notorious "Invalid Date" rendering on the activity feed.
function parseTs(ts) {
  if (!ts) return '';
  // Already has explicit timezone info? Use as-is.
  if (/Z$|[+-]\d{2}:?\d{2}$/.test(ts)) return ts;
  // Naive ISO, treat as UTC.
  return ts + 'Z';
}

function groupByDay(events) {
  const groups = new Map();
  for (const e of events) {
    const d = e.ts ? new Date(parseTs(e.ts)) : null;
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

  const fmt = (iso) => iso ? new Date(parseTs(iso)).toLocaleString() : ', ';
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
              {persona.name}, run history
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

// ── Custom-agent card ─────────────────────────────────────────────────────
// Cloned-template or user-built agent. Same result-modal treatment as the
// built-in personas so clicking "Run now" never feels like a dead click.
function CustomAgentCard({ agent, onRan, onEdit }) {
  const ca = agent;
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState('');
  const navigate = useNavigate();

  const run = async () => {
    if (running) return;
    setRunning(true); setResult(null); setErr('');
    try {
      const r = await runCustomAgent(ca.id);
      // Backend returns: { ok, reason?, agent_id, answer, tool_calls, run_id, budget? }
      if (r.ok === false && r.reason === 'disabled') {
        setResult({
          tone: 'skip',
          summary: 'Agent is paused.',
          hint: 'Enable the agent from its Edit panel before running.',
          detail: r,
        });
      } else if (r.ok === false && r.reason === 'local_fallback_refused') {
        // Cloud token cap hit; local Ollama fallback can't reliably do tool
        // calling and refused. The answer text is usually a stock "I'm a
        // text-based AI…" line, show that with the real cause.
        const used = r.budget?.tokens_used;
        const cap  = r.budget?.tokens_cap;
        setResult({
          tone: 'skip',
          summary: 'Cloud budget exhausted, fell back to local model.',
          details: `Today's cloud usage: ${used ? used.toLocaleString() : '?'} / ${cap ? cap.toLocaleString() : '?'} tokens. ` +
                   `The local fallback model couldn't drive tools so the agent answered as a chatbot instead of doing its job.`,
          hint: 'Raise the cap with the CLOUD_TOKEN_DAILY_CAP env var (set it to 0 to disable) and restart the backend. The cloud Mistral 14B handles tool-calling correctly.',
          customAnswer: r.answer || '',
          customTools: r.tool_calls || [],
          detail: r,
        });
      } else if (r.ok === false && r.reason === 'no_tools_called') {
        setResult({
          tone: 'skip',
          summary: "Agent didn't call any tools.",
          details: 'The agent had tools available but chose not to use them. Often this means the goal prompt is too vague or the model misunderstood it.',
          hint: "Click Edit and tighten the goal, e.g. 'Use search_knowledge with category=competitor to find pricing changes' rather than 'check competitor pricing'.",
          customAnswer: r.answer || '',
          customTools: r.tool_calls || [],
          detail: r,
        });
      } else if (r.ok === false) {
        setResult({
          tone: 'skip',
          summary: 'Run failed',
          details: r.error || 'The agent loop returned an error.',
          detail: r,
        });
      } else {
        const tools = (r.tool_calls || []).map(t => t.name || t.tool || '');
        const fellBack = r.budget?.fell_back_to_local;
        setResult({
          tone: 'success',
          summary: `${ca.name} just ran`,
          details: (tools.length ? `Called ${tools.length} tool${tools.length === 1 ? '' : 's'}: ${tools.join(', ')}`
                                 : 'No tools needed, answered from context.')
                   + (fellBack ? ' (ran on local model, cloud budget hit)' : ''),
          link: ca.output_target === 'inbox' ? { label: 'Open Inbox', href: '/inbox' } : null,
          customAnswer: r.answer || '',
          customTools: r.tool_calls || [],
          detail: r,
        });
      }
      onRan?.();
    } catch (e) {
      console.error(`[CustomAgents] ${ca.name} failed:`, e);
      setResult({
        tone: 'skip',
        summary: 'Run failed',
        details: e.message || 'See console for details.',
        hint: 'If this keeps happening, the backend may be down or the agent goal needs more tools.',
        detail: {},
      });
      setErr(e.message || 'Run failed');
    } finally {
      setRunning(false);
    }
  };

  const fmtSchedule = (m) => m < 60 ? `${m} min`
    : m % 1440 === 0 ? `${m / 1440} d`
    : m % 60 === 0 ? `${m / 60} hr`
    : `${m} min`;

  return (
    <div className="panel" style={{
      padding: 16, display: 'flex', flexDirection: 'column', gap: 10,
      opacity: ca.enabled ? 1 : 0.6,
      borderStyle: ca.enabled ? 'solid' : 'dashed',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 22 }}>{ca.emoji || '🤖'}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>{ca.name}</div>
          <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>
            {ca.description || <em>No description</em>}
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
        <button
          onClick={run}
          className="btn-primary"
          style={{ fontSize: 11, padding: '5px 12px' }}
          disabled={!ca.enabled || running}
        >
          {running
            ? <><Loader2 size={10} style={{ animation: 'spin 1s linear infinite' }} /> Working…</>
            : <><Play size={10} /> Run now</>}
        </button>
        <button onClick={onEdit} className="btn-ghost" style={{ fontSize: 11, padding: '5px 10px' }}>
          <Settings2 size={10} /> Edit
        </button>
      </div>
      <div style={{ fontSize: 10, color: 'var(--color-text-dim)', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <span><Clock size={9} style={{ verticalAlign: 'middle' }} /> every {fmtSchedule(ca.interval_minutes)}</span>
        <span>→ {ca.output_target}</span>
        <span>· {ca.tool_whitelist.length} tool{ca.tool_whitelist.length === 1 ? '' : 's'}</span>
      </div>
      {err && <div style={{ fontSize: 11, color: 'var(--color-err)' }}>{err}</div>}

      {result && (
        <AgentResultModal
          agentKey={`custom:${ca.id}`}
          agentName={ca.name}
          emoji={ca.emoji || '🤖'}
          result={result}
          onClose={() => setResult(null)}
          onOpenSurface={(path) => navigate(path)}
        />
      )}
    </div>
  );
}


// ── Run-result modal ─────────────────────────────────────────────────────────
// Shown after the user clicks "Run now". The point is to give NEW USERS
// proof-of-work, show the actual artifact (briefing text, list of stale
// deals, etc.) inline, not just a "Done." toast. For skipped agents this
// becomes an inline setup CTA instead of a confusing dead-end.
function AgentResultModal({ agentKey, agentName, emoji, result, onClose, onOpenSurface }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose?.(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const tone = result.tone || 'success';
  const accent = tone === 'success' ? 'var(--color-ok)'
               : tone === 'skip'    ? 'var(--color-warn)'
               : tone === 'info'    ? 'var(--color-info)'
                                    : 'var(--color-text-dim)';

  // Render via portal directly into document.body so the fixed-position
  // backdrop can't be clipped by any ancestor with transform/filter/
  // overflow CSS (e.g. the card's transition: transform creates a
  // containing block in some browsers).
  return createPortal((
    <div onClick={onClose}
         style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)',
                  zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  padding: 20 }}>
      <div onClick={(e) => e.stopPropagation()}
           style={{
             background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)',
             borderRadius: 14, padding: 22, width: 640, maxWidth: '100%',
             maxHeight: '85vh', overflow: 'auto',
             boxShadow: '0 24px 56px rgba(0,0,0,0.55)',
           }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: 14 }}>
          <div style={{
            width: 42, height: 42, borderRadius: 10,
            background: 'color-mix(in srgb, var(--color-accent) 14%, transparent)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 22, flexShrink: 0,
          }}>{emoji || <Bot size={20} />}</div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)', letterSpacing: 0.5,
                          textTransform: 'uppercase', fontWeight: 700, marginBottom: 2 }}>
              {agentName} just ran
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              {tone === 'success' && <Check size={16} color={accent} />}
              {tone === 'skip'    && <AlertTriangle size={16} color={accent} />}
              {tone === 'info'    && <Activity size={16} color={accent} />}
              <span style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text)' }}>
                {result.summary}
              </span>
            </div>
            {result.details && (
              <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)', marginTop: 4, lineHeight: 1.5 }}>
                {result.details}
              </div>
            )}
          </div>
          <button onClick={onClose}
                  style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)',
                           cursor: 'pointer', flexShrink: 0 }}>
            <X size={18} />
          </button>
        </div>

        {/* The actual artifact, rendered inline */}
        <AgentArtifact agentKey={agentKey} result={result} onOpenSurface={onOpenSurface} />

        {/* Skip hint, when there's nothing to show, explain why + how to fix */}
        {result.hint && tone !== 'success' && (
          <div style={{
            marginTop: 14, padding: '10px 12px',
            background: 'color-mix(in srgb, ' + accent + ' 8%, transparent)',
            border: '1px solid color-mix(in srgb, ' + accent + ' 30%, transparent)',
            borderRadius: 'var(--r-md)',
            fontSize: 12.5, color: 'var(--color-text)', lineHeight: 1.55,
          }}>
            <div style={{ fontWeight: 600, marginBottom: 4 }}>What's missing</div>
            {result.hint}
          </div>
        )}

        {/* Action buttons */}
        <div style={{ display: 'flex', gap: 8, marginTop: 18, flexWrap: 'wrap' }}>
          {result.link && (
            <button type="button" className="btn-primary"
                    onClick={() => { onOpenSurface(result.link.href); onClose(); }}>
              {result.link.label} <ExternalLink size={12} />
            </button>
          )}
          <button type="button" className="btn-ghost" onClick={onClose} style={{ marginLeft: 'auto' }}>
            Close
          </button>
        </div>
      </div>
    </div>
  ), document.body);
}


// Per-agent artifact renderer, shows the actual content the agent produced.
// New users see proof of work inline; they don't have to hunt for the
// briefing in another tab.
function AgentArtifact({ agentKey, result }) {
  const d = result.detail || {};

  // Custom-agent answer, render the LLM's reply + which tools it called
  // so the user can see exactly what the agent did.
  if (agentKey?.startsWith?.('custom:') && result.customAnswer) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div style={{
          padding: '14px 16px', borderRadius: 'var(--r-md)',
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
          fontSize: 13, color: 'var(--color-text)', lineHeight: 1.55,
          whiteSpace: 'pre-wrap',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          maxHeight: 360, overflow: 'auto',
        }}>
          {result.customAnswer}
        </div>
        {(result.customTools || []).length > 0 && (
          <div style={{
            padding: '10px 12px', borderRadius: 8,
            background: 'var(--color-bg)',
            border: '1px solid var(--color-border)',
            fontSize: 11,
          }}>
            <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 0.5,
                          textTransform: 'uppercase', color: 'var(--color-text-dim)',
                          marginBottom: 4 }}>
              Tools used during this run
            </div>
            <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
              {(result.customTools || []).map((t, i) => (
                <code key={i} style={{
                  fontSize: 10, padding: '2px 6px', borderRadius: 4,
                  background: 'var(--color-surface-1)', color: 'var(--color-text)',
                  border: '1px solid var(--color-border)',
                }}>
                  {t.name || t.tool || '(unknown)'}
                </code>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Briefing-style agents, render the narrative text
  if ((agentKey === 'morning_briefing' || agentKey === 'evening_digest') && d.narrative) {
    return (
      <div style={{
        padding: '14px 16px', borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        fontSize: 13, color: 'var(--color-text)', lineHeight: 1.6,
        whiteSpace: 'pre-wrap',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        maxHeight: 360, overflow: 'auto',
      }}>
        {d.narrative}
      </div>
    );
  }

  // Stale-deal watcher, show how many + a "what now" line
  if (agentKey === 'stale_deal_watcher' && Number(d.stale_deals || 0) > 0) {
    return (
      <div style={{
        padding: '14px 16px', borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        fontSize: 13, color: 'var(--color-text)', lineHeight: 1.6,
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          <div style={{ padding: 10, borderRadius: 8, background: 'var(--color-bg)' }}>
            <div style={{ fontSize: 10, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 700 }}>Stale deals</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-warn)' }}>{d.stale_deals}</div>
          </div>
          <div style={{ padding: 10, borderRadius: 8, background: 'var(--color-bg)' }}>
            <div style={{ fontSize: 10, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 700 }}>Follow-up tasks created</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-ok)' }}>{d.created || 0}</div>
          </div>
        </div>
        <div style={{ marginTop: 10, fontSize: 12, color: 'var(--color-text-muted)' }}>
          Open Tasks to see the new follow-ups Arjun added for each stale deal.
        </div>
      </div>
    );
  }

  // Invoice reminder, show how many were drafted
  if (agentKey === 'invoice_reminder' && Number(d.queued || 0) > 0) {
    return (
      <div style={{
        padding: '14px 16px', borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        fontSize: 13, color: 'var(--color-text)', lineHeight: 1.6,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div>
            <div style={{ fontSize: 10, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 700 }}>Invoices checked</div>
            <div style={{ fontSize: 22, fontWeight: 700 }}>{d.candidates || 0}</div>
          </div>
          <div>
            <div style={{ fontSize: 10, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 700 }}>Reminders drafted</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--color-accent)' }}>{d.queued}</div>
          </div>
        </div>
        <div style={{ marginTop: 10, fontSize: 12, color: 'var(--color-text-muted)' }}>
          Drafts wait for your approval in Inbox before going out.
        </div>
      </div>
    );
  }

  // Email triage results, show how many got triaged
  if (agentKey === 'email_triage' && Number(d.processed || 0) > 0) {
    return (
      <div style={{
        padding: '14px 16px', borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        fontSize: 13, color: 'var(--color-text)',
      }}>
        <div style={{ fontSize: 22, fontWeight: 700, color: 'var(--color-ok)' }}>
          {d.processed} email{d.processed === 1 ? '' : 's'} triaged
        </div>
        <div style={{ marginTop: 4, fontSize: 12, color: 'var(--color-text-muted)' }}>
          Reply drafts (if any) are queued for your approval in Inbox.
        </div>
      </div>
    );
  }

  // Meeting prep, show pushed count
  if (agentKey === 'meeting_prep' && Number(d.pushed || 0) > 0) {
    return (
      <div style={{
        padding: '14px 16px', borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        fontSize: 13, color: 'var(--color-text)',
      }}>
        <div style={{ fontSize: 22, fontWeight: 700 }}>
          {d.pushed} meeting brief{d.pushed === 1 ? '' : 's'} ready
        </div>
        <div style={{ marginTop: 4, fontSize: 12, color: 'var(--color-text-muted)' }}>
          Each brief covers the contact's recent interactions, open deals, and suggested talking points.
        </div>
      </div>
    );
  }

  // "Idle" / nothing-to-do case, explain what the agent WATCHES for and
  // what it'll DO when it finds something, so new users on an empty
  // workspace see real value rather than a hollow "nothing happened".
  if (result.tone === 'idle') {
    const profile = IDLE_PROFILES[agentKey] || {
      watches: 'changes in your workspace',
      produces: 'a tagged item in the relevant queue',
      example: ', ',
    };
    return (
      <div style={{
        padding: '18px 16px', borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <div style={{ fontSize: 26 }}>🌱</div>
          <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
            Nothing to act on right now, that's healthy.
            This agent runs on a schedule and will surface work the moment something changes.
          </div>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
          <div style={{
            padding: 10, borderRadius: 8, background: 'var(--color-bg)',
            border: '1px solid var(--color-border)',
          }}>
            <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 0.5,
                          textTransform: 'uppercase', color: 'var(--color-text-dim)',
                          marginBottom: 4 }}>What I watch for</div>
            <div style={{ fontSize: 11.5, color: 'var(--color-text)', lineHeight: 1.45 }}>
              {profile.watches}
            </div>
          </div>
          <div style={{
            padding: 10, borderRadius: 8, background: 'var(--color-bg)',
            border: '1px solid var(--color-border)',
          }}>
            <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: 0.5,
                          textTransform: 'uppercase', color: 'var(--color-text-dim)',
                          marginBottom: 4 }}>What I do</div>
            <div style={{ fontSize: 11.5, color: 'var(--color-text)', lineHeight: 1.45 }}>
              {profile.produces}
            </div>
          </div>
        </div>
        {profile.example && (
          <div style={{
            marginTop: 10, padding: '8px 10px', borderRadius: 6,
            fontSize: 11, color: 'var(--color-text-muted)',
            background: 'color-mix(in srgb, var(--color-accent) 6%, transparent)',
            border: '1px dashed color-mix(in srgb, var(--color-accent) 25%, transparent)',
            lineHeight: 1.5,
          }}>
            <b style={{ color: 'var(--color-text)' }}>Example: </b>
            {profile.example}
          </div>
        )}
      </div>
    );
  }

  // Vox, special-cased contact-pick CTA could go here later
  if (agentKey === 'outbound_caller') {
    return (
      <div style={{
        padding: '14px 16px', borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        fontSize: 13, color: 'var(--color-text-muted)', lineHeight: 1.6,
      }}>
        Vox is your outbound caller. Once a contact has a phone number, you can
        queue a real call from the Vox console, Vox will dial, have a short
        conversation following a script, and file a summary on the contact.
      </div>
    );
  }

  // Default fallback, nothing to render beyond the header summary
  return null;
}


export default function Agents() {
  const [personas, setPersonas] = useState([]);
  const [scheduleByKey, setScheduleByKey] = useState({});
  const [customAgents, setCustomAgentsList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [activity, setActivity] = useState([]);
  const [activityLoading, setActivityLoading] = useState(true);
  const [runsDrawer, setRunsDrawer] = useState(null);
  const [builderInitial, setBuilderInitial] = useState(null);
  const [showBuilder, setShowBuilder] = useState(false);
  const [showGallery, setShowGallery] = useState(false);
  const navigate = useNavigate();

  // `silent`: skip the loading-flag dance on background refreshes (e.g.
  // after Run Now). Otherwise the loading flag flips to true, the
  // {!loading && ...} render branch unmounts every PersonaCard, and any
  // local state (including a freshly-set result modal) is wiped before
  // the user can see it.
  const load = useCallback(async ({ silent = false } = {}) => {
    if (!silent) setLoading(true);
    setErr('');
    try {
      const [ppl, sch, ca] = await Promise.all([
        listPersonas(),
        getAgentSchedule().catch(() => ({ schedule: [] })),
        listCustomAgents().catch(() => []),
      ]);
      setPersonas(ppl);
      const byKey = {};
      for (const s of (sch.schedule || [])) byKey[s.agent_key] = s;
      setScheduleByKey(byKey);
      setCustomAgentsList(ca);
    } catch (e) { setErr(e.message); }
    finally { if (!silent) setLoading(false); }
  }, []);

  const loadActivity = useCallback(async () => {
    setActivityLoading(true);
    try { setActivity(await listActivity({ hours: 48, limit: 50 })); }
    catch { /* non-critical */ }
    finally { setActivityLoading(false); }
  }, []);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load(); loadActivity(); }, [load, loadActivity]);

  const onRenamed = (updated) => {
    setPersonas(prev => prev.map(p => p.agent_key === updated.agent_key ? { ...p, ...updated } : p));
  };
  const onEnabledChanged = (updated) => {
    setPersonas(prev => prev.map(p => p.agent_key === updated.agent_key ? { ...p, ...updated } : p));
  };

  const onIntervalChanged = async (agent_key, minutes) => {
    try {
      const r = minutes == null
        ? await resetAgentInterval(agent_key)
        : await setAgentInterval(agent_key, minutes);
      setScheduleByKey(prev => ({ ...prev, [agent_key]: r }));
    } catch (e) {
      alert(`Couldn't save: ${e.message}`);
    }
  };

  // Custom-agent runs now happen INSIDE each CustomAgentCard so it can
  // own a result modal the same way PersonaCard does. The parent only
  // needs to know how to refresh the lists after a successful run.
  const onCustomRanRefresh = () => { loadActivity(); load({ silent: true }); };

  const onCustomSaved = (saved) => {
    setShowBuilder(false);
    setBuilderInitial(null);
    load();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Agents</h1>
          <p>Your autonomous team, each agent has a name, a role, and a shift. Rename them anything you like.</p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn-ghost" onClick={() => setShowGallery(true)} title="Start from a template">
            <Sparkles size={13} /> Templates
          </button>
          <button
            className="btn-primary"
            onClick={() => { setBuilderInitial(null); setShowBuilder(true); }}
            title="Build a custom agent from scratch"
          >
            <Plus size={13} /> New custom agent
          </button>
        </div>
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
                schedule={scheduleByKey[p.agent_key]}
                onRenamed={onRenamed}
                onEnabledChanged={onEnabledChanged}
                onIntervalChanged={onIntervalChanged}
                onOpenSurface={(path) => navigate(path)}
                onRanAgent={() => { loadActivity(); load({ silent: true }); }}
                onOpenRuns={(persona) => setRunsDrawer(persona)}
              />
            ))}
          </div>
        )}

        {/* Custom agents (user-built) */}
        {!loading && customAgents.length > 0 && (
          <div style={{ marginTop: 22 }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, margin: 0, fontSize: 14, color: 'var(--color-text)', marginBottom: 10 }}>
              <Sparkles size={15} color="var(--color-accent)" />
              Custom agents
              <span style={{ fontSize: 11, color: 'var(--color-text-dim)', fontWeight: 400 }}>
                built by you
              </span>
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 12 }}>
              {customAgents.map(ca => (
                <CustomAgentCard
                  key={ca.id}
                  agent={ca}
                  onRan={onCustomRanRefresh}
                  onEdit={() => { setBuilderInitial(ca); setShowBuilder(true); }}
                />
              ))}
            </div>
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
              No activity in the last 48 hours. Agents will appear here as they run, Atlas writes the
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
          team's vocabulary, they'll keep their role and behaviour, just wear the new name.
        </div>
      </div>

      {runsDrawer && (
        <RunsDrawer persona={runsDrawer} onClose={() => setRunsDrawer(null)} />
      )}
      {showBuilder && (
        <CustomAgentBuilder
          initial={builderInitial}
          onClose={() => { setShowBuilder(false); setBuilderInitial(null); }}
          onSaved={onCustomSaved}
        />
      )}
      {showGallery && (
        <CustomAgentGallery
          onClose={() => setShowGallery(false)}
          onCreated={() => { setShowGallery(false); load(); }}
        />
      )}
    </div>
  );
}
