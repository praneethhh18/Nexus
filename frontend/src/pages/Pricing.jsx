/**
 * In-app plan and contact page.
 *
 * Public prices are intentionally hidden while NexusAgent is early. The
 * 14-day Pro trial remains the onboarding path; after the trial, users land
 * here and contact us to continue. Razorpay integration remains in
 * services/billing.js and api/routers/billing.py for manual/approved use.
 */
import { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight, CalendarDays, CheckCircle2, Mail, MessageSquare,
  Phone, ShieldCheck, Sparkles, Users, Zap,
} from 'lucide-react';
import { getCurrentBusiness, getUser } from '../services/auth';
import { getSubscription } from '../services/billing';

const CONTACT_EMAIL = 'hi@nexusagent.in';

const PLANS = [
  {
    id: 'starter',
    name: 'Starter',
    icon: Zap,
    desc: 'For solo operators and small teams who want a guided setup.',
    items: ['Small team rollout', 'Core agent workflows', 'WhatsApp and email guidance'],
  },
  {
    id: 'pro',
    name: 'Pro',
    icon: Sparkles,
    featured: true,
    desc: 'The full 14-day trial experience and the usual next step after evaluation.',
    items: ['All AI agents', 'Cloud LLM polish layer', 'Calendar, email, proposals, CRM workflows'],
  },
  {
    id: 'privacy',
    name: 'Privacy',
    icon: ShieldCheck,
    desc: 'For sensitive customer data and Privacy Bridge deployments.',
    items: ['Privacy Bridge setup', 'PII-aware cloud routing', 'Priority onboarding'],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    icon: Users,
    desc: 'For dedicated infra, custom SLA, SSO, and customer-cloud deployment.',
    items: ['Your cloud or VPC', 'Custom limits', 'Founder-led implementation plan'],
  },
];

function encodeMail({ subject, body }) {
  return `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

export default function Pricing() {
  const user = getUser();
  const business = getCurrentBusiness();
  const [sub, setSub] = useState(null);

  useEffect(() => {
    let mounted = true;
    getSubscription()
      .then((s) => { if (mounted) setSub(s); })
      .catch(() => {});
    return () => { mounted = false; };
  }, []);

  const requestedPlan = useMemo(() => {
    if (typeof window === 'undefined') return '';
    return new URLSearchParams(window.location.search).get('plan') || '';
  }, []);

  const currentPlan = sub?.plan_key || business?.plan || 'free';
  const trialEnded = Boolean(sub?.trial_expired);
  const isTrial = Boolean(sub?.is_trial);
  const days = sub?.trial_days_remaining;

  const contactHref = (planName = 'NexusAgent') => encodeMail({
    subject: `[NexusAgent] Pricing discussion for ${planName}`,
    body:
      `Hi,\n\nI'd like to discuss NexusAgent pricing and the right plan.\n\n` +
      `Workspace: ${business?.name || ''}\n` +
      `User: ${user?.email || ''}\n` +
      `Current plan: ${currentPlan}\n` +
      `Requested plan: ${requestedPlan || planName}\n\n` +
      `A good time to talk:\n\nThanks.`,
  });

  return (
    <div className="page-body">
      <div style={{ maxWidth: 1080, margin: '0 auto', width: '100%' }}>
        <header style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 320px), 1fr))',
          gap: 18,
          alignItems: 'stretch',
          marginBottom: 26,
        }}>
          <section style={{
            background: 'var(--color-surface-2)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--r-xl)',
            padding: 24,
            boxShadow: 'var(--shadow-1)',
          }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              padding: '5px 10px', borderRadius: 'var(--r-pill)',
              background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
              fontSize: 11, fontWeight: 700, textTransform: 'uppercase',
              letterSpacing: 0.6, marginBottom: 16,
            }}>
              <MessageSquare size={13} /> Pricing by conversation
            </div>
            <h1 style={{
              fontSize: 28, fontWeight: 750, color: 'var(--color-text)',
              marginBottom: 10, letterSpacing: 0,
            }}>
              Let us discuss the right NexusAgent plan.
            </h1>
            <p style={{
              color: 'var(--color-text-muted)', fontSize: 14,
              lineHeight: 1.65, maxWidth: 720,
            }}>
              NexusAgent is still a new product, so we are not showing fixed
              public prices here. Start with the 14-day Pro trial, then contact
              us when you are ready to continue. We will map the plan, usage,
              setup help, and billing method with you directly.
            </p>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 18 }}>
              <a href={contactHref(requestedPlan || 'Plan')} className="btn-primary" style={{ textDecoration: 'none' }}>
                <Mail size={14} /> Contact us <ArrowRight size={14} />
              </a>
              <a href="/settings" className="btn-ghost" style={{ textDecoration: 'none' }}>
                View settings
              </a>
            </div>
          </section>

          <TrialStatus
            isTrial={isTrial}
            trialEnded={trialEnded}
            days={days}
            contactHref={contactHref('Trial continuation')}
          />
        </header>

        <section style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 14,
          marginBottom: 24,
        }}>
          {PLANS.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              current={currentPlan === plan.id}
              contactHref={contactHref(plan.name)}
            />
          ))}
        </section>

        <section style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: 14,
          marginBottom: 18,
        }}>
          <InfoBox
            icon={CalendarDays}
            title="Trial stays connected"
            body="The 14-day Pro trial still activates through signup and email verification. After day 14, Pro features close unless we move you to a paid or custom plan."
          />
          <InfoBox
            icon={ShieldCheck}
            title="No free bypass after expiry"
            body="Expired trials are treated as Free immediately by the backend gates, even if the cleanup job has not run yet."
          />
          <InfoBox
            icon={Phone}
            title="Razorpay stays available"
            body="Razorpay checkout remains in the codebase for approved payments, but this page now routes customers to contact first."
          />
        </section>

        <ContactStrip href={contactHref('NexusAgent')} />
      </div>
    </div>
  );
}

function TrialStatus({ isTrial, trialEnded, days, contactHref }) {
  let title = '14-day Pro trial';
  let body = 'New users can start the trial from the landing page. No card is required.';
  let tone = 'var(--color-accent-soft)';

  if (isTrial) {
    title = days === 0 ? 'Trial ends today' : `${days ?? 0} trial days left`;
    body = 'Contact us before it ends and we will discuss the right continuation plan.';
  } else if (trialEnded) {
    title = 'Trial ended';
    body = 'Your workspace is now on Free. Contact us to continue with Pro or a custom plan.';
    tone = 'rgba(245,158,11,0.14)';
  }

  return (
    <aside style={{
      background: 'var(--color-surface-2)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--r-xl)',
      padding: 20,
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
      minHeight: 190,
    }}>
      <div style={{
        width: 38, height: 38, borderRadius: 'var(--r-md)',
        background: tone, color: 'var(--color-accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Sparkles size={18} />
      </div>
      <div>
        <h2 style={{ fontSize: 18, color: 'var(--color-text)', marginBottom: 6 }}>{title}</h2>
        <p style={{ fontSize: 13, color: 'var(--color-text-muted)', lineHeight: 1.55 }}>{body}</p>
      </div>
      <a href={contactHref} className="btn-ghost" style={{ marginTop: 'auto', textDecoration: 'none', justifyContent: 'center' }}>
        Discuss continuation
      </a>
    </aside>
  );
}

function PlanCard({ plan, current, contactHref }) {
  const Icon = plan.icon;
  return (
    <article style={{
      background: 'var(--color-surface-2)',
      border: plan.featured
        ? '1px solid color-mix(in srgb, var(--color-accent) 48%, transparent)'
        : '1px solid var(--color-border)',
      borderRadius: 'var(--r-lg)',
      padding: 18,
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
      boxShadow: plan.featured ? 'var(--shadow-2)' : 'var(--shadow-1)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 'var(--r-md)',
          background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Icon size={16} />
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-text)' }}>{plan.name}</div>
          {current && <div style={{ fontSize: 11, color: 'var(--color-ok)' }}>Current plan</div>}
        </div>
      </div>
      <p style={{ fontSize: 12.5, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>{plan.desc}</p>
      <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 7, margin: 0, padding: 0 }}>
        {plan.items.map((item) => (
          <li key={item} style={{ display: 'flex', gap: 8, fontSize: 12.5, color: 'var(--color-text-muted)' }}>
            <CheckCircle2 size={13} style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: 2 }} />
            <span>{item}</span>
          </li>
        ))}
      </ul>
      <a href={contactHref} className={plan.featured ? 'btn-primary' : 'btn-ghost'} style={{
        marginTop: 'auto',
        textDecoration: 'none',
        justifyContent: 'center',
      }}>
        Contact us <ArrowRight size={13} />
      </a>
    </article>
  );
}

function InfoBox({ icon: Icon, title, body }) {
  return (
    <div style={{
      background: 'var(--color-surface-1)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--r-lg)',
      padding: 16,
      display: 'flex',
      gap: 12,
      alignItems: 'flex-start',
    }}>
      <div style={{
        width: 32, height: 32, borderRadius: 'var(--r-md)',
        background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <Icon size={16} />
      </div>
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--color-text)', marginBottom: 4 }}>{title}</div>
        <p style={{ fontSize: 12.5, color: 'var(--color-text-muted)', lineHeight: 1.55 }}>{body}</p>
      </div>
    </div>
  );
}

function ContactStrip({ href }) {
  return (
    <div style={{
      display: 'flex', gap: 12, flexWrap: 'wrap',
      alignItems: 'center',
      padding: 16,
      background: 'var(--color-surface-2)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--r-lg)',
    }}>
      <span style={{ fontSize: 12.5, color: 'var(--color-text-muted)', flex: 1, minWidth: 220 }}>
        Need pricing, extension, onboarding, or Razorpay payment help?
      </span>
      <a href={href} className="btn-primary" style={{ textDecoration: 'none' }}>
        <Mail size={13} /> Email {CONTACT_EMAIL}
      </a>
    </div>
  );
}
