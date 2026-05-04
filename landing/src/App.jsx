import { useState } from 'react';
import {
  ShieldCheck, ArrowRight, CheckCircle2, X,
  Mail, Phone, Search, Brain, Sun, Target, Clock, Lock,
  TrendingUp, ChevronDown, Menu, Check,
} from 'lucide-react';
import Aurora   from './components/Aurora';
import BlurText from './components/BlurText';
import Magnet   from './components/Magnet';

const APP_URL  = import.meta.env.VITE_APP_URL  || 'https://app.nexusagent.in';
const MAIL     = 'hi@nexusagent.in';
const GITHUB   = 'https://github.com/praneethhh18/Nexus';

// ── Data ─────────────────────────────────────────────────────────────────────

const AGENTS = [
  {
    name: 'Atlas', role: 'Chief of Staff', emoji: '🌅', color: '#F59E0B',
    desc: 'Delivers your 8 AM briefing: open tasks, overdue invoices, today\'s meetings, stale deals — one clean page.',
    icon: Sun,
  },
  {
    name: 'Iris', role: 'Inbox Triage', emoji: '📬', color: '#38BDF8',
    desc: 'Reads new email every 15 min, classifies intent, and surfaces reply drafts for one-click approval.',
    icon: Mail,
  },
  {
    name: 'Kira', role: 'Invoice Chaser', emoji: '💰', color: '#10B981',
    desc: 'Detects overdue invoices and drafts polite payment reminders. Approve or skip in one click.',
    icon: TrendingUp,
  },
  {
    name: 'Arjun', role: 'Pipeline Watcher', emoji: '🎯', color: '#F97316',
    desc: 'Flags deals silent for 7+ days and suggests a next action you can take immediately.',
    icon: Target,
  },
  {
    name: 'Sage', role: 'Meeting Prep', emoji: '📋', color: '#8B5CF6',
    desc: '30 min before any calendar event, compiles contact history, open items, and a one-page agenda.',
    icon: Clock,
  },
  {
    name: 'Echo', role: 'Memory Keeper', emoji: '🧠', color: '#FB7185',
    desc: 'Weekly review of all conversations — distils key facts into your permanent business memory store.',
    icon: Brain,
  },
  {
    name: 'Nyx', role: 'Research Agent', emoji: '🔍', color: '#6366F1',
    desc: 'Deep-dives on companies, prospects, and market segments. Returns structured summaries with cited sources.',
    icon: Search,
  },
  {
    name: 'Vox', role: 'Voice Agent', emoji: '📞', color: '#06B6D4',
    desc: 'Makes outbound calls via SIP/PSTN. Transcribes and summarises every call, then logs it to your CRM.',
    icon: Phone,
  },
];

const STATS = [
  { value: '8', label: 'AI agents', suffix: '' },
  { value: '5', label: 'Minute setup', suffix: '' },
  { value: '100', label: 'Data private', suffix: '%' },
  { value: '₹0', label: 'To start', suffix: '' },
];


const HOW_IT_WORKS = [
  {
    step: '01', title: 'Connect your tools',
    desc: 'Link email, calendar, and import contacts in under 5 minutes. OAuth + CSV — no complex setup.',
    items: ['Gmail / Outlook', 'Google Calendar', 'CSV contact import', 'WhatsApp (optional)'],
  },
  {
    step: '02', title: 'Agents run in the background',
    desc: 'Your 8 agents start immediately. They monitor inbox, flag invoices, prep meetings — round the clock.',
    items: ['No prompting required', 'Runs on your laptop', 'Local LLM by default', 'Cloud only when you allow'],
  },
  {
    step: '03', title: 'You approve, not manage',
    desc: 'Check your unified nudge inbox every morning. Approve a reply, trigger a follow-up, or skip. Done in minutes.',
    items: ['One-click approvals', 'Inline context for every task', 'Nothing sent without your OK', 'Full audit trail'],
  },
];

const PRIVACY_POINTS = [
  {
    n: '01', title: 'Kill switch',
    body: 'Set ALLOW_CLOUD_LLM=false. Every prompt stays on your local model. One flag, zero exceptions, no restart needed.',
  },
  {
    n: '02', title: 'Sensitivity routing',
    body: 'Any prompt touching DB rows, customer records, or credentials is force-routed to local inference — regardless of your global setting.',
  },
  {
    n: '03', title: 'PII redaction',
    body: 'Emails, phones, Aadhaar/PAN, cards, secrets → opaque tokens before anything hits the cloud. Restored in the response.',
  },
  {
    n: '04', title: 'Audit log',
    body: 'Every cloud call logged as a SHA-256 fingerprint + character count. The raw prompt is never stored. Compliance-ready from day one.',
  },
];

const COMPARE_ROWS = [
  { feature: 'Autonomous AI agents',   nexus: true,    notion: false,    salesforce: false,    zoho: false   },
  { feature: 'Local-first / private',  nexus: true,    notion: false,    salesforce: false,    zoho: false   },
  { feature: 'Outbound voice calls',   nexus: true,    notion: false,    salesforce: 'Add-on', zoho: false   },
  { feature: 'WhatsApp integration',   nexus: true,    notion: false,    salesforce: false,    zoho: true    },
  { feature: 'Self-hosted option',     nexus: true,    notion: false,    salesforce: false,    zoho: false   },
  { feature: 'Built-in document RAG',  nexus: true,    notion: 'Basic',  salesforce: false,    zoho: false   },
  { feature: 'Starting price',         nexus: '₹0',   notion: '₹800/mo', salesforce: '₹6,000/mo', zoho: '₹1,400/mo' },
];

const TIERS = [
  {
    name: 'Free', price: '₹0', cadence: 'forever',
    desc: 'For solo operators exploring the local-first stack.',
    items: ['1 user · 1 business', '2 agents of your choice', '100 documents in RAG', 'Local LLM only', 'Community support'],
    cta: 'Start free', featured: false, href: `${APP_URL}/setup`,
  },
  {
    name: 'Pro', price: '₹3,999', cadence: '/month',
    desc: 'For small teams ready to put all 8 agents to work.',
    items: ['Up to 5 users', 'All 8 agents + custom builder', '1,000 documents', 'Cloud LLM toggle', 'Outbound voice (Vox)', 'Priority support'],
    cta: 'Start 14-day trial', featured: true, href: `${APP_URL}/setup`,
  },
  {
    name: 'Business', price: '₹12,999', cadence: '/month',
    desc: 'For growing businesses that need SSO + hands-on onboarding.',
    items: ['Up to 20 users', 'Unlimited documents', 'SSO (Google / Microsoft)', 'WhatsApp bridge', 'SLA + onboarding call'],
    cta: 'Talk to us', featured: false, href: `mailto:${MAIL}`,
  },
  {
    name: 'Self-hosted', price: '₹24,999', cadence: 'one-time',
    desc: 'Your server, your data, your rules. Yours forever.',
    items: ['Unlimited everything', 'Docker + Helm deploy', 'Source code access', 'Updates for 12 months', 'Private Slack channel'],
    cta: 'Buy license', featured: false, href: `mailto:${MAIL}`,
  },
];

const FAQS = [
  {
    q: 'Does my data really stay local?',
    a: 'Yes. Embeddings are always local via Ollama. Prompts touching customer data are force-routed to the local LLM. When you allow cloud calls, prompts are PII-redacted first and audited — the raw prompt is never stored.',
  },
  {
    q: 'What hardware do I need?',
    a: 'Any laptop with 8 GB RAM runs Llama 3.1 8B well. 16 GB lets you use 14B+ models. The setup wizard detects your RAM and recommends the right model tier automatically.',
  },
  {
    q: 'How does it compare to Zoho CRM or Salesforce?',
    a: 'Zoho and Salesforce are databases you manually maintain. NexusAgent is an active team that updates the CRM for you — chasing payments, flagging stale deals, prepping meetings — while keeping your data private on your machine.',
  },
  {
    q: 'Can Vox make calls to Indian numbers?',
    a: 'Yes. Vox uses Twilio SIP trunking and supports Indian PSTN numbers out of the box. You need a Twilio account and a DID number (~₹200/month). Call costs are standard Twilio rates.',
  },
  {
    q: 'Can I run it completely offline?',
    a: 'Yes. Set ALLOW_CLOUD_LLM=false. Everything runs locally — Ollama for LLM, local embeddings for RAG. Voice calls require Twilio (internet only for that service). Everything else is fully offline-capable.',
  },
  {
    q: 'How do I export my data if I want to leave?',
    a: 'Settings → Export all data → ZIP. You get every table as CSV: contacts, tasks, invoices, documents, conversations, agent runs. No lock-in, no export fees, no waiting.',
  },
];

// ── Components ────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <>
      <Nav />
      <main>
        <Hero />
        <StatsStrip />
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

function Nav() {
  const [open, setOpen] = useState(false);
  return (
    <header className="nav-wrap">
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
          <a href={`${APP_URL}/login`}  className="btn btn-ghost btn-sm">Sign in</a>
          <a href={`${APP_URL}/setup`}  className="btn btn-primary btn-sm">
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

function Hero() {
  return (
    <section id="top" className="hero-section">
      {/* Aurora animated WebGL background */}
      <div className="hero-aurora">
        <Aurora
          colorStops={['#7C3AED', '#06B6D4', '#8B5CF6']}
          amplitude={0.7}
          blend={0.25}
          speed={0.6}
        />
      </div>

      <div className="container hero-center">
        <div className="hero-badge">
          <ShieldCheck size={11} />
          Local-first · Privacy by design · Made for Indian SMBs
        </div>

        {/* BlurText animated headline */}
        <BlurText
          text="Your private AI team"
          tag="h1"
          className="hero-headline"
          animateBy="words"
          direction="bottom"
          delay={100}
          stepDuration={0.4}
        />
        <BlurText
          text="that works while you sleep"
          tag="h1"
          className="hero-headline grad-text"
          animateBy="words"
          direction="bottom"
          delay={100}
          stepDuration={0.4}
          style={{ marginTop: 0 }}
        />

        <p className="hero-sub" style={{ animationDelay: '0.4s' }}>
          8 named AI agents handle your inbox, chase invoices, prep meetings,
          watch your pipeline, and make outbound calls — all running on your
          laptop. The cloud only sees redacted data, and only when you allow it.
        </p>

        <div className="hero-actions">
          <Magnet magnetStrength={4}>
            <a href={`${APP_URL}/setup`} className="btn btn-primary btn-lg">
              Start free <ArrowRight size={15} />
            </a>
          </Magnet>
          <Magnet magnetStrength={4}>
            <a href="#agents" className="btn btn-ghost btn-lg">
              Meet the agents
            </a>
          </Magnet>
        </div>

        <div className="hero-trust">
          <span><CheckCircle2 size={13} className="icon-ok" /> No credit card</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> 5-minute install</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> Self-hostable</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> ₹0 to start</span>
        </div>
      </div>
    </section>
  );
}

function StatsStrip() {
  return (
    <div className="stats-strip">
      <div className="container stats-inner">
        {STATS.map(s => (
          <div key={s.label} className="stat-item">
            <span className="stat-value">{s.value}{s.suffix}</span>
            <span className="stat-label">{s.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Problem() {
  return (
    <section className="section section-alt">
      <div className="container problem-inner">
        <div className="problem-text">
          <span className="eyebrow">The problem</span>
          <h2 className="section-h2">Your business runs on 7 tools.<br />None of them talk to each other.</h2>
          <p className="section-lead">
            Email, CRM, invoicing, docs, spreadsheets, chat — every one of them holds
            a piece of your business. None of them act on it. You become the integration
            layer, manually copying data and chasing follow-ups all day.
          </p>
          <p className="section-lead" style={{ marginTop: 12 }}>
            Meanwhile, every SaaS tool trains on your client data, locks you into annual
            contracts, and raises prices 12% every renewal.
          </p>
        </div>
        <div className="problem-callout">
          <div className="callout-card">
            <div className="callout-line">
              <X size={16} className="icon-err" />
              <span>Email tool doesn't know your CRM</span>
            </div>
            <div className="callout-line">
              <X size={16} className="icon-err" />
              <span>Invoices go unpaid for weeks</span>
            </div>
            <div className="callout-line">
              <X size={16} className="icon-err" />
              <span>Deals go stale with no follow-up</span>
            </div>
            <div className="callout-line">
              <X size={16} className="icon-err" />
              <span>Meetings start without context</span>
            </div>
            <div className="callout-line">
              <X size={16} className="icon-err" />
              <span>Vendor AI reads your customer data</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className="section">
      <div className="container">
        <div className="section-header">
          <span className="eyebrow">How it works</span>
          <h2 className="section-h2">From zero to autonomous in 5 minutes</h2>
        </div>
        <div className="steps-grid">
          {HOW_IT_WORKS.map((s, i) => (
            <div key={i} className="step-card">
              <div className="step-number">{s.step}</div>
              <h3 className="step-title">{s.title}</h3>
              <p className="step-desc">{s.desc}</p>
              <ul className="step-list">
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

function AgentsSection() {
  return (
    <section id="agents" className="section section-alt">
      <div className="container">
        <div className="section-header">
          <span className="eyebrow">The team</span>
          <h2 className="section-h2">8 agents that work while you sleep</h2>
          <p className="section-sub">
            Each agent has a single responsibility and runs on a schedule.
            Rename any of them — they keep their role, just wear your preferred name.
          </p>
        </div>
        <div className="agents-grid">
          {AGENTS.map(a => {
            const Icon = a.icon;
            return (
              <div key={a.name} className="agent-card" style={{ '--agent-color': a.color }}>
                <div className="agent-icon-wrap">
                  <Icon size={18} />
                </div>
                <div className="agent-meta">
                  <span className="agent-role">{a.role}</span>
                  <span className="agent-name">{a.name}</span>
                </div>
                <p className="agent-desc">{a.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function PrivacySection() {
  return (
    <section id="privacy" className="section privacy-section">
      <div className="privacy-bg-glow" />
      <div className="container">
        <div className="section-header">
          <span className="eyebrow">The differentiator</span>
          <h2 className="section-h2">4 layers between your data and the cloud</h2>
          <p className="section-sub">
            Every outbound prompt passes through four gates before leaving your machine.
            Because "we don't train on your data" in a privacy policy is not a privacy posture.
          </p>
        </div>
        <div className="privacy-grid">
          {PRIVACY_POINTS.map(p => (
            <div key={p.n} className="privacy-card">
              <div className="privacy-num">{p.n}</div>
              <div className="privacy-content">
                <Lock size={14} className="privacy-icon" />
                <h3 className="privacy-title">{p.title}</h3>
                <p className="privacy-body">{p.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CompareTable() {
  const renderCell = (val) => {
    if (val === true)  return <Check size={16} className="icon-ok" />;
    if (val === false) return <X size={16} className="icon-dim" />;
    return <span className="compare-val">{val}</span>;
  };
  return (
    <section className="section section-alt">
      <div className="container">
        <div className="section-header">
          <span className="eyebrow">Compare</span>
          <h2 className="section-h2">Why NexusAgent, not Zoho or Salesforce</h2>
        </div>
        <div className="compare-wrap">
          <table className="compare-table">
            <thead>
              <tr>
                <th className="compare-feature-col">Feature</th>
                <th className="compare-nexus">NexusAgent</th>
                <th>Notion AI</th>
                <th>Salesforce</th>
                <th>Zoho CRM</th>
              </tr>
            </thead>
            <tbody>
              {COMPARE_ROWS.map(row => (
                <tr key={row.feature}>
                  <td className="compare-feature">{row.feature}</td>
                  <td className="compare-nexus">{renderCell(row.nexus)}</td>
                  <td>{renderCell(row.notion)}</td>
                  <td>{renderCell(row.salesforce)}</td>
                  <td>{renderCell(row.zoho)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  return (
    <section id="pricing" className="section">
      <div className="container">
        <div className="section-header">
          <span className="eyebrow">Pricing</span>
          <h2 className="section-h2">Free to start. Simple to scale.</h2>
          <p className="section-sub">Prices shown in ₹. USD pricing available at checkout. + GST as applicable.</p>
        </div>
        <div className="pricing-grid">
          {TIERS.map(t => (
            <div key={t.name} className={`price-card ${t.featured ? 'price-featured' : ''}`}>
              {t.featured && <div className="price-badge">Most popular</div>}
              <div className="price-name">{t.name}</div>
              <div className="price-amount">
                {t.price}
                <span className="price-cadence">{t.cadence}</span>
              </div>
              <p className="price-desc">{t.desc}</p>
              <ul className="price-list">
                {t.items.map(item => (
                  <li key={item}>
                    <CheckCircle2 size={13} className="icon-ok" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <a href={t.href} className={`btn ${t.featured ? 'btn-primary' : 'btn-ghost'} price-cta`}>
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
      <div className="container faq-container">
        <div className="section-header">
          <span className="eyebrow">FAQ</span>
          <h2 className="section-h2">Common questions</h2>
        </div>
        <div className="faq-list">
          {FAQS.map((f, i) => (
            <details key={i} className="faq-item">
              <summary className="faq-summary">
                <span>{f.q}</span>
                <ChevronDown size={16} className="faq-chevron" />
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
    <section className="cta-section">
      <div className="cta-orb cta-orb-1" />
      <div className="cta-orb cta-orb-2" />
      <div className="container cta-inner">
        <h2 className="cta-headline">Your team of 8 is ready.</h2>
        <p className="cta-sub">
          Five minutes to set up. Zero vendor lock-in.<br />Your data stays yours.
        </p>
        <div className="cta-actions">
          <Magnet magnetStrength={4}>
            <a href={`${APP_URL}/setup`} className="btn btn-primary btn-lg">
              Start free <ArrowRight size={15} />
            </a>
          </Magnet>
          <Magnet magnetStrength={4}>
            <a href={GITHUB} target="_blank" rel="noreferrer" className="btn btn-ghost btn-lg">
              View source on GitHub
            </a>
          </Magnet>
        </div>
        <p className="cta-fine">No credit card · Self-hostable · Runs on your laptop</p>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer-wrap">
      <div className="container footer-inner">
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
          <a href="mailto:hi@nexusagent.in">Contact</a>
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
        <div className="container footer-bottom-inner">
          <span>© {new Date().getFullYear()} NexusAgent. Built in India 🇮🇳</span>
          <span>nexusagent.in</span>
        </div>
      </div>
    </footer>
  );
}
