import { useState, useEffect } from 'react';
import {
  ShieldCheck, ArrowRight, CheckCircle2, X,
  Mail, Phone, Search, Brain, Sun, Target, Clock, Lock,
  TrendingUp, ChevronDown, Menu, Check,
} from 'lucide-react';

const APP_URL = import.meta.env.VITE_APP_URL || 'https://app.nexusagent.in';
const MAIL    = 'hi@nexusagent.in';
const GITHUB  = 'https://github.com/praneethhh18/Nexus';

// ── Logo Mark SVG ─────────────────────────────────────────────────────────────

function LogoMark({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ flexShrink: 0 }}>
      <rect width="32" height="32" rx="8" fill="#1D4ED8"/>
      {/* N strokes */}
      <line x1="9"  y1="8.5" x2="9"  y2="23.5" stroke="white" strokeWidth="2.2" strokeLinecap="round"/>
      <line x1="9"  y1="8.5" x2="23" y2="23.5" stroke="white" strokeWidth="2.2" strokeLinecap="round"/>
      <line x1="23" y1="8.5" x2="23" y2="23.5" stroke="white" strokeWidth="2.2" strokeLinecap="round"/>
      {/* Corner nodes */}
      <circle cx="9"  cy="8.5"  r="2.6" fill="white"/>
      <circle cx="9"  cy="23.5" r="2.6" fill="white"/>
      <circle cx="23" cy="8.5"  r="2.6" fill="white"/>
      <circle cx="23" cy="23.5" r="2.6" fill="white"/>
      {/* Centre node on diagonal */}
      <circle cx="16" cy="16"   r="1.9" fill="rgba(255,255,255,0.55)"/>
    </svg>
  );
}

// ── Data ─────────────────────────────────────────────────────────────────────

const AGENTS = [
  { name: 'Atlas', role: 'Daily Briefing',    emoji: '🌅', color: '#F59E0B', icon: Sun,
    desc: 'Each morning, pulls together your open tasks, overdue invoices, and today\'s meetings into one summary.' },
  { name: 'Iris',  role: 'Inbox Triage',      emoji: '📬', color: '#0EA5E9', icon: Mail,
    desc: 'Checks your inbox on a schedule, classifies emails by intent, and drafts suggested replies for you to review.' },
  { name: 'Kira',  role: 'Invoice Follow-up', emoji: '💰', color: '#10B981', icon: TrendingUp,
    desc: 'Looks for overdue invoices and drafts a follow-up message. You approve before anything is sent.' },
  { name: 'Arjun', role: 'Pipeline Review',   emoji: '🎯', color: '#F97316', icon: Target,
    desc: 'Surfaces deals that haven\'t had activity in a while and suggests what to do next.' },
  { name: 'Sage',  role: 'Meeting Prep',      emoji: '📋', color: '#8B5CF6', icon: Clock,
    desc: 'Before a scheduled meeting, gathers relevant contact history and open items so you\'re not going in blind.' },
  { name: 'Echo',  role: 'Memory Keeper',     emoji: '🧠', color: '#EC4899', icon: Brain,
    desc: 'Periodically reviews your conversations and notes key facts about contacts and deals into a searchable store.' },
  { name: 'Nyx',   role: 'Research',          emoji: '🔍', color: '#6366F1', icon: Search,
    desc: 'Runs web research on a company or contact and returns a structured summary you can use before a call.' },
  { name: 'Vox',   role: 'Voice Calls',       emoji: '📞', color: '#06B6D4', icon: Phone,
    desc: 'Makes outbound calls over SIP and logs a transcript and summary back to the CRM. Needs a Twilio account.' },
];

const HOW_IT_WORKS = [
  { step: '01', title: 'Connect your accounts',
    desc: 'Link Gmail, Google Calendar, and bring in contacts via CSV. No coding needed.',
    items: ['Gmail / Outlook', 'Google Calendar', 'CSV contact import', 'WhatsApp (optional)'] },
  { step: '02', title: 'Workflows run on a schedule',
    desc: 'Each agent checks for tasks at a set interval and queues anything that needs your attention.',
    items: ['Runs on your laptop', 'Uses Ollama by default', 'Cloud LLM opt-in', 'You control the schedule'] },
  { step: '03', title: 'You review and confirm',
    desc: 'Nothing gets sent or logged without your approval. You see what the agent found and decide what to do.',
    items: ['Approve or skip each suggestion', 'See the context behind every task', 'Full action history', 'No surprises'] },
];

const PRIVACY_POINTS = [
  { n: '01', title: 'Local by default',
    body: 'NexusAgent runs on Ollama. By default, no prompts leave your machine. You can opt into cloud LLMs if you need them.' },
  { n: '02', title: 'Sensitive data stays local',
    body: 'Prompts that touch customer records or credentials are always routed to the local model, regardless of your cloud setting.' },
  { n: '03', title: 'PII scrubbing before cloud calls',
    body: 'If you enable cloud LLMs, emails, phone numbers, and other personal data are replaced with placeholders before the prompt is sent.' },
  { n: '04', title: 'Action log',
    body: 'Every agent action is recorded — what it checked, what it suggested, and what you approved. You always have a clear trail.' },
];

const COMPARE_ROWS = [
  { feature: 'Runs on your laptop',        nexus: true,       zoho: false,          salesforce: false         },
  { feature: 'Local LLM support',          nexus: true,       zoho: false,          salesforce: false         },
  { feature: 'Data stays on your machine', nexus: true,       zoho: false,          salesforce: false         },
  { feature: 'Scheduled AI workflows',     nexus: true,       zoho: 'Partial',      salesforce: 'Partial'     },
  { feature: 'Outbound voice (SIP)',        nexus: true,       zoho: 'Add-on',       salesforce: 'Add-on'      },
  { feature: 'Self-hosted option',         nexus: true,       zoho: false,          salesforce: false         },
  { feature: 'Starting price',             nexus: 'Free',     zoho: '₹1,400/mo',   salesforce: '₹6,000/mo'   },
];

const TIERS = [
  { name: 'Free',        price: '₹0',      period: 'forever',   featured: false,
    desc: 'Try NexusAgent with a couple of workflows on your own machine.',
    items: ['1 user', '2 workflows active', 'Local LLM only', 'Up to 100 documents', 'GitHub issues for support'],
    cta: 'Get started',        href: `${APP_URL}/setup` },
  { name: 'Starter',     price: '₹1,499',  period: '/month',    featured: false,
    desc: 'More workflows for solo users who want to run everything locally.',
    items: ['2 users', '5 workflows active', 'Local LLM only', 'Up to 500 documents', 'No voice calls', 'Email support'],
    cta: 'Get early access',   href: `mailto:${MAIL}` },
  { name: 'Pro',         price: '₹5,499',  period: '/month',    featured: false,
    desc: 'All 8 workflows for a small team, with cloud LLM as an option.',
    items: ['Up to 5 users', 'All 8 workflows', 'Up to 1,000 documents', 'Cloud LLM opt-in', '50 voice min/mo included', 'Email support'],
    cta: 'Get early access',   href: `mailto:${MAIL}` },
  { name: 'Business',    price: '₹17,999', period: '/month',    featured: false,
    desc: 'For teams that need more users, SSO, and direct onboarding help.',
    items: ['Up to 20 users', 'Unlimited documents', 'SSO (Google / Microsoft)', 'WhatsApp integration', '200 voice min/mo included', 'Onboarding call included'],
    cta: 'Talk to us',         href: `mailto:${MAIL}` },
  { name: 'Self-hosted', price: '₹34,999', period: 'one-time',  featured: false,
    desc: 'Deploy on your own server. One-time payment, no recurring fees.',
    items: ['Unlimited users', 'Docker deploy', 'Source code access', '12 months of updates', 'Setup support via email'],
    cta: 'Contact us',         href: `mailto:${MAIL}` },
];

const FAQS = [
  { q: 'Does my data stay on my machine?',
    a: 'By default, yes. NexusAgent uses Ollama to run a local LLM, so prompts don\'t leave your laptop. If you enable a cloud LLM, personal data in prompts is replaced with placeholders before being sent. You can disable cloud entirely with one config flag.' },
  { q: 'What hardware do I need?',
    a: 'You need a laptop or desktop with at least 8 GB RAM to run a small local model (Llama 3.1 8B). 16 GB gives you better model options. You also need to have Ollama installed before setup.' },
  { q: 'How is this different from Zoho or Salesforce?',
    a: 'Zoho and Salesforce are CRM databases — you enter data, they store it. NexusAgent adds scheduled workflows that check your inbox, flag overdue invoices, and prep meeting notes, all running on your own machine. They serve different purposes and you might use both.' },
  { q: 'Can Vox make calls to Indian numbers?',
    a: 'Yes, but you need a Twilio account with a DID number. Twilio supports Indian PSTN numbers. The call cost is billed directly by Twilio at their standard rates — NexusAgent doesn\'t add a markup.' },
  { q: 'Can I run it without internet?',
    a: 'Most features work offline — the local LLM, CRM, documents, and workflow scheduling all run on your machine. Voice calls need Twilio (internet required). If you\'ve enabled a cloud LLM, that needs internet too.' },
  { q: 'Can I export my data?',
    a: 'Yes. You can export all your contacts, tasks, documents, and agent history from settings. Everything comes out as CSV files. There\'s no export fee and no lock-in.' },
];


// ── App ───────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <Problem />
        <HowItWorks />
        <AgentsSection />
        <PrivacySection />
        <CompareTable />
        <Pricing />
        <FAQ />
        <CTA />
      </main>
      <Footer />
    </>
  );
}

// ── Nav ───────────────────────────────────────────────────────────────────────

function Nav() {
  const [open, setOpen]       = useState(false);
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 8);
    window.addEventListener('scroll', fn, { passive: true });
    return () => window.removeEventListener('scroll', fn);
  }, []);
  return (
    <header className={`nav-wrap ${scrolled ? 'nav-scrolled' : ''}`}>
      <div className="container nav-inner">
        <a href="#top" className="logo">
          <LogoMark size={32} />
          NexusAgent
        </a>
        <nav className={`nav-links ${open ? 'nav-open' : ''}`}>
          <a href="#agents"  onClick={() => setOpen(false)}>Agents</a>
          <a href="#privacy" onClick={() => setOpen(false)}>Privacy</a>
          <a href="#pricing" onClick={() => setOpen(false)}>Pricing</a>
          <a href="#faq"     onClick={() => setOpen(false)}>FAQ</a>
        </nav>
        <div className="nav-ctas">
          <a href={`${APP_URL}/login`} className="nav-signin">Sign in</a>
          <a href={`${APP_URL}/setup`} className="btn btn-primary btn-sm">
            Start free <ArrowRight size={13} />
          </a>
        </div>
        <button className="nav-burger" onClick={() => setOpen(o => !o)} aria-label="Menu">
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>
    </header>
  );
}

// ── Hero ──────────────────────────────────────────────────────────────────────

function Hero() {
  return (
    <section id="top" className="hero-section">
      <div className="container hero-inner">
        <div className="hero-badge">
          <ShieldCheck size={12} />
          Local-first · Privacy by design · Made for Indian SMBs
        </div>

        <h1 className="hero-h1">
          An AI business team<br />
          that runs on <strong>your laptop</strong>
        </h1>

        <p className="hero-sub">
          8 agents handle your CRM, inbox, invoices, meetings, and outbound calls —
          running locally by default, so your data stays on your machine unless you
          choose otherwise.
        </p>

        <div className="hero-actions">
          <a href={`${APP_URL}/setup`} className="btn btn-primary btn-lg">
            Get started free <ArrowRight size={14} />
          </a>
          <a href="#how-it-works" className="btn btn-outline btn-lg">
            See how it works
          </a>
        </div>

        <div className="hero-trust">
          <span><CheckCircle2 size={13} className="icon-ok" /> No credit card</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> Open source</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> Self-hostable</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> Runs on your laptop</span>
        </div>
      </div>
    </section>
  );
}

// ── Agent Hub Visual ─────────────────────────────────────────────────────────

function AgentHubVisual() {
  const W = 560, H = 420, cx = 280, cy = 204;

  // Spread positions — no overlaps, asymmetric
  const NODES = [
    { role: 'Chief of Staff',  Icon: Sun,        color: '#F59E0B', x: 148, y: 58  },
    { role: 'Research',        Icon: Search,     color: '#6366F1', x: 50,  y: 156 },
    { role: 'Inbox Triage',    Icon: Mail,       color: '#0EA5E9', x: 62,  y: 302 },
    { role: 'Invoice Chaser',  Icon: TrendingUp, color: '#10B981', x: 222, y: 374 },
    { role: 'Meeting Prep',    Icon: Clock,      color: '#8B5CF6', x: 394, y: 358 },
    { role: 'Pipeline Watch',  Icon: Target,     color: '#F97316', x: 492, y: 172 },
    { role: 'Voice Agent',     Icon: Phone,      color: '#06B6D4', x: 422, y: 58  },
    { role: 'Memory Keeper',   Icon: Brain,      color: '#EC4899', x: 280, y: 38  },
  ].map((n, i) => {
    // Right-angle path: horizontal-first or vertical-first based on which delta is larger
    const dx = Math.abs(n.x - cx), dy = Math.abs(n.y - cy);
    const bendX = dx >= dy ? cx      : n.x;  // horizontal-first → bend at (cx, n.y)
    const bendY = dx >= dy ? n.y     : cy;   // vertical-first   → bend at (n.x, cy)
    const pathD = `M ${n.x} ${n.y} L ${bendX} ${bendY} L ${cx} ${cy}`;
    return { ...n, bendX, bendY, pathD, id: `np${i}` };
  });

  return (
    <div className="hub-vis">
      <svg className="hub-svg" viewBox={`0 0 ${W} ${H}`} fill="none">
        <defs>
          <pattern id="hub-dots" width="26" height="26" patternUnits="userSpaceOnUse">
            <circle cx="13" cy="13" r="1" fill="rgba(99,102,241,0.08)" />
          </pattern>
          {NODES.map(n => (
            <path key={n.id} id={n.id} d={n.pathD} />
          ))}
        </defs>

        {/* Dot grid background */}
        <rect width={W} height={H} fill="url(#hub-dots)" rx="20" />

        {/* Center pulse rings */}
        <circle cx={cx} cy={cy} r="44" stroke="rgba(29,78,216,0.10)" strokeWidth="1" fill="none">
          <animate attributeName="r"       values="44;64;44" dur="3.2s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.7;0;0.7" dur="3.2s" repeatCount="indefinite" />
        </circle>
        <circle cx={cx} cy={cy} r="44" stroke="rgba(29,78,216,0.06)" strokeWidth="1" fill="none">
          <animate attributeName="r"       values="44;84;44" dur="3.2s" begin="1s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.5;0;0.5" dur="3.2s" begin="1s" repeatCount="indefinite" />
        </circle>

        {NODES.map((n, i) => (
          <g key={n.id}>
            {/* Right-angle connector line */}
            <path
              d={n.pathD}
              stroke={n.color} strokeWidth="1.5"
              strokeDasharray="5 5" opacity="0.22"
              fill="none"
            />
            {/* Diamond at the bend point */}
            <polygon
              points={`
                ${n.bendX},${n.bendY - 5}
                ${n.bendX + 5},${n.bendY}
                ${n.bendX},${n.bendY + 5}
                ${n.bendX - 5},${n.bendY}
              `}
              fill={n.color} opacity="0.55"
            />
            {/* Travelling dot along the right-angle path */}
            <circle r="3.5" fill={n.color} opacity="0.95">
              <animateMotion
                dur={`${1.7 + i * 0.19}s`}
                repeatCount="indefinite"
                begin={`${i * 0.42}s`}
              >
                <mpath href={`#${n.id}`} />
              </animateMotion>
            </circle>
          </g>
        ))}
      </svg>

      {/* Agent icon nodes — no card, no text */}
      {NODES.map(n => (
        <div key={n.role} className="hub-node"
          style={{ left: `${(n.x / W) * 100}%`, top: `${(n.y / H) * 100}%`, '--nc': n.color }}>
          <n.Icon size={20} />
        </div>
      ))}

      {/* Center hub — same style as nodes but larger */}
      <div className="hub-center-icon"
        style={{ left: `${(cx / W) * 100}%`, top: `${(cy / H) * 100}%` }}>
        <LogoMark size={52} />
      </div>
    </div>
  );
}

// ── Problem ───────────────────────────────────────────────────────────────────

function Problem() {
  return (
    <section className="section section-alt">
      <div className="container problem-grid">
        <div className="problem-text">
          <span className="eyebrow">The problem</span>
          <h2 className="section-h2">
            Your business runs on 7 tools.<br />
            None of them act on it.
          </h2>
          <p className="section-sub">
            Email, CRM, invoicing, docs, spreadsheets — every one holds a piece
            of your business but none of them work for you. You become the
            integration layer, manually copying data and chasing follow-ups all day.
          </p>
          <p className="section-sub" style={{ marginTop: 12 }}>
            NexusAgent puts 8 dedicated agents to work — each one focused on a
            single job, all of them feeding into your business.
          </p>
        </div>
        <AgentHubVisual />
      </div>
    </section>
  );
}

// ── How It Works ──────────────────────────────────────────────────────────────

function HowItWorks() {
  return (
    <section id="how-it-works" className="section">
      <div className="container">
        <div className="section-header section-header-c">
          <span className="eyebrow">How it works</span>
          <h2 className="section-h2">Connect, configure, approve</h2>
          <p className="section-sub">
            Link your accounts, set your schedules, and review what each agent surfaces.
            No code, no config files, no surprises.
          </p>
        </div>
        <div className="steps-grid">
          {HOW_IT_WORKS.map(s => (
            <div key={s.step} className="step-card">
              <div className="step-num">{s.step}</div>
              <h3 className="step-title">{s.title}</h3>
              <p className="step-desc">{s.desc}</p>
              <ul className="step-checklist">
                {s.items.map(item => (
                  <li key={item}>
                    <Check size={12} className="icon-ok" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── Agents ────────────────────────────────────────────────────────────────────

function AgentsSection() {
  return (
    <section id="agents" className="section section-alt">
      <div className="container">
        <div className="section-header section-header-c">
          <span className="eyebrow">The team</span>
          <h2 className="section-h2">8 agents, each with one job</h2>
          <p className="section-sub">
            Each agent runs on a schedule and surfaces tasks for your review.
            Rename any of them — the role stays, only the label changes.
          </p>
        </div>
        <div className="agents-grid">
          {AGENTS.map(a => (
            <div key={a.name} className="agent-card" style={{ '--agent-color': a.color }}>
              <div className="agent-color-bar" />
              <div className="agent-body">
                <div className="agent-emoji-box">{a.emoji}</div>
                <div className="agent-role">{a.role}</div>
                <div className="agent-name">{a.name}</div>
                <p className="agent-desc">{a.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── Privacy ───────────────────────────────────────────────────────────────────

function PrivacySection() {
  return (
    <section id="privacy" className="section section-alt">
      <div className="container">
        <div className="section-header section-header-c">
          <span className="eyebrow">The differentiator</span>
          <h2 className="section-h2">
            4 layers between your data and the cloud
          </h2>
          <p className="section-sub" style={{ margin: '12px auto 0' }}>
            Every outbound prompt passes through four gates before leaving your machine.
            Because "we don't train on your data" is not a privacy posture.
          </p>
        </div>
        <div className="privacy-grid">
          {PRIVACY_POINTS.map(p => (
            <div key={p.n} className="privacy-card">
              <div className="privacy-num">{p.n}</div>
              <div className="privacy-icon-box">
                <Lock size={18} />
              </div>
              <h3 className="privacy-title">{p.title}</h3>
              <p className="privacy-body">{p.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── Compare Table ─────────────────────────────────────────────────────────────

function CompareTable() {
  const cell = val => {
    if (val === true)  return <Check size={16} className="icon-ok" />;
    if (val === false) return <X size={16} className="icon-dim" />;
    return <span className="compare-badge">{val}</span>;
  };
  return (
    <section className="section section-alt">
      <div className="container">
        <div className="section-header section-header-c">
          <span className="eyebrow">Compare</span>
          <h2 className="section-h2">Why NexusAgent, not Zoho or Salesforce</h2>
        </div>
        <div className="compare-wrap">
          <table className="compare-table">
            <thead>
              <tr>
                <th className="compare-feat-col">Feature</th>
                <th className="compare-nexus-col">NexusAgent</th>
                <th>Zoho CRM</th>
                <th>Salesforce</th>
              </tr>
            </thead>
            <tbody>
              {COMPARE_ROWS.map(row => (
                <tr key={row.feature}>
                  <td className="compare-feat">{row.feature}</td>
                  <td className="compare-nexus-col">{cell(row.nexus)}</td>
                  <td>{cell(row.zoho)}</td>
                  <td>{cell(row.salesforce)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

// ── Pricing ───────────────────────────────────────────────────────────────────

function Pricing() {
  return (
    <section id="pricing" className="section">
      <div className="container">
        <div className="section-header section-header-c">
          <span className="eyebrow">Pricing</span>
          <h2 className="section-h2">Free to start. Simple to scale.</h2>
          <p className="section-sub">
            Prices in ₹. USD available at checkout. GST as applicable.
          </p>
        </div>
        <div className="pricing-grid">
          {TIERS.map(t => (
            <div key={t.name} className={`price-card ${t.featured ? 'price-featured' : ''}`}>
              {t.featured && <div className="price-pop-tag">Most popular</div>}
              <div className="price-name">{t.name}</div>
              <div className="price-row">
                <span className="price-amount">{t.price}</span>
                <span className="price-period">{t.period}</span>
              </div>
              <p className="price-desc">{t.desc}</p>
              <div className="price-divider" />
              <ul className="price-list">
                {t.items.map(item => (
                  <li key={item}>
                    {t.featured
                      ? <CheckCircle2 size={14} className="icon-ok-light" />
                      : <CheckCircle2 size={14} className="icon-ok" />}
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <a href={t.href} className={`btn price-cta ${t.featured ? 'btn-white' : 'btn-outline'}`}>
                {t.cta} <ArrowRight size={13} />
              </a>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ── FAQ ───────────────────────────────────────────────────────────────────────

function FAQ() {
  return (
    <section id="faq" className="section section-alt">
      <div className="container">
        <div className="section-header">
          <span className="eyebrow">FAQ</span>
          <h2 className="section-h2">Common questions</h2>
        </div>
        <div className="faq-wrap">
          <div className="faq-list">
            {FAQS.map((f, i) => (
              <details key={i} className="faq-item">
                <summary className="faq-summary">
                  <span>{f.q}</span>
                  <ChevronDown size={16} className="faq-chevron" />
                </summary>
                <div className="faq-body">{f.a}</div>
              </details>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// ── CTA ───────────────────────────────────────────────────────────────────────

function CTA() {
  return (
    <section className="cta-section">
      <div className="cta-glow" />
      <div className="container cta-body">
        <h2 className="cta-h2">Try it on your machine.</h2>
        <p className="cta-sub">
          Free to start. No vendor lock-in.<br />
          Your data stays on your laptop by default.
        </p>
        <div className="cta-btns">
          <a href={`${APP_URL}/setup`} className="btn btn-primary btn-lg">
            Start free <ArrowRight size={15} />
          </a>
          <a href={GITHUB} target="_blank" rel="noreferrer" className="btn btn-ghost-dark btn-lg">
            View source on GitHub
          </a>
        </div>
        <p className="cta-fine">No credit card · Self-hostable · Runs on your laptop</p>
      </div>
    </section>
  );
}

// ── Footer ────────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="footer-wrap">
      <div className="footer-inner">
        <div className="footer-brand">
          <a href="#top" className="logo">
            <LogoMark size={32} />
            NexusAgent
          </a>
          <p className="footer-tagline">
            AI workflows for your business, running locally.<br />
            8 agents. Local-first. Your data stays yours.
          </p>
          <p className="footer-contact">
            <a href={`mailto:${MAIL}`}>{MAIL}</a>
          </p>
        </div>
        <div className="footer-col">
          <div className="footer-col-title">Product</div>
          <a href="#agents">Agents</a>
          <a href="#privacy">Privacy</a>
          <a href="#pricing">Pricing</a>
          <a href="#faq">FAQ</a>
        </div>
        <div className="footer-col">
          <div className="footer-col-title">Company</div>
          <a href={`mailto:${MAIL}`}>Contact</a>
          <a href={GITHUB} target="_blank" rel="noreferrer">GitHub</a>
          <a href={`${APP_URL}/login`}>Sign in</a>
          <a href={`${APP_URL}/setup`}>Get started</a>
        </div>
        <div className="footer-col">
          <div className="footer-col-title">Legal</div>
          <a href="#">Privacy Policy</a>
          <a href="#">Terms of Service</a>
          <a href="#">Security</a>
          <a href="#">Data Handling</a>
        </div>
      </div>
      <div className="footer-bottom">
        <div className="footer-bottom-inner">
          <span>© {new Date().getFullYear()} NexusAgent. Built in India 🇮🇳</span>
          <span>nexusagent.in</span>
        </div>
      </div>
    </footer>
  );
}
