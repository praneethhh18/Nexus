/**
 * Audit log — the privacy-first product's most demo-worthy page.
 *
 * Two tabs:
 *   1. Actions   — every tool call by the agent or a user (the existing
 *                  `/api/audit` feed). Useful for "what did Atlas actually do?"
 *   2. Cloud LLM — every prompt that left the machine. Provider, model,
 *                  redaction count + kinds, payload SHA-256 fingerprint,
 *                  timestamp. Backed by `/api/privacy/audit`.
 *
 * The header summary shows both counts so a viewer instantly understands the
 * trust posture: "12,847 actions logged · 348 cloud calls · 4,212 PII values
 * redacted before any of them left the machine."
 *
 * Design intent — buyers' CTOs spend 30 seconds on this page deciding whether
 * to forward the product to procurement. Make those 30 seconds count.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Activity, Search, Download, Check, X, Cloud, ShieldCheck, Eye, EyeOff,
  AlertCircle, ServerCog, Hash, Trash2, RefreshCw,
} from 'lucide-react';
import { auditList, privacyAudit, privacyStatus, privacyAuditClear } from '../services/security';
import { getToken, getBusinessId } from '../services/auth';
import EmptyState from '../components/EmptyState';

const SHORT_KIND = {
  EMAIL: 'Email', PHONE: 'Phone', AADHAAR: 'Aadhaar', PAN: 'PAN', SSN: 'SSN',
  CARD: 'Card', SECRET: 'Secret', IP: 'IP', PATH: 'Path',
};

const KIND_TONE = {
  EMAIL: 'info', PHONE: 'info', SECRET: 'err', CARD: 'err',
  AADHAAR: 'warn', PAN: 'warn', SSN: 'warn',
  IP: 'muted', PATH: 'muted',
};


function formatWhen(iso) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString([], {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit', second: '2-digit',
    });
  } catch { return iso.substring(0, 19); }
}

function formatTs(ts) {
  if (!ts) return '—';
  try {
    return new Date(Number(ts) * 1000).toLocaleString([], {
      month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
    });
  } catch { return '—'; }
}

function fmtBytes(n) {
  if (!n) return '0 B';
  const u = ['B', 'KB', 'MB']; let i = 0; let v = n;
  while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
  return `${v.toFixed(v < 10 ? 1 : 0)} ${u[i]}`;
}


export default function AuditLog() {
  const [tab, setTab]               = useState('actions');
  const [msg, setMsg]               = useState('');

  // Actions tab
  const [rows, setRows]             = useState([]);
  const [actionsLoading, setActionsLoading] = useState(false);
  const [filters, setFilters]       = useState({ tool: '', search: '', success: '' });

  // Cloud-LLM tab
  const [privacyData, setPrivacyData] = useState({ stats: null, entries: [] });
  const [privacy, setPrivacy]         = useState(null);
  const [cloudLoading, setCloudLoading] = useState(false);
  const [showFingerprint, setShowFingerprint] = useState(false);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 3000); };

  // ── Load actions ──────────────────────────────────────────────────────
  const reloadActions = useCallback(async () => {
    setActionsLoading(true);
    try {
      const params = { limit: 200 };
      if (filters.tool) params.tool = filters.tool;
      if (filters.search) params.search = filters.search;
      if (filters.success !== '') params.success = filters.success;
      const data = await auditList(params);
      setRows(data || []);
    } catch (e) { flash(`Failed: ${e.message}`); }
    setActionsLoading(false);
  }, [filters]);

  // ── Load cloud audit ──────────────────────────────────────────────────
  const reloadCloud = useCallback(async () => {
    setCloudLoading(true);
    try {
      const [log, status] = await Promise.all([
        privacyAudit(200).catch(() => ({ stats: null, entries: [] })),
        privacyStatus().catch(() => null),
      ]);
      setPrivacyData(log);
      setPrivacy(status);
    } catch (e) { flash(`Failed: ${e.message}`); }
    setCloudLoading(false);
  }, []);

  useEffect(() => { reloadActions(); }, [reloadActions]);
  useEffect(() => { if (tab === 'cloud') reloadCloud(); }, [tab, reloadCloud]);
  useEffect(() => {
    const h = () => { reloadActions(); reloadCloud(); };
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reloadActions, reloadCloud]);

  // ── CSV export of actions tab ─────────────────────────────────────────
  const downloadCsv = async () => {
    const t = getToken(); const b = getBusinessId();
    const h = {}; if (t) h['Authorization'] = `Bearer ${t}`; if (b) h['X-Business-Id'] = b;
    try {
      const r = await fetch('/api/audit/export?limit=10000', { headers: h });
      if (!r.ok) throw new Error(await r.text());
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `audit_log_${Date.now()}.csv`; a.click();
      URL.revokeObjectURL(url);
    } catch (e) { flash(`Export failed: ${e.message}`); }
  };

  const clearCloudLog = async () => {
    if (!confirm('Clear the cloud-call audit log? This deletes outputs/cloud_audit.jsonl. Existing in-chat badges will keep working.')) return;
    try {
      await privacyAuditClear();
      flash('Cloud audit log cleared.');
      reloadCloud();
    } catch (e) { flash(`Clear failed: ${e.message}`); }
  };

  // ── Counts for the unified header ─────────────────────────────────────
  const stats = privacyData.stats || {};
  const cloudTotal = stats.total || 0;
  const redactionTotal = stats.total_redactions || 0;
  const cloud24h = stats.last_24h || 0;
  const actionsTotal = rows.length;  // partial — full count only via export

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <h1>Audit log</h1>
          <p>Every action your agents took. Every prompt that left the machine.</p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn-ghost btn-sm" onClick={() => { reloadActions(); reloadCloud(); }}>
            <RefreshCw size={11} /> Refresh
          </button>
          {tab === 'actions' && (
            <button className="btn-ghost btn-sm" onClick={downloadCsv}>
              <Download size={11} /> Export CSV
            </button>
          )}
        </div>
      </div>

      {msg && (
        <div style={{ padding: '6px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>
      )}

      {/* ── Privacy-first summary band ─────────────────────────────────── */}
      <div style={{
        margin: '12px 24px 4px',
        padding: 14,
        background: 'linear-gradient(135deg, var(--color-surface-2), var(--color-surface-1))',
        border: '1px solid color-mix(in srgb, var(--color-accent) 22%, var(--color-border))',
        borderRadius: 'var(--r-lg)',
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
          <SummaryCell
            icon={<Activity size={14} />}
            label="Actions logged (this view)"
            value={actionsTotal.toLocaleString()}
            sub="Tool calls by agents and users"
            tone="info"
          />
          <SummaryCell
            icon={<Cloud size={14} />}
            label="Cloud LLM calls"
            value={cloudTotal.toLocaleString()}
            sub={`${cloud24h} in the last 24 hours`}
            tone={privacy?.allow_cloud_llm === false ? 'muted' : 'accent'}
          />
          <SummaryCell
            icon={<ShieldCheck size={14} />}
            label="PII values redacted"
            value={redactionTotal.toLocaleString()}
            sub="Stripped before leaving the machine"
            tone="ok"
          />
          <SummaryCell
            icon={privacy?.allow_cloud_llm ? <Cloud size={14} /> : <ShieldCheck size={14} />}
            label="Cloud kill-switch"
            value={privacy?.allow_cloud_llm === false ? 'OFF (local only)' : 'On'}
            sub={privacy?.cloud_model || (privacy?.cloud_configured ? 'Configured' : 'No cloud configured')}
            tone={privacy?.allow_cloud_llm === false ? 'ok' : 'dim'}
          />
        </div>
      </div>

      {/* ── Tabs ───────────────────────────────────────────────────────── */}
      <div style={{ padding: '8px 24px 0', borderBottom: '1px solid var(--color-border)' }}>
        <div style={{ display: 'inline-flex', gap: 2 }}>
          <TabButton id="actions" label="Actions" icon={<Activity size={12} />} active={tab === 'actions'} onClick={setTab} />
          <TabButton id="cloud"   label={`Cloud calls${cloudTotal ? ` (${cloudTotal})` : ''}`}
                     icon={<Cloud size={12} />} active={tab === 'cloud'} onClick={setTab} />
        </div>
      </div>

      {/* ── Actions tab ─────────────────────────────────────────────────── */}
      {tab === 'actions' && (
        <>
          <div style={{ display: 'flex', gap: 8, padding: '10px 24px 8px', alignItems: 'center', flexWrap: 'wrap' }}>
            <Search size={12} color="var(--color-text-dim)" />
            <input
              className="field-input" placeholder="Search input or output text…"
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              style={{ fontSize: 11, width: 240 }}
            />
            <input
              className="field-input" placeholder='Tool name, e.g. "agent.send_email"'
              value={filters.tool}
              onChange={(e) => setFilters({ ...filters, tool: e.target.value })}
              style={{ fontSize: 11, width: 240 }}
            />
            <select
              className="field-select" value={filters.success}
              onChange={(e) => setFilters({ ...filters, success: e.target.value })}
              style={{ fontSize: 11 }}
            >
              <option value="">All outcomes</option>
              <option value="true">Success only</option>
              <option value="false">Failures only</option>
            </select>
          </div>

          <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
            {actionsLoading && rows.length === 0 ? (
              <p style={{ color: 'var(--color-text-dim)', fontSize: 12, textAlign: 'center' }}>Loading…</p>
            ) : rows.length === 0 ? (
              <EmptyState
                icon={Activity}
                title="No actions match those filters"
                description="Every tool call by the AI shows up here — approvals, emails, SQL queries, report generation. Clear filters or wait for the next action."
              />
            ) : (
              <div className="table-panel">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{ width: 150 }}>Time</th>
                      <th style={{ width: 180 }}>Tool</th>
                      <th style={{ width: 120 }}>Actor</th>
                      <th>Input</th>
                      <th>Output</th>
                      <th style={{ width: 80, textAlign: 'right' }}>Duration</th>
                      <th style={{ width: 50, textAlign: 'center' }}>OK</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.map((r) => (
                      <tr key={r.event_id}>
                        <td style={{ fontSize: 10.5, color: 'var(--color-text-muted)' }}>{formatWhen(r.timestamp)}</td>
                        <td><code style={{ fontSize: 10.5 }}>{r.tool_name}</code></td>
                        <td style={{ fontSize: 11 }}>{r.actor_name || '—'}</td>
                        <td
                          style={{ fontSize: 11, maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                          title={r.input_summary}
                        >
                          {r.input_summary}
                        </td>
                        <td
                          style={{ fontSize: 11, maxWidth: 280, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                          title={r.output_summary}
                        >
                          {r.output_summary}
                        </td>
                        <td style={{ textAlign: 'right', fontSize: 10.5, color: 'var(--color-text-dim)' }}>
                          {r.duration_ms || 0}ms
                        </td>
                        <td style={{ textAlign: 'center' }}>
                          {r.success
                            ? <Check size={12} color="var(--color-accent)" />
                            : <X size={12} color="var(--color-err)" />}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {/* ── Cloud calls tab ─────────────────────────────────────────────── */}
      {tab === 'cloud' && (
        <CloudTab
          loading={cloudLoading}
          stats={privacyData.stats}
          entries={privacyData.entries}
          privacy={privacy}
          showFingerprint={showFingerprint}
          onToggleFingerprint={() => setShowFingerprint(v => !v)}
          onClear={clearCloudLog}
        />
      )}
    </div>
  );
}


// ── Cloud-call panel ─────────────────────────────────────────────────────────
function CloudTab({ loading, stats, entries, privacy, showFingerprint, onToggleFingerprint, onClear }) {
  // Distribution by provider
  const providerEntries = useMemo(() => {
    const out = stats?.by_provider || {};
    return Object.entries(out).sort((a, b) => b[1] - a[1]);
  }, [stats]);

  if (loading && (!entries || entries.length === 0)) {
    return (
      <div style={{ padding: 30, color: 'var(--color-text-dim)', fontSize: 12, textAlign: 'center' }}>
        Loading cloud audit log…
      </div>
    );
  }

  // Honest "nothing here" state — common in privacy-first deployments because
  // ALLOW_CLOUD_LLM is off, and the empty log is the *good* answer.
  const emptyReason = (() => {
    if ((entries || []).length > 0) return null;
    if (privacy && privacy.allow_cloud_llm === false) return 'kill-switch-off';
    if (privacy && !privacy.cloud_configured) return 'no-cloud';
    return 'no-traffic';
  })();

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: '14px 24px 24px' }}>
      {/* Toolbar */}
      <div style={{
        display: 'flex', gap: 8, marginBottom: 14, alignItems: 'center', flexWrap: 'wrap',
      }}>
        <button className="btn-ghost btn-sm" onClick={onToggleFingerprint}>
          {showFingerprint ? <EyeOff size={11} /> : <Eye size={11} />}
          {showFingerprint ? 'Hide fingerprints' : 'Show fingerprints'}
        </button>
        {entries && entries.length > 0 && (
          <button className="btn-ghost btn-sm" onClick={onClear} style={{ color: 'var(--color-err)' }}>
            <Trash2 size={11} /> Clear log
          </button>
        )}
        <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--color-text-dim)' }}>
          Showing the last {Math.min(200, (entries || []).length)} cloud calls. Older entries are still on disk.
        </span>
      </div>

      {/* Provider distribution */}
      {providerEntries.length > 0 && (
        <div style={{
          padding: 12, marginBottom: 14,
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--r-md)',
        }}>
          <div style={{
            fontSize: 10, fontWeight: 700, letterSpacing: 0.6, textTransform: 'uppercase',
            color: 'var(--color-text-dim)', marginBottom: 6,
          }}>By provider</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {providerEntries.map(([prov, n]) => (
              <span key={prov} className="pill-base pill-info">
                {prov}<span style={{ marginLeft: 6, opacity: 0.7 }}>{n}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Empty state — most common in production with cloud off */}
      {emptyReason && (
        <EmptyCloud reason={emptyReason} privacy={privacy} />
      )}

      {/* Entries — newest first */}
      {entries && entries.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {entries.map((e, i) => (
            <CloudCallCard key={i} entry={e} showFingerprint={showFingerprint} />
          ))}
        </div>
      )}
    </div>
  );
}


function CloudCallCard({ entry, showFingerprint }) {
  const kinds = entry.kinds || {};
  const kindEntries = Object.entries(kinds).filter(([, n]) => n > 0).sort((a, b) => b[1] - a[1]);
  const provider = entry.provider || 'unknown';
  const model = entry.model || '—';
  const sha = entry.sha256 || entry.sha || '';
  const redactions = entry.redactions || 0;
  const promptChars = entry.prompt_chars || 0;
  const responseChars = entry.response_chars || 0;
  const mode = (entry.meta && entry.meta.mode) || 'invoke';
  const sensitive = (entry.meta && entry.meta.sensitive) || false;

  return (
    <div style={{
      padding: 14,
      background: 'var(--color-surface-2)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--r-md)',
      display: 'flex', flexDirection: 'column', gap: 8,
    }}>
      {/* Top row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <span className="pill-base pill-info">
          <Cloud size={10} /> {provider}
        </span>
        <code style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>{model}</code>
        <span style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>{mode}</span>
        {sensitive && (
          <span className="pill-base pill-warn" title="This call was marked sensitive — should have been forced local">
            sensitive
          </span>
        )}
        <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--color-text-dim)', fontFeatureSettings: '"tnum"' }}>
          {formatTs(entry.ts)}
        </span>
      </div>

      {/* Stats row */}
      <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', fontSize: 11.5, color: 'var(--color-text-muted)' }}>
        <span>
          <strong style={{ color: redactions > 0 ? 'var(--color-accent)' : 'var(--color-text)' }}>
            {redactions}
          </strong>{' '}
          {redactions === 1 ? 'value' : 'values'} redacted
        </span>
        <span>
          Prompt: <strong style={{ color: 'var(--color-text)' }}>{fmtBytes(promptChars)}</strong>
        </span>
        {responseChars > 0 && (
          <span>
            Response: <strong style={{ color: 'var(--color-text)' }}>{fmtBytes(responseChars)}</strong>
          </span>
        )}
      </div>

      {/* Redaction-kind breakdown */}
      {kindEntries.length > 0 && (
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {kindEntries.map(([k, n]) => {
            const tone = KIND_TONE[k] || 'muted';
            return (
              <span key={k} className={`pill-base pill-${tone}`}>
                {SHORT_KIND[k] || k} <span style={{ marginLeft: 4, opacity: 0.7 }}>{n}</span>
              </span>
            );
          })}
        </div>
      )}

      {/* SHA fingerprint — collapsible */}
      {showFingerprint && sha && (
        <div style={{
          padding: '6px 10px',
          background: 'var(--color-surface-1)',
          border: '1px dashed var(--color-border)',
          borderRadius: 'var(--r-sm)',
          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace',
          fontSize: 10.5, color: 'var(--color-text-dim)',
          display: 'flex', alignItems: 'center', gap: 6,
          wordBreak: 'break-all',
        }}>
          <Hash size={10} />
          <span>{sha}</span>
        </div>
      )}
    </div>
  );
}


function EmptyCloud({ reason, privacy }) {
  if (reason === 'kill-switch-off') {
    return (
      <div style={{
        padding: 24,
        background: 'color-mix(in srgb, var(--color-accent) 8%, var(--color-surface-2))',
        border: '1px solid color-mix(in srgb, var(--color-accent) 28%, transparent)',
        borderRadius: 'var(--r-md)',
        textAlign: 'center',
      }}>
        <ShieldCheck size={36} color="var(--color-accent)" style={{ margin: '0 auto 10px', opacity: 0.85 }} />
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)', marginBottom: 4 }}>
          Cloud kill-switch is OFF
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)', maxWidth: 480, margin: '0 auto', lineHeight: 1.55 }}>
          <code>ALLOW_CLOUD_LLM=false</code> is set. Every prompt — chat, reports, briefings — runs on the local model. Nothing leaves the machine, so this log stays empty by design.
        </div>
      </div>
    );
  }
  if (reason === 'no-cloud') {
    return (
      <div style={{
        padding: 24,
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--r-md)',
        textAlign: 'center',
      }}>
        <ServerCog size={36} color="var(--color-text-dim)" style={{ margin: '0 auto 10px' }} />
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)', marginBottom: 4 }}>
          No cloud LLM configured
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)', maxWidth: 480, margin: '0 auto', lineHeight: 1.55 }}>
          You haven't set up Anthropic Claude or AWS Bedrock. The product is running on local Ollama only — which is fine, you just won't see entries here. Configure a cloud provider in <code>.env</code> if you want polished prose on aggregates.
        </div>
      </div>
    );
  }
  // no-traffic — cloud is on but nothing has fired yet
  return (
    <div style={{
      padding: 24,
      background: 'var(--color-surface-2)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--r-md)',
      textAlign: 'center',
    }}>
      <Cloud size={36} color="var(--color-text-dim)" style={{ margin: '0 auto 10px' }} />
      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)', marginBottom: 4 }}>
        No cloud calls yet
      </div>
      <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)', maxWidth: 480, margin: '0 auto', lineHeight: 1.55 }}>
        Cloud is enabled on <strong>{privacy?.cloud_model || privacy?.provider || 'your configured provider'}</strong>, but nothing has fired since the audit log was last cleared. Ask the AI to summarise something or generate a report — entries will appear here.
      </div>
    </div>
  );
}


// ── Bits ─────────────────────────────────────────────────────────────────────
function SummaryCell({ icon, label, value, sub, tone = 'dim' }) {
  const toneColor = {
    accent: 'var(--color-accent)',
    info:   'var(--color-info)',
    ok:     'var(--color-ok)',
    warn:   'var(--color-warn)',
    err:    'var(--color-err)',
    dim:    'var(--color-text-dim)',
    muted:  'var(--color-text-muted)',
  }[tone];
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', gap: 4,
      padding: '8px 10px',
      background: 'var(--color-surface-1)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--r-md)',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6,
        color: toneColor, fontSize: 10, fontWeight: 700,
        letterSpacing: 0.5, textTransform: 'uppercase',
      }}>
        {icon}
        <span>{label}</span>
      </div>
      <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text)', letterSpacing: '-0.01em', fontFeatureSettings: '"tnum"' }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: 10.5, color: 'var(--color-text-dim)' }}>{sub}</div>}
    </div>
  );
}


function TabButton({ id, label, icon, active, onClick }) {
  return (
    <button
      onClick={() => onClick(id)}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '8px 14px',
        border: 'none', cursor: 'pointer',
        background: 'transparent',
        color: active ? 'var(--color-accent)' : 'var(--color-text-muted)',
        fontSize: 12.5, fontWeight: 600,
        borderBottom: active
          ? '2px solid var(--color-accent)'
          : '2px solid transparent',
        marginBottom: -1,
        transition: 'color var(--dur-fast) var(--ease-out)',
      }}
    >
      {icon}
      {label}
    </button>
  );
}
