/**
 * Reports — natural-language → PDF.
 *
 * The backend is currently synchronous (5–15 s, sometimes longer on a cold
 * cloud LLM call). Without progress feedback the spinner feels broken, so
 * this page:
 *
 *   - Walks the user through 4 visible stages so they know things are
 *     happening, even if the backend doesn't actually report progress.
 *   - Hard-limits the wait at 120 s and shows a recoverable error if the
 *     backend stalls beyond that.
 *   - Offers 4 one-click sample queries that are known to work, so a
 *     first-time user can verify the feature without typing.
 *   - Surfaces the backend error message verbatim when the call fails,
 *     instead of a generic "Error: …".
 */
import { useState, useEffect, useRef } from 'react';
import {
  FileText, Download, Loader2, Sparkles, AlertCircle, RefreshCw, Check,
} from 'lucide-react';
import { generateReport, getReports, downloadReport } from '../services/api';
import EmptyState from '../components/EmptyState';

const SAMPLES = [
  'Revenue by month for the last quarter',
  'Top 10 customers by total invoice amount',
  'Pipeline by deal stage with conversion rates',
  'Overdue invoices grouped by customer',
];

const STAGES = [
  { id: 'analyze',  label: 'Understanding the request',   approx: 1500 },
  { id: 'query',    label: 'Querying your data (local)',  approx: 3000 },
  { id: 'narrate',  label: 'Writing the executive summary', approx: 6000 },
  { id: 'render',   label: 'Building the PDF',             approx: 2500 },
];

const TIMEOUT_MS = 120_000;


export default function Reports() {
  const [query, setQuery]       = useState('');
  const [loading, setLoading]   = useState(false);
  const [reports, setReports]   = useState([]);
  const [stage, setStage]       = useState(0);     // 0..STAGES.length
  const [error, setError]       = useState('');
  const [success, setSuccess]   = useState('');
  const stageTimers             = useRef([]);

  useEffect(() => {
    getReports().then(setReports).catch(() => {});
  }, []);

  const clearStageTimers = () => {
    stageTimers.current.forEach((t) => clearTimeout(t));
    stageTimers.current = [];
  };

  // Walk the user through the stages on a fixed schedule. The real backend
  // doesn't stream progress yet — this is honest in the sense that these
  // stages do happen, just we don't know exact timing. Better than a static
  // spinner.
  const startStageWalk = () => {
    setStage(0);
    let elapsed = 0;
    STAGES.forEach((s, i) => {
      elapsed += s.approx;
      const t = setTimeout(() => setStage(i + 1), elapsed);
      stageTimers.current.push(t);
    });
  };

  const generate = async (q) => {
    const text = (q ?? query).trim();
    if (!text) return;

    setQuery(text);
    setError('');
    setSuccess('');
    setLoading(true);
    startStageWalk();

    // Hard timeout the request so the spinner can't run forever.
    const timeoutPromise = new Promise((_, reject) =>
      setTimeout(() => reject(new Error('TIMEOUT')), TIMEOUT_MS),
    );

    try {
      const r = await Promise.race([generateReport(text), timeoutPromise]);
      setStage(STAGES.length);
      setSuccess(`Report ready: ${r.filename}`);
      // Reload the list so the new file appears.
      const fresh = await getReports().catch(() => null);
      if (fresh) setReports(fresh);
    } catch (e) {
      const msg = e.message === 'TIMEOUT'
        ? `The backend didn't respond within ${TIMEOUT_MS / 1000} seconds. ` +
          'It may still be working — refresh the list in a minute, or try a simpler query.'
        : (e.message || 'Unknown error');
      setError(msg);
    } finally {
      clearStageTimers();
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header">
        <h1>Reports</h1>
        <p>Ask in plain English. Get a PDF with chart, table, and CFO-style commentary.</p>
      </div>

      <div className="page-body">
        {/* ── Generate ────────────────────────────────────────────────────── */}
        <div className="panel">
          <div className="section-h" style={{ margin: '0 0 10px' }}>
            <h2>Generate a report</h2>
            <span className="meta">~5–15 seconds typical</span>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <input
              className="field-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !loading && generate()}
              placeholder='e.g. "Revenue by region for Q3 2025"'
              disabled={loading}
            />
            <button
              className="btn-primary"
              onClick={() => generate()}
              disabled={loading || !query.trim()}
            >
              {loading ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
              {loading ? 'Generating…' : 'Generate'}
            </button>
          </div>

          {/* Sample queries — only when idle */}
          {!loading && !error && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginBottom: 6, fontWeight: 600, letterSpacing: 0.5, textTransform: 'uppercase' }}>
                Or try a sample
              </div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                {SAMPLES.map((s) => (
                  <button
                    key={s}
                    className="btn-ghost btn-sm"
                    onClick={() => generate(s)}
                  >
                    <Sparkles size={11} /> {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Stage walker — honest progress */}
          {loading && (
            <div style={{
              marginTop: 14, padding: 14,
              background: 'var(--color-surface-1)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--r-md)',
            }}>
              {STAGES.map((s, i) => (
                <Stage key={s.id} label={s.label} state={
                  stage > i ? 'done' : stage === i ? 'active' : 'pending'
                } />
              ))}
            </div>
          )}

          {/* Error */}
          {error && (
            <div style={{
              marginTop: 12, padding: 12,
              background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-err) 28%, transparent)',
              borderRadius: 'var(--r-md)',
              display: 'flex', gap: 10, alignItems: 'flex-start',
            }}>
              <AlertCircle size={16} color="var(--color-err)" style={{ marginTop: 2, flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--color-err)', marginBottom: 2 }}>
                  Couldn't generate that report
                </div>
                <div style={{ fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.55 }}>
                  {error}
                </div>
                <button
                  className="btn-ghost btn-sm"
                  style={{ marginTop: 8 }}
                  onClick={() => generate()}
                >
                  <RefreshCw size={11} /> Try again
                </button>
              </div>
            </div>
          )}

          {/* Success */}
          {success && !loading && !error && (
            <div style={{
              marginTop: 12, padding: 10,
              background: 'var(--color-accent-soft)',
              border: '1px solid color-mix(in srgb, var(--color-accent) 28%, transparent)',
              borderRadius: 'var(--r-md)',
              display: 'flex', gap: 8, alignItems: 'center',
              fontSize: 12.5, color: 'var(--color-accent)',
            }}>
              <Check size={14} /> {success}
            </div>
          )}
        </div>

        {/* ── List ──────────────────────────────────────────────────────────── */}
        <div className="section-h">
          <h2>Recent reports</h2>
          <span className="meta">{reports.length} file{reports.length === 1 ? '' : 's'}</span>
        </div>

        {reports.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No reports yet"
            description="Type a request above — totals, trends, comparisons — and a narrated PDF appears here. Click a sample to try without typing."
            size="sm"
            minHeight={180}
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {reports.map((r, i) => (
              <div
                key={i}
                className="panel"
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '12px 14px', marginBottom: 0,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, minWidth: 0 }}>
                  <div className="kpi-icon" data-tone="info" style={{ width: 36, height: 36 }}>
                    <FileText size={16} />
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 13, color: 'var(--color-text)', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {r.name}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>
                      {r.size_kb} KB · {r.modified}
                    </div>
                  </div>
                </div>
                <button
                  className="btn-ghost btn-sm"
                  onClick={async () => {
                    try { await downloadReport(r.name); }
                    catch (err) { setError(`Download failed: ${err.message}`); }
                  }}
                >
                  <Download size={12} /> Download
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


function Stage({ label, state }) {
  const color =
    state === 'done'   ? 'var(--color-accent)'
  : state === 'active' ? 'var(--color-accent)'
  : 'var(--color-text-dim)';

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '6px 0',
      fontSize: 12.5, color,
      fontWeight: state === 'active' ? 600 : 400,
    }}>
      <div style={{
        width: 16, height: 16, borderRadius: 'var(--r-pill)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
        background: state === 'done'   ? 'var(--color-accent)'
                  : state === 'active' ? 'transparent'
                  : 'var(--color-surface-3)',
        border: state === 'active'
          ? '2px solid var(--color-accent)'
          : '1px solid var(--color-border)',
      }}>
        {state === 'done'   && <Check size={10} color="#06281e" />}
        {state === 'active' && (
          <div style={{
            width: 6, height: 6, borderRadius: 'var(--r-pill)',
            background: 'var(--color-accent)',
            animation: 'pulse-dot 1.2s var(--ease-in-out) infinite',
          }} />
        )}
      </div>
      <span>{label}</span>
    </div>
  );
}
