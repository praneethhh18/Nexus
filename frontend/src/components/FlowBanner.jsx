import { useState } from 'react';
import { ArrowRight, X, Info } from 'lucide-react';

/**
 * Explains how the current page fits the business flow:
 *   Lead → Deal → Task → Invoice → Paid
 * Renders a single strip at the top of CRM / Tasks / Invoices pages,
 * with the current step highlighted. Dismissable per-page via localStorage.
 */

const STEPS = [
  { key: 'lead',    label: 'Lead',    desc: 'A new contact lands in CRM' },
  { key: 'deal',    label: 'Deal',    desc: 'Move through the pipeline' },
  { key: 'task',    label: 'Task',    desc: 'Work to close the deal' },
  { key: 'invoice', label: 'Invoice', desc: 'Bill the customer' },
  { key: 'paid',    label: 'Paid',    desc: 'Revenue in the bank' },
];

export default function FlowBanner({ currentStep }) {
  const storageKey = `nexus_flow_banner_${currentStep}_dismissed`;
  const [dismissed, setDismissed] = useState(
    typeof window !== 'undefined' && localStorage.getItem(storageKey) === '1'
  );
  if (dismissed) return null;

  return (
    <div style={{
      padding: '12px 14px',
      marginBottom: 14,
      borderRadius: 'var(--r-lg)',
      background: 'color-mix(in srgb, var(--color-accent) 6%, var(--color-surface-2))',
      border: '1px solid color-mix(in srgb, var(--color-accent) 22%, transparent)',
      display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6,
        color: 'var(--color-accent)',
        fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.6,
        flexShrink: 0,
      }}>
        <Info size={13} /> How this fits the flow
      </div>

      <div style={{
        display: 'flex', alignItems: 'center', gap: 4,
        flex: 1, minWidth: 320, flexWrap: 'wrap',
      }}>
        {STEPS.map((s, i) => {
          const active = s.key === currentStep;
          return (
            <div key={s.key} style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div
                title={s.desc}
                style={{
                  padding: '4px 10px',
                  borderRadius: 'var(--r-pill)',
                  fontSize: 11,
                  fontWeight: active ? 600 : 500,
                  color: active ? 'var(--color-accent)' : 'var(--color-text-muted)',
                  background: active ? 'color-mix(in srgb, var(--color-accent) 14%, transparent)' : 'transparent',
                  border: `1px solid ${active ? 'color-mix(in srgb, var(--color-accent) 30%, transparent)' : 'var(--color-border)'}`,
                  whiteSpace: 'nowrap',
                  transition: 'all var(--dur-fast) var(--ease-out)',
                }}
              >
                {s.label}
              </div>
              {i < STEPS.length - 1 && (
                <ArrowRight size={11} color="var(--color-text-dim)" style={{ flexShrink: 0 }} />
              )}
            </div>
          );
        })}
      </div>

      <button
        onClick={() => { localStorage.setItem(storageKey, '1'); setDismissed(true); }}
        title="Hide this hint"
        style={{
          background: 'none', border: 'none',
          color: 'var(--color-text-dim)', cursor: 'pointer',
          padding: 4, display: 'flex', alignItems: 'center', flexShrink: 0,
        }}
      >
        <X size={14} />
      </button>
    </div>
  );
}
