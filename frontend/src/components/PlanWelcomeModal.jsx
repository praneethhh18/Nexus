/**
 * Plan welcome modal — fires on /?welcome=<plan> after a verified payment.
 *
 * Reads the plan key from the URL query string, fetches the live plan
 * catalogue from /api/billing/plans, and shows:
 *   - Confetti header ("Welcome to Pro!")
 *   - Receipt summary (amount + payment cycle)
 *   - "What's now unlocked" feature list (top 6)
 *   - Quick-start CTAs:
 *       • "Start your first AI agent" → /agents
 *       • "Invite your team" → /team  (only if plan unlocks more seats)
 *       • "Maybe later" closes the modal
 *
 * On close: strips ?welcome from the URL so a refresh doesn't re-open it.
 *
 * Designed to ALSO drive feature spotlight (F) and team invite nudge (G)
 * from the post-purchase plan in one place — no separate components needed
 * for the first version.
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, X, ArrowRight, Users, Zap, CheckCircle2 } from 'lucide-react';
import { getPlans } from '../services/billing';

export default function PlanWelcomeModal() {
  const navigate = useNavigate();
  const [planKey, setPlanKey] = useState(null);
  const [planMeta, setPlanMeta] = useState(null);

  useEffect(() => {
    // Read ?welcome=<key> exactly once on mount.
    const params = new URLSearchParams(window.location.search);
    const k = params.get('welcome');
    if (!k) return;
    setPlanKey(k);
    // Fetch live catalogue so prices/features can't drift between the
    // hardcoded TIERS list and the actual paid plan. /plans is public.
    getPlans()
      .then(({ plans }) => setPlanMeta(plans?.[k] || null))
      .catch(() => setPlanMeta(null));
  }, []);

  const close = () => {
    setPlanKey(null);
    // Strip ?welcome from the URL without reloading. Keeps history clean.
    const url = new URL(window.location.href);
    url.searchParams.delete('welcome');
    window.history.replaceState({}, '', url.pathname + (url.search || ''));
  };

  if (!planKey) return null;

  const label = planMeta?.label || planKey.toUpperCase();
  const price = planMeta?.price_inr ?? null;
  const period = planMeta?.period === 'monthly' ? '/month'
                : planMeta?.period === 'one-time' ? 'one-time'
                : planMeta?.period || '';
  const features = (planMeta?.features || []).slice(0, 6);
  const usersLimit = planMeta?.limits?.users || 1;

  return (
    <div
      onClick={close}
      style={{
        position: 'fixed', inset: 0, zIndex: 9999,
        background: 'rgba(15, 23, 42, 0.65)',
        backdropFilter: 'blur(6px)',
        display: 'grid', placeItems: 'center', padding: 16,
        animation: 'fade-in 200ms ease-out',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: 500, width: '100%',
          background: 'var(--color-surface-0)',
          borderRadius: 16,
          overflow: 'hidden',
          boxShadow: '0 24px 60px rgba(0,0,0,0.4)',
          animation: 'fade-up 320ms cubic-bezier(0.2, 0.9, 0.3, 1.2)',
        }}
      >
        {/* Header — gradient hero with the "welcome" copy */}
        <div style={{
          background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
          padding: '32px 28px 26px',
          color: '#fff',
          position: 'relative',
        }}>
          <button
            onClick={close}
            aria-label="Close"
            style={{
              position: 'absolute', top: 14, right: 14,
              background: 'rgba(255,255,255,0.15)',
              border: 'none', color: '#fff',
              width: 28, height: 28, borderRadius: 8,
              cursor: 'pointer',
              display: 'grid', placeItems: 'center',
            }}
          >
            <X size={14} />
          </button>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            background: 'rgba(255,255,255,0.18)',
            padding: '4px 10px', borderRadius: 999,
            fontSize: 11, fontWeight: 600, letterSpacing: 0.6,
            textTransform: 'uppercase', marginBottom: 10,
          }}>
            <Sparkles size={12} /> Payment received
          </div>
          <h2 style={{ margin: 0, fontSize: 26, fontWeight: 700, letterSpacing: '-0.02em' }}>
            Welcome to {label}
          </h2>
          {price !== null && price > 0 && (
            <p style={{ margin: '6px 0 0', opacity: 0.9, fontSize: 14 }}>
              ₹{price.toLocaleString('en-IN')} {period} — your account is now active.
            </p>
          )}
        </div>

        {/* Body */}
        <div style={{ padding: '24px 28px' }}>
          {features.length > 0 && (
            <>
              <div style={{
                fontSize: 11, fontWeight: 700, letterSpacing: 0.6,
                textTransform: 'uppercase', color: 'var(--color-text-dim)',
                marginBottom: 12,
              }}>
                What's now unlocked
              </div>
              <ul style={{
                listStyle: 'none', padding: 0, margin: '0 0 22px',
                display: 'flex', flexDirection: 'column', gap: 8,
              }}>
                {features.map((f, i) => (
                  <li key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 8,
                    fontSize: 13.5, color: 'var(--color-text)',
                    lineHeight: 1.5,
                  }}>
                    <CheckCircle2
                      size={15}
                      style={{ color: '#10B981', flexShrink: 0, marginTop: 2 }}
                    />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          <div style={{
            fontSize: 11, fontWeight: 700, letterSpacing: 0.6,
            textTransform: 'uppercase', color: 'var(--color-text-dim)',
            marginBottom: 10,
          }}>
            Get started
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
            <button
              onClick={() => { close(); navigate('/agents'); }}
              className="btn-primary"
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                justifyContent: 'space-between', width: '100%',
                padding: '11px 14px', textAlign: 'left',
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <Zap size={14} /> Activate your AI agents
              </span>
              <ArrowRight size={14} />
            </button>

            {/* Team invite nudge — show only if the plan unlocks >1 user. */}
            {usersLimit > 1 && (
              <button
                onClick={() => { close(); navigate('/team'); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  justifyContent: 'space-between', width: '100%',
                  padding: '11px 14px', textAlign: 'left',
                  background: 'var(--color-surface-1)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 8, cursor: 'pointer',
                  color: 'var(--color-text)',
                }}
              >
                <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Users size={14} />
                  Invite up to {usersLimit - 1} teammate{usersLimit > 2 ? 's' : ''}
                </span>
                <ArrowRight size={14} />
              </button>
            )}
          </div>

          <p style={{
            fontSize: 11.5, color: 'var(--color-text-dim)',
            margin: 0, textAlign: 'center', lineHeight: 1.5,
          }}>
            Receipt + GST invoice on its way to your email.<br/>
            Need anything? Reply to that email — we read every one.
          </p>
        </div>
      </div>
    </div>
  );
}
