/**
 * Plan welcome modal — fires on /?welcome=<plan> after a verified trial
 * activation or paid checkout.
 *
 * Design intent: this is the customer's first impression of the product
 * AFTER they've committed. Make it feel earned, not templated:
 *   - Real brand mark (not a celebratory emoji)
 *   - Subtle eyebrow + confident headline (not a "🎉 TRIAL ACTIVATED" pill)
 *   - Stats row that says something specific about THIS plan (8 agents,
 *     500 WhatsApp, 100 voice min) — not a generic 6-bullet checklist
 *   - One primary CTA — the wizard already activated the agents and
 *     invites belong in Settings, so duplicating those CTAs here just
 *     creates a "now what?" moment
 *   - One quiet line of fine print
 *
 * Defers itself if the onboarding wizard hasn't finished yet (sessionStorage
 * + 'nexus-onboarding-closed' event re-fires it after the wizard closes).
 */
import { useEffect, useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { getPlans } from '../services/billing';
import { shouldShowOnboarding } from './OnboardingWizard';
import BrandMark from './BrandMark';

// sessionStorage key used to defer the welcome modal until AFTER the first-run
// onboarding wizard has been completed.
const PENDING_WELCOME_KEY = 'nexus_pending_welcome';


export default function PlanWelcomeModal() {
  const [planKey, setPlanKey] = useState(null);
  const [planMeta, setPlanMeta] = useState(null);
  const isTrial = planKey === 'trial';

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlKey = params.get('welcome');
    const stashedKey = sessionStorage.getItem(PENDING_WELCOME_KEY);

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
    const fetchKey = k === 'trial' ? 'pro' : k;
    getPlans()
      .then(({ plans }) => setPlanMeta(plans?.[fetchKey] || null))
      .catch(() => setPlanMeta(null));
  }, []);

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
    const url = new URL(window.location.href);
    url.searchParams.delete('welcome');
    window.history.replaceState({}, '', url.pathname + (url.search || ''));
  };

  if (!planKey) return null;

  const label = planMeta?.label || planKey.toUpperCase();
  const limits = planMeta?.limits || {};
  const price = planMeta?.price_inr ?? null;
  const period = planMeta?.period === 'monthly' ? '/month' : planMeta?.period || '';

  // Three concrete numbers. Composed at render time from the live plan
  // catalogue so the modal is always honest about what THIS customer is
  // getting (Pro vs Starter vs Privacy etc.).
  const stats = [
    { value: limits.agents || 8,             label: 'AI agents' },
    { value: limits.whatsapp_per_month || 500, label: 'WhatsApp / mo', suffix: '' },
    { value: limits.voice_minutes_per_month || 100, label: 'voice min / mo' },
  ];

  return (
    <>
      <ModalStyles />
      <div className="pwm-backdrop" onClick={close} role="dialog" aria-modal="true">
        <div className="pwm-card" onClick={(e) => e.stopPropagation()}>
          {/* Decorative top ribbon — a single thin gradient line that anchors
              the brand colors without being a hero band. */}
          <div className="pwm-ribbon" aria-hidden />

          <div className="pwm-body">
            <div className="pwm-brand-row">
              <BrandMark size={38} />
              <div className="pwm-eyebrow">
                {isTrial ? 'Your trial is live' : 'Plan activated'}
              </div>
            </div>

            <h2 className="pwm-h2">
              {isTrial ? (
                <>You're on <span className="pwm-h2-grad">Pro for 14 days</span>.</>
              ) : (
                <>Welcome to <span className="pwm-h2-grad">{label}</span>.</>
              )}
            </h2>

            <p className="pwm-sub">
              {isTrial
                ? 'Full access to every agent. No card on file. Cancel anytime from Settings.'
                : (price !== null && price > 0
                    ? `₹${price.toLocaleString('en-IN')} ${period} — your account is now active.`
                    : 'Your account is now active.')}
            </p>

            <div className="pwm-stats">
              {stats.map((s) => (
                <div key={s.label} className="pwm-stat">
                  <div className="pwm-stat-value">{s.value}</div>
                  <div className="pwm-stat-label">{s.label}</div>
                </div>
              ))}
            </div>

            <button onClick={close} className="pwm-cta">
              Open my workspace <ArrowRight size={15} />
            </button>

            <p className="pwm-fine">
              {isTrial
                ? "Heads-up emails on day 11 and day 13. No surprise charges, ever."
                : 'Receipt + GST invoice on its way to your email.'}
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

function ModalStyles() {
  return (
    <style>{`
      .pwm-backdrop {
        position: fixed; inset: 0; z-index: 9999;
        background: rgba(8, 10, 18, 0.88);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        display: grid; place-items: center; padding: 20px;
        animation: pwm-fade-in 240ms ease-out;
      }
      @keyframes pwm-fade-in {
        from { opacity: 0; } to { opacity: 1; }
      }

      .pwm-card {
        width: 100%; max-width: 540px;
        background: var(--color-surface-1);
        border: 1px solid var(--color-border);
        border-radius: 20px;
        position: relative;
        box-shadow: 0 30px 80px rgba(0,0,0,0.55), 0 0 0 1px rgba(255,255,255,0.04);
        animation: pwm-card-in 380ms cubic-bezier(.16,.84,.32,1);
        overflow: hidden;
        color: var(--color-text);
      }
      @keyframes pwm-card-in {
        from { opacity: 0; transform: translateY(14px) scale(.98); }
        to   { opacity: 1; transform: translateY(0)    scale(1);   }
      }

      .pwm-ribbon {
        height: 3px; width: 100%;
        background: linear-gradient(90deg, #10b981 0%, #6366f1 50%, #8b5cf6 100%);
      }

      .pwm-body {
        padding: 36px 36px 28px;
        display: flex; flex-direction: column; gap: 18px;
      }

      .pwm-brand-row {
        display: flex; align-items: center; gap: 12px; margin-bottom: 4px;
      }
      .pwm-eyebrow {
        font-size: 11.5px; font-weight: 600;
        letter-spacing: 0.6px; text-transform: uppercase;
        color: var(--color-text-muted);
      }

      .pwm-h2 {
        margin: 0; font-size: 26px; font-weight: 700;
        line-height: 1.2; letter-spacing: -0.02em;
        color: var(--color-text);
      }
      .pwm-h2-grad {
        background: linear-gradient(90deg, #10b981, #6366f1, #8b5cf6);
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent; color: transparent;
      }

      .pwm-sub {
        margin: 0; font-size: 14px; line-height: 1.6;
        color: var(--color-text-muted);
        max-width: 44ch;
      }

      .pwm-stats {
        display: grid; grid-template-columns: repeat(3, 1fr);
        gap: 4px;
        margin: 6px 0 4px;
        padding: 16px 4px;
        border-top: 1px solid var(--color-border);
        border-bottom: 1px solid var(--color-border);
      }
      .pwm-stat { text-align: center; }
      .pwm-stat-value {
        font-size: 22px; font-weight: 700; letter-spacing: -0.01em;
        color: var(--color-text); line-height: 1.1;
      }
      .pwm-stat-label {
        font-size: 11px; color: var(--color-text-dim);
        margin-top: 4px; letter-spacing: 0.3px;
      }

      .pwm-cta {
        display: inline-flex; align-items: center; justify-content: center;
        gap: 8px;
        width: 100%; margin-top: 4px;
        padding: 13px 18px;
        background: linear-gradient(135deg, #10b981 0%, #6366f1 100%);
        color: #fff;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        font-size: 14.5px; font-weight: 600; letter-spacing: 0.01em;
        cursor: pointer;
        box-shadow: 0 6px 24px rgba(99,102,241,0.28);
        transition: transform 140ms ease, box-shadow 180ms ease;
      }
      .pwm-cta:hover {
        transform: translateY(-1px);
        box-shadow: 0 12px 32px rgba(99,102,241,0.38);
      }
      .pwm-cta:active {
        transform: translateY(0);
      }

      .pwm-fine {
        margin: 4px 0 0;
        font-size: 12px; line-height: 1.55;
        color: var(--color-text-dim);
        text-align: center;
      }

      @media (max-width: 560px) {
        .pwm-card { border-radius: 16px; }
        .pwm-body { padding: 28px 22px 22px; }
        .pwm-h2 { font-size: 22px; }
        .pwm-stat-value { font-size: 20px; }
      }
    `}</style>
  );
}
