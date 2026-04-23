import { useState, useEffect, useCallback } from 'react';
import { BarChart3, TrendingUp, Zap, AlertTriangle, Activity, Clock, Calendar as CalendarIcon } from 'lucide-react';
import { pipelineVelocity, revenueForecast, agentImpact, churnRisk } from '../services/analytics';

const money = (v, cur = 'USD') => new Intl.NumberFormat('en-US', {
  style: 'currency', currency: cur || 'USD', maximumFractionDigits: 0,
}).format(v || 0);

const STAGE_COLORS = {
  lead: '#60a5fa', qualified: '#a78bfa', proposal: '#f59e0b',
  negotiation: '#ec4899', won: '#22c55e', lost: '#6b7280',
};

const RISK_COLORS = { high: '#ef4444', medium: '#f59e0b', low: '#22c55e' };

function Panel({ icon: Icon, title, action, children, color = '#60a5fa' }) {
  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h3 style={{ display: 'flex', alignItems: 'center', gap: 6, margin: 0 }}>
          <Icon size={15} color={color} /> {title}
        </h3>
        {action}
      </div>
      {children}
    </div>
  );
}

function Velocity({ data }) {
  if (!data) return <p style={{ color: '#64748b', fontSize: 11 }}>Loading…</p>;
  if (data.total_deals_tracked === 0) {
    return <p style={{ color: '#64748b', fontSize: 12 }}>No deals tracked yet — create some to see velocity.</p>;
  }
  const stages = ['lead', 'qualified', 'proposal', 'negotiation', 'won', 'lost'];
  const maxDays = Math.max(1, ...stages.map(s => data.by_stage[s]?.avg_days || 0));
  return (
    <div>
      <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 10 }}>
        Overall lead → won rate: <strong style={{ color: '#22c55e' }}>{data.overall_win_rate_pct ?? '—'}%</strong>
        {' · '}{data.total_deals_tracked} deals tracked
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {stages.map(s => {
          const row = data.by_stage[s] || {};
          const pct = row.avg_days ? (row.avg_days / maxDays) * 100 : 0;
          return (
            <div key={s}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
                <span style={{ color: '#94a3b8', textTransform: 'capitalize' }}>
                  {s} · entered {row.entered_count || 0}
                  {row.win_rate_pct !== null && row.win_rate_pct !== undefined && s !== 'won' && s !== 'lost' &&
                    <> · {row.win_rate_pct}% reach won</>}
                </span>
                <span style={{ color: STAGE_COLORS[s], fontWeight: 600 }}>
                  {row.avg_days === null || row.avg_days === undefined ? '—' : `${row.avg_days}d avg`}
                </span>
              </div>
              <div style={{ height: 5, background: '#0f172a', borderRadius: 3, overflow: 'hidden' }}>
                <div style={{ width: `${Math.min(pct, 100)}%`, height: '100%', background: STAGE_COLORS[s], transition: 'width 0.3s' }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Forecast({ data }) {
  if (!data) return <p style={{ color: '#64748b', fontSize: 11 }}>Loading…</p>;
  if (!data.months?.length) return <p style={{ color: '#64748b', fontSize: 12 }}>No upcoming forecast data — add expected-close dates to your deals.</p>;
  const maxW = Math.max(1, ...data.months.map(m => m.weighted));
  return (
    <div>
      <div style={{ display: 'flex', gap: 16, fontSize: 11, color: '#94a3b8', marginBottom: 10 }}>
        <div>Weighted: <strong style={{ color: '#22c55e', fontSize: 13 }}>{money(data.totals.weighted, data.currency)}</strong></div>
        <div>Unweighted: <strong style={{ color: '#e2e8f0' }}>{money(data.totals.unweighted, data.currency)}</strong></div>
        <div>Deals: <strong style={{ color: '#e2e8f0' }}>{data.totals.deal_count}</strong></div>
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', height: 120 }}>
        {data.months.map(m => {
          const h = (m.weighted / maxW) * 100;
          return (
            <div key={m.month} style={{ flex: 1, textAlign: 'center', minWidth: 0 }}>
              <div style={{ fontSize: 9, color: '#64748b', marginBottom: 4 }}>{money(m.weighted, data.currency)}</div>
              <div style={{ height: `${Math.max(h, 2)}%`, background: 'linear-gradient(180deg, #22c55e, #0f766e)', borderRadius: '4px 4px 0 0', minHeight: 2 }} />
              <div style={{ fontSize: 9, color: '#94a3b8', marginTop: 4 }}>{m.month.substring(5)}</div>
            </div>
          );
        })}
      </div>
      <div style={{ marginTop: 12, padding: 8, background: '#0f172a', borderRadius: 6, fontSize: 10, color: '#64748b' }}>
        Last 90 days won: {money(data.last_90_won?.total_value || 0, data.currency)} · {data.last_90_won?.deal_count || 0} deals
      </div>
    </div>
  );
}

function Impact({ data, days, onDaysChange }) {
  if (!data) return <p style={{ color: '#64748b', fontSize: 11 }}>Loading…</p>;
  const topTools = (data.by_tool || []).slice(0, 8);
  const maxCount = Math.max(1, ...topTools.map(t => t.count));
  return (
    <div>
      <div style={{ display: 'flex', gap: 16, fontSize: 11, color: '#94a3b8', marginBottom: 10 }}>
        <div>Tool calls: <strong style={{ color: '#e2e8f0' }}>{data.total_tool_calls}</strong></div>
        <div>Success: <strong style={{ color: '#22c55e' }}>{data.success_rate_pct}%</strong></div>
        <div>Approvals executed: <strong style={{ color: '#e2e8f0' }}>{data.approvals.executed}</strong></div>
        <div>Minutes saved (est.): <strong style={{ color: '#a78bfa' }}>~{data.estimated_minutes_saved}</strong></div>
      </div>
      {topTools.length === 0 ? (
        <p style={{ color: '#64748b', fontSize: 11 }}>No agent activity in this window yet.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
          {topTools.map(t => {
            const pct = (t.count / maxCount) * 100;
            return (
              <div key={t.tool}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, marginBottom: 2 }}>
                  <code style={{ color: '#e2e8f0' }}>{t.tool}</code>
                  <span style={{ color: '#94a3b8' }}>{t.count} · {t.avg_duration_ms}ms avg</span>
                </div>
                <div style={{ height: 4, background: '#0f172a', borderRadius: 2, overflow: 'hidden' }}>
                  <div style={{ width: `${pct}%`, height: '100%', background: '#a78bfa' }} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function Churn({ data }) {
  if (!data) return <p style={{ color: '#64748b', fontSize: 11 }}>Loading…</p>;
  if (!data.deals?.length) return <p style={{ color: '#64748b', fontSize: 12 }}>No open deals to score.</p>;
  return (
    <div>
      <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 10 }}>
        {data.total_high} high-risk · {data.total_medium} medium-risk · looking at top {data.deals.length} by value
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 320, overflow: 'auto' }}>
        {data.deals.map(d => {
          const color = RISK_COLORS[d.risk_level];
          return (
            <div key={d.deal_id} style={{ padding: 10, background: '#0f172a', borderRadius: 6, borderLeft: `3px solid ${color}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 12, fontWeight: 500, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {d.name}
                  </div>
                  <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>
                    {d.stage} · {money(d.value, d.currency)} · {d.probability_pct || 0}%
                  </div>
                  {d.factors?.length > 0 && (
                    <div style={{ fontSize: 10, color: '#64748b', marginTop: 4 }}>
                      {d.factors.join(' · ')}
                    </div>
                  )}
                  {d.suggested_action && (
                    <div style={{ fontSize: 11, color: '#fbbf24', marginTop: 6, padding: 6, background: '#f59e0b15', borderRadius: 4 }}>
                      💡 {d.suggested_action}
                    </div>
                  )}
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0 }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color }}>{d.risk_score}</div>
                  <div style={{ fontSize: 9, color, textTransform: 'uppercase', fontWeight: 600 }}>{d.risk_level}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function Analytics() {
  const [velocity, setVelocity] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [impact, setImpact] = useState(null);
  const [churn, setChurn] = useState(null);
  const [horizonMonths, setHorizonMonths] = useState(6);
  const [impactDays, setImpactDays] = useState(30);
  const [msg, setMsg] = useState('');

  const reload = useCallback(async () => {
    try {
      const [v, f, i, c] = await Promise.all([
        pipelineVelocity().catch(() => null),
        revenueForecast(horizonMonths).catch(() => null),
        agentImpact(impactDays).catch(() => null),
        churnRisk(15).catch(() => null),
      ]);
      setVelocity(v); setForecast(f); setImpact(i); setChurn(c);
    } catch (e) { setMsg(`Failed: ${e.message}`); }
  }, [horizonMonths, impactDays]);

  useEffect(() => { reload(); }, [reload]);
  useEffect(() => {
    const h = () => reload();
    window.addEventListener('nexus-business-changed', h);
    return () => window.removeEventListener('nexus-business-changed', h);
  }, [reload]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <h1>Analytics</h1>
        <p>Pipeline velocity, revenue forecast, agent impact, and deal churn risk</p>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: '#60a5fa' }}>{msg}</div>}

      <div className="page-body">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <Panel icon={Clock} title="Pipeline velocity" color="#60a5fa">
            <Velocity data={velocity} />
          </Panel>

          <Panel
            icon={TrendingUp}
            title="Revenue forecast"
            color="#22c55e"
            action={
              <select value={horizonMonths} onChange={(e) => setHorizonMonths(parseInt(e.target.value))}
                style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 6, color: '#e2e8f0', fontSize: 11, padding: '4px 8px' }}>
                {[3, 6, 9, 12].map(m => <option key={m} value={m}>{m} months</option>)}
              </select>
            }
          >
            <Forecast data={forecast} />
          </Panel>

          <Panel
            icon={Zap}
            title="Agent impact"
            color="#a78bfa"
            action={
              <select value={impactDays} onChange={(e) => setImpactDays(parseInt(e.target.value))}
                style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 6, color: '#e2e8f0', fontSize: 11, padding: '4px 8px' }}>
                {[7, 14, 30, 60, 90].map(d => <option key={d} value={d}>last {d} days</option>)}
              </select>
            }
          >
            <Impact data={impact} days={impactDays} onDaysChange={setImpactDays} />
          </Panel>

          <Panel icon={AlertTriangle} title="Deal churn risk" color="#ef4444">
            <Churn data={churn} />
          </Panel>
        </div>
      </div>
    </div>
  );
}
