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
import { useState } from 'react';
import {
  CheckCircle2, Sparkles, ArrowRight, ShieldCheck, Mail,
  ExternalLink, Server, Users as UsersIcon, Zap,
} from 'lucide-react';
import { getCurrentBusiness, getUser } from '../services/auth';

// ── Tiers ────────────────────────────────────────────────────────────────────
const TIERS = [
  {
    id: 'free',
    name: 'Free',
    price: '₹0',
    cadence: 'forever',
    desc: 'For solo operators trying the local-first stack.',
    items: [
      '1 user · 1 business',
      '2 agents (you pick which)',
      '100 documents in RAG',
      'Local LLM only',
      'Community support',
    ],
    cta: 'Stay on Free',
    icon: Zap,
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '₹3,999',
    cadence: '/ month',
    desc: 'For small teams that want the whole agent team working.',
    items: [
      'Up to 5 users',
      'All 6 agents + custom builder',
      '1,000 documents',
      'Cloud LLM toggle (Claude / Bedrock)',
      'Priority email support',
    ],
    cta: 'Upgrade to Pro',
    featured: true,
    icon: Sparkles,
  },
  {
    id: 'business',
    name: 'Business',
    price: '₹12,999',
    cadence: '/ month',
    desc: 'For growing teams that need SSO + onboarding.',
    items: [
      'Up to 20 users',
      'Unlimited documents',
      'SSO (Google / Microsoft)',
      'Per-integration permissions',
      'SLA + onboarding call',
    ],
    cta: 'Talk to us',
    icon: UsersIcon,
  },
  {
    id: 'self_hosted',
    name: 'Self-hosted',
    price: '₹24,999',
    cadence: 'one-time',
    desc: 'Run the whole stack on your own server. Yours forever.',
    items: [
      'Unlimited everything',
      'Docker + Helm deploy',
      'Source access',
      '12 months of updates',
      'Community support',
    ],
    cta: 'Buy license',
    icon: Server,
  },
];

const FAQS = [
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

  const subjectFor = (tier) => encodeURIComponent(
    `[NexusAgent] Upgrade to ${tier.name} — ${business?.name || 'my workspace'}`,
  );
  const bodyFor = (tier) => encodeURIComponent(
    `Hi,\n\nI'd like to upgrade my workspace to ${tier.name}.\n\n` +
    `Workspace: ${business?.name || '—'}\nUser: ${user?.email || '—'}\n\n` +
    `Please send the next steps.\n\nThanks.`,
  );
  const ctaFor = (tier) => {
    if (tier.id === currentTier) return null;
    if (tier.id === 'business' || tier.id === 'self_hosted') {
      return `mailto:hi@nexusagent.app?subject=${subjectFor(tier)}&body=${bodyFor(tier)}`;
    }
    if (tier.id === 'free') return null;
    return `mailto:hi@nexusagent.app?subject=${subjectFor(tier)}&body=${bodyFor(tier)}`;
  };

  return (
    <div className="page-body" style={{ maxWidth: 1180, margin: '0 auto' }}>
      <Header currentTier={currentTier} />
      <Tiers currentTier={currentTier} ctaFor={ctaFor} />
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


function Tiers({ currentTier, ctaFor }) {
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
          href={ctaFor(t)}
        />
      ))}
    </div>
  );
}


function TierCard({ tier, isCurrent, href }) {
  const Icon = tier.icon;
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
        ) : href ? (
          <a
            href={href}
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
