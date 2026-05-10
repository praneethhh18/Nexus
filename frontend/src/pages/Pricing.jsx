/**
 * In-app pricing & plan page.
 *
 * Shows the four tiers (Free / Pro / Business / Self-hosted) with a
 * "Current plan" badge on whichever tier the user is on. Until a billing
 * provider is wired up, "Upgrade" opens mailto:hi@nexusagent.app with a
 * pre-filled subject so the team can take payment manually.
 *
 * Source of truth for the tier data is duplicated with landing/src/App.jsx
 * deliberately — the landing site is a separate Vite app and we don't want
 * to share a build dependency for one constant.
 */
import { useState, useEffect, useRef } from 'react';
import {
  CheckCircle2, Sparkles, ArrowRight, ShieldCheck, Mail,
  ExternalLink, Server, Users as UsersIcon, Zap, Cloud, Loader2,
} from 'lucide-react';
import { getCurrentBusiness, getUser } from '../services/auth';
import { openRazorpayCheckout } from '../services/billing';

// Map of in-app tier id → backend plan key. Tiers in this map open
// Razorpay; tiers without a mapping fall back to mailto (license sales,
// custom-quote conversations). Source of truth for plan keys + prices is
// api/routers/billing.py PLANS dict.
const RZP_PLAN_FOR_TIER = {
  starter: 'starter',
  pro:     'pro',
  privacy: 'privacy',
};

// Reverse map — backend plan key → in-app tier id. Used by the
// `?plan=X` deeplink path (visitor came from the public landing page
// pricing section). Lets us auto-trigger checkout for the right tier.
const TIER_FOR_RZP_PLAN = Object.fromEntries(
  Object.entries(RZP_PLAN_FOR_TIER).map(([tierId, planKey]) => [planKey, tierId])
);

// ── Tiers ────────────────────────────────────────────────────────────────────
// Source of truth for prices: api/routers/billing.py PLANS dict.
// Touch both files in the same PR so the marketing copy and the actual
// Razorpay charge stay aligned.
const TIERS = [
  {
    id: 'free',
    name: 'Free',
    price: '₹0',
    cadence: 'forever',
    desc: 'For solo operators trying the local-first stack.',
    items: [
      '1 user · 1 business',
      '2 AI agents (you pick which)',
      '100 documents in RAG',
      'Local LLM only',
      'Community support',
    ],
    cta: 'Stay on Free',
    icon: Zap,
  },
  {
    id: 'starter',
    name: 'Starter',
    price: '₹1,499',
    cadence: '/ month',
    desc: 'Solo + a teammate, a small list, modest WhatsApp volume.',
    items: [
      '2 users',
      '5 AI agents',
      '500 documents',
      '100 WhatsApp/mo · 30 voice mins/mo',
      'Local LLM only',
      'Email support',
    ],
    cta: 'Subscribe',
    icon: Zap,
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '₹5,999',
    cadence: '/ month',
    desc: 'All 8 agents + cloud LLM for a 5-person team — the obvious one.',
    items: [
      'Up to 5 users',
      'All 8 AI agents',
      '2,000 documents',
      '500 WhatsApp/mo · 100 voice mins/mo',
      'Cloud LLM (Claude / Bedrock)',
      'AI proposals + Calendar + Email',
    ],
    cta: 'Subscribe',
    featured: true,
    icon: Sparkles,
  },
  {
    id: 'privacy',
    name: 'Privacy',
    price: '₹14,999',
    cadence: '/ month',
    desc: 'Sensitive prompts run on YOUR laptop via the Privacy Bridge.',
    items: [
      'Up to 10 users',
      '10,000 documents',
      '2,000 WhatsApp/mo · 300 voice mins/mo',
      'Privacy Bridge (data stays on your laptop)',
      'Cloud LLM with PII redaction',
      'Priority 24h support',
    ],
    cta: 'Subscribe',
    icon: ShieldCheck,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: 'Custom',
    cadence: 'contact us',
    desc: 'We deploy on YOUR cloud. Dedicated infra, custom SLA, isolated data.',
    items: [
      'We deploy on your AWS / Azure / GCP',
      'Unlimited users + documents',
      'Privacy Bridge included',
      'SSO (Okta / Google / Microsoft)',
      'Dedicated infra + isolated data',
      '24/7 priority support + onboarding',
    ],
    cta: 'Talk to sales',
    icon: Server,
  },
];

const FAQS = [
  {
    q: 'Do I need my own AWS / Anthropic API key?',
    a: 'No. NexusAgent is an independent product and the cloud-LLM compute is provided from our end — included in your subscription. The only exception is the Self-hosted plan, where you run the whole stack and can bring your own keys if you want cloud polish on top of the local model.',
  },
  {
    q: 'Can I change plans later?',
    a: 'Yes. Upgrade or downgrade anytime — proration is handled automatically. Self-hosted is a one-time purchase, not a subscription.',
  },
  {
    q: 'What payment methods do you accept?',
    a: 'Cards (Stripe), UPI for Indian customers, and bank transfer for Business / Self-hosted plans. We will issue a GST invoice on every payment.',
  },
  {
    q: 'Is there a free trial of Pro?',
    a: '14 days. No card required. We email you a reminder two days before it ends — you can cancel from this page in one click.',
  },
  {
    q: 'What happens to my data if I cancel?',
    a: 'You stay on the Free tier with full data access. If you exceed Free limits, features lock until you re-upgrade or export — but nothing is ever deleted automatically.',
  },
];

// ── Page ─────────────────────────────────────────────────────────────────────
export default function Pricing() {
  const user = getUser();
  const business = getCurrentBusiness();
  const currentTier = (business?.plan || 'free').toLowerCase();

  // Razorpay checkout state — `paying` is the tier id currently in flight,
  // null when nothing is in-flight. Used to disable other CTAs + show spinner.
  const [paying, setPaying]     = useState(null);
  const [payMsg, setPayMsg]     = useState('');
  const [payErr, setPayErr]     = useState('');
  // Guard against the auto-checkout effect firing twice in StrictMode.
  const autoCheckoutFired       = useRef(false);

  const subjectFor = (tier) => encodeURIComponent(
    `[NexusAgent] Upgrade to ${tier.name} — ${business?.name || 'my workspace'}`,
  );
  const bodyFor = (tier) => encodeURIComponent(
    `Hi,\n\nI'd like to upgrade my workspace to ${tier.name}.\n\n` +
    `Workspace: ${business?.name || '—'}\nUser: ${user?.email || '—'}\n\n` +
    `Please send the next steps.\n\nThanks.`,
  );
  const mailtoFor = (tier) =>
    `mailto:hi@nexusagent.app?subject=${subjectFor(tier)}&body=${bodyFor(tier)}`;

  // Either an href (string), an onClick handler (function), or null (disabled).
  // The TierCard knows how to render each shape.
  const ctaFor = (tier) => {
    if (tier.id === currentTier) return null;
    if (tier.id === 'free') return null;

    const rzpPlan = RZP_PLAN_FOR_TIER[tier.id];
    if (rzpPlan) {
      return async () => {
        setPayMsg(''); setPayErr(''); setPaying(tier.id);
        try {
          const result = await openRazorpayCheckout({
            plan:    rzpPlan,
            email:   user?.email || '',
            name:    business?.name || user?.name || '',
            contact: user?.phone || '',
          });
          setPayMsg(`Payment verified. Welcome to ${tier.name}!`);
          // Light reload after a beat so the "current plan" badge updates
          // once the backend persists the subscription change.
          setTimeout(() => window.location.reload(), 1500);
          return result;
        } catch (e) {
          // Cancelled by user is not an error — silent dismiss.
          if (/cancel/i.test(String(e?.message || ''))) {
            setPayMsg('');
          } else {
            setPayErr(String(e?.message || 'Payment failed'));
          }
        } finally {
          setPaying(null);
        }
      };
    }

    // intentional fall-through: mailto for license / quote tiers below.
    return mailtoFor(tier);
  };

  // Deeplink: visitor clicked "Subscribe to Pro" on the public landing page,
  // got bounced through /login, landed here with ?plan=pro. Auto-open the
  // Razorpay modal so they don't have to hunt for the upgrade button.
  // We only fire ONCE per page load (StrictMode would run effects twice).
  useEffect(() => {
    if (autoCheckoutFired.current) return;
    const params = new URLSearchParams(window.location.search);
    const planFromUrl = params.get('plan');
    if (!planFromUrl) return;
    const tierId = TIER_FOR_RZP_PLAN[planFromUrl];
    if (!tierId) return;
    if (tierId === currentTier) return;        // already subscribed; nothing to do
    autoCheckoutFired.current = true;
    const tier = TIERS.find(t => t.id === tierId);
    if (tier) {
      const handler = ctaFor(tier);
      if (typeof handler === 'function') handler();
    }
    // Strip ?plan= from the URL so a refresh doesn't re-open the modal.
    window.history.replaceState({}, '', window.location.pathname);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="page-body" style={{ maxWidth: 1180, margin: '0 auto' }}>
      <Header currentTier={currentTier} />

      {(payMsg || payErr) && (
        <div style={{
          padding: '10px 14px', borderRadius: 'var(--r-md)',
          background: payErr ? 'rgba(239,68,68,0.10)' : 'rgba(16,185,129,0.10)',
          color: payErr ? '#DC2626' : '#10B981',
          border: `1px solid ${payErr ? 'rgba(239,68,68,0.3)' : 'rgba(16,185,129,0.3)'}`,
          marginBottom: 18, fontSize: 13,
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          {payErr ? '⚠ ' : '✓ '}
          {payErr || payMsg}
          <button
            onClick={() => { setPayMsg(''); setPayErr(''); }}
            style={{
              marginLeft: 'auto', background: 'transparent', border: 'none',
              color: 'inherit', cursor: 'pointer', fontSize: 12,
            }}
          >dismiss</button>
        </div>
      )}

      <Tiers currentTier={currentTier} ctaFor={ctaFor} payingTierId={paying} />
      <ServiceModel />
      <PrivacyAssurance />
      <FAQ />
      <ContactStrip />
    </div>
  );
}


// ── Pieces ───────────────────────────────────────────────────────────────────
function Header({ currentTier }) {
  const tier = TIERS.find(t => t.id === currentTier) || TIERS[0];
  return (
    <div style={{
      display: 'flex', flexDirection: 'column', gap: 14,
      paddingBottom: 24, borderBottom: '1px solid var(--color-border)',
      marginBottom: 28,
    }}>
      <span style={{
        alignSelf: 'flex-start',
        display: 'inline-flex', alignItems: 'center', gap: 6,
        padding: '4px 10px', borderRadius: 'var(--r-pill)',
        fontSize: 11, fontWeight: 600, letterSpacing: 0.6,
        textTransform: 'uppercase',
        background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
        border: '1px solid color-mix(in srgb, var(--color-accent) 28%, transparent)',
      }}>
        Current plan · {tier.name}
      </span>
      <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--color-text)' }}>
        Plans &amp; pricing
      </h1>
      <p style={{ fontSize: 14, color: 'var(--color-text-muted)', maxWidth: 720, lineHeight: 1.6 }}>
        Free for one person, forever. Pay only when your team grows or when you
        want a license you own outright. All prices in ₹ — USD pricing
        available at checkout.
      </p>
    </div>
  );
}


function Tiers({ currentTier, ctaFor, payingTierId }) {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
      gap: 14, marginBottom: 40,
    }}>
      {TIERS.map((t) => (
        <TierCard
          key={t.id}
          tier={t}
          isCurrent={t.id === currentTier}
          cta={ctaFor(t)}
          isPaying={payingTierId === t.id}
          anyPaying={!!payingTierId}
        />
      ))}
    </div>
  );
}


function TierCard({ tier, isCurrent, cta, isPaying, anyPaying }) {
  const Icon = tier.icon;
  // cta is either a string (href / mailto), a function (Razorpay handler),
  // or null (no action — current plan or not purchasable from here).
  const isFn   = typeof cta === 'function';
  const isHref = typeof cta === 'string' && cta.length > 0;
  return (
    <div
      style={{
        position: 'relative',
        background: 'var(--color-surface-2)',
        border: tier.featured
          ? '1px solid color-mix(in srgb, var(--color-accent) 50%, transparent)'
          : '1px solid var(--color-border)',
        borderRadius: 'var(--r-xl)',
        padding: 22,
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        boxShadow: tier.featured
          ? '0 12px 32px color-mix(in srgb, var(--color-accent) 14%, transparent), inset 0 1px 0 rgba(255,255,255,0.04)'
          : 'var(--shadow-1)',
        transition: 'transform var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out)',
      }}
    >
      {/* Featured ribbon */}
      {tier.featured && !isCurrent && (
        <div style={{
          position: 'absolute', top: -10, right: 16,
          padding: '3px 10px', borderRadius: 'var(--r-pill)',
          background: 'var(--color-accent)', color: '#06281e',
          fontSize: 10, fontWeight: 800, letterSpacing: 0.6, textTransform: 'uppercase',
          boxShadow: 'var(--shadow-2)',
        }}>
          Most popular
        </div>
      )}

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 32, height: 32, borderRadius: 'var(--r-md)',
          background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Icon size={16} />
        </div>
        <div style={{
          fontSize: 12, fontWeight: 700, letterSpacing: 0.6,
          textTransform: 'uppercase', color: 'var(--color-text-muted)',
        }}>
          {tier.name}
        </div>
        {isCurrent && (
          <div style={{
            marginLeft: 'auto',
            padding: '2px 8px', borderRadius: 'var(--r-pill)',
            background: 'color-mix(in srgb, var(--color-ok) 14%, transparent)',
            color: 'var(--color-ok)',
            fontSize: 10, fontWeight: 700, letterSpacing: 0.5,
          }}>
            CURRENT
          </div>
        )}
      </div>

      {/* Price */}
      <div style={{ fontSize: 30, fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--color-text)' }}>
        {tier.price}
        <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-text-muted)', marginLeft: 4 }}>
          {tier.cadence}
        </span>
      </div>

      {/* Description */}
      <p style={{ fontSize: 12.5, color: 'var(--color-text-muted)', minHeight: 36, lineHeight: 1.5 }}>
        {tier.desc}
      </p>

      {/* Items */}
      <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 7, margin: '4px 0 12px' }}>
        {tier.items.map((x) => (
          <li key={x} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', fontSize: 12.5, color: 'var(--color-text-muted)' }}>
            <CheckCircle2 size={13} style={{ color: 'var(--color-accent)', flexShrink: 0, marginTop: 1.5 }} />
            <span>{x}</span>
          </li>
        ))}
      </ul>

      {/* CTA */}
      <div style={{ marginTop: 'auto' }}>
        {isCurrent ? (
          <div style={{
            padding: '10px 14px',
            border: '1px dashed var(--color-border-strong)',
            borderRadius: 'var(--r-md)',
            color: 'var(--color-text-dim)',
            fontSize: 12, textAlign: 'center',
          }}>
            You are on this plan
          </div>
        ) : isFn ? (
          <button
            type="button"
            onClick={cta}
            disabled={anyPaying}
            className={tier.featured ? 'btn-primary' : 'btn-ghost'}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
              width: '100%', cursor: anyPaying ? 'wait' : 'pointer',
              opacity: anyPaying && !isPaying ? 0.55 : 1,
            }}
          >
            {isPaying ? (
              <>
                <Loader2 size={13} style={{ animation: 'spin 1s linear infinite' }} />
                Opening checkout…
              </>
            ) : (
              <>{tier.cta} <ArrowRight size={13} /></>
            )}
          </button>
        ) : isHref ? (
          <a
            href={cta}
            className={tier.featured ? 'btn-primary' : 'btn-ghost'}
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
              width: '100%',
              textDecoration: 'none',
            }}
          >
            {tier.cta} <ArrowRight size={13} />
          </a>
        ) : (
          <button className="btn-ghost" style={{ width: '100%', justifyContent: 'center' }} disabled>
            {tier.cta}
          </button>
        )}
      </div>
    </div>
  );
}


function ServiceModel() {
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 14,
      padding: 18,
      background: 'var(--color-surface-2)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--r-lg)',
      marginBottom: 18,
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: 'var(--r-md)',
        background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <Cloud size={18} />
      </div>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)', marginBottom: 4 }}>
          How the service works — what you pay for, what we cover
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)', lineHeight: 1.65 }}>
          NexusAgent is an independent product, built and operated by us. Your
          subscription is for the product itself — features, support, and
          updates. The cloud-LLM compute that powers polish-layer writing
          (Bedrock&nbsp;/ Anthropic) is provided <strong>from our end</strong>;
          you don't bring or pay for your own API keys. Local AI on your
          machine (Ollama) is and always will be free. The Self-hosted plan
          is the one exception — there you run the whole stack on your
          infrastructure and bring your own keys if you want cloud polish.
        </div>
      </div>
    </div>
  );
}


function PrivacyAssurance() {
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: 14,
      padding: 18,
      background: 'var(--color-surface-1)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--r-lg)',
      marginBottom: 32,
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: 'var(--r-md)',
        background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        flexShrink: 0,
      }}>
        <ShieldCheck size={18} />
      </div>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)', marginBottom: 4 }}>
          Every plan keeps customer data on your machine
        </div>
        <div style={{ fontSize: 12.5, color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
          Free, Pro, Business, and Self-hosted all use the same four-layer
          privacy gate. The only thing you pay for is more seats, more
          documents, and access to the cloud-LLM polish layer (which never
          sees your row data).
        </div>
      </div>
    </div>
  );
}


function FAQ() {
  const [open, setOpen] = useState(0);
  return (
    <div style={{ marginBottom: 32 }}>
      <h2 style={{
        fontSize: 18, fontWeight: 600, letterSpacing: '-0.01em',
        color: 'var(--color-text)', marginBottom: 14,
      }}>
        Frequently asked
      </h2>
      <div style={{
        background: 'var(--color-surface-2)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--r-lg)',
        overflow: 'hidden',
      }}>
        {FAQS.map((f, i) => (
          <FAQItem
            key={i}
            faq={f}
            isOpen={open === i}
            onToggle={() => setOpen(open === i ? -1 : i)}
            isLast={i === FAQS.length - 1}
          />
        ))}
      </div>
    </div>
  );
}


function FAQItem({ faq, isOpen, onToggle, isLast }) {
  return (
    <div style={{ borderBottom: isLast ? 'none' : '1px solid var(--color-border)' }}>
      <button
        onClick={onToggle}
        style={{
          width: '100%', textAlign: 'left',
          padding: '14px 18px',
          background: 'transparent', border: 'none', cursor: 'pointer',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          color: isOpen ? 'var(--color-accent)' : 'var(--color-text)',
          fontSize: 13, fontWeight: 600,
          transition: 'color var(--dur-fast) var(--ease-out)',
        }}
      >
        <span>{faq.q}</span>
        <span style={{
          fontSize: 16,
          color: 'var(--color-text-dim)',
          transform: isOpen ? 'rotate(45deg)' : 'rotate(0deg)',
          transition: 'transform var(--dur-base) var(--ease-out)',
          display: 'inline-block', lineHeight: 1,
        }}>＋</span>
      </button>
      {isOpen && (
        <div style={{
          padding: '0 18px 14px',
          fontSize: 12.5, color: 'var(--color-text-muted)', lineHeight: 1.6,
          animation: 'fade-up var(--dur-base) var(--ease-out)',
        }}>
          {faq.a}
        </div>
      )}
    </div>
  );
}


function ContactStrip() {
  return (
    <div style={{
      display: 'flex', gap: 12, flexWrap: 'wrap',
      padding: 16,
      background: 'var(--color-surface-2)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--r-lg)',
      marginBottom: 16,
    }}>
      <a
        href="mailto:hi@nexusagent.app?subject=NexusAgent%20pricing%20question"
        className="btn-ghost"
        style={{ textDecoration: 'none' }}
      >
        <Mail size={13} /> Email us
      </a>
      <a
        href="https://github.com/praneethhh18/Nexus"
        target="_blank"
        rel="noreferrer"
        className="btn-ghost"
        style={{ textDecoration: 'none' }}
      >
        <ExternalLink size={13} /> Source on GitHub
      </a>
      <span style={{ marginLeft: 'auto', alignSelf: 'center', fontSize: 11.5, color: 'var(--color-text-dim)' }}>
        Need a custom plan? Reply to any email — we read everything.
      </span>
    </div>
  );
}
