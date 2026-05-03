/**
 * Vox agent page · /agents/vox
 *
 * Three sections, top→bottom:
 *   1. Pending dials queue   — /api/approvals filtered to tool_name=vox_dial
 *      with Approve / Deny buttons.
 *   2. Today's usage strip   — /api/vox/usage; minutes used / cap, calls today.
 *      Yellow warning when ≥80% of cap.
 *   3. Recent calls          — /api/vox/calls; expand to view transcript.
 */
import { useState, useEffect, useCallback } from 'react';
import {
  Phone, PhoneCall, PhoneOff, Loader2, Clock, ChevronDown, ChevronRight,
  CheckCircle2, XCircle, AlertTriangle, Mic, RefreshCw,
} from 'lucide-react';
import {
  listRecentCalls, getCall, getUsage, listPendingDials,
  approveDial, rejectDial,
} from '../services/vox';

// ── Helpers ────────────────────────────────────────────────────────────────
function formatWhen(iso) {
  if (!iso) return '';
  try {
    const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z');
    const mins = Math.floor((Date.now() - d.getTime()) / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    if (mins < 1440) return `${Math.floor(mins / 60)}h ago`;
    return `${Math.floor(mins / 1440)}d ago`;
  } catch { return iso.slice(0, 16); }
}

function formatDuration(sec) {
  if (sec == null) return '—';
  if (sec < 60) return `${sec}s`;
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return s ? `${m}m ${s}s` : `${m}m`;
}

// Outcome → color tone for badges
const OUTCOME_TONES = {
  answered_interested: { color: 'var(--color-ok)', label: 'Interested' },
  answered_declined:   { color: 'var(--color-warn)', label: 'Declined' },
  voicemail:           { color: 'var(--color-text-dim)', label: 'Voicemail' },
  no_answer:           { color: 'var(--color-text-dim)', label: 'No answer' },
  wrong_number:        { color: 'var(--color-warn)', label: 'Wrong number' },
  dnc_request:         { color: 'var(--color-err)', label: 'Do not call' },
  call_failed:         { color: 'var(--color-err)', label: 'Failed' },
};


function OutcomeBadge({ outcome }) {
  const t = OUTCOME_TONES[outcome] || { color: 'var(--color-text-dim)', label: outcome || '—' };
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      padding: '2px 8px', borderRadius: 'var(--r-pill)',
      fontSize: 10, fontWeight: 700, letterSpacing: 0.4,
      color: t.color,
      background: `color-mix(in srgb, ${t.color} 12%, transparent)`,
      border: `1px solid color-mix(in srgb, ${t.color} 30%, transparent)`,
    }}>{t.label}</span>
  );
}


// ── Section 1: pending dials queue ─────────────────────────────────────────
function PendingDialsQueue({ pending, onAction, busy }) {
  if (pending.length === 0) {
    return (
      <div style={{
        padding: 14, borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-2)',
        border: '1px dashed var(--color-border)',
        color: 'var(--color-text-dim)', fontSize: 13, textAlign: 'center',
      }}>
        No dials waiting for approval. Vox will queue actions here when triggered.
      </div>
    );
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {pending.map((a) => {
        const args = a.args || {};
        return (
          <div key={a.id} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
            padding: 12, borderRadius: 'var(--r-md)',
            background: 'var(--color-surface-2)',
            border: '1px solid color-mix(in srgb, var(--color-warn) 30%, transparent)',
          }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 3 }}>
                <PhoneCall size={13} color="var(--color-warn)" />
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>
                  {a.summary || `Dial contact ${args.contact_id || '?'}`}
                </span>
              </div>
              <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
                Queued {formatWhen(a.created_at)} · purpose: {args.purpose || '—'}
              </div>
            </div>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                className="btn-primary"
                disabled={busy === a.id}
                onClick={() => onAction(a.id, 'approve')}
              >
                {busy === a.id ? <Loader2 size={11} className="spin" /> : <CheckCircle2 size={11} />}
                Approve
              </button>
              <button
                className="btn-ghost"
                disabled={busy === a.id}
                onClick={() => onAction(a.id, 'reject')}
                style={{ color: 'var(--color-err)' }}
              >
                <XCircle size={11} /> Deny
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}


// ── Section 2: today's usage strip ─────────────────────────────────────────
function UsageStrip({ usage }) {
  if (!usage) return null;
  const minsUsed = usage.minutes_used || 0;
  const cap = usage.cap_minutes || 0;
  const pct = cap > 0 ? Math.min(100, (minsUsed / cap) * 100) : 0;
  const warn = cap > 0 && pct >= 80;
  const tone = warn ? 'var(--color-warn)' : 'var(--color-accent)';

  return (
    <div style={{
      padding: 14, borderRadius: 'var(--r-md)',
      background: 'var(--color-surface-2)',
      border: `1px solid color-mix(in srgb, ${tone} 25%, transparent)`,
      display: 'flex', flexDirection: 'column', gap: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Clock size={13} color={tone} />
          <span style={{ fontSize: 12, fontWeight: 700, letterSpacing: 0.4, color: 'var(--color-text)' }}>
            TODAY · {usage.day_iso}
          </span>
          {warn && (
            <span title="80% of daily cap used"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: 3,
                           fontSize: 10, color: 'var(--color-warn)' }}>
              <AlertTriangle size={10} /> Approaching cap
            </span>
          )}
        </div>
        <div style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
          ${(usage.est_cost_usd || (minsUsed * 0.20)).toFixed(2)} est · {usage.calls || usage.calls_count || 0} calls
        </div>
      </div>
      <div>
        <div style={{
          height: 8, borderRadius: 4,
          background: 'var(--color-surface-1)',
          overflow: 'hidden', position: 'relative',
        }}>
          <div style={{
            position: 'absolute', inset: 0, width: `${pct}%`,
            background: tone, transition: 'width 200ms ease-out',
          }} />
        </div>
        <div style={{
          display: 'flex', justifyContent: 'space-between',
          marginTop: 4, fontSize: 11, color: 'var(--color-text-dim)',
        }}>
          <span>{minsUsed.toFixed(1)} min used</span>
          <span>{cap > 0 ? `cap ${cap.toFixed(0)} min/day` : 'no cap'}</span>
        </div>
      </div>
    </div>
  );
}


// ── Section 3: recent calls list ───────────────────────────────────────────
function CallRow({ call, onExpand, expanded, detail }) {
  const summary = (detail && detail.summary) || {};
  return (
    <div style={{
      borderRadius: 'var(--r-md)',
      background: 'var(--color-surface-2)',
      border: '1px solid var(--color-border)',
    }}>
      <button
        onClick={() => onExpand(call.call_id)}
        style={{
          width: '100%', textAlign: 'left',
          display: 'flex', alignItems: 'center', gap: 10,
          padding: 10, background: 'transparent', border: 'none',
          cursor: 'pointer', color: 'var(--color-text)',
        }}
      >
        {expanded
          ? <ChevronDown size={13} color="var(--color-text-dim)" />
          : <ChevronRight size={13} color="var(--color-text-dim)" />}
        <Phone size={13} color="var(--color-accent)" />
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2 }}>
            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)', whiteSpace: 'nowrap',
                           overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {call.headline || `Call ${(call.call_id || '').slice(0, 12)}`}
            </span>
            <OutcomeBadge outcome={call.outcome} />
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
            {formatWhen(call.started_at)} · {formatDuration(call.duration_sec)}
          </div>
        </div>
      </button>

      {expanded && detail && (
        <div style={{
          padding: 12, borderTop: '1px solid var(--color-border)',
          fontSize: 12, color: 'var(--color-text)',
        }}>
          {/* Structured summary */}
          {summary.next_action && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 0.5,
                            color: 'var(--color-text-dim)', textTransform: 'uppercase', marginBottom: 3 }}>
                Next action
              </div>
              <div>{summary.next_action}</div>
            </div>
          )}
          {summary.key_points?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: 0.5,
                            color: 'var(--color-text-dim)', textTransform: 'uppercase', marginBottom: 3 }}>
                Key points
              </div>
              <ul style={{ margin: 0, paddingLeft: 18, lineHeight: 1.5 }}>
                {summary.key_points.map((kp, i) => <li key={i}>{kp}</li>)}
              </ul>
            </div>
          )}
          {summary.sentiment && (
            <div style={{ marginBottom: 10, fontSize: 11, color: 'var(--color-text-muted)' }}>
              Sentiment: <strong style={{ color: 'var(--color-text)' }}>{summary.sentiment}</strong>
            </div>
          )}

          {/* Transcript turns */}
          {detail.turns?.length > 0 && (
            <details style={{ marginTop: 10 }}>
              <summary style={{ cursor: 'pointer', fontSize: 11, color: 'var(--color-text-dim)' }}>
                Transcript ({detail.turns.length} turn{detail.turns.length === 1 ? '' : 's'})
              </summary>
              <div style={{
                marginTop: 8, padding: 10, borderRadius: 'var(--r-sm)',
                background: 'var(--color-surface-1)',
                fontSize: 12, fontFamily: 'var(--font-mono)',
                maxHeight: 280, overflowY: 'auto',
              }}>
                {detail.turns.map((t, i) => (
                  <div key={i} style={{ marginBottom: 6 }}>
                    <strong style={{
                      color: t.role === 'agent' || t.role === 'assistant'
                        ? 'var(--color-accent)' : 'var(--color-text)',
                    }}>{t.role}:</strong> {t.text || t.content || ''}
                  </div>
                ))}
              </div>
            </details>
          )}

          {/* Audit metadata */}
          <div style={{ marginTop: 10, fontSize: 10, color: 'var(--color-text-dim)' }}>
            call_sid: {call.call_id} · transcript_sha: {(detail.transcript_sha256 || '').slice(0, 12)}
            {(detail.transcript_sha256 || '').length > 0 ? '…' : '(missing)'}
          </div>
        </div>
      )}
    </div>
  );
}


// ── Page ───────────────────────────────────────────────────────────────────
export default function VoxAgent() {
  const [pending, setPending]   = useState([]);
  const [usage, setUsage]       = useState(null);
  const [calls, setCalls]       = useState([]);
  const [expanded, setExpanded] = useState(null);   // call_id of the open row
  const [details, setDetails]   = useState({});      // call_id → fetched detail
  const [busy, setBusy]         = useState(null);    // action_id mid-approve
  const [loading, setLoading]   = useState(true);
  const [err, setErr]           = useState(null);

  const reload = useCallback(async () => {
    try {
      const [p, u, c] = await Promise.all([
        listPendingDials(),
        getUsage(),
        listRecentCalls(50),
      ]);
      setPending(p); setUsage(u); setCalls(c); setErr(null);
    } catch (e) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    // Refresh the queue every 30s so a freshly-queued dial appears without
    // a manual reload. Keeps the page feeling live without WebSockets.
    const t = setInterval(reload, 30_000);
    return () => clearInterval(t);
  }, [reload]);

  const handleAction = async (actionId, kind) => {
    setBusy(actionId);
    try {
      if (kind === 'approve') await approveDial(actionId);
      else                    await rejectDial(actionId, 'Denied by user from Vox page');
      await reload();
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(null);
    }
  };

  const handleExpand = async (callId) => {
    if (expanded === callId) { setExpanded(null); return; }
    setExpanded(callId);
    if (!details[callId]) {
      try {
        const d = await getCall(callId);
        setDetails((prev) => ({ ...prev, [callId]: d }));
      } catch (e) {
        setErr(`Failed to load call ${callId}: ${e.message}`);
      }
    }
  };

  return (
    <div className="page-body" style={{ maxWidth: 980, margin: '0 auto' }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        paddingBottom: 14, borderBottom: '1px solid var(--color-border)',
        marginBottom: 22,
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Mic size={20} color="var(--color-accent)" />
            <h1 style={{ fontSize: 22, margin: 0, fontWeight: 700, letterSpacing: '-0.02em' }}>Vox</h1>
            <span className="pill"
                  style={{ background: 'var(--color-accent-soft)', color: 'var(--color-accent)' }}>
              outbound voice agent
            </span>
          </div>
          <p style={{ fontSize: 13, color: 'var(--color-text-muted)', margin: '6px 0 0',
                      maxWidth: 640, lineHeight: 1.5 }}>
            Queues calls for approval, runs the Pipecat pipeline (Twilio + Groq + ElevenLabs)
            on dial, records transcripts and outcomes locally.
          </p>
        </div>
        <button className="btn-ghost" onClick={reload} disabled={loading}>
          <RefreshCw size={11} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Refresh
        </button>
      </div>

      {err && (
        <div style={{
          padding: 10, marginBottom: 14, borderRadius: 'var(--r-md)',
          background: 'color-mix(in srgb, var(--color-err) 12%, transparent)',
          border: '1px solid color-mix(in srgb, var(--color-err) 30%, transparent)',
          color: 'var(--color-err)', fontSize: 12,
        }}>{err}</div>
      )}

      {/* Section 1: Queue */}
      <section style={{ marginBottom: 28 }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, fontSize: 14 }}>
          <PhoneOff size={14} color="var(--color-warn)" />
          Pending dials ({pending.length})
        </h3>
        <PendingDialsQueue pending={pending} onAction={handleAction} busy={busy} />
      </section>

      {/* Section 2: Usage */}
      <section style={{ marginBottom: 28 }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, fontSize: 14 }}>
          <Clock size={14} color="var(--color-accent)" />
          Today's usage
        </h3>
        <UsageStrip usage={usage} />
      </section>

      {/* Section 3: Recent calls */}
      <section>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, fontSize: 14 }}>
          <Phone size={14} color="var(--color-accent)" />
          Recent calls ({calls.length})
        </h3>
        {calls.length === 0 ? (
          <div style={{
            padding: 14, borderRadius: 'var(--r-md)',
            background: 'var(--color-surface-2)',
            border: '1px dashed var(--color-border)',
            color: 'var(--color-text-dim)', fontSize: 13, textAlign: 'center',
          }}>
            No calls yet. They'll appear here as Vox completes them.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {calls.map((c) => (
              <CallRow
                key={c.call_id}
                call={c}
                onExpand={handleExpand}
                expanded={expanded === c.call_id}
                detail={details[c.call_id]}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
