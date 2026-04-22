import { useState } from 'react';
import { Play, ArrowDown, ArrowUp } from 'lucide-react';
import { runWhatIf } from '../services/api';

const EXAMPLES = [
  "What if our revenue drops 20%?",
  "What if we increase prices by 10% and lose 15% of customers?",
  "What if the South region improves by 30%?",
  "What if our top product's sales dropped 25%?",
];

export default function WhatIf() {
  const [scenario, setScenario] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const run = async () => {
    if (!scenario.trim()) return;
    setLoading(true); setError(''); setResult(null);
    try { const r = await runWhatIf(scenario); r.error ? setError(r.error) : setResult(r); }
    catch (e) { setError(e.message); }
    setLoading(false);
  };

  const pct = result?.net_impact_pct || 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header"><h1>What-If Simulator</h1><p>Model business scenarios and get AI-powered impact analysis</p></div>
      <div className="page-body">
        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <input className="field-input" value={scenario} onChange={e => setScenario(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && run()} placeholder="Describe a business scenario..." />
          <button className="btn-primary" onClick={run} disabled={loading || !scenario.trim()}>
            <Play size={14} /> {loading ? 'Running...' : 'Simulate'}
          </button>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 16 }}>
          {EXAMPLES.map((ex, i) => (
            <button key={i} className="btn-ghost" onClick={() => setScenario(ex)} style={{ fontSize: 11 }}>{ex.substring(0, 38)}...</button>
          ))}
        </div>

        {error && <div className="panel" style={{ color: '#f87171', borderColor: '#f8717120' }}>{error}</div>}

        {result && (<>
          <div className="panel"><p style={{ fontSize: 13, color: 'white', fontWeight: 500 }}>{result.scenario_description}</p></div>
          <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
            <div className="stat-card"><div className="value">${(result.before_total_revenue || 0).toLocaleString()}</div><div className="label">Before Revenue</div></div>
            <div className="stat-card">
              <div className="value">${(result.after_total_revenue || 0).toLocaleString()}</div>
              <div style={{ fontSize: 12, fontWeight: 600, marginTop: 2, color: pct >= 0 ? '#4ade80' : '#f87171', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                {pct >= 0 ? <ArrowUp size={12} /> : <ArrowDown size={12} />}{Math.abs(pct).toFixed(1)}%
              </div>
              <div className="label">After Revenue</div>
            </div>
            <div className="stat-card"><div className="value">{result.net_impact || 'N/A'}</div><div className="label">Net Impact</div></div>
          </div>
          {result.assumptions && <div className="panel"><h3>Assumptions</h3><p style={{ fontSize: 12, color: '#94a3b8', whiteSpace: 'pre-wrap' }}>{result.assumptions}</p></div>}
          {result.critique && <div className="panel"><h3>CFO Critique</h3><p style={{ fontSize: 12, color: '#94a3b8', whiteSpace: 'pre-wrap' }}>{result.critique}</p></div>}
        </>)}
      </div>
    </div>
  );
}
