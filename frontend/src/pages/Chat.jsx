import { useState, useRef, useEffect, useCallback } from 'react';
import { Send, Plus, Download, Sparkles, Mic, MicOff, Upload, BarChart3,
         PanelLeftClose, PanelLeftOpen, MessageSquare, Trash2, Search, AudioLines,
         Sun, Moon, ArrowRight, Lock, Unlock } from 'lucide-react';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { sendMessage, getConversation, getConversations, deleteConversation,
         exportMarkdown, uploadDocument, downloadReport,
         setConversationSensitive } from '../services/api';
import { agentChat } from '../services/agent';
import { getToken, getBusinessId } from '../services/auth';
import { transcribeBlob, voiceSupported } from '../services/voice';
import { privacyStatus } from '../services/security';
import { briefingLatest, eveningLatest } from '../services/briefing';
import VoiceMode from '../components/VoiceMode';
import { Zap } from 'lucide-react';

const TOOL_CLASS = { rag: 'tool-rag', sql: 'tool-sql', action: 'tool-action', report: 'tool-report', whatif: 'tool-whatif' };

// ── Slash commands ──────────────────────────────────────────────────────────
// Each command maps a terse shortcut to a natural-language request the agent
// already knows how to execute via its existing tool registry. Nothing new
// server-side — just a speed layer on top of agent mode.
const SLASH_COMMANDS = [
  { cmd: '/remind',  args: '<customer>',        desc: 'Draft an invoice reminder email',
    rewrite: (a) => `Draft an invoice reminder email for ${a || 'the most overdue invoice'}.` },
  { cmd: '/task',    args: '<title>',           desc: 'Create a new task',
    rewrite: (a) => `Create a task: ${a}.` },
  { cmd: '/deal',    args: '<name>',            desc: 'Create a deal at the lead stage',
    rewrite: (a) => `Create a deal called "${a}" at the lead stage.` },
  { cmd: '/contact', args: '<name>',            desc: 'Add a new contact to CRM',
    rewrite: (a) => `Add a contact named ${a} to the CRM.` },
  { cmd: '/invoice', args: '<customer> <amt>',  desc: 'Draft an invoice',
    rewrite: (a) => `Draft an invoice for ${a}.` },
  { cmd: '/brief',   args: '',                  desc: "Run today's morning briefing",
    rewrite: () => `Generate today's morning briefing.` },
  { cmd: '/triage',  args: '',                  desc: 'Run email triage now',
    rewrite: () => `Run email triage on the inbox now.` },
  { cmd: '/whatif',  args: '<scenario>',         desc: 'Run a what-if simulation',
    // Marker only — actually handled inline by `runWhatIfInline` so we get
    // a structured before/after card instead of a free-text agent reply.
    inline: 'whatif',
    rewrite: (a) => `What if ${a || 'revenue drops 10%'}?` },
];

function parseSlash(input) {
  const trimmed = input.trimStart();
  if (!trimmed.startsWith('/')) return null;
  const [head, ...rest] = trimmed.split(/\s+/);
  const match = SLASH_COMMANDS.find(c => c.cmd === head);
  if (!match) return null;
  return { match, args: rest.join(' ').trim() };
}


// ── /whatif renderer ────────────────────────────────────────────────────────
// Convert the structured what-if response into a markdown card so the
// existing message renderer can show it without a new component. Keeps the
// inline rendering pipeline simple — same path as every other reply.
function renderWhatIfMarkdown(scenarioText, r) {
  if (!r || r.error) {
    return [
      `**What-If: ${scenarioText}**`,
      ``,
      `> ${r?.error || 'Simulation failed.'}`,
    ].join('\n');
  }

  const fmt = (n) => Number.isFinite(n) ? `$${Math.round(n).toLocaleString()}` : '—';
  const before = r.before_total_revenue;
  const after  = r.after_total_revenue;
  const pct    = r.net_impact_pct;
  const arrow  = (pct ?? 0) >= 0 ? '↑' : '↓';
  const sign   = (pct ?? 0) >= 0 ? '' : '';

  const lines = [
    `**What-If: ${r.scenario_description || scenarioText}**`,
    ``,
    `| | Before | After | Change |`,
    `|---|---:|---:|---:|`,
    `| Revenue | ${fmt(before)} | ${fmt(after)} | ${arrow} ${sign}${(pct ?? 0).toFixed(1)}% |`,
    ``,
    `**Net impact:** ${r.net_impact || '—'}`,
  ];
  if (r.assumptions) {
    lines.push('', '**Assumptions**', '', r.assumptions);
  }
  if (r.critique) {
    lines.push('', '**CFO critique**', '', r.critique);
  }
  return lines.join('\n');
}

// ── Privacy badge ───────────────────────────────────────────────────────────
// Shown under an assistant message to make data-handling visible: whether the
// reply came from the local model or the cloud, and if cloud, how many PII
// values were redacted before the prompt left the machine.
function PrivacyBadge({ stats }) {
  const [expanded, setExpanded] = useState(false);
  if (!stats) return null;
  const cloud = (stats.cloud_calls || 0) > 0;
  const local = (stats.local_calls || 0) > 0;
  if (!cloud && !local) return null;

  const kinds = stats.by_kind || {};
  const kindEntries = Object.entries(kinds).sort((a, b) => b[1] - a[1]);
  const provider = stats.provider || (cloud ? 'cloud' : 'ollama');
  const forcedLocal = stats.sensitive_forced_local || stats.kill_switch_blocked;

  const color = cloud ? 'var(--color-info)' : 'var(--color-ok)';
  const bg = cloud
    ? 'color-mix(in srgb, var(--color-info) 10%, transparent)'
    : 'color-mix(in srgb, var(--color-ok) 10%, transparent)';
  const border = cloud
    ? 'color-mix(in srgb, var(--color-info) 28%, transparent)'
    : 'color-mix(in srgb, var(--color-ok) 28%, transparent)';

  let label;
  if (cloud && stats.redactions > 0) {
    label = `Sent to ${provider} · ${stats.redactions} value${stats.redactions === 1 ? '' : 's'} redacted`;
  } else if (cloud) {
    label = `Sent to ${provider} · no PII detected`;
  } else if (forcedLocal) {
    label = `Local only · ${stats.sensitive_forced_local ? 'sensitive data' : 'cloud disabled'}`;
  } else {
    label = `Local · ${provider}`;
  }

  const hasDetails = kindEntries.length > 0 || forcedLocal || (stats.calls?.length || 0) > 0;

  return (
    <div style={{ marginTop: 6 }}>
      <button
        onClick={() => hasDetails && setExpanded(v => !v)}
        title={hasDetails ? (expanded ? 'Hide details' : 'Show what was redacted') : ''}
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 6,
          fontSize: 10, fontWeight: 600, letterSpacing: 0.3,
          padding: '2px 8px', borderRadius: 'var(--r-pill)',
          color, background: bg, border: `1px solid ${border}`,
          cursor: hasDetails ? 'pointer' : 'default',
        }}
      >
        <span style={{
          width: 6, height: 6, borderRadius: '50%',
          background: color, boxShadow: `0 0 6px ${color}`,
        }} />
        {label}
        {hasDetails && (
          <span style={{ fontSize: 9, opacity: 0.7 }}>{expanded ? '▾' : '▸'}</span>
        )}
      </button>
      {expanded && hasDetails && (
        <div style={{
          marginTop: 4, padding: '8px 10px', borderRadius: 'var(--r-sm)',
          background: 'var(--color-surface-1)', border: `1px solid ${border}`,
          fontSize: 10, color: 'var(--color-text-muted)',
          display: 'flex', flexDirection: 'column', gap: 6,
        }}>
          {kindEntries.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center' }}>
              <span style={{ color: 'var(--color-text-dim)' }}>Redacted:</span>
              {kindEntries.map(([k, n]) => (
                <span key={k} style={{
                  padding: '1px 6px', borderRadius: 'var(--r-pill)',
                  background: 'var(--color-surface-2)', border: '1px solid var(--color-border)',
                  fontWeight: 600, color: 'var(--color-text)',
                }}>
                  {n} {k.toLowerCase()}{n > 1 ? 's' : ''}
                </span>
              ))}
            </div>
          )}
          {stats.sensitive_forced_local && (
            <span style={{ color: 'var(--color-warn)' }}>
              · sensitive flag forced local (cloud was bypassed)
            </span>
          )}
          {stats.kill_switch_blocked && (
            <span style={{ color: 'var(--color-warn)' }}>
              · cloud kill switch on (forced local)
            </span>
          )}
          {stats.calls?.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <span style={{ color: 'var(--color-text-dim)' }}>
                {stats.calls.length} call{stats.calls.length > 1 ? 's' : ''}:
              </span>
              {stats.calls.map((c, i) => (
                <div key={i} style={{
                  display: 'flex', gap: 8, alignItems: 'center',
                  padding: '3px 8px', borderRadius: 'var(--r-sm)',
                  background: c.cloud ? 'color-mix(in srgb, var(--color-info) 6%, transparent)' : 'color-mix(in srgb, var(--color-ok) 6%, transparent)',
                  fontFamily: 'var(--font-mono, monospace)', fontSize: 10,
                }}>
                  <span style={{
                    color: c.cloud ? 'var(--color-info)' : 'var(--color-ok)',
                    fontWeight: 700, minWidth: 38,
                  }}>{c.cloud ? 'CLOUD' : 'LOCAL'}</span>
                  <span style={{ color: 'var(--color-text)' }}>{c.provider}{c.model ? ` · ${c.model.split('-').slice(0, 3).join('-')}` : ''}</span>
                  {c.sha && (
                    <span title={`Prompt SHA-256: ${c.sha} (${c.chars} chars)`}
                          style={{ color: 'var(--color-text-dim)' }}>
                      sha:{c.sha.slice(0, 8)}
                    </span>
                  )}
                  {c.redactions > 0 && (
                    <span style={{ color: 'var(--color-warn)' }}>−{c.redactions}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

const QUICK = [
  { label: 'Revenue by Region', query: 'Show me revenue by region' },
  { label: 'Company Policy', query: 'What does our company policy say about remote work?' },
  { label: 'Sales Report', query: 'Generate a sales performance report' },
  { label: 'What-If Analysis', query: 'What if revenue drops 20%?' },
];

// ── Chart Component ──────────────────────────────────────────────────────────
function DataChart({ sqlData }) {
  if (!sqlData?.data?.length || !sqlData?.columns?.length) return null;
  const cols = sqlData.columns;
  const data = sqlData.data.slice(0, 20);

  // Find a string column (x-axis) and a numeric column (y-axis)
  let xCol = null, yCol = null;
  for (const col of cols) {
    const val = data[0]?.[col];
    if (!xCol && typeof val === 'string') xCol = col;
    if (!yCol && typeof val === 'number') yCol = col;
  }
  if (!xCol) xCol = cols[0];
  if (!yCol) yCol = cols[cols.length > 1 ? 1 : 0];

  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
        <BarChart3 size={14} color="var(--color-accent)" />
        <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-muted)' }}>Data ({sqlData.row_count} rows)</span>
      </div>
      {/* Bar chart using CSS */}
      <div style={{ background: 'var(--color-surface-1)', borderRadius: 8, padding: 12, border: '1px solid var(--color-surface-2)' }}>
        {data.map((row, i) => {
          const label = String(row[xCol] || '').substring(0, 20);
          const val = Number(row[yCol]) || 0;
          const maxVal = Math.max(...data.map(r => Number(r[yCol]) || 0));
          const pct = maxVal > 0 ? (val / maxVal) * 100 : 0;
          return (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span style={{ fontSize: 10, color: 'var(--color-text-muted)', minWidth: 80, textAlign: 'right' }}>{label}</span>
              <div style={{ flex: 1, height: 16, background: 'var(--color-surface-2)', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg, var(--color-accent), #8b5cf6)', borderRadius: 4, transition: 'width 0.3s' }} />
              </div>
              <span style={{ fontSize: 10, color: 'var(--color-text-dim)', minWidth: 60 }}>
                {typeof val === 'number' && val > 1000 ? `$${(val / 1000).toFixed(1)}k` : val}
              </span>
            </div>
          );
        })}
      </div>
      {/* Data table */}
      <details style={{ marginTop: 6 }}>
        <summary style={{ fontSize: 10, color: 'var(--color-text-dim)', cursor: 'pointer' }}>View raw data</summary>
        <div style={{ overflowX: 'auto', marginTop: 4 }}>
          <table className="data-table">
            <thead><tr>{cols.map(c => <th key={c}>{c}</th>)}</tr></thead>
            <tbody>{data.map((row, i) => (
              <tr key={i}>{cols.map(c => <td key={c}>{String(row[c] ?? '')}</td>)}</tr>
            ))}</tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [streamingText, setStreamingText] = useState(''); // Live streaming tokens
  const [chartData, setChartData] = useState(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [convId, setConvId] = useState(null);
  const [recording, setRecording] = useState(false);
  const [agentMode, setAgentMode] = useState(() => {
    const saved = localStorage.getItem('nexus_agent_mode');
    return saved === null ? true : saved === '1';
  });
  const [conversations, setConversations] = useState([]);
  const [historyOpen, setHistoryOpen] = useState(() => localStorage.getItem('nexus_chat_history_open') !== '0');
  const [historySearch, setHistorySearch] = useState('');
  const [slashIdx, setSlashIdx] = useState(0);
  const [voiceOpen, setVoiceOpen] = useState(false);
  const [privacy, setPrivacy] = useState(null);
  const [briefing, setBriefing] = useState(null);
  const [evening, setEvening] = useState(null);
  const [convSensitive, setConvSensitive] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading, streamingText]);

  // Load privacy posture once for the footer label.
  useEffect(() => { privacyStatus().then(setPrivacy).catch(() => {}); }, []);

  // Pull today's briefing(s) for the welcome ribbon. Dashboard handles auto-run;
  // here we just display whatever's fresh, so users who land on /chat directly
  // still see the daily-habit hook. Evening only renders after 4 PM local.
  useEffect(() => {
    const today = new Date().toISOString().slice(0, 10);
    briefingLatest().then(b => {
      if (b?.id && b?.data?.date === today) setBriefing(b);
    }).catch(() => {});
    if (new Date().getHours() >= 16) {
      eveningLatest().then(e => {
        if (e?.id && e?.data?.date === today) setEvening(e);
      }).catch(() => {});
    }
  }, []);

  // Conversation history — loaded here, not in the app sidebar
  const loadConversations = useCallback(() => {
    getConversations().then(setConversations).catch(() => {});
  }, []);
  useEffect(() => {
    loadConversations();
    const iv = setInterval(loadConversations, 15000);
    return () => clearInterval(iv);
  }, [loadConversations]);
  // Refresh right after a new message lands (so the new conversation title appears)
  useEffect(() => {
    if (messages.length > 0) { loadConversations(); }
  }, [convId, messages.length, loadConversations]);

  const toggleHistory = () => {
    setHistoryOpen(v => {
      localStorage.setItem('nexus_chat_history_open', v ? '0' : '1');
      return !v;
    });
  };

  const loadConversation = async (id) => {
    try {
      const data = await getConversation(id);
      setMessages(data.messages || []);
      setConvId(id);
      setChartData(null);
      setConvSensitive(!!data.info?.sensitive);
    }
    catch {}
  };

  const toggleConvSensitive = async () => {
    const next = !convSensitive;
    setConvSensitive(next);  // optimistic
    if (!convId) return;     // new chats: synced after first send creates the row
    try {
      await setConversationSensitive(convId, next);
    } catch (e) {
      setConvSensitive(!next);  // revert on failure
      console.error('Failed to set sensitive flag', e);
    }
  };

  // If the user toggled "lock" on a brand-new chat, push the flag once the
  // first send creates the server-side conversation row.
  useEffect(() => {
    if (convId && convSensitive) {
      setConversationSensitive(convId, true).catch(() => {});
    }
  }, [convId]); // eslint-disable-line react-hooks/exhaustive-deps

  const removeConversation = async (e, id) => {
    e.stopPropagation();
    if (!confirm('Delete this conversation?')) return;
    await deleteConversation(id).catch(() => {});
    setConversations(c => c.filter(x => x.conversation_id !== id));
    if (convId === id) { setMessages([]); setConvId(null); setChartData(null); setConvSensitive(false); }
  };

  const filteredConvs = conversations.filter(c =>
    !historySearch.trim() || (c.title || '').toLowerCase().includes(historySearch.toLowerCase())
  );

  useEffect(() => {
    const onLoad = async (e) => {
      try {
        const data = await getConversation(e.detail);
        setMessages(data.messages || []);
        setConvId(e.detail);
        setConvSensitive(!!data.info?.sensitive);
      } catch {}
    };
    const onNew = () => {
      setMessages([]); setConvId(null); setChartData(null);
      setConvSensitive(false);
      inputRef.current?.focus();
    };
    const onRerun = (e) => { send(e.detail); };
    window.addEventListener('nexus-load-conv', onLoad);
    window.addEventListener('nexus-new-chat', onNew);
    window.addEventListener('nexus-rerun', onRerun);
    return () => { window.removeEventListener('nexus-load-conv', onLoad); window.removeEventListener('nexus-new-chat', onNew); window.removeEventListener('nexus-rerun', onRerun); };
  }, []);

  // ── Voice Recording ────────────────────────────────────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      const chunks = [];
      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setRecording(false);
        // Send to transcription API (authenticated)
        try {
          const text = await transcribeBlob(blob);
          if (text) {
            setInput(text);
            inputRef.current?.focus();
          }
        } catch (err) {
          console.error('Transcription failed:', err);
        }
      };
      mediaRecRef.current = mediaRecorder;
      mediaRecorder.start();
      setRecording(true);
      // Auto-stop after 5 seconds
      setTimeout(() => { if (mediaRecorder.state === 'recording') mediaRecorder.stop(); }, 5000);
    } catch (err) {
      console.error('Mic access denied:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecRef.current?.state === 'recording') mediaRecRef.current.stop();
  };

  const toggleAgentMode = () => {
    const next = !agentMode;
    setAgentMode(next);
    localStorage.setItem('nexus_agent_mode', next ? '1' : '0');
  };

  // Slash menu — visible when input starts with "/" and hasn't been confirmed yet.
  const slashHead = input.trimStart().split(/\s+/)[0];
  const slashMatches = input.trimStart().startsWith('/') && !input.includes(' ')
    ? SLASH_COMMANDS.filter(c => c.cmd.startsWith(slashHead.toLowerCase()))
    : [];
  useEffect(() => { setSlashIdx(0); }, [slashHead, slashMatches.length]);

  const acceptSlash = (cmd) => {
    // Insert "{cmd} " so the user can type args next
    setInput(cmd.cmd + (cmd.args ? ' ' : ''));
    inputRef.current?.focus();
  };

  const send = async (text = input) => {
    if (!text.trim() || loading) return;
    // Rewrite slash commands → natural language that the agent tool system understands
    const slash = parseSlash(text);
    const q = (slash ? slash.match.rewrite(slash.args) : text).trim();
    // Show the user the command they typed, but send the rewrite to the agent
    const display = slash ? text.trim() : q;
    setInput('');
    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { role: 'user', content: display, tools_used: [], timestamp: ts }]);
    setLoading(true);
    setStreamingText('');

    // Inline slash commands — bypass the agent pipeline and render a
    // structured card. Currently only /whatif. Keep this list short — the
    // default slash path is "rewrite to natural language and run as agent."
    if (slash?.match.inline === 'whatif') {
      try {
        const { runWhatIf } = await import('../services/api');
        const r = await runWhatIf(slash.args || 'revenue drops 10%');
        const md = renderWhatIfMarkdown(slash.args || 'revenue drops 10%', r);
        setMessages(prev => [...prev, {
          role: 'assistant', content: md, tools_used: ['whatif'], timestamp: ts,
        }]);
      } catch (err) {
        setMessages(prev => [...prev, {
          role: 'assistant', content: `What-If failed: ${err.message}`,
          tools_used: [], timestamp: ts,
        }]);
      }
      setLoading(false);
      setStreamingText('');
      return;
    }

    // Slash commands imply agent mode — force it on so the tools actually run.
    const useAgentForThisTurn = agentMode || !!slash;

    // Agent mode — tool-using (no streaming, returns complete turn)
    if (useAgentForThisTurn) {
      try {
        const res = await agentChat(q, convId);
        if (!convId && res.conversation_id) setConvId(res.conversation_id);
        setMessages(prev => [...prev, res.message]);
      } catch (err) {
        setMessages(prev => [...prev, {
          role: 'assistant', content: `Error: ${err.message}`,
          tools_used: [], timestamp: ts,
        }]);
      }
      setLoading(false);
      setStreamingText('');
      return;
    }

    // Try WebSocket streaming first
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/chat`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      let ready = false;

      ws.onopen = () => {
        // Auth frame must come first
        ws.send(JSON.stringify({
          type: 'auth',
          token: getToken() || '',
          business_id: getBusinessId() || '',
        }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'ready') {
          ready = true;
          ws.send(JSON.stringify({ query: q, conversation_id: convId }));
        } else if (data.type === 'token') {
          setStreamingText(prev => prev + data.token);
        } else if (data.type === 'done') {
          if (data.conversation_id && !convId) setConvId(data.conversation_id);
          setMessages(prev => [...prev, data.message]);
          if (data.state?.sql_results?.data?.length) setChartData(data.state.sql_results);
          setStreamingText('');
          setLoading(false);
          ws.close();
        } else if (data.type === 'error') {
          ws.close();
          if (!ready) {
            // Auth failed — fall back to REST (which will 401 → redirect to login)
            _sendRest(q, ts);
          } else {
            setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${data.error}`, tools_used: [], timestamp: ts }]);
            setStreamingText('');
            setLoading(false);
          }
        }
      };

      ws.onerror = () => {
        ws.close();
        _sendRest(q, ts);
      };

      ws.onclose = () => { wsRef.current = null; };

    } catch {
      _sendRest(q, ts);
    }
  };

  const _sendRest = async (q, ts) => {
    // REST fallback when WebSocket fails
    try {
      const res = await sendMessage(q, convId);
      if (!convId && res.conversation_id) setConvId(res.conversation_id);
      setMessages(prev => [...prev, res.message]);
      if (res.state?.sql_results?.data?.length) setChartData(res.state.sql_results);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}`, tools_used: [], timestamp: ts }]);
    }
    setStreamingText('');
    setLoading(false);
  };

  const doExport = async () => {
    try {
      const res = await exportMarkdown(messages);
      const blob = new Blob([res.markdown], { type: 'text/markdown' });
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `nexus_chat_${Date.now()}.md`; a.click();
    } catch {}
  };

  // ── Document Upload ────────────────────────────────────────────────────────
  const handleDocUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const data = await uploadDocument(file);
      if (data.chunks_added) {
        send(`I just uploaded ${file.name}. What's in this document?`);
      }
    } catch (err) {
      console.error('Upload failed:', err);
    }
    e.target.value = '';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button onClick={toggleHistory} title={historyOpen ? 'Hide chat history' : 'Show chat history'}
            style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer', padding: 4, display: 'flex', alignItems: 'center' }}>
            {historyOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
          </button>
          <div>
            <h1>Chat {agentMode && <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--color-ok)', background: 'color-mix(in srgb, var(--color-ok) 8%, transparent)', border: '1px solid color-mix(in srgb, var(--color-ok) 25%, transparent)', padding: '2px 8px', borderRadius: 10, verticalAlign: 'middle', marginLeft: 8 }}>AGENT</span>}</h1>
            <p>{agentMode ? 'Ask me to do things — create tasks, add contacts, draft invoices, send emails (with approval)' : 'Ask about your business data, documents, or operations'}</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <button
            onClick={toggleConvSensitive}
            title={convSensitive
              ? 'This chat is locked to local-only LLM. Click to unlock.'
              : 'Lock this chat to local-only LLM (no cloud calls).'}
            style={{
              display: 'flex', alignItems: 'center', gap: 4,
              padding: '5px 10px', fontSize: 11, borderRadius: 6, cursor: 'pointer',
              border: `1px solid ${convSensitive ? 'color-mix(in srgb, var(--color-warn) 45%, transparent)' : 'var(--color-border-strong)'}`,
              background: convSensitive ? 'color-mix(in srgb, var(--color-warn) 10%, transparent)' : 'transparent',
              color: convSensitive ? 'var(--color-warn)' : 'var(--color-text-muted)',
            }}
          >
            {convSensitive ? <Lock size={12} /> : <Unlock size={12} />}
            {convSensitive ? 'Local only' : 'Hybrid'}
          </button>
          <button
            onClick={toggleAgentMode}
            title={agentMode ? 'Switch to passive chat (answers only, no actions)' : 'Switch to agent mode (can take actions)'}
            style={{
              display: 'flex', alignItems: 'center', gap: 4,
              padding: '5px 10px', fontSize: 11, borderRadius: 6, cursor: 'pointer',
              border: `1px solid ${agentMode ? 'color-mix(in srgb, var(--color-ok) 38%, transparent)' : 'var(--color-border-strong)'}`,
              background: agentMode ? 'color-mix(in srgb, var(--color-ok) 8%, transparent)' : 'transparent',
              color: agentMode ? 'var(--color-ok)' : 'var(--color-text-muted)',
            }}
          >
            <Zap size={12} /> {agentMode ? 'Agent ON' : 'Agent OFF'}
          </button>
          {voiceSupported() && (
            <button
              onClick={() => setVoiceOpen(true)}
              className="action-btn"
              title="Hands-free voice conversation"
              style={{ color: 'var(--color-accent)' }}
            >
              <AudioLines size={13} /> Voice chat
            </button>
          )}
          {/* Document upload button */}
          <label className="action-btn" style={{ cursor: 'pointer' }}>
            <Upload size={13} /> Upload Doc
            <input type="file" accept=".pdf,.txt,.docx" onChange={handleDocUpload} style={{ display: 'none' }} />
          </label>
          {messages.length > 0 && (
            <>
              <button className="action-btn" onClick={doExport}><Download size={13} /> Export</button>
              <button className="action-btn" onClick={() => { setMessages([]); setConvId(null); setChartData(null); setConvSensitive(false); }}><Plus size={13} /> New</button>
            </>
          )}
        </div>
      </div>

      {/* History + Messages + Chart sidebar */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* History panel */}
        {historyOpen && (
          <aside style={{
            width: 240, flexShrink: 0,
            borderRight: '1px solid var(--color-border)',
            background: 'var(--color-surface-1)',
            display: 'flex', flexDirection: 'column',
          }}>
            <div style={{ padding: '10px 12px', borderBottom: '1px solid var(--color-border)', display: 'flex', gap: 6, alignItems: 'center' }}>
              <button className="btn-primary" style={{ flex: 1, justifyContent: 'center', fontSize: 12, padding: '7px 10px' }}
                onClick={() => { setMessages([]); setConvId(null); setChartData(null); setConvSensitive(false); inputRef.current?.focus(); }}>
                <Plus size={13} /> New chat
              </button>
            </div>
            <div style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-border)', display: 'flex', gap: 6, alignItems: 'center' }}>
              <Search size={12} style={{ color: 'var(--color-text-dim)', flexShrink: 0 }} />
              <input value={historySearch} onChange={e => setHistorySearch(e.target.value)} placeholder="Search chats"
                style={{ flex: 1, background: 'transparent', border: 'none', outline: 'none', color: 'var(--color-text)', fontSize: 12 }} />
            </div>
            <div style={{ flex: 1, overflowY: 'auto', padding: 6 }}>
              {filteredConvs.length === 0 && (
                <div style={{ padding: '16px 8px', fontSize: 11, color: 'var(--color-text-dim)', textAlign: 'center' }}>
                  {conversations.length === 0 ? 'No chats yet. Start by asking a question below.' : 'No matches.'}
                </div>
              )}
              {filteredConvs.map(c => {
                const active = c.conversation_id === convId;
                return (
                  <div key={c.conversation_id}
                    onClick={() => loadConversation(c.conversation_id)}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 8,
                      padding: '7px 10px', borderRadius: 'var(--r-sm)',
                      fontSize: 12, color: active ? 'var(--color-text)' : 'var(--color-text-muted)',
                      background: active ? 'var(--color-accent-soft)' : 'transparent',
                      border: `1px solid ${active ? 'color-mix(in srgb, var(--color-accent) 25%, transparent)' : 'transparent'}`,
                      cursor: 'pointer', marginBottom: 2,
                      transition: 'background var(--dur-fast) var(--ease-out), color var(--dur-fast) var(--ease-out)',
                    }}
                    onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = 'var(--color-surface-3)'; }}
                    onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent'; }}
                  >
                    <MessageSquare size={12} style={{ flexShrink: 0, opacity: 0.5 }} />
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.title}</span>
                    <button onClick={(e) => removeConversation(e, c.conversation_id)}
                      title="Delete chat"
                      style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 2, opacity: 0.5 }}
                      onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--color-err)'; e.currentTarget.style.opacity = 1; }}
                      onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--color-text-dim)'; e.currentTarget.style.opacity = 0.5; }}>
                      <Trash2 size={12} />
                    </button>
                  </div>
                );
              })}
            </div>
          </aside>
        )}

        {/* Chat */}
        <div className="chat-area" style={{ flex: 1 }}>
          {messages.length === 0 && !loading && (
            <div className="welcome">
              <div className="welcome-icon"><Sparkles size={24} color="var(--color-info)" /></div>
              <h2>Welcome to NexusAgent</h2>
              <p>Your AI business assistant. Ask about data, documents, generate reports, or run scenarios.</p>

              {briefing && (
                <div style={{
                  marginBottom: 16, padding: '12px 14px',
                  borderRadius: 'var(--r-md)',
                  background: 'linear-gradient(135deg, color-mix(in srgb, var(--color-accent) 8%, var(--color-surface-2)), var(--color-surface-2))',
                  border: '1px solid color-mix(in srgb, var(--color-accent) 22%, transparent)',
                  display: 'flex', alignItems: 'center', gap: 12, textAlign: 'left',
                  maxWidth: 720, width: '100%',
                }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 'var(--r-sm)', flexShrink: 0,
                    background: 'color-mix(in srgb, var(--color-accent) 16%, transparent)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Sun size={16} color="var(--color-accent)" />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-accent)', letterSpacing: 0.5 }}>TODAY</span>
                      {briefing.data?.tasks?.due_today_count > 0 && (
                        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                          {briefing.data.tasks.due_today_count} task{briefing.data.tasks.due_today_count > 1 ? 's' : ''} due
                        </span>
                      )}
                      {briefing.data?.invoices?.overdue_count > 0 && (
                        <span style={{ fontSize: 11, color: 'var(--color-warn)' }}>
                          · {briefing.data.invoices.overdue_count} invoice{briefing.data.invoices.overdue_count > 1 ? 's' : ''} overdue
                        </span>
                      )}
                      {briefing.data?.pipeline?.open_deal_count > 0 && (
                        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                          · {briefing.data.pipeline.open_deal_count} open deal{briefing.data.pipeline.open_deal_count > 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                    <div style={{
                      fontSize: 12, color: 'var(--color-text)',
                      overflow: 'hidden', textOverflow: 'ellipsis',
                      display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                      lineHeight: 1.5,
                    }}>
                      {(briefing.narrative || '').replace(/[#*_`]/g, '').split('\n').filter(Boolean)[0] || 'See your full briefing on the dashboard.'}
                    </div>
                  </div>
                  <Link to="/" style={{
                    flexShrink: 0, fontSize: 11, fontWeight: 600,
                    color: 'var(--color-accent)', textDecoration: 'none',
                    display: 'inline-flex', alignItems: 'center', gap: 4,
                    padding: '6px 10px', borderRadius: 'var(--r-sm)',
                  }}>
                    Open <ArrowRight size={12} />
                  </Link>
                </div>
              )}

              {evening && (
                <div style={{
                  marginBottom: 16, padding: '12px 14px',
                  borderRadius: 'var(--r-md)',
                  background: 'linear-gradient(135deg, color-mix(in srgb, var(--color-info) 8%, var(--color-surface-2)), var(--color-surface-2))',
                  border: '1px solid color-mix(in srgb, var(--color-info) 22%, transparent)',
                  display: 'flex', alignItems: 'center', gap: 12, textAlign: 'left',
                  maxWidth: 720, width: '100%',
                }}>
                  <div style={{
                    width: 32, height: 32, borderRadius: 'var(--r-sm)', flexShrink: 0,
                    background: 'color-mix(in srgb, var(--color-info) 16%, transparent)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                  }}>
                    <Moon size={16} color="var(--color-info)" />
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--color-info)', letterSpacing: 0.5 }}>TODAY'S WRAP</span>
                      {evening.data?.tasks?.completed_today_count > 0 && (
                        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                          {evening.data.tasks.completed_today_count} task{evening.data.tasks.completed_today_count > 1 ? 's' : ''} closed
                        </span>
                      )}
                      {evening.data?.invoices?.paid_today_count > 0 && (
                        <span style={{ fontSize: 11, color: 'var(--color-ok)' }}>
                          · {evening.data.invoices.paid_today_count} paid
                        </span>
                      )}
                      {evening.data?.invoices?.sent_today_count > 0 && (
                        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                          · {evening.data.invoices.sent_today_count} sent
                        </span>
                      )}
                      {evening.data?.pipeline?.advanced_today_count > 0 && (
                        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                          · {evening.data.pipeline.advanced_today_count} deal{evening.data.pipeline.advanced_today_count > 1 ? 's' : ''} moved
                        </span>
                      )}
                    </div>
                    <div style={{
                      fontSize: 12, color: 'var(--color-text)',
                      overflow: 'hidden', textOverflow: 'ellipsis',
                      display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                      lineHeight: 1.5,
                    }}>
                      {(evening.narrative || '').replace(/[#*_`]/g, '').split('\n').filter(Boolean)[0] || 'See your full wrap on the dashboard.'}
                    </div>
                  </div>
                  <Link to="/" style={{
                    flexShrink: 0, fontSize: 11, fontWeight: 600,
                    color: 'var(--color-info)', textDecoration: 'none',
                    display: 'inline-flex', alignItems: 'center', gap: 4,
                    padding: '6px 10px', borderRadius: 'var(--r-sm)',
                  }}>
                    Open <ArrowRight size={12} />
                  </Link>
                </div>
              )}

              <div className="quick-grid">
                {QUICK.map((qa, i) => (
                  <button key={i} className="quick-btn" onClick={() => send(qa.query)}>
                    <div className="title">{qa.label}</div>
                    <div className="desc">{qa.query}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`msg-row ${msg.role === 'user' ? 'user' : ''}`}>
              {msg.role === 'assistant' && <div className="msg-avatar bot">N</div>}
              <div className={`msg-bubble ${msg.role === 'user' ? 'user' : 'bot'}`}>
                <div className="chat-markdown"><ReactMarkdown>{msg.content}</ReactMarkdown></div>
                {/* Agent tool calls */}
                {msg.tool_calls?.length > 0 && (
                  <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {msg.tool_calls.map((tc, j) => (
                      <div key={j}>
                        <div style={{
                          fontSize: 10, padding: '4px 10px', borderRadius: 6,
                          background: tc.pending_approval ? 'color-mix(in srgb, var(--color-warn) 8%, transparent)' : (tc.error ? 'color-mix(in srgb, var(--color-err) 8%, transparent)' : 'color-mix(in srgb, var(--color-ok) 8%, transparent)'),
                          border: `1px solid ${tc.pending_approval ? 'color-mix(in srgb, var(--color-warn) 25%, transparent)' : (tc.error ? 'color-mix(in srgb, var(--color-err) 25%, transparent)' : 'color-mix(in srgb, var(--color-ok) 25%, transparent)')}`,
                          color: tc.pending_approval ? 'var(--color-warn)' : (tc.error ? 'var(--color-err)' : 'var(--color-ok)'),
                        }}>
                          {tc.pending_approval ? '⏸ ' : tc.error ? '✗ ' : '✓ '}
                          <code style={{ fontSize: 10 }}>{tc.name}</code>
                          {tc.pending_approval && <span> — waiting for your approval</span>}
                          {tc.error && <span> — {tc.error}</span>}
                          {tc.summary && <span style={{ color: 'var(--color-text-muted)' }}> · {tc.summary}</span>}
                        </div>
                        {/* Downloadable files produced by this tool */}
                        {tc.files?.length > 0 && (
                          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginTop: 4, marginLeft: 14 }}>
                            {tc.files.map((f, k) => (
                              <button
                                key={k}
                                onClick={async () => {
                                  try { await downloadReport(f.filename); }
                                  catch (err) { alert(`Download failed: ${err.message}`); }
                                }}
                                style={{
                                  fontSize: 11, padding: '4px 10px', borderRadius: 6,
                                  background: 'var(--color-surface-2)', border: '1px solid var(--color-border-strong)',
                                  color: 'var(--color-info)', cursor: 'pointer',
                                  display: 'inline-flex', alignItems: 'center', gap: 4,
                                }}
                                title={`Download ${f.filename}`}
                              >
                                <Download size={11} /> {f.filename}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {msg.pending_approvals?.length > 0 && (
                  <div style={{
                    marginTop: 8, padding: '8px 12px', borderRadius: 8,
                    background: 'color-mix(in srgb, var(--color-warn) 8%, transparent)', border: '1px solid color-mix(in srgb, var(--color-warn) 25%, transparent)',
                    fontSize: 11, color: 'var(--color-warn)',
                  }}>
                    {msg.pending_approvals.length} action{msg.pending_approvals.length > 1 ? 's' : ''} queued. Review in your <a href="/inbox" style={{ color: 'var(--color-info)', textDecoration: 'underline' }}>Inbox</a>.
                  </div>
                )}
                {msg.tools_used?.length > 0 && !msg.tool_calls && (
                  <div className="msg-tools">
                    {msg.tools_used.map((t, j) => <span key={j} className={`tool-badge ${TOOL_CLASS[t] || ''}`}>{t.replace(/_/g, ' ')}</span>)}
                  </div>
                )}
                {msg.multi_agent && msg.agents_used?.length > 0 && (
                  <div style={{ marginTop: 6, fontSize: 10, color: '#a78bfa', background: '#8b5cf610', border: '1px solid #8b5cf620', borderRadius: 12, padding: '2px 8px', display: 'inline-block' }}>
                    Multi-Agent: {msg.agents_used.map(a => a.replace('Agent', '')).join(', ')}
                  </div>
                )}
                {msg.sources_used?.length > 0 && (
                  <div className="msg-sources">{msg.sources_used.map((s, j) => <div key={j} className="msg-source">{s}</div>)}</div>
                )}
                {msg.role === 'assistant' && msg.privacy && <PrivacyBadge stats={msg.privacy} />}
                {msg.timestamp && <div className="msg-time">{msg.timestamp}</div>}
              </div>
              {msg.role === 'user' && <div className="msg-avatar human">U</div>}
            </div>
          ))}

          {/* Streaming response — tokens appear live */}
          {streamingText && (
            <div className="msg-row">
              <div className="msg-avatar bot">N</div>
              <div className="msg-bubble bot">
                <div className="chat-markdown" style={{ fontSize: 13 }}>
                  <ReactMarkdown>{streamingText}</ReactMarkdown>
                  <span style={{ display: 'inline-block', width: 6, height: 14, background: 'var(--color-accent)', marginLeft: 2, animation: 'pulse-dot 0.8s ease-in-out infinite', borderRadius: 1 }} />
                </div>
              </div>
            </div>
          )}

          {/* Thinking dots when waiting */}
          {loading && !streamingText && (
            <div className="msg-row">
              <div className="msg-avatar bot">N</div>
              <div className="msg-bubble bot">
                <div className="thinking">
                  <div className="thinking-dot" /><div className="thinking-dot" /><div className="thinking-dot" />
                  <span style={{ fontSize: 11, color: 'var(--color-text-dim)', marginLeft: 6 }}>Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Right panel — Chart */}
        {chartData && (
          <div style={{ width: 320, borderLeft: '1px solid var(--color-surface-2)', padding: 12, overflow: 'auto', flexShrink: 0 }}>
            <DataChart sqlData={chartData} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="chat-input-bar" style={{ position: 'relative' }}>
        {/* Slash command typeahead */}
        {slashMatches.length > 0 && (
          <div style={{
            position: 'absolute', bottom: '100%', left: 24, right: 24,
            marginBottom: 6,
            background: 'var(--color-surface-2)',
            border: '1px solid var(--color-border-strong)',
            borderRadius: 'var(--r-md)',
            boxShadow: 'var(--shadow-2)',
            padding: 4,
            maxHeight: 260, overflowY: 'auto',
            animation: 'fade-up var(--dur-fast) var(--ease-out)',
          }}>
            {slashMatches.map((c, i) => (
              <div
                key={c.cmd}
                onMouseEnter={() => setSlashIdx(i)}
                onMouseDown={(e) => { e.preventDefault(); acceptSlash(c); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '8px 10px', borderRadius: 'var(--r-sm)',
                  cursor: 'pointer',
                  background: i === slashIdx ? 'var(--color-accent-soft)' : 'transparent',
                  border: `1px solid ${i === slashIdx ? 'color-mix(in srgb, var(--color-accent) 22%, transparent)' : 'transparent'}`,
                }}
              >
                <code style={{
                  fontSize: 12, fontWeight: 600, color: 'var(--color-accent)',
                  background: 'transparent', padding: 0, minWidth: 80,
                }}>{c.cmd}</code>
                <code style={{ fontSize: 11, color: 'var(--color-text-dim)', background: 'transparent', padding: 0 }}>
                  {c.args}
                </code>
                <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 'auto' }}>
                  {c.desc}
                </span>
              </div>
            ))}
            <div style={{ fontSize: 10, color: 'var(--color-text-dim)', padding: '6px 10px 2px', display: 'flex', gap: 8 }}>
              <span>↑↓ navigate</span>
              <span>Tab / Enter to select</span>
              <span>Esc to cancel</span>
            </div>
          </div>
        )}

        <div className="chat-input-wrap">
          {/* Voice button */}
          <button onClick={recording ? stopRecording : startRecording}
            style={{
              padding: 6, borderRadius: 8, border: 'none', cursor: 'pointer', transition: 'all 0.15s',
              background: recording ? 'color-mix(in srgb, var(--color-err) 13%, transparent)' : 'transparent',
              color: recording ? 'var(--color-err)' : 'var(--color-text-dim)',
            }}>
            {recording ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              // Slash menu navigation
              if (slashMatches.length > 0) {
                if (e.key === 'ArrowDown') {
                  e.preventDefault();
                  setSlashIdx(i => (i + 1) % slashMatches.length);
                  return;
                }
                if (e.key === 'ArrowUp') {
                  e.preventDefault();
                  setSlashIdx(i => (i - 1 + slashMatches.length) % slashMatches.length);
                  return;
                }
                if (e.key === 'Tab' || (e.key === 'Enter' && slashMatches[slashIdx]?.cmd !== slashHead)) {
                  // Tab always accepts; Enter accepts only if the user hasn't typed a full command yet
                  e.preventDefault();
                  acceptSlash(slashMatches[slashIdx]);
                  return;
                }
                if (e.key === 'Escape') { setInput(''); return; }
              }
              if (e.key === 'Enter' && !e.shiftKey) send();
            }}
            placeholder={recording ? 'Listening... (5 sec)' : 'Ask, or type / for commands…'}
            disabled={loading} />
          <button className="send-btn" onClick={() => send()} disabled={loading || !input.trim()}>
            <Send size={15} />
          </button>
        </div>
        <div className="chat-footer">
          NexusAgent v2.0
          {privacy && (
            <>
              {' '}&middot;{' '}
              {privacy.cloud_configured && privacy.allow_cloud_llm ? (
                <>
                  Hybrid ({privacy.provider}
                  {privacy.cloud_model ? ` · ${privacy.cloud_model}` : ''})
                  {privacy.redact_pii && ' · PII redacted'}
                </>
              ) : (
                <>100% Local &middot; nothing leaves your machine</>
              )}
              {privacy.audit_enabled && ' · audited'}
            </>
          )}
        </div>
      </div>

      {/* Voice mode modal */}
      <VoiceMode
        open={voiceOpen}
        onClose={() => setVoiceOpen(false)}
        convId={convId}
        setConvId={setConvId}
        onTranscript={(text) => {
          const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          setMessages(prev => [...prev, { role: 'user', content: text, tools_used: [], timestamp: ts }]);
        }}
        onAgentReply={(msg) => {
          if (msg) setMessages(prev => [...prev, msg]);
        }}
      />
    </div>
  );
}
