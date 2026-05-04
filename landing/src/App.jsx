import { useState, useEffect } from 'react';
import {
  ShieldCheck, ArrowRight, CheckCircle2, X,
  Mail, Phone, Search, Brain, Sun, Target, Clock, Lock,
  TrendingUp, ChevronDown, Menu, Check,
} from 'lucide-react';

const APP_URL = import.meta.env.VITE_APP_URL || 'https://app.nexusagent.in';
const MAIL    = 'hi@nexusagent.in';
const GITHUB  = 'https://github.com/praneethhh18/Nexus';

// ── Data ─────────────────────────────────────────────────────────────────────

const AGENTS = [
  { name: 'Atlas', role: 'Chief of Staff',    emoji: '🌅', color: '#F59E0B', icon: Sun,
    desc: 'Delivers your 8 AM briefing: open tasks, overdue invoices, today\'s meetings, stale deals — one clean page.' },
  { name: 'Iris',  role: 'Inbox Triage',      emoji: '📬', color: '#0EA5E9', icon: Mail,
    desc: 'Reads new email every 15 min, classifies intent, and surfaces reply drafts for one-click approval.' },
  { name: 'Kira',  role: 'Invoice Chaser',    emoji: '💰', color: '#10B981', icon: TrendingUp,
    desc: 'Detects overdue invoices and drafts polite payment reminders. Approve or skip in one click.' },
  { name: 'Arjun', role: 'Pipeline Watcher',  emoji: '🎯', color: '#F97316', icon: Target,
    desc: 'Flags deals silent for 7+ days and suggests a next action you can take immediately.' },
  { name: 'Sage',  role: 'Meeting Prep',      emoji: '📋', color: '#8B5CF6', icon: Clock,
    desc: '30 min before any calendar event, compiles contact history, open items, and a one-page agenda.' },
  { name: 'Echo',  role: 'Memory Keeper',     emoji: '🧠', color: '#EC4899', icon: Brain,
    desc: 'Weekly review of all conversations — distils key facts into your permanent business memory store.' },
  { name: 'Nyx',   role: 'Research Agent',    emoji: '🔍', color: '#6366F1', icon: Search,
    desc: 'Deep-dives on companies, prospects, and market segments. Returns structured summaries with cited sources.' },
  { name: 'Vox',   role: 'Voice Agent',       emoji: '📞', color: '#06B6D4', icon: Phone,
    desc: 'Makes outbound calls via SIP/PSTN. Transcribes and summarises every call, then logs it to your CRM.' },
];

const HOW_IT_WORKS = [
  { step: '01', title: 'Connect your tools',
    desc: 'Link email, calendar, and import contacts in under 5 minutes. OAuth + CSV — no complex setup.',
    items: ['Gmail / Outlook', 'Google Calendar', 'CSV contact import', 'WhatsApp (optional)'] },
  { step: '02', title: 'Agents run in the background',
    desc: 'Your 8 agents start immediately. They monitor inbox, flag invoices, prep meetings — round the clock.',
    items: ['No prompting required', 'Runs on your laptop', 'Local LLM by default', 'Cloud only when you allow'] },
  { step: '03', title: 'You approve, not manage',
    desc: 'Check your unified inbox every morning. Approve a reply, trigger a follow-up, or skip. Done in minutes.',
    items: ['One-click approvals', 'Inline context for every task', 'Nothing sent without your OK', 'Full audit trail'] },
];

const PRIVACY_POINTS = [
  { n: '01', title: 'Kill switch',
    body: 'Set ALLOW_CLOUD_LLM=false. Every prompt stays on your local model. One flag, zero exceptions, no restart needed.' },
  { n: '02', title: 'Sensitivity routing',
    body: 'Any prompt touching DB rows, customer records, or credentials is force-routed to local inference — regardless of your global setting.' },
  { n: '03', title: 'PII redaction',
    body: 'Emails, phones, Aadhaar/PAN, cards, secrets → opaque tokens before anything hits the cloud. Restored in the response.' },
  { n: '04', title: 'Audit log',
    body: 'Every cloud call logged as a SHA-256 fingerprint + character count. The raw prompt is never stored. Compliance-ready from day one.' },
];

const COMPARE_ROWS = [
  { feature: 'Autonomous AI agents',  nexus: true,   notion: false,   salesforce: false,     zoho: false },
  { feature: 'Local-first / private', nexus: true,   notion: false,   salesforce: false,     zoho: false },
  { feature: 'Outbound voice calls',  nexus: true,   notion: false,   salesforce: 'Add-on',  zoho: false },
  { feature: 'WhatsApp integration',  nexus: true,   notion: false,   salesforce: false,     zoho: true  },
  { feature: 'Self-hosted option',    nexus: true,   notion: false,   salesforce: false,     zoho: false },
  { feature: 'Built-in document RAG', nexus: true,   notion: 'Basic', salesforce: false,     zoho: false },
  { feature: 'Starting price',        nexus: '₹0',   notion: '₹800/mo', salesforce: '₹6,000/mo', zoho: '₹1,400/mo' },
];

const TIERS = [
  { name: 'Free',        price: '₹0',      period: 'forever',   featured: false,
    desc: 'For solo operators exploring the local-first stack.',
    items: ['1 user · 1 business', '2 agents of your choice', '100 documents in RAG', 'Local LLM only', 'Community support'],
    cta: 'Start free',         href: `${APP_URL}/setup` },
  { name: 'Pro',         price: '₹3,999',  period: '/month',    featured: true,
    desc: 'For small teams ready to put all 8 agents to work.',
    items: ['Up to 5 users', 'All 8 agents + custom builder', '1,000 documents', 'Cloud LLM toggle', 'Outbound voice (Vox)', 'Priority support'],
    cta: 'Start 14-day trial', href: `${APP_URL}/setup` },
  { name: 'Business',   price: '₹12,999', period: '/month',    featured: false,
    desc: 'For growing businesses that need SSO + hands-on onboarding.',
    items: ['Up to 20 users', 'Unlimited documents', 'SSO (Google / Microsoft)', 'WhatsApp bridge', 'SLA + onboarding call'],
    cta: 'Talk to us',         href: `mailto:${MAIL}` },
  { name: 'Self-hosted', price: '₹24,999', period: 'one-time',  featured: false,
    desc: 'Your server, your data, your rules. Yours forever.',
    items: ['Unlimited everything', 'Docker + Helm deploy', 'Source code access', 'Updates for 12 months', 'Private Slack channel'],
    cta: 'Buy license',        href: `mailto:${MAIL}` },
];

const FAQS = [
  { q: 'Does my data really stay local?',
    a: 'Yes. Embeddings are always local via Ollama. Prompts touching customer data are force-routed to the local LLM. When you allow cloud calls, prompts are PII-redacted first and audited — the raw prompt is never stored.' },
  { q: 'What hardware do I need?',
    a: 'Any laptop with 8 GB RAM runs Llama 3.1 8B well. 16 GB lets you use 14B+ models. The setup wizard detects your RAM and recommends the right model tier automatically.' },
  { q: 'How does it compare to Zoho CRM or Salesforce?',
    a: 'Zoho and Salesforce are databases you manually maintain. NexusAgent is an active team that updates the CRM for you — chasing payments, flagging stale deals, prepping meetings — while keeping your data private on your machine.' },
  { q: 'Can Vox make calls to Indian numbers?',
    a: 'Yes. Vox uses Twilio SIP trunking and supports Indian PSTN numbers out of the box. You need a Twilio account and a DID number (~₹200/month). Call costs are standard Twilio rates.' },
  { q: 'Can I run it completely offline?',
    a: 'Yes. Set ALLOW_CLOUD_LLM=false. Everything runs locally — Ollama for LLM, local embeddings for RAG. Voice calls require Twilio (internet only for that service). Everything else is fully offline-capable.' },
  { q: 'How do I export my data if I want to leave?',
    a: 'Settings → Export all data → ZIP. You get every table as CSV: contacts, tasks, invoices, documents, conversations, agent runs. No lock-in, no export fees, no waiting.' },
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
          <span className="logo-mark">N</span>
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
          The AI business team<br />
          that keeps your data <strong>private</strong>
        </h1>

        <p className="hero-sub">
          8 autonomous agents handle your CRM, inbox, invoices, meetings, and
          outbound calls — running on your laptop, your data never leaving your machine.
        </p>

        <div className="hero-actions">
          <a href={`${APP_URL}/setup`} className="btn btn-primary btn-lg">
            Start free — it's ₹0 <ArrowRight size={14} />
          </a>
          <a href="#how-it-works" className="btn btn-outline btn-lg">
            See how it works
          </a>
        </div>

        <div className="hero-trust">
          <span><CheckCircle2 size={13} className="icon-ok" /> No credit card</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> 5-minute setup</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> Self-hostable</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> Runs on your laptop</span>
        </div>
      </div>
    </section>
  );
}

// ── Problem ───────────────────────────────────────────────────────────────────

function Problem() {
  const pains = [
    'Email tool doesn\'t know your CRM',
    'Invoices go unpaid for weeks',
    'Deals go stale with no follow-up',
    'Meetings start without any context',
    'Vendor AI reads your customer data',
  ];
  return (
    <section className="section section-alt">
      <div className="container problem-grid">
        <div className="problem-text">
          <span className="eyebrow">The problem</span>
          <h2 className="section-h2">
            Your business runs on 7 tools.<br />
            None of them talk to each other.
          </h2>
          <p className="section-sub">
            Email, CRM, invoicing, docs, spreadsheets — every one holds a piece
            of your business. None of them act on it. You become the integration
            layer, manually copying data and chasing follow-ups all day.
          </p>
          <p className="section-sub" style={{ marginTop: 10 }}>
            Meanwhile, every SaaS tool trains on your client data, locks you into
            annual contracts, and raises prices 12% every renewal.
          </p>
        </div>
        <div className="pain-stack">
          {pains.map(text => (
            <div key={text} className="pain-item">
              <div className="pain-icon-box">
                <X size={14} className="icon-err" />
              </div>
              <span>{text}</span>
            </div>
          ))}
        </div>
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
          <h2 className="section-h2">From zero to autonomous in 5 minutes</h2>
          <p className="section-sub">
            No devops, no configuration files, no API keys to hunt down. Just connect
            your tools and your agents start working.
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
          <h2 className="section-h2">8 agents that work while you sleep</h2>
          <p className="section-sub">
            Each agent has a single responsibility and runs on a schedule.
            Rename any of them — they keep their role, just your preferred name.
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
                <th>Notion AI</th>
                <th>Salesforce</th>
                <th>Zoho CRM</th>
              </tr>
            </thead>
            <tbody>
              {COMPARE_ROWS.map(row => (
                <tr key={row.feature}>
                  <td className="compare-feat">{row.feature}</td>
                  <td className="compare-nexus-col">{cell(row.nexus)}</td>
                  <td>{cell(row.notion)}</td>
                  <td>{cell(row.salesforce)}</td>
                  <td>{cell(row.zoho)}</td>
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
        <h2 className="cta-h2">Your team of 8 is ready.</h2>
        <p className="cta-sub">
          Five minutes to set up. Zero vendor lock-in.<br />
          Your data stays on your machine, always.
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
            <span className="logo-mark">N</span>
            NexusAgent
          </a>
          <p className="footer-tagline">
            A private AI business OS for Indian SMBs.<br />
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
