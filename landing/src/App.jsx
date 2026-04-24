/**
 * NexusAgent public landing page.
 *
 * Single-page marketing site: hero → problem → solution (six agents) →
 * privacy (the differentiator) → features → pricing → FAQ → CTA.
 *
 * Deploys to Vercel or Netlify — static output, no server required.
 * CTA buttons point to /app/signup so the user can host the real app on
 * app.<yourdomain> (or localhost for self-hosters).
 */
import { useState } from 'react';
import {
  ShieldCheck, ArrowRight, CheckCircle2, Bot, Zap, Layers, Terminal,
  Inbox, Mail, FileText, Users, BarChart3, GitBranch, Play,
} from 'lucide-react';

const APP_URL = import.meta.env.VITE_APP_URL || '/app';

// ── Data ──────────────────────────────────────────────────────────────────
const AGENTS = [
  { emoji: '☀️', name: 'Atlas', role: 'Chief of staff',
    desc: 'One-page morning briefing every day at 8 AM.' },
  { emoji: '📬', name: 'Iris', role: 'Inbox triage',
    desc: 'Reads new email every 15 min, classifies, queues replies.' },
  { emoji: '💰', name: 'Kira', role: 'Invoice chaser',
    desc: 'Spots overdue invoices, drafts reminders for approval.' },
  { emoji: '🎯', name: 'Arjun', role: 'Pipeline watcher',
    desc: 'Flags stale deals and suggests a next action.' },
  { emoji: '📎', name: 'Sage', role: 'Meeting prep',
    desc: '30 min before a meeting, prepares a briefing on the contact.' },
  { emoji: '🧠', name: 'Echo', role: 'Memory keeper',
    desc: 'Weekly review of conversation history, distils what matters.' },
];

const FEATURES = [
  { icon: Inbox,     title: 'Smart Inbox',
    desc: 'Approvals, nudges, overdue items, today\'s meetings — one page.' },
  { icon: Terminal,  title: 'Natural-language SQL',
    desc: 'Ask in plain English, get SQL with self-correction.' },
  { icon: FileText,  title: 'Private RAG',
    desc: 'Upload PDFs, ask questions. Embeddings never leave your machine.' },
  { icon: GitBranch, title: 'Workflow builder',
    desc: 'Drag-and-drop triggers, conditions, loops, error handling.' },
  { icon: Bot,       title: 'Custom agents',
    desc: 'Build your own autonomous agent in a form — no code.' },
  { icon: BarChart3, title: 'Reports + analytics',
    desc: 'PDF reports from redacted aggregates, CFO-style commentary.' },
  { icon: Users,     title: 'Multi-tenant',
    desc: 'One install, multiple businesses. Row-level isolation.' },
  { icon: Mail,      title: 'Voice mode',
    desc: 'Hands-free conversation with Whisper + local TTS.' },
];

const PRIVACY_POINTS = [
  {
    title: 'Kill switch',
    body: 'Set ALLOW_CLOUD_LLM=false and every prompt stays on the local model. One flag, zero exceptions.',
  },
  {
    title: 'Sensitivity routing',
    body: 'Any prompt touching DB rows, customer records, or credentials is force-routed to local inference.',
  },
  {
    title: 'PII redaction',
    body: 'Emails, phones, Aadhaar/PAN/SSN, cards, secrets → opaque tokens before anything hits the cloud.',
  },
  {
    title: 'Audit log',
    body: 'Every cloud call logged as a SHA-256 fingerprint + character count. Never the raw prompt.',
  },
];

const TIERS = [
  {
    name:  'Free',
    price: '₹0',
    cadence: 'forever',
    desc:  'For solo operators who want to try the local-first stack.',
    items: [
      '1 user · 1 business',
      '2 agents (you pick which)',
      '100 documents in RAG',
      'Local LLM only',
      'Community support',
    ],
    cta:  'Start free',
    featured: false,
  },
  {
    name:  'Pro',
    price: '₹3,999',
    cadence: '/ month',
    desc:  'For small teams that want the whole team working.',
    items: [
      'Up to 5 users',
      'All 6 agents + custom builder',
      '1,000 documents',
      'Cloud LLM toggle (Claude / Bedrock)',
      'Priority email support',
    ],
    cta:  'Start 14-day trial',
    featured: true,
  },
  {
    name:  'Business',
    price: '₹12,999',
    cadence: '/ month',
    desc:  'For growing businesses that need SSO + onboarding support.',
    items: [
      'Up to 20 users',
      'Unlimited documents',
      'SSO (Google / Microsoft)',
      'Per-integration permissions',
      'SLA + onboarding call',
    ],
    cta:  'Talk to us',
    featured: false,
  },
  {
    name:  'Self-hosted',
    price: '₹24,999',
    cadence: 'one-time',
    desc:  'Run the whole stack on your own server. Yours forever.',
    items: [
      'Unlimited everything',
      'Docker + Helm deploy',
      'Source access',
      'Updates for 12 months',
      'Community support',
    ],
    cta:  'Buy license',
    featured: false,
  },
];

const FAQS = [
  {
    q: 'Does my data really stay local?',
    a: 'Yes. Embeddings are always local via Ollama. Chat prompts that touch customer data are force-routed to the local LLM. When you explicitly allow cloud calls for reasoning, prompts are PII-redacted first and audited — the raw prompt is never stored or sent beyond that one API call.',
  },
  {
    q: 'What hardware do I need?',
    a: 'Any laptop with 8+ GB RAM runs the default Llama 3.1 8B model fine. 16 GB lets you use bigger models. The setup wizard detects your RAM and recommends the right tier.',
  },
  {
    q: 'How does it compare to Notion AI or Zapier?',
    a: 'Notion AI gives you text completion; Zapier gives you plumbing. NexusAgent gives you autonomous agents that read your CRM, write your invoices, and chase overdue payments — plus the plumbing. And none of your business data leaves the machine unless you say so.',
  },
  {
    q: 'Can I run it without the cloud LLM at all?',
    a: 'Yes. Set ALLOW_CLOUD_LLM=false in your .env. Everything works — the reports and briefings will be slightly less polished prose, but every feature still runs on the local model.',
  },
  {
    q: 'Is it open source?',
    a: 'The self-hosted license gives you source access + a commercial right to deploy inside your org. The hosted plans ship the same binary. We\'re working on a community edition for solo users.',
  },
  {
    q: 'How do I migrate off?',
    a: 'Click Export all my data in Settings. You get a ZIP of every table as CSV — contacts, tasks, invoices, documents, conversations, agent runs. No lock-in.',
  },
];


// ── Page ──────────────────────────────────────────────────────────────────
export default function App() {
  return (
    <>
      <Nav />
      <Hero />
      <Problem />
      <Agents />
      <Privacy />
      <Features />
      <Pricing />
      <FAQ />
      <CTA />
      <Footer />
    </>
  );
}


function Nav() {
  return (
    <div className="nav">
      <div className="container nav-inner">
        <a href="#top" className="logo">NexusAgent</a>
        <nav>
          <a href="#agents"  className="nav-link">Agents</a>
          <a href="#privacy" className="nav-link">Privacy</a>
          <a href="#pricing" className="nav-link">Pricing</a>
          <a href="#faq"     className="nav-link">FAQ</a>
        </nav>
        <div>
          <a href={`${APP_URL}/login`}  className="btn btn-ghost"   style={{ padding: '8px 14px' }}>Sign in</a>
          <a href={`${APP_URL}/setup`}  className="btn btn-primary" style={{ marginLeft: 8, padding: '8px 16px' }}>
            Start free <ArrowRight size={14} />
          </a>
        </div>
      </div>
    </div>
  );
}


function Hero() {
  return (
    <section id="top" style={{ position: 'relative', paddingTop: 110, paddingBottom: 120, overflow: 'hidden' }}>
      <div className="hero-gradient" />
      <div className="container" style={{ position: 'relative' }}>
        <span className="pill" style={{ marginBottom: 20 }}>
          <ShieldCheck size={11} /> Local-first · privacy by design
        </span>
        <h1 style={{ maxWidth: 860, marginTop: 18 }}>
          A private AI business OS with a team of autonomous agents —
          <span style={{ background: 'linear-gradient(135deg, var(--accent), var(--accent-2))', WebkitBackgroundClip: 'text', color: 'transparent' }}>
            {' '}runs on your laptop.
          </span>
        </h1>
        <p style={{
          maxWidth: 680, marginTop: 18, fontSize: 18, color: 'var(--text-muted)', lineHeight: 1.6,
        }}>
          Six named agents watch your inbox, chase invoices, prep meetings, flag stale deals,
          and brief you every morning. Everything runs on your machine. The cloud only sees
          redacted aggregates — and only when you explicitly allow it.
        </p>
        <div style={{ marginTop: 28, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <a href={`${APP_URL}/setup`} className="btn btn-primary">
            Start free <ArrowRight size={14} />
          </a>
          <a href="#agents" className="btn btn-ghost">
            <Play size={13} /> See the agents
          </a>
        </div>
        <div style={{ marginTop: 36, display: 'flex', gap: 24, flexWrap: 'wrap', color: 'var(--text-dim)', fontSize: 13 }}>
          <span><CheckCircle2 size={12} style={{ color: 'var(--ok)', verticalAlign: 'middle' }} /> No credit card</span>
          <span><CheckCircle2 size={12} style={{ color: 'var(--ok)', verticalAlign: 'middle' }} /> 5-minute install</span>
          <span><CheckCircle2 size={12} style={{ color: 'var(--ok)', verticalAlign: 'middle' }} /> Self-hostable</span>
        </div>
      </div>
    </section>
  );
}


function Problem() {
  return (
    <section className="section-compact">
      <div className="container">
        <span className="eyebrow">The problem</span>
        <h2 style={{ marginTop: 12, maxWidth: 820 }}>
          Your business data is scattered across seven tools.
        </h2>
        <p style={{ marginTop: 14, fontSize: 16, color: 'var(--text-muted)', maxWidth: 720 }}>
          Email, CRM, invoicing, docs, spreadsheets, chat — every one of them wants a seat
          at your data table. Every one of them trains on your prompts. Every subscription
          renews at 12% more next year.
        </p>
      </div>
    </section>
  );
}


function Agents() {
  return (
    <section id="agents" className="section">
      <div className="container">
        <span className="eyebrow">The team</span>
        <h2 style={{ marginTop: 12 }}>Six agents that work while you sleep</h2>
        <p style={{ marginTop: 12, fontSize: 16, color: 'var(--text-muted)', maxWidth: 700 }}>
          Rename any of them anything you like. They keep their role, they just wear the new name.
        </p>
        <div className="grid grid-3" style={{ marginTop: 32 }}>
          {AGENTS.map(a => (
            <div key={a.name} className="card agent-card">
              <div className="agent-emoji">{a.emoji}</div>
              <div className="agent-role">{a.role}</div>
              <div className="agent-name">{a.name}</div>
              <div className="agent-desc">{a.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}


function Privacy() {
  return (
    <section id="privacy" className="section" style={{
      background: 'linear-gradient(180deg, var(--bg) 0%, var(--bg-1) 100%)',
    }}>
      <div className="container">
        <span className="eyebrow">The differentiator</span>
        <h2 style={{ marginTop: 12 }}>Four layers of privacy between your data and the cloud</h2>
        <p style={{ marginTop: 12, fontSize: 16, color: 'var(--text-muted)', maxWidth: 720 }}>
          Every outbound prompt passes through four gates before leaving your machine.
          Because "our privacy policy says we don't train on your data" is not a privacy posture.
        </p>
        <div className="grid grid-2" style={{ marginTop: 32 }}>
          {PRIVACY_POINTS.map((p, i) => (
            <div key={p.title} className="card" style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
              <div style={{
                width: 36, height: 36, borderRadius: 10,
                background: 'color-mix(in srgb, var(--ok) 16%, transparent)',
                color: 'var(--ok)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                flexShrink: 0, fontWeight: 700, fontSize: 14,
              }}>{i + 1}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>{p.title}</div>
                <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>{p.body}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}


function Features() {
  return (
    <section className="section">
      <div className="container">
        <span className="eyebrow">Everything you need</span>
        <h2 style={{ marginTop: 12 }}>Replaces seven subscriptions</h2>
        <div className="grid grid-4" style={{ marginTop: 32 }}>
          {FEATURES.map(f => {
            const Icon = f.icon;
            return (
              <div key={f.title} className="card" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <div style={{
                  width: 34, height: 34, borderRadius: 8,
                  background: 'color-mix(in srgb, var(--accent) 16%, transparent)',
                  color: 'var(--accent)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <Icon size={18} />
                </div>
                <div style={{ fontWeight: 700, fontSize: 14 }}>{f.title}</div>
                <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>{f.desc}</div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}


function Pricing() {
  return (
    <section id="pricing" className="section">
      <div className="container">
        <span className="eyebrow">Pricing</span>
        <h2 style={{ marginTop: 12 }}>Free for one person. Self-hosted license if you want it forever.</h2>
        <p style={{ marginTop: 12, fontSize: 16, color: 'var(--text-muted)' }}>
          Prices shown in ₹. USD pricing available at checkout.
        </p>
        <div className="grid grid-4" style={{ marginTop: 32 }}>
          {TIERS.map(t => (
            <div key={t.name} className={`price-card ${t.featured ? 'featured' : ''}`}>
              {t.featured && (
                <span className="pill" style={{ alignSelf: 'flex-start', background: 'color-mix(in srgb, var(--accent) 14%, transparent)', color: 'var(--accent)', borderColor: 'color-mix(in srgb, var(--accent) 30%, transparent)' }}>
                  Most popular
                </span>
              )}
              <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: 0.5, textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                {t.name}
              </div>
              <div className="price-amount">
                {t.price} <small>{t.cadence}</small>
              </div>
              <div style={{ color: 'var(--text-muted)', fontSize: 13, minHeight: 36 }}>{t.desc}</div>
              <ul className="price-list">
                {t.items.map(x => (
                  <li key={x}>
                    <CheckCircle2 size={12} style={{ color: 'var(--ok)', flexShrink: 0, marginTop: 3 }} />
                    <span>{x}</span>
                  </li>
                ))}
              </ul>
              <a
                href={t.name === 'Business' ? 'mailto:hi@nexusagent.app' : `${APP_URL}/setup`}
                className={t.featured ? 'btn btn-primary' : 'btn btn-ghost'}
                style={{ justifyContent: 'center', marginTop: 'auto' }}
              >
                {t.cta} <ArrowRight size={13} />
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}


function FAQ() {
  return (
    <section id="faq" className="section">
      <div className="container" style={{ maxWidth: 760 }}>
        <span className="eyebrow">Questions</span>
        <h2 style={{ marginTop: 12 }}>FAQ</h2>
        <div style={{ marginTop: 24 }}>
          {FAQS.map((f, i) => (
            <details key={i} className="faq">
              <summary>
                <span>{f.q}</span>
                <span style={{ color: 'var(--text-dim)', fontSize: 14 }}>＋</span>
              </summary>
              <div className="faq-answer">{f.a}</div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}


function CTA() {
  return (
    <section className="section" style={{
      background: 'linear-gradient(135deg, color-mix(in srgb, var(--accent) 18%, var(--bg)), color-mix(in srgb, var(--accent-2) 12%, var(--bg)))',
      borderBottom: 'none',
    }}>
      <div className="container" style={{ textAlign: 'center' }}>
        <h2>Your team of six is ready.</h2>
        <p style={{ marginTop: 14, fontSize: 18, color: 'var(--text-muted)' }}>
          Five minutes to set up. Zero vendor lock-in. Your data stays yours.
        </p>
        <div style={{ marginTop: 28, display: 'inline-flex', gap: 12 }}>
          <a href={`${APP_URL}/setup`} className="btn btn-primary">
            Start free <ArrowRight size={14} />
          </a>
          <a href="https://github.com/praneethhh18/Nexus" target="_blank" rel="noreferrer" className="btn btn-ghost">
            Source on GitHub
          </a>
        </div>
      </div>
    </section>
  );
}


function Footer() {
  return (
    <div className="container footer">
      <span>© {new Date().getFullYear()} NexusAgent</span>
      <span>
        <a href="#privacy" style={{ marginRight: 16 }}>Privacy</a>
        <a href="#pricing" style={{ marginRight: 16 }}>Pricing</a>
        <a href={`${APP_URL}/login`}>Sign in</a>
      </span>
    </div>
  );
}
