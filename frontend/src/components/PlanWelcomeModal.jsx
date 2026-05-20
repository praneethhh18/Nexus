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
import { useEffect, useMemo, useState } from 'react';
import { Sparkles, X, ArrowRight, Zap, CheckCircle2, Gift } from 'lucide-react';
import { getPlans } from '../services/billing';
import { shouldShowOnboarding } from './OnboardingWizard';

// sessionStorage key used to defer the welcome modal until AFTER the first-run
// onboarding wizard has been completed. Without this, a fresh signup saw the
// trial-activated modal stack on top of (or compete with) the setup wizard.
const PENDING_WELCOME_KEY = 'nexus_pending_welcome';

// CSS-only confetti — 60 particles, deterministic placement per session so
// React doesn't re-randomise on every render and cause jitter.
function ConfettiBurst() {
  const pieces = useMemo(() => {
    const colors = ['#6366F1', '#8B5CF6', '#10B981', '#F59E0B', '#EC4899', '#06B6D4'];
    return Array.from({ length: 60 }, (_, i) => ({
      left: Math.random() * 100,
      delay: Math.random() * 0.6,
      duration: 1.6 + Math.random() * 1.6,
      color: colors[i % colors.length],
      size: 6 + Math.random() * 6,
      rotate: Math.random() * 360,
      drift: (Math.random() - 0.5) * 80,
    }));
  }, []);
  return (
    <div style={{
      position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none',
    }} aria-hidden>
      {pieces.map((p, i) => (
        <span
          key={i}
          style={{
            position: 'absolute',
            top: -20,
            left: `${p.left}%`,
            width: p.size, height: p.size * 0.45,
            background: p.color,
            transform: `rotate(${p.rotate}deg)`,
            animation: `nexus-confetti-fall ${p.duration}s ${p.delay}s ease-in forwards`,
            ['--drift']: `${p.drift}px`,
          }}
        />
      ))}
      <style>{`
        @keyframes nexus-confetti-fall {
          0%   { transform: translate(0, -20px) rotate(0deg); opacity: 1; }
          80%  { opacity: 1; }
          100% { transform: translate(var(--drift), 520px) rotate(720deg); opacity: 0; }
        }
      `}</style>
    </div>
  );
}

export default function PlanWelcomeModal() {
  const [planKey, setPlanKey] = useState(null);
  const [planMeta, setPlanMeta] = useState(null);
  const isTrial = planKey === 'trial';

  useEffect(() => {
    // Read ?welcome=<key> exactly once on mount, OR a deferred welcome that
    // was parked in sessionStorage by an earlier mount that handed off to
    // the onboarding wizard.
    const params = new URLSearchParams(window.location.search);
    const urlKey = params.get('welcome');
    const stashedKey = sessionStorage.getItem(PENDING_WELCOME_KEY);

    // If a first-run wizard is still pending, defer the welcome modal:
    // stash the key, strip ?welcome from the URL, render nothing. The
    // wizard's celebrated step (or close) re-fires this modal by writing
    // /?welcome=<key> back into the URL. This is what turned 3 stacked
    // modals into a single linear flow.
    if (urlKey && shouldShowOnboarding()) {
      sessionStorage.setItem(PENDING_WELCOME_KEY, urlKey);
      const url = new URL(window.location.href);
      url.searchParams.delete('welcome');
      window.history.replaceState({}, '', url.pathname + (url.search || ''));
      return;
    }

    const k = urlKey || stashedKey;
    if (!k) return;
    if (stashedKey) sessionStorage.removeItem(PENDING_WELCOME_KEY);
    setPlanKey(k);
    // For the trial flow we always show the Pro feature set — the trial
    // unlocks Pro. For paid plans, fetch the live catalogue so prices /
    // features can't drift from the actual Razorpay charge.
    const fetchKey = k === 'trial' ? 'pro' : k;
    getPlans()
      .then(({ plans }) => setPlanMeta(plans?.[fetchKey] || null))
      .catch(() => setPlanMeta(null));
  }, []);

  // Replay handler: when the onboarding wizard finishes, Layout dispatches
  // 'nexus-onboarding-closed'. If we stashed a welcome key while the wizard
  // was open, fire it now so the trial celebration plays AFTER setup, not
  // on top of it.
  useEffect(() => {
    const onWizardClosed = () => {
      const k = sessionStorage.getItem(PENDING_WELCOME_KEY);
      if (!k) return;
      sessionStorage.removeItem(PENDING_WELCOME_KEY);
      setPlanKey(k);
      const fetchKey = k === 'trial' ? 'pro' : k;
      getPlans()
        .then(({ plans }) => setPlanMeta(plans?.[fetchKey] || null))
        .catch(() => setPlanMeta(null));
    };
    window.addEventListener('nexus-onboarding-closed', onWizardClosed);
    return () => window.removeEventListener('nexus-onboarding-closed', onWizardClosed);
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

  return (
    <div
      onClick={close}
      style={{
        position: 'fixed', inset: 0, zIndex: 9999,
        // Heavier backdrop + stronger blur than before so the half-loaded
        // dashboard underneath stops bleeding through the modal copy.
        background: 'rgba(8, 10, 18, 0.88)',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
        display: 'grid', placeItems: 'center', padding: 16,
        animation: 'fade-in 200ms ease-out',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: 500, width: '100%',
          // Surface-1 (one step lighter than the page bg) so the card has
          // visible separation from the very dark backdrop. With surface-0
          // the card and backdrop collapsed to the same dark colour in
          // dark theme and the feature copy was nearly invisible.
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
          borderRadius: 16,
          overflow: 'hidden',
          boxShadow: '0 24px 60px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.04)',
          animation: 'fade-up 320ms cubic-bezier(0.2, 0.9, 0.3, 1.2)',
          color: 'var(--color-text)',
        }}
      >
        {/* Header — gradient hero with the "welcome" copy + confetti on trial */}
        <div style={{
          background: 'linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%)',
          padding: '32px 28px 26px',
          color: '#fff',
          position: 'relative',
          overflow: 'hidden',
        }}>
          {isTrial && <ConfettiBurst />}
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
              zIndex: 2,
            }}
          >
            <X size={14} />
          </button>
          <div style={{ position: 'relative', zIndex: 2 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: 'rgba(255,255,255,0.18)',
              padding: '4px 10px', borderRadius: 999,
              fontSize: 11, fontWeight: 600, letterSpacing: 0.6,
              textTransform: 'uppercase', marginBottom: 10,
            }}>
              {isTrial
                ? <><Gift size={12} /> Trial activated</>
                : <><Sparkles size={12} /> Payment received</>}
            </div>
            <h2 style={{ margin: 0, fontSize: 26, fontWeight: 700, letterSpacing: '-0.02em' }}>
              {isTrial ? '🎉 You\'re on Pro — 14 days, on us' : `Welcome to ${label}`}
            </h2>
            {isTrial ? (
              <p style={{ margin: '6px 0 0', opacity: 0.95, fontSize: 14 }}>
                Full access to all 8 AI agents · no card required · cancel anytime.
              </p>
            ) : (price !== null && price > 0 && (
              <p style={{ margin: '6px 0 0', opacity: 0.9, fontSize: 14 }}>
                ₹{price.toLocaleString('en-IN')} {period} — your account is now active.
              </p>
            ))}
          </div>
        </div>

        {/* Body */}
        <div style={{ padding: '24px 28px' }}>
          {features.length > 0 && (
            <>
              <div style={{
                fontSize: 11, fontWeight: 700, letterSpacing: 0.6,
                textTransform: 'uppercase', color: 'var(--color-text-muted)',
                marginBottom: 12,
              }}>
                {isTrial ? 'What you get for the next 14 days' : 'What\'s now unlocked'}
              </div>
              <ul style={{
                listStyle: 'none', padding: 0, margin: '0 0 22px',
                display: 'flex', flexDirection: 'column', gap: 10,
              }}>
                {features.map((f, i) => (
                  <li key={i} style={{
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                    fontSize: 14, color: 'var(--color-text)',
                    lineHeight: 1.55, fontWeight: 500,
                  }}>
                    <CheckCircle2
                      size={16}
                      style={{ color: '#10B981', flexShrink: 0, marginTop: 1 }}
                    />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </>
          )}

          {/* Single CTA. Agent activation already happened in wizard Step 5
              and team invites live in Settings — duplicating those flows
              here just gives the user three places to do the same thing
              and a "now what?" moment after each. Keep this clean: one
              button that drops them into the dashboard they just earned. */}
          <div style={{ marginBottom: 16 }}>
            <button
              onClick={close}
              className="btn-primary"
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                justifyContent: 'center', width: '100%',
                padding: '13px 14px', fontSize: 14, fontWeight: 600,
              }}
            >
              <Zap size={14} /> Get started
              <ArrowRight size={14} />
            </button>
          </div>

          <p style={{
            fontSize: 12, color: 'var(--color-text-muted)',
            margin: 0, textAlign: 'center', lineHeight: 1.55,
          }}>
            {isTrial ? (
              <>
                We'll email you on day 11 and day 13 — no surprise charges, ever.<br/>
                Cancel anytime from Settings → Billing. Questions? Just reply to any email.
              </>
            ) : (
              <>
                Receipt + GST invoice on its way to your email.<br/>
                Need anything? Reply to that email — we read every one.
              </>
            )}
          </p>
        </div>
      </div>
    </div>
  );
}
