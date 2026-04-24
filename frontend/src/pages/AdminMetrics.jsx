/**
 * Admin metrics dashboard (11.2).
 *
 * Two scopes:
 *   - Global: requires owner/admin role; shows DAU/WAU/MAU + top tenants.
 *   - Tenant: available to any logged-in user; their own business only.
 *
 * Numbers-first layout — KPI tiles at the top, event totals table,
 * day-by-day mini-bar chart for API calls + agent runs (no charting lib,
 * a row of flex'd bars is enough for a snapshot).
 */
import { useEffect, useState } from 'react';
import {
  BarChart3, Users, Activity, Building2, RefreshCw, Loader2, Globe, Home,
} from 'lucide-react';
import { getGlobalMetrics, getTenantMetrics } from '../services/metrics';
import EmptyState from '../components/EmptyState';


function Tile({ icon: Icon, label, value, sub, color = 'var(--color-accent)' }) {
  return (
    <div className="panel" style={{
      padding: 14, display: 'flex', alignItems: 'center', gap: 12,
    }}>
      <div style={{
        width: 38, height: 38, borderRadius: 'var(--r-md)',
        background: `color-mix(in srgb, ${color} 16%, transparent)`,
        color, display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon size={18} />
      </div>
      <div>
        <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{label}</div>
        <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--color-text)' }}>{value}</div>
        {sub && (
          <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 1 }}>{sub}</div>
        )}
      </div>
    </div>
  );
}


function Sparkbars({ series, color }) {
  if (!series || series.length === 0) return null;
  const max = Math.max(1, ...series.map(d => d.count));
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-end', gap: 2,
      height: 60, padding: 4,
      background: 'var(--color-surface-1)', borderRadius: 'var(--r-sm)',
    }}>
      {series.map((d, i) => {
        const h = Math.max(2, Math.round((d.count / max) * 56));
        return (
          <div
            key={d.day}
            title={`${d.day} — ${d.count}`}
            style={{
              flex: 1,
              height: h,
              background: d.count > 0 ? color : 'var(--color-surface-2)',
              borderRadius: 2,
              opacity: 0.85,
            }}
          />
        );
      })}
    </div>
  );
}


export default function AdminMetrics() {
  const [scope, setScope] = useState('tenant');   // 'tenant' | 'global'
  const [days, setDays]   = useState(30);
  const [data, setData]   = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr]     = useState('');

  const load = async () => {
    setLoading(true); setErr('');
    try {
      const d = scope === 'global'
        ? await getGlobalMetrics(days)
        : await getTenantMetrics(days);
      setData(d);
    } catch (e) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-line */ }, [scope, days]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Metrics</h1>
          <p>Usage over the last {days} days</p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            className={scope === 'tenant' ? 'btn-primary' : 'btn-ghost'}
            onClick={() => setScope('tenant')}
            style={{ fontSize: 12 }}
          >
            <Home size={11} /> My business
          </button>
          <button
            className={scope === 'global' ? 'btn-primary' : 'btn-ghost'}
            onClick={() => setScope('global')}
            style={{ fontSize: 12 }}
            title="Admin only — aggregates every tenant"
          >
            <Globe size={11} /> Global
          </button>
          <select
            className="field-select"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            style={{ fontSize: 12 }}
          >
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
          </select>
          <button
            onClick={load}
            disabled={loading}
            className="btn-ghost"
            style={{ fontSize: 12 }}
          >
            <RefreshCw size={11} style={loading ? { animation: 'spin 1s linear infinite' } : {}} />
            Refresh
          </button>
        </div>
      </div>

      <div className="page-body">
        {err && (
          <div className="panel" style={{ color: 'var(--color-err)', fontSize: 12 }}>
            {err}{scope === 'global' && ' — global metrics need owner/admin.'}
          </div>
        )}

        {loading && !data && (
          <div style={{ color: 'var(--color-text-dim)', fontSize: 12, padding: 20 }}>
            <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> Loading…
          </div>
        )}

        {data && (
          <>
            {/* KPI tiles */}
            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: 10, marginBottom: 16,
            }}>
              <Tile icon={Users}      label="Daily active users"   value={data.dau}   color="var(--color-info)" />
              <Tile icon={Users}      label="Weekly active users"  value={data.wau}   color="#a78bfa" />
              <Tile icon={Users}      label="Monthly active users" value={data.mau}   color="var(--color-warn)" />
              <Tile icon={Activity}   label="API calls"            value={(data.totals?.api_call || 0).toLocaleString()} color="var(--color-ok)" />
              <Tile icon={BarChart3}  label="Agent runs"           value={(data.totals?.agent_run || 0).toLocaleString()} color="#ec4899" />
              {data.scope === 'global' && (
                <Tile icon={Building2} label="Active businesses"   value={data.active_businesses} color="var(--color-accent)" />
              )}
            </div>

            {/* Time series */}
            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: 10, marginBottom: 16,
            }}>
              <div className="panel" style={{ padding: 14 }}>
                <h3 style={{ margin: 0, fontSize: 13, color: 'var(--color-text)', marginBottom: 8 }}>
                  API calls · last {days} days
                </h3>
                <Sparkbars series={data.api_series || []} color="var(--color-ok)" />
              </div>
              <div className="panel" style={{ padding: 14 }}>
                <h3 style={{ margin: 0, fontSize: 13, color: 'var(--color-text)', marginBottom: 8 }}>
                  Agent runs · last {days} days
                </h3>
                <Sparkbars series={data.runs_series || []} color="#ec4899" />
              </div>
            </div>

            {/* Event totals */}
            <div className="panel" style={{ padding: 14, marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: 13, color: 'var(--color-text)', marginBottom: 10 }}>
                Event totals
              </h3>
              <table className="data-table" style={{ fontSize: 12, width: '100%' }}>
                <thead><tr><th>Event</th><th style={{ textAlign: 'right' }}>Count</th></tr></thead>
                <tbody>
                  {Object.entries(data.totals || {}).map(([k, v]) => (
                    <tr key={k}>
                      <td><code style={{ fontSize: 10 }}>{k}</code></td>
                      <td style={{ textAlign: 'right' }}>{v.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Top tenants (global only) */}
            {data.scope === 'global' && (
              <div className="panel" style={{ padding: 14 }}>
                <h3 style={{ margin: 0, fontSize: 13, color: 'var(--color-text)', marginBottom: 10 }}>
                  Top tenants by API calls
                </h3>
                {(!data.top_tenants || data.top_tenants.length === 0) ? (
                  <EmptyState
                    icon={Building2}
                    title="No tenant activity yet"
                    description="Once any business generates traffic, they'll appear here ranked by API call volume."
                    size="sm"
                    minHeight={120}
                  />
                ) : (
                  <table className="data-table" style={{ fontSize: 12, width: '100%' }}>
                    <thead>
                      <tr><th>Business ID</th><th style={{ textAlign: 'right' }}>API calls</th></tr>
                    </thead>
                    <tbody>
                      {data.top_tenants.map(t => (
                        <tr key={t.business_id}>
                          <td><code style={{ fontSize: 10 }}>{t.business_id}</code></td>
                          <td style={{ textAlign: 'right' }}>{t.count.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
