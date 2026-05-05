/**
 * Integrations marketplace — browse, connect, disconnect, health-check.
 *
 * Shows every shipped provider grouped by category. Connected providers
 * display their health status (green/red dot) + config preview + disconnect.
 * "needs_oauth" providers show a form that accepts the client_id / secret
 * / webhook URL. "coming_soon" providers render as ghost cards.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Plug, CheckCircle2, AlertCircle, Clock, ExternalLink, X, Loader2, Trash2,
  ShieldCheck, RefreshCw,
} from 'lucide-react';
import {
  listProviders, listConnections, connectProvider, disconnectProvider, pingProvider,
} from '../services/integrations';
import { calendarStart, calendarStatus, calendarDisconnect } from '../services/calendar';
import EmptyState from '../components/EmptyState';


const STATUS_META = {
  available:    { label: 'Ready to connect',  color: 'var(--color-ok)'     },
  needs_oauth:  { label: 'Bring your own key', color: 'var(--color-info)'  },
  coming_soon:  { label: 'Coming soon',        color: 'var(--color-text-dim)' },
};

const AUTH_FIELDS = {
  oauth2:        [
    { key: 'client_id',     label: 'OAuth client ID',     type: 'text' },
    { key: 'client_secret', label: 'OAuth client secret', type: 'password' },
    { key: 'redirect_uri',  label: 'Redirect URI (optional)', type: 'text' },
  ],
  api_key:       [{ key: 'api_key', label: 'API key', type: 'password' }],
  bot_token:     [{ key: 'bot_token', label: 'Bot token', type: 'password' }],
  shared_secret: [{ key: 'webhook_secret', label: 'Shared secret', type: 'password' }],
  webhook:       [{ key: 'webhook_url', label: 'Webhook URL', type: 'text' }],
};


function ConnectForm({ provider, onCancel, onSaved }) {
  const fields = AUTH_FIELDS[provider.auth_type] || AUTH_FIELDS.api_key;
  const [values, setValues] = useState(() =>
    Object.fromEntries(fields.map(f => [f.key, '']))
  );
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  const save = async () => {
    setBusy(true); setErr('');
    try {
      const saved = await connectProvider(provider.key, values);
      onSaved?.(saved);
    } catch (e) { setErr(String(e.message || e)); }
    finally { setBusy(false); }
  };

  return (
    <div style={{
      padding: 12, marginTop: 8, borderTop: '1px solid var(--color-border)',
      display: 'flex', flexDirection: 'column', gap: 8,
    }}>
      {fields.map(f => (
        <div key={f.key}>
          <label style={{ display: 'block', fontSize: 10, color: 'var(--color-text-muted)', marginBottom: 3 }}>
            {f.label}
          </label>
          <input
            type={f.type}
            className="field-input"
            value={values[f.key] || ''}
            onChange={(e) => setValues(v => ({ ...v, [f.key]: e.target.value }))}
            style={{ fontSize: 11, width: '100%' }}
          />
        </div>
      ))}
      {err && <div style={{ fontSize: 11, color: 'var(--color-err)' }}>{err}</div>}
      <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
        <button className="btn-ghost" onClick={onCancel} disabled={busy} style={{ fontSize: 11 }}>
          Cancel
        </button>
        <button className="btn-primary" onClick={save} disabled={busy} style={{ fontSize: 11 }}>
          {busy ? <Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} /> : <Plug size={11} />}
          Connect
        </button>
      </div>
    </div>
  );
}


function GoogleCalendarCard({ provider }) {
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    calendarStatus()
      .then(setStatus)
      .catch(() => setStatus({ configured: false, connected: false }));
  }, []);

  const connect = async () => {
    setBusy(true); setErr('');
    try {
      const { authorize_url } = await calendarStart();
      const popup = window.open(authorize_url, 'google-cal-oauth',
        'width=520,height=620,left=200,top=100');
      const interval = setInterval(() => {
        if (!popup || popup.closed) {
          clearInterval(interval);
          calendarStatus().then(setStatus).catch(() => {});
          setBusy(false);
        }
      }, 1000);
    } catch (e) {
      setErr(e.message || String(e));
      setBusy(false);
    }
  };

  const disconnect = async () => {
    if (!confirm('Disconnect Google Calendar?')) return;
    try {
      await calendarDisconnect();
      setStatus(s => ({ ...s, connected: false, connection: null }));
    } catch (e) { alert(e.message); }
  };

  const isConnected = status?.connected;
  const notConfigured = status && !status.configured;
  const dotColor = isConnected ? 'var(--color-ok)' : 'var(--color-text-dim)';

  return (
    <div className="panel" style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <span style={{ fontSize: 24 }}>{provider.icon || '📅'}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: 13, fontWeight: 600, color: 'var(--color-text)',
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            {provider.name}
            <span style={{
              width: 7, height: 7, borderRadius: '50%', background: dotColor,
              boxShadow: `0 0 6px ${dotColor}`,
            }} />
          </div>
          <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 2 }}>
            {isConnected
              ? `Connected · ${status.connection?.account_email || 'calendar linked'}`
              : notConfigured
              ? 'Set GOOGLE_CLIENT_ID + GOOGLE_CLIENT_SECRET in .env to enable'
              : 'Not connected'}
          </div>
        </div>
      </div>

      <p style={{ fontSize: 11, color: 'var(--color-text-muted)', margin: 0, lineHeight: 1.5 }}>
        {provider.description}
      </p>

      {err && (
        <div style={{
          padding: '4px 8px', fontSize: 10, borderRadius: 'var(--r-sm)',
          background: 'color-mix(in srgb, var(--color-err) 10%, transparent)',
          color: 'var(--color-err)',
        }}>
          <AlertCircle size={10} style={{ verticalAlign: 'middle' }} /> {err}
        </div>
      )}

      <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
        {!isConnected && !notConfigured && (
          <button
            onClick={connect} disabled={busy || status === null}
            className="btn-primary"
            style={{ fontSize: 11, padding: '4px 10px' }}
          >
            {busy
              ? <Loader2 size={10} style={{ animation: 'spin 1s linear infinite' }} />
              : <Plug size={10} />}
            Connect with Google
          </button>
        )}
        {isConnected && (
          <button onClick={disconnect} className="btn-ghost"
            style={{ fontSize: 11, padding: '4px 8px', color: 'var(--color-err)' }}>
            <Trash2 size={10} /> Disconnect
          </button>
        )}
        {provider.docs_url && (
          <a href={provider.docs_url} target="_blank" rel="noreferrer"
            className="btn-ghost"
            style={{ fontSize: 10, padding: '4px 8px', marginLeft: 'auto' }}>
            Docs <ExternalLink size={10} />
          </a>
        )}
      </div>
    </div>
  );
}


function ProviderCard({ provider, connection, onConnected, onDisconnected }) {
  const [expanded, setExpanded] = useState(false);
  const [pinging, setPinging] = useState(false);
  const [health, setHealth] = useState(null);

  const statusMeta = STATUS_META[provider.status] || STATUS_META.coming_soon;
  const isConnected = !!connection;
  const canConnect = provider.status !== 'coming_soon';

  const doDisconnect = async () => {
    if (!confirm(`Disconnect ${provider.name}?`)) return;
    try {
      await disconnectProvider(provider.key);
      onDisconnected?.(provider.key);
    } catch (e) { alert(e.message); }
  };

  const doPing = async () => {
    setPinging(true);
    try {
      const r = await pingProvider(provider.key);
      setHealth(r);
    } catch (e) { setHealth({ ok: false, error: e.message }); }
    finally { setPinging(false); }
  };

  const healthOk = connection?.last_health_ok;
  const dotColor = isConnected
    ? (healthOk === 1 ? 'var(--color-ok)'
       : healthOk === 0 ? 'var(--color-err)'
       : 'var(--color-warn)')
    : statusMeta.color;

  return (
    <div className="panel" style={{
      padding: 14, display: 'flex', flexDirection: 'column', gap: 8,
      opacity: provider.status === 'coming_soon' ? 0.55 : 1,
      borderStyle: provider.status === 'coming_soon' ? 'dashed' : 'solid',
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
        <span style={{ fontSize: 24 }}>{provider.icon || '🔌'}</span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontSize: 13, fontWeight: 600, color: 'var(--color-text)',
            display: 'flex', alignItems: 'center', gap: 6,
          }}>
            {provider.name}
            <span style={{
              width: 7, height: 7, borderRadius: '50%', background: dotColor,
              boxShadow: `0 0 6px ${dotColor}`,
            }} />
          </div>
          <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 2 }}>
            {isConnected
              ? (healthOk === 1 ? 'Connected · healthy'
                 : healthOk === 0 ? 'Connected · error — check health'
                 : 'Connected · not yet pinged')
              : statusMeta.label}
          </div>
        </div>
      </div>

      <p style={{
        fontSize: 11, color: 'var(--color-text-muted)',
        margin: 0, lineHeight: 1.5,
      }}>
        {provider.description}
      </p>

      {connection?.last_health_error && (
        <div style={{
          padding: '4px 8px', fontSize: 10, borderRadius: 'var(--r-sm)',
          background: 'color-mix(in srgb, var(--color-err) 10%, transparent)',
          color: 'var(--color-err)',
        }}>
          <AlertCircle size={10} style={{ verticalAlign: 'middle' }} /> {connection.last_health_error}
        </div>
      )}

      <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
        {!isConnected && canConnect && (
          <button
            onClick={() => setExpanded(x => !x)}
            className="btn-primary"
            style={{ fontSize: 11, padding: '4px 10px' }}
          >
            <Plug size={10} /> {expanded ? 'Cancel' : 'Connect'}
          </button>
        )}
        {isConnected && (
          <>
            <button
              onClick={doPing} disabled={pinging}
              className="btn-ghost"
              style={{ fontSize: 11, padding: '4px 8px' }}
            >
              <RefreshCw size={10} style={pinging ? { animation: 'spin 1s linear infinite' } : {}} />
              Health check
            </button>
            <button
              onClick={doDisconnect}
              className="btn-ghost"
              style={{ fontSize: 11, padding: '4px 8px', color: 'var(--color-err)' }}
            >
              <Trash2 size={10} /> Disconnect
            </button>
          </>
        )}
        {provider.docs_url && (
          <a
            href={provider.docs_url} target="_blank" rel="noreferrer"
            className="btn-ghost"
            style={{ fontSize: 10, padding: '4px 8px', marginLeft: 'auto' }}
          >
            Docs <ExternalLink size={10} />
          </a>
        )}
      </div>

      {expanded && !isConnected && canConnect && (
        <ConnectForm
          provider={provider}
          onCancel={() => setExpanded(false)}
          onSaved={(c) => { setExpanded(false); onConnected?.(c); }}
        />
      )}

      {health && (
        <div style={{
          fontSize: 10, padding: 6, borderRadius: 'var(--r-sm)',
          background: health.ok
            ? 'color-mix(in srgb, var(--color-ok) 8%, transparent)'
            : 'color-mix(in srgb, var(--color-err) 8%, transparent)',
          color: health.ok ? 'var(--color-ok)' : 'var(--color-err)',
        }}>
          {health.ok
            ? <><CheckCircle2 size={9} style={{ verticalAlign: 'middle' }} /> Healthy</>
            : <><AlertCircle size={9} style={{ verticalAlign: 'middle' }} /> {health.error || 'Unknown error'}</>}
        </div>
      )}
    </div>
  );
}


export default function Integrations() {
  const [providers, setProviders] = useState([]);
  const [categories, setCategories] = useState({});
  const [connections, setConnections] = useState({});   // keyed by provider
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  const load = useCallback(async () => {
    setLoading(true); setErr('');
    try {
      const [cat, conns] = await Promise.all([listProviders(), listConnections()]);
      setProviders(cat.providers || []);
      setCategories(cat.categories || {});
      const byProvider = {};
      for (const c of conns) byProvider[c.provider] = c;
      setConnections(byProvider);
    } catch (e) { setErr(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const byCategory = useMemo(() => {
    const out = {};
    for (const p of providers) {
      const k = p.category || 'other';
      if (!out[k]) out[k] = [];
      out[k].push(p);
    }
    return out;
  }, [providers]);

  const connectedCount = Object.keys(connections).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <h1>Integrations</h1>
        <p>
          Connect NexusAgent to the tools you already use.{' '}
          <strong style={{ color: 'var(--color-text)' }}>{connectedCount}</strong> active connection{connectedCount === 1 ? '' : 's'}.
        </p>
      </div>

      <div className="page-body">
        {err && (
          <div className="panel" style={{ color: 'var(--color-err)', fontSize: 12 }}>{err}</div>
        )}

        {loading && (
          <div style={{ color: 'var(--color-text-dim)', fontSize: 12, padding: 20 }}>Loading…</div>
        )}

        {!loading && providers.length === 0 && (
          <EmptyState
            icon={Plug}
            title="No integrations available"
            description="The integration catalog could not be loaded. Check the backend is reachable."
          />
        )}

        {!loading && Object.entries(byCategory).map(([cat, items]) => (
          <div key={cat} style={{ marginBottom: 22 }}>
            <h3 style={{
              display: 'flex', alignItems: 'center', gap: 8, margin: 0,
              fontSize: 13, color: 'var(--color-text-muted)',
              textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10,
            }}>
              {categories[cat] || cat}
            </h3>
            <div style={{
              display: 'grid', gap: 10,
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            }}>
              {items.map(p => (
                p.key === 'google_calendar'
                  ? <GoogleCalendarCard key={p.key} provider={p} />
                  : <ProviderCard
                      key={p.key}
                      provider={p}
                      connection={connections[p.key]}
                      onConnected={load}
                      onDisconnected={load}
                    />
              ))}
            </div>
          </div>
        ))}

        <div className="panel" style={{
          marginTop: 4, padding: 14, fontSize: 11, color: 'var(--color-text-muted)',
          lineHeight: 1.55, display: 'flex', alignItems: 'flex-start', gap: 10,
        }}>
          <ShieldCheck size={14} color="var(--color-info)" style={{ flexShrink: 0, marginTop: 2 }} />
          <div>
            <strong style={{ color: 'var(--color-text)' }}>Privacy note.</strong>{' '}
            Credentials you paste here are stored in your local SQLite database and sent only
            to the provider you enable. Inbound webhooks arrive at <code>/api/webhooks/{'{provider}'}</code>{' '}
            and are HMAC-verified against your shared secret — unsigned payloads are rejected.
          </div>
        </div>
      </div>
    </div>
  );
}
