/**
 * Self-contained "Connect your WhatsApp" widget for the Settings page.
 *
 * State machine:
 *   idle           → user hasn't started connecting (shows "Connect" button)
 *   connecting     → backend says bridge is initialising; show spinner
 *   qr_pending     → QR available; render it; poll for status change
 *   connected      → show profile (phone, name); offer Disconnect
 *   disconnected   → connection dropped; show retry button + last error
 *   logged_out     → WhatsApp side terminated session; needs full reconnect
 *
 * Polls /api/whatsapp/tenant/status every 2 seconds while QR is on screen.
 * Stops polling on "connected" or after 5 min (saves backend cycles).
 */
import { useEffect, useState, useRef, useCallback } from 'react';
import { QRCodeSVG } from 'qrcode.react';
import {
  MessageSquare, Smartphone, CheckCircle2, XCircle, Loader2,
  Power, RefreshCw, AlertTriangle,
} from 'lucide-react';
import {
  connectWhatsApp, getWhatsAppStatus, disconnectWhatsApp,
} from '../services/whatsapp_tenant';

const POLL_MS = 2000;
const MAX_POLL_TIME_MS = 5 * 60 * 1000;   // give up after 5 min

// Status pill, declared at module scope (not inside the parent component)
// so React's static-components rule passes and we don't recreate the
// component on every render. Stateless, takes `status` as a prop.
const STATUS_MAP = {
  idle:         { color: 'var(--color-text-dim)',    label: 'Not connected',        Icon: MessageSquare },
  connecting:   { color: '#3B82F6',                  label: 'Connecting…',           Icon: Loader2,        spin: true },
  qr_pending:   { color: '#F59E0B',                  label: 'Waiting for scan',      Icon: Smartphone },
  connected:    { color: '#10B981',                  label: 'Connected',             Icon: CheckCircle2 },
  disconnected: { color: '#EF4444',                  label: 'Disconnected',          Icon: XCircle },
  logged_out:   { color: '#EF4444',                  label: 'Logged out',            Icon: AlertTriangle },
};

function StatusChip({ status }) {
  const s = STATUS_MAP[status] || STATUS_MAP.idle;
  const Icon = s.Icon;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '3px 9px', borderRadius: 999,
      fontSize: 11, fontWeight: 600,
      background: 'color-mix(in srgb, ' + s.color + ' 18%, transparent)',
      color: s.color,
    }}>
      <Icon size={12} style={s.spin ? { animation: 'spin 1s linear infinite' } : undefined} />
      {s.label}
    </span>
  );
}

export default function WhatsAppConnect() {
  const [status, setStatus] = useState('idle');
  const [qr, setQr] = useState(null);
  const [profile, setProfile] = useState(null);
  const [lastError, setLastError] = useState('');
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  // Refs for cleanup, poll timer + start time. Setting state inside the
  // poll wouldn't auto-stop the interval; we manage it imperatively.
  const pollTimer = useRef(null);
  const pollStarted = useRef(0);

  const stopPolling = useCallback(() => {
    if (pollTimer.current) {
      clearInterval(pollTimer.current);
      pollTimer.current = null;
    }
  }, []);

  const applySnapshot = useCallback((snap) => {
    if (!snap) return;
    setStatus(snap.status || 'idle');
    setQr(snap.qr || null);
    setProfile(snap.profile || null);
    setLastError(snap.last_error || '');
    if (snap.status === 'connected') {
      stopPolling();
      setMsg('✅ WhatsApp connected. Inbound messages will now route through NexusAgent.');
    }
    if (snap.status === 'logged_out') {
      stopPolling();
      setMsg('Your WhatsApp session was terminated. Disconnect + reconnect to pair again.');
    }
  }, [stopPolling]);

  const startPolling = useCallback(() => {
    stopPolling();
    pollStarted.current = Date.now();
    pollTimer.current = setInterval(async () => {
      if (Date.now() - pollStarted.current > MAX_POLL_TIME_MS) {
        stopPolling();
        setMsg('Connection attempt timed out. Click Connect to try again.');
        return;
      }
      try {
        const snap = await getWhatsAppStatus();
        applySnapshot(snap);
      } catch {
        // Network blip, keep polling silently. The next successful poll
        // will refresh the UI; flashing transient errors is just noise.
      }
    }, POLL_MS);
  }, [applySnapshot, stopPolling]);

  // Initial: get current state on mount. Lets a refresh resume a connected
  // session display without making the user click Connect again.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const snap = await getWhatsAppStatus();
        if (!cancelled) applySnapshot(snap);
      } catch {
        // Bridge not running, plan-gated, etc., silent; user can click
        // Connect and we'll surface the real error then.
      }
    })();
    return () => { cancelled = true; stopPolling(); };
  }, [applySnapshot, stopPolling]);

  const handleConnect = async () => {
    setBusy(true);
    setMsg('');
    setLastError('');
    try {
      const snap = await connectWhatsApp();
      applySnapshot(snap);
      // Once the bridge is connecting, start polling for QR + status changes.
      startPolling();
    } catch (e) {
      const m = String(e?.message || '');
      if (/requires the .* plan/i.test(m)) {
        setMsg('WhatsApp is a Starter plan feature. Upgrade at /pricing.');
      } else if (/bridge unreachable/i.test(m)) {
        setMsg('WhatsApp bridge isn\'t running. Start it: cd whatsapp_bridge && npm start');
      } else {
        setMsg(m || 'Failed to start connection');
      }
    } finally {
      setBusy(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Disconnect WhatsApp? You\'ll need to scan the QR again to reconnect.')) return;
    setBusy(true);
    try {
      await disconnectWhatsApp();
      setStatus('idle');
      setQr(null);
      setProfile(null);
      setLastError('');
      setMsg('Disconnected. Click Connect to pair a different WhatsApp number.');
    } catch (e) {
      setMsg(String(e?.message || 'Disconnect failed'));
    } finally {
      setBusy(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────────
  return (
    <div style={{
      padding: 18, borderRadius: 'var(--r-lg, 12px)',
      background: 'var(--color-surface-1)',
      border: '1px solid var(--color-border)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 12 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 10,
          background: '#25D366', color: '#fff',
          display: 'grid', placeItems: 'center', flexShrink: 0,
        }}>
          <MessageSquare size={18} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <strong style={{ fontSize: 14 }}>WhatsApp Business</strong>
            <StatusChip status={status} />
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-text-dim)', marginTop: 2 }}>
            Connect your WhatsApp number so leads can message you and agents auto-reply.
          </div>
        </div>
      </div>

      {/* Message/error banner */}
      {(msg || lastError) && (
        <div style={{
          padding: '8px 11px', borderRadius: 8,
          background: 'var(--color-surface-2)',
          border: '1px solid var(--color-border)',
          fontSize: 12, marginBottom: 12,
          color: lastError ? '#DC2626' : 'var(--color-text)',
        }}>
          {lastError ? `⚠ ${lastError}` : msg}
        </div>
      )}

      {/* State-specific body */}
      {status === 'idle' || status === 'disconnected' ? (
        <button
          onClick={handleConnect}
          disabled={busy}
          className="btn-primary"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 16px', fontSize: 13,
          }}
        >
          {busy ? (
            <>
              <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} />
              Starting…
            </>
          ) : (
            <>
              <Smartphone size={13} /> Connect WhatsApp
            </>
          )}
        </button>
      ) : null}

      {status === 'connecting' && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--color-text-dim)' }}>
          <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} />
          Generating QR code… this takes 2-5 seconds.
        </div>
      )}

      {status === 'qr_pending' && qr && (
        <div style={{
          display: 'flex', flexDirection: 'column', alignItems: 'center',
          gap: 12, padding: '12px 0',
        }}>
          <div style={{
            padding: 14, background: '#fff', borderRadius: 10,
            boxShadow: '0 4px 12px rgba(0,0,0,0.06)',
          }}>
            <QRCodeSVG value={qr} size={232} level="L" />
          </div>
          <ol style={{
            fontSize: 12, color: 'var(--color-text-dim)',
            lineHeight: 1.6, paddingLeft: 18, margin: 0,
            maxWidth: 360,
          }}>
            <li>Open <b>WhatsApp Business</b> on your phone (the number you want connected).</li>
            <li>Tap <b>Settings → Linked Devices → Link a Device</b>.</li>
            <li>Scan this code with your phone.</li>
          </ol>
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
            QR refreshes automatically every ~30s. Don't close this page.
          </div>
        </div>
      )}

      {status === 'connected' && profile && (
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          gap: 12, flexWrap: 'wrap',
        }}>
          <div>
            <div style={{ fontSize: 13, color: 'var(--color-text)' }}>
              <b>+{profile.phone}</b>
              {profile.name && <span style={{ color: 'var(--color-text-dim)' }}> · {profile.name}</span>}
            </div>
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 2 }}>
              Linked {profile.linked_at ? new Date(profile.linked_at).toLocaleString() : ''}
            </div>
          </div>
          <button
            onClick={handleDisconnect}
            disabled={busy}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              padding: '7px 12px', borderRadius: 8,
              background: 'transparent',
              border: '1px solid rgba(239,68,68,0.4)',
              color: '#DC2626', cursor: 'pointer', fontSize: 12,
            }}
          >
            <Power size={12} /> Disconnect
          </button>
        </div>
      )}

      {status === 'logged_out' && (
        <button
          onClick={handleDisconnect}
          disabled={busy}
          className="btn-ghost"
          style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '8px 14px', fontSize: 13,
          }}
        >
          <RefreshCw size={13} /> Reset + reconnect
        </button>
      )}
    </div>
  );
}
