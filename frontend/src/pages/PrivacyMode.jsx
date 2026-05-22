import { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck, Download, RefreshCw, Copy, Check, AlertTriangle,
  Cpu, Wifi, WifiOff, Power, KeyRound, Laptop,
} from 'lucide-react';
import {
  getBridgeState, issueBridgeToken, revokeBridge, pingBridge,
} from '../services/privacy_bridge';

const STATUS_META = {
  unconfigured: { label: 'Not set up',         tone: 'dim',  Icon: AlertTriangle, sub: 'Sensitive prompts go to cloud (with PII redaction).' },
  registered:   { label: 'Registered',         tone: 'warn', Icon: Wifi,          sub: 'Waiting for first health check…' },
  healthy:      { label: 'Active, local AI',  tone: 'good', Icon: ShieldCheck,   sub: 'Sensitive prompts compute on your laptop.' },
  down:         { label: 'Bridge offline',     tone: 'bad',  Icon: WifiOff,       sub: 'Falling back to cloud (with PII redaction). Restart the installer on your laptop.' },
  revoked:      { label: 'Disabled',           tone: 'dim',  Icon: Power,         sub: 'Issue a new token to re-enable.' },
};

function timeAgo(iso) {
  if (!iso) return ', ';
  const t = new Date(iso).getTime();
  if (!t) return iso;
  const s = Math.max(0, Math.floor((Date.now() - t) / 1000));
  if (s < 60)    return `${s}s ago`;
  if (s < 3600)  return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

function StatusPill({ status }) {
  const meta = STATUS_META[status] || STATUS_META.unconfigured;
  const Icon = meta.Icon;
  const colors = {
    good: { bg: 'rgba(16,185,129,0.12)',  fg: '#10B981', dot: '#10B981' },
    warn: { bg: 'rgba(245,158,11,0.12)',  fg: '#D97706', dot: '#F59E0B' },
    bad:  { bg: 'rgba(239,68,68,0.12)',   fg: '#DC2626', dot: '#EF4444' },
    dim:  { bg: 'var(--color-surface-1)', fg: 'var(--color-text-dim)', dot: 'var(--color-text-dim)' },
  }[meta.tone];
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 6,
      background: colors.bg, color: colors.fg,
      padding: '4px 10px', borderRadius: 999,
      fontSize: 12, fontWeight: 600,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: colors.dot }} />
      <Icon size={12} />
      {meta.label}
    </span>
  );
}

function SectionCard({ children, ...rest }) {
  return (
    <div style={{
      background: 'var(--color-surface-0)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--r-lg, 12px)',
      padding: 18,
      ...rest,
    }}>
      {children}
    </div>
  );
}

export default function PrivacyMode() {
  const [state, setState]       = useState(null);
  const [loading, setLoading]   = useState(true);
  const [token, setToken]       = useState(null);
  const [tokenCopied, setTokCopied] = useState(false);
  const [busy, setBusy]         = useState(false);
  const [msg, setMsg]           = useState('');

  const reload = useCallback(async () => {
    try {
      const s = await getBridgeState();
      setState(s);
    } catch (e) {
      setMsg(`Failed to load: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { reload(); }, [reload]);

  // Auto-refresh while waiting for the installer to register, so the user
  // doesn't have to click anything when their laptop comes online.
  useEffect(() => {
    if (!state) return;
    if (state.status === 'registered' || state.status === 'down') {
      const t = setInterval(reload, 6000);
      return () => clearInterval(t);
    }
  }, [state, reload]);

  const onIssueToken = async () => {
    if (!confirm('Issue a new bridge token? Any previously-installed bridge will stop working until you re-paste this token into the installer.')) return;
    setBusy(true);
    try {
      const r = await issueBridgeToken();
      setToken(r.token);
      setTokCopied(false);
      await reload();
    } catch (e) {
      setMsg(`Failed: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const onCopyToken = async () => {
    if (!token) return;
    try {
      await navigator.clipboard.writeText(token);
      setTokCopied(true);
      setTimeout(() => setTokCopied(false), 2000);
    } catch {}
  };

  const onPing = async () => {
    setBusy(true);
    try {
      const s = await pingBridge();
      setState(s);
    } catch (e) {
      setMsg(`Ping failed: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const onRevoke = async () => {
    if (!confirm('Disable Privacy Bridge? Sensitive prompts will fall back to cloud (with PII redaction). You can re-enable anytime by issuing a new token.')) return;
    setBusy(true);
    try {
      const s = await revokeBridge();
      setState(s);
      setToken(null);
    } catch (e) {
      setMsg(`Failed: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <div style={{ padding: 24, color: 'var(--color-text-dim)' }}>Loading Privacy Mode…</div>;
  }

  const status = state?.status || 'unconfigured';
  const meta   = STATUS_META[status] || STATUS_META.unconfigured;
  const isOn   = status === 'healthy' || status === 'registered' || status === 'down';

  return (
    <div style={{ padding: 24, maxWidth: 880, display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            display: 'grid', placeItems: 'center',
            background: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
            color: '#fff',
          }}>
            <ShieldCheck size={20} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: 22 }}>Privacy Mode</h1>
            <div style={{ color: 'var(--color-text-dim)', fontSize: 13 }}>
              Run sensitive AI prompts on your own laptop instead of the cloud.
            </div>
          </div>
        </div>
      </div>

      {msg && (
        <div style={{
          padding: '10px 12px', borderRadius: 8,
          background: 'rgba(239,68,68,0.08)', color: '#DC2626', fontSize: 13,
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <AlertTriangle size={14} /> {msg}
          <button onClick={() => setMsg('')} style={{
            marginLeft: 'auto', background: 'transparent', border: 'none',
            color: 'inherit', cursor: 'pointer', fontSize: 12,
          }}>dismiss</button>
        </div>
      )}

      {/* Status card */}
      <SectionCard>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }}>
              Bridge status
            </div>
            <StatusPill status={status} />
            <div style={{ marginTop: 8, fontSize: 13, color: 'var(--color-text-dim)' }}>
              {meta.sub}
            </div>
          </div>
          <button
            onClick={onPing}
            disabled={busy || status === 'unconfigured' || status === 'revoked'}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '7px 12px', borderRadius: 8, fontSize: 13,
              background: 'var(--color-surface-1)', color: 'var(--color-text)',
              border: '1px solid var(--color-border)', cursor: 'pointer',
              opacity: busy ? 0.5 : 1,
            }}
          >
            <RefreshCw size={13} /> Re-check
          </button>
        </div>

        {isOn && (
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: 10, marginTop: 14,
          }}>
            <Detail icon={<Laptop size={13} />} label="Endpoint" value={
              state?.endpoint_url
                ? state.endpoint_url.replace('https://', '').slice(0, 42) + (state.endpoint_url.length > 50 ? '…' : '')
                : ', '
            } />
            <Detail icon={<Cpu size={13} />} label="Models" value={
              (state?.ollama_models || []).slice(0, 3).join(', ') || ', '
            } />
            <Detail icon={<RefreshCw size={13} />} label="Last check" value={timeAgo(state?.last_pinged_at)} />
            <Detail icon={<KeyRound size={13} />} label="Registered" value={timeAgo(state?.registered_at)} />
          </div>
        )}

        {state?.last_ping_error && status === 'down' && (
          <div style={{
            marginTop: 12, padding: '8px 10px', borderRadius: 8,
            background: 'rgba(239,68,68,0.08)', color: '#DC2626',
            fontSize: 12, fontFamily: 'ui-monospace, SFMono-Regular, monospace',
          }}>
            {state.last_ping_error}
          </div>
        )}
      </SectionCard>

      {/* Setup wizard */}
      <SectionCard>
        <div style={{ fontWeight: 600, marginBottom: 4 }}>Set up on your laptop</div>
        <div style={{ color: 'var(--color-text-dim)', fontSize: 13, marginBottom: 14 }}>
          One-time setup. Once installed, the bridge runs quietly in your system tray and reconnects automatically.
        </div>

        <Step n={1} title="Download the installer">
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            <DownloadBtn os="Windows"  href="/downloads/privacy-bridge/NexusAgent-Privacy-Bridge-Setup.exe" />
            <DownloadBtn os="macOS"    href="/downloads/privacy-bridge/NexusAgent-Privacy-Bridge.dmg" />
            <DownloadBtn os="Linux"    href="/downloads/privacy-bridge/NexusAgent-Privacy-Bridge.AppImage" />
          </div>
        </Step>

        <Step n={2} title="Install Ollama (if you don't have it)">
          <div style={{ fontSize: 13, color: 'var(--color-text-dim)' }}>
            The bridge installer will detect Ollama automatically. If missing, it opens{' '}
            <a href="https://ollama.com/download" target="_blank" rel="noreferrer" style={{ color: 'var(--color-accent)' }}>
              ollama.com/download
            </a>{' '}
            in your browser.
          </div>
        </Step>

        <Step n={3} title="Get a bridge token & paste it">
          {!token ? (
            <button
              onClick={onIssueToken}
              disabled={busy}
              style={{
                display: 'inline-flex', alignItems: 'center', gap: 6,
                padding: '8px 14px', borderRadius: 8, fontSize: 13, fontWeight: 600,
                background: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
                color: '#fff', border: 'none', cursor: 'pointer',
                opacity: busy ? 0.5 : 1,
              }}
            >
              <KeyRound size={13} /> {state?.token ? 'Issue new token' : 'Generate token'}
            </button>
          ) : (
            <div>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 8,
                background: 'var(--color-surface-1)',
                border: '1px solid var(--color-border)',
                borderRadius: 8, padding: '8px 10px',
              }}>
                <code style={{ flex: 1, fontSize: 12, color: 'var(--color-text)', userSelect: 'all', wordBreak: 'break-all' }}>
                  {token}
                </code>
                <button
                  onClick={onCopyToken}
                  style={{
                    display: 'inline-flex', alignItems: 'center', gap: 4,
                    padding: '5px 9px', borderRadius: 6, fontSize: 12,
                    background: tokenCopied ? '#10B981' : 'var(--color-surface-2, #fff)',
                    color: tokenCopied ? '#fff' : 'var(--color-text)',
                    border: '1px solid var(--color-border)', cursor: 'pointer',
                  }}
                >
                  {tokenCopied ? <Check size={12} /> : <Copy size={12} />}
                  {tokenCopied ? 'Copied' : 'Copy'}
                </button>
              </div>
              <div style={{ marginTop: 6, fontSize: 11, color: 'var(--color-text-dim)' }}>
                Paste this into the installer when it asks. We'll only show it once, keep it safe.
              </div>
            </div>
          )}
        </Step>

        {state?.token && !token && (
          <div style={{
            marginTop: 12, fontSize: 12, color: 'var(--color-text-dim)',
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            <Check size={12} /> A token was previously issued. If you've lost it, generate a new one (the old one stops working).
          </div>
        )}
      </SectionCard>

      {/* Danger zone */}
      {(status !== 'unconfigured' && status !== 'revoked') && (
        <SectionCard style={{ borderColor: 'rgba(239,68,68,0.25)' }}>
          <div style={{ fontWeight: 600, marginBottom: 4 }}>Disable Privacy Bridge</div>
          <div style={{ color: 'var(--color-text-dim)', fontSize: 13, marginBottom: 12 }}>
            Sensitive prompts will fall back to cloud-with-PII-redaction. Re-enable anytime by issuing a new token.
          </div>
          <button
            onClick={onRevoke}
            disabled={busy}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '7px 12px', borderRadius: 8, fontSize: 13,
              background: 'transparent', color: '#DC2626',
              border: '1px solid rgba(239,68,68,0.45)', cursor: 'pointer',
              opacity: busy ? 0.5 : 1,
            }}
          >
            <Power size={13} /> Disable bridge
          </button>
        </SectionCard>
      )}
    </div>
  );
}

function Detail({ icon, label, value }) {
  return (
    <div style={{
      padding: '10px 12px', borderRadius: 8,
      background: 'var(--color-surface-1)',
      border: '1px solid var(--color-border)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600 }}>
        {icon} {label}
      </div>
      <div style={{ marginTop: 4, fontSize: 13, color: 'var(--color-text)', wordBreak: 'break-word' }}>
        {value}
      </div>
    </div>
  );
}

function Step({ n, title, children }) {
  return (
    <div style={{ display: 'flex', gap: 12, marginTop: 12, alignItems: 'flex-start' }}>
      <div style={{
        flex: '0 0 26px', height: 26, borderRadius: '50%',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        display: 'grid', placeItems: 'center',
        fontSize: 12, fontWeight: 600, color: 'var(--color-text-dim)',
      }}>
        {n}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>{title}</div>
        {children}
      </div>
    </div>
  );
}

function DownloadBtn({ os, href }) {
  return (
    <a
      href={href}
      style={{
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '8px 12px', borderRadius: 8, fontSize: 13, fontWeight: 500,
        background: 'var(--color-surface-1)', color: 'var(--color-text)',
        border: '1px solid var(--color-border)',
        textDecoration: 'none',
      }}
    >
      <Download size={13} /> {os}
    </a>
  );
}
