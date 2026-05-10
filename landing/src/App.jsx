import { useState, useEffect, useRef, useCallback } from 'react';
import {
  ShieldCheck, ArrowRight, CheckCircle2, X,
  Mail, Phone, Moon, Brain, Sun, Target, Clock, Lock,
  TrendingUp, ChevronDown, Menu, Check, Loader2,
} from 'lucide-react';
import Aurora, { AuroraErrorBoundary } from './components/Aurora';

const APP_URL = import.meta.env.VITE_APP_URL || 'https://app.nexusagent.in';
const MAIL    = 'hi@nexusagent.in';
const GITHUB  = 'https://github.com/praneethhh18/Nexus';

// ── Early-access modal ────────────────────────────────────────────────────────

function EarlyAccessModal({ tier, onClose }) {
  const [name,    setName]    = useState('');
  const [email,   setEmail]   = useState('');
  const [loading, setLoading] = useState(false);
  const [done,    setDone]    = useState(false);
  const [error,   setError]   = useState('');
  const emailRef = useRef(null);

  useEffect(() => { emailRef.current?.focus(); }, []);

  // Close on Escape
  useEffect(() => {
    const fn = e => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', fn);
    return () => window.removeEventListener('keydown', fn);
  }, [onClose]);

  const submit = async e => {
    e.preventDefault();
    setError(''); setLoading(true);
    try {
      const res = await fetch('/api/waitlist', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, tier }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Something went wrong');
      setDone(true);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <div className="modal-overlay" onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
      <div className="modal-box">
        <button className="modal-close" onClick={onClose}><X size={16} /></button>
        {done ? (
          <div className="modal-done">
            <CheckCircle2 size={40} className="icon-ok" />
            <h3>You're on the list!</h3>
            <p>We'll reach out to <strong>{email}</strong> when {tier} access opens.</p>
            <button className="btn btn-outline" onClick={onClose}>Close</button>
          </div>
        ) : (
          <>
            <div className="modal-tier-badge">{tier}</div>
            <h3 className="modal-title">Get early access</h3>
            <p className="modal-sub">Leave your details and we'll contact you when your plan is ready.</p>
            <form className="modal-form" onSubmit={submit}>
              <input
                type="text" placeholder="Your name" value={name}
                onChange={e => setName(e.target.value)}
                className="modal-input"
              />
              <input
                ref={emailRef}
                type="email" placeholder="Work email *" value={email}
                onChange={e => setEmail(e.target.value)}
                required className="modal-input"
              />
              {error && <p className="modal-error">{error}</p>}
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? <Loader2 size={15} className="spin" /> : <ArrowRight size={15} />}
                {loading ? 'Submitting…' : 'Join waitlist'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}

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

// Pricing source of truth: api/routers/billing.py PLANS dict.
// Update there + here in the same PR — landing must always reflect what
// Razorpay actually charges. Tiers with a `plan` field hand off to the
// signup → in-app /pricing?plan=X auto-checkout funnel.
const TIERS = [
  { name: 'Free',        price: '₹0',       period: 'forever',  featured: false,
    desc: 'Try NexusAgent with a couple of agents on your own machine.',
    items: ['1 user', '2 AI agents', 'Local LLM only', '100 documents in RAG', 'GitHub-issue support'],
    cta: 'Get started',        href: `${APP_URL}/setup` },
  { name: 'Starter',     price: '₹1,499',   period: '/month',   featured: false,
    desc: 'For solo operators with a small list and modest WhatsApp volume.',
    items: ['2 users', '5 AI agents', '500 documents', '100 WhatsApp/mo', '30 voice mins/mo', 'Email support'],
    cta: 'Subscribe',          plan: 'starter' },
  { name: 'Pro',         price: '₹5,999',   period: '/month',   featured: true,
    desc: 'All 8 agents + cloud LLM for a 5-person team — the obvious one.',
    items: ['Up to 5 users', 'All 8 AI agents', '2,000 documents', '500 WhatsApp/mo',
            '100 voice mins/mo', 'Cloud LLM (Claude / Bedrock)', 'AI proposals + Calendar + Email'],
    cta: 'Subscribe',          plan: 'pro' },
  { name: 'Privacy',     price: '₹14,999',  period: '/month',   featured: false,
    desc: 'Sensitive prompts run on YOUR laptop via the Privacy Bridge.',
    items: ['Up to 10 users', '10,000 documents', '2,000 WhatsApp/mo', '300 voice mins/mo',
            'Privacy Bridge (data on your laptop)', 'Cloud LLM with PII redaction', 'Priority 24h support'],
    cta: 'Subscribe',          plan: 'privacy' },
  { name: 'Self-hosted', price: '₹4,99,000', period: 'one-time', featured: false,
    desc: 'Full source + Docker deploy on your own infra. One-time license + optional support.',
    items: ['Unlimited users on your server', 'Docker + Helm deploy', 'Full source code access',
            '12 months of updates included', 'Bring-your-own API keys (no usage fees from us)',
            'Optional ₹74,999/year support contract'],
    cta: 'Talk to sales',      href: `mailto:${MAIL}` },
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

// Nav links — easier to keep the pill animation and the rendered <a>s in sync
const NAV_LINKS = [
  { id: 'agents',  label: 'Agents',  href: '#agents'  },
  { id: 'privacy', label: 'Privacy', href: '#privacy' },
  { id: 'pricing', label: 'Pricing', href: '#pricing' },
  { id: 'faq',     label: 'FAQ',     href: '#faq'     },
];

function Nav() {
  const [open, setOpen]         = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [hidden,   setHidden]   = useState(false);
  const [hoveredLink, setHoveredLink] = useState(null);
  const [pillStyle, setPillStyle]     = useState({ opacity: 0 });

  const wrapRef     = useRef(null);
  const linksRef    = useRef(null);
  const ctaRef      = useRef(null);
  const linkRefs    = useRef({});

  // Scrolled + smart-sticky: hide on scroll-down past the fold, show on scroll-up.
  // Always visible within the first 80px so the top of the page never feels broken.
  useEffect(() => {
    let lastY = window.scrollY;
    const fn = () => {
      const y = window.scrollY;
      setScrolled(y > 8);
      if (y < 80) {
        setHidden(false);             // top of page — always visible
      } else if (y > lastY + 4) {
        setHidden(true);              // scrolling DOWN — vanish
      } else if (y < lastY - 4) {
        setHidden(false);             // scrolling UP — reveal
      }
      lastY = y;
    };
    window.addEventListener('scroll', fn, { passive: true });
    return () => window.removeEventListener('scroll', fn);
  }, []);

  // Don't keep a stale pill visible while the header is hidden — looks weird
  // when the bar reappears with a glowing pill at a non-hovered link.
  useEffect(() => {
    if (hidden && pillStyle.opacity) setPillStyle((s) => ({ ...s, opacity: 0 }));
  }, [hidden, pillStyle.opacity]);

  // Sliding pill — recompute target rect whenever hover changes
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => {
    if (!hoveredLink || !linksRef.current) {
      setPillStyle((s) => ({ ...s, opacity: 0 }));
      return;
    }
    const el = linkRefs.current[hoveredLink];
    if (!el) return;
    const parentRect = linksRef.current.getBoundingClientRect();
    const rect = el.getBoundingClientRect();
    setPillStyle({
      opacity: 1,
      transform: `translate3d(${rect.left - parentRect.left}px, ${rect.top - parentRect.top}px, 0)`,
      width: `${rect.width}px`,
      height: `${rect.height}px`,
    });
  }, [hoveredLink]);

  // Cursor spotlight — write --mx / --my CSS vars on the wrap
  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap) return;
    const onMove = (e) => {
      const rect = wrap.getBoundingClientRect();
      wrap.style.setProperty('--mx', `${e.clientX - rect.left}px`);
      wrap.style.setProperty('--my', `${e.clientY - rect.top}px`);
    };
    wrap.addEventListener('mousemove', onMove);
    return () => wrap.removeEventListener('mousemove', onMove);
  }, []);

  // Magnetic CTA — pull "Start free" gently toward cursor when within 100px
  useEffect(() => {
    const btn = ctaRef.current;
    if (!btn) return;
    const onMove = (e) => {
      const rect = btn.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      const dx = e.clientX - cx;
      const dy = e.clientY - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const RANGE = 100;
      if (dist < RANGE) {
        const pull = (1 - dist / RANGE) * 10;
        const ux = dx / (dist || 1), uy = dy / (dist || 1);
        btn.style.transform = `translate3d(${ux * pull}px, ${uy * pull}px, 0)`;
      } else if (btn.style.transform) {
        btn.style.transform = '';
      }
    };
    window.addEventListener('mousemove', onMove);
    return () => {
      window.removeEventListener('mousemove', onMove);
      if (btn) btn.style.transform = '';
    };
  }, []);

  return (
    <header ref={wrapRef} className={`nav-wrap ${scrolled ? 'nav-scrolled' : ''} ${hidden ? 'nav-hidden' : ''}`}>
      {/* Animated WebGL aurora behind everything — error boundary so a stale
          GPU driver can't break the whole header. */}
      <div className="nav-aurora" aria-hidden>
        <AuroraErrorBoundary>
          <Aurora
            colorStops={['#7C3AED', '#06B6D4', '#3B82F6']}
            amplitude={0.6}
            blend={0.5}
            speed={0.7}
          />
        </AuroraErrorBoundary>
      </div>

      {/* Cursor-tracking radial spotlight overlay */}
      <div className="nav-spotlight" aria-hidden />

      <div className="container nav-inner">
        <a href="#top" className="logo">
          <LogoMark size={32} />
          NexusAgent
        </a>

        <nav
          ref={linksRef}
          className={`nav-links ${open ? 'nav-open' : ''}`}
          onMouseLeave={() => setHoveredLink(null)}
        >
          {/* Sliding pill — single absolutely-positioned element that flies
              between the hovered link's bounds */}
          <span
            className="nav-pill"
            style={pillStyle}
            aria-hidden
          />
          {NAV_LINKS.map((l) => (
            <a
              key={l.id}
              ref={(el) => { linkRefs.current[l.id] = el; }}
              href={l.href}
              onMouseEnter={() => setHoveredLink(l.id)}
              onClick={() => setOpen(false)}
            >
              {l.label}
            </a>
          ))}
        </nav>

        <div className="nav-ctas">
          <a href={`${APP_URL}/login`} className="nav-signin">Sign in</a>
          <a
            ref={ctaRef}
            href={`${APP_URL}/setup`}
            className="btn btn-primary btn-sm nav-cta-magnetic"
          >
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
        <div className="hero-eyebrow">
          <ShieldCheck size={12} />
          Built for the Indian SMB grind
        </div>

        <h1 className="hero-h1">
          <span className="hero-h1-line">An AI business team</span>
          <span className="hero-h1-line">that runs on <strong>your laptop</strong></span>
        </h1>

        <p className="hero-sub">
          A growing team of specialised agents handling CRM, inbox, invoices,
          meetings and calls — locally by default, so your data stays on your machine.
        </p>

        <div className="hero-actions">
          <a href={`${APP_URL}/setup`} className="btn btn-primary btn-lg">
            Start free <ArrowRight size={14} />
          </a>
          <a href="#agents" className="btn btn-outline btn-lg">
            Meet the team
          </a>
        </div>

        <div className="hero-trust">
          <span><CheckCircle2 size={13} className="icon-ok" /> No credit card</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> Open source</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> Self-hostable</span>
          <span><CheckCircle2 size={13} className="icon-ok" /> Runs offline</span>
        </div>
      </div>
    </section>
  );
}


// ── Agents data (interactive, auto-playing demo) ────────────────────────────

const DEMO_AGENTS = [
  {
    id: 'atlas', name: 'Atlas', role: 'Daily briefing',
    Icon: Sun, c: '#F59E0B',
    tagline: 'Your morning at a glance.',
    desc: 'Each morning, Atlas pulls together your open tasks, overdue invoices, and today\'s meetings into a single summary you can scan in 30 seconds.',
    schedule: 'Every morning · 8:00 AM',
    runsOn: 'Local LLM (Ollama)',
    connects: ['Gmail', 'Google Calendar', 'Internal CRM'],
    statuses: ['Reading calendar…', 'Pulling open tasks…', 'Building summary'],
    suggestion: 'Suggestion · Follow up with Mehta Industries — last touched 14 days ago.',
  },
  {
    id: 'iris', name: 'Iris', role: 'Inbox triage',
    Icon: Mail, c: '#0EA5E9',
    tagline: 'Your inbox, sorted.',
    desc: 'Checks your inbox on a schedule, classifies emails by intent (urgent / lead / FYI), and drafts suggested replies for you to review before sending.',
    schedule: 'Every 30 minutes',
    runsOn: 'Local LLM (Ollama)',
    connects: ['Gmail / IMAP', 'Internal CRM'],
    statuses: ['Fetching new mail…', 'Classifying intent…', 'Drafting reply'],
    suggestion: 'Draft ready · Reply to Rohan about contract v3, attach revised pricing.',
  },
  {
    id: 'kira', name: 'Kira', role: 'Invoice follow-up',
    Icon: TrendingUp, c: '#10B981',
    tagline: 'Get paid on time.',
    desc: 'Looks for overdue invoices and drafts polite follow-up messages in Hindi or English. You approve before anything gets sent — never any surprises.',
    schedule: 'Daily · 10:00 AM',
    runsOn: 'Local LLM (Ollama)',
    connects: ['Internal CRM', 'Gmail', 'WhatsApp'],
    statuses: ['Scanning invoices…', 'Found 3 overdue…', 'Drafting reminders'],
    suggestion: 'Send 3 reminders · Polite follow-up drafted in Hindi + English.',
  },
  {
    id: 'arjun', name: 'Arjun', role: 'Pipeline review',
    Icon: Target, c: '#F97316',
    tagline: 'No deal slips through.',
    desc: 'Surfaces deals that haven\'t had activity in a while, suggests next actions based on history, and flags the highest-value risks for your attention.',
    schedule: 'Weekly · Monday 9:00 AM',
    runsOn: 'Local LLM (Ollama)',
    connects: ['Internal CRM'],
    statuses: ['Reading 24 deals…', 'Checking activity…', 'Ranking risk'],
    suggestion: 'Top risk · Acme Foods — proposal sent, no reply for 16 days.',
  },
  {
    id: 'sage', name: 'Sage', role: 'Meeting prep',
    Icon: Clock, c: '#8B5CF6',
    tagline: 'Walk in prepared.',
    desc: 'Before each scheduled meeting, gathers relevant contact history, open items, and past notes so you\'re not going in blind. Briefing arrives 15 minutes early.',
    schedule: '15 minutes before each meeting',
    runsOn: 'Local LLM (Ollama)',
    connects: ['Google Calendar', 'Internal CRM'],
    statuses: ['Reading calendar…', 'Pulling contact history…', 'Building brief'],
    suggestion: 'Brief ready · 4 PM with Mehta — pricing pushback on tier 2 last call.',
  },
  {
    id: 'echo', name: 'Echo', role: 'Memory keeper',
    Icon: Brain, c: '#EC4899',
    tagline: 'Never forget a detail.',
    desc: 'Periodically reviews your conversations and notes the key facts about contacts and deals into a searchable memory store you can query in plain English.',
    schedule: 'Hourly',
    runsOn: 'Local LLM (Ollama) + embeddings',
    connects: ['Gmail', 'Vox transcripts', 'Internal CRM'],
    statuses: ['Indexing emails…', 'Extracting facts…', 'Updating memory'],
    suggestion: '3 new memories · Acme Net-30, CFO Anjali approval, Q2 ₹4.8L.',
  },
  {
    id: 'vox', name: 'Vox', role: 'Voice calls',
    Icon: Phone, c: '#06B6D4',
    tagline: 'Outbound calls, fully logged.',
    desc: 'Makes outbound calls over SIP using ElevenLabs voice, captures full transcripts, and logs a structured summary back to the CRM. Bring your own Twilio.',
    schedule: 'On demand',
    runsOn: 'Cloud (Groq + ElevenLabs + Twilio)',
    connects: ['Twilio', 'Internal CRM'],
    statuses: ['Dialling +91 98765…', 'Speaking…', 'Transcribing'],
    suggestion: 'Logged · Payment expected by Friday — INV-2087 marked "promised".',
  },
  {
    id: 'nyx', name: 'Nyx', role: 'Evening digest',
    Icon: Moon, c: '#6366F1',
    tagline: 'End your day with a summary.',
    desc: 'At 6 PM, wraps up the day — tasks closed, invoices sent, deals advanced — and suggests what to tackle tomorrow morning so you start clear-headed.',
    schedule: 'Every evening · 6:00 PM',
    runsOn: 'Local LLM (Ollama)',
    connects: ['Internal CRM', 'Gmail'],
    statuses: ['Tallying actions…', 'Summarising day…', 'Planning tomorrow'],
    suggestion: 'Tomorrow · 3 meetings, prep needed for Mehta — block 30 min at 3:30 PM.',
  },
];

// ── Hooks: streaming text + work cycle ──────────────────────────────────────

function useStream(text, speed = 22, deps = []) {
  const [out, setOut] = useState('');
  useEffect(() => {
    setOut('');
    if (!text) return;
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setOut(text.slice(0, i));
      if (i >= text.length) clearInterval(id);
    }, speed);
    return () => clearInterval(id);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text, ...deps]);
  return out;
}

// Phases: scan (0) → think (1) → reveal (2) → click (3) → done (4)
const PHASE_DURATIONS = [1100, 1100, 1900, 700, 600];

function useWorkPhase(active, paused, onCycleEnd) {
  const [phase, setPhase] = useState(0);

  // Reset phase whenever the active agent changes
  useEffect(() => { setPhase(0); }, [active]);

  useEffect(() => {
    if (paused) return;
    const id = setTimeout(() => {
      if (phase < 4) {
        setPhase(phase + 1);
      } else {
        onCycleEnd();
      }
    }, PHASE_DURATIONS[phase]);
    return () => clearTimeout(id);
  }, [phase, paused, onCycleEnd]);

  return phase;
}

// ── Network background — drifting nodes + connecting strings ───────────────

const NETWORK_NODES = [
  { x: 12,  y: 18, r: 4 },
  { x: 28,  y: 8,  r: 3 },
  { x: 46,  y: 22, r: 5 },
  { x: 64,  y: 12, r: 3.5 },
  { x: 82,  y: 26, r: 4 },
  { x: 92,  y: 52, r: 3 },
  { x: 78,  y: 76, r: 4 },
  { x: 56,  y: 88, r: 3.5 },
  { x: 32,  y: 80, r: 4 },
  { x: 8,   y: 64, r: 3 },
  { x: 18,  y: 44, r: 3.5 },
  { x: 70,  y: 48, r: 4 },
];

const NETWORK_LINES = [
  [0,1],[1,2],[2,3],[3,4],[4,5],[5,6],[6,7],[7,8],[8,9],[9,10],[10,0],
  [2,10],[3,11],[7,11],[2,11],[5,11],[1,11],[8,10],[6,11],[0,8],
];

function AgentNetwork({ color }) {
  return (
    <div className="agent-network" aria-hidden style={{ '--c': color }}>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="agent-network-svg">
        {NETWORK_LINES.map(([a, b], i) => {
          const A = NETWORK_NODES[a], B = NETWORK_NODES[b];
          // Curved path through a midpoint with slight offset for organic feel
          const mx = (A.x + B.x) / 2 + (i % 2 === 0 ? 2 : -2);
          const my = (A.y + B.y) / 2 + (i % 3 === 0 ? -2 : 2);
          return (
            <path
              key={i}
              d={`M ${A.x} ${A.y} Q ${mx} ${my} ${B.x} ${B.y}`}
              className="agent-network-line"
              style={{ animationDelay: `${(i % 6) * 0.4}s` }}
            />
          );
        })}
        {NETWORK_NODES.map((n, i) => (
          <g key={i}>
            <circle cx={n.x} cy={n.y} r={n.r * 1.6} className="agent-network-node-halo"
                    style={{ animationDelay: `${(i % 5) * 0.3}s` }} />
            <circle cx={n.x} cy={n.y} r={n.r} className="agent-network-node" />
          </g>
        ))}
      </svg>
    </div>
  );
}

// ── Live Demo Panel ─────────────────────────────────────────────────────────

function LiveDemoPanel({ active, onPick, paused, phase }) {
  const agent = DEMO_AGENTS.find(a => a.id === active);

  // Status ticker: scan/think → status; reveal → "Ready"; click/done → "Approved ✓"
  const statusText =
    phase === 0 ? agent.statuses[0] :
    phase === 1 ? agent.statuses[1] :
    phase === 2 ? agent.statuses[2] :
                  'Approved ✓';

  return (
    <div className="hero-dash">
      <div className="hero-dash-glow hero-dash-glow-a" />
      <div className="hero-dash-glow hero-dash-glow-b" />

      <div className="hero-dash-frame">
        <div className="hero-dash-chrome">
          <span className="dot dot-r" />
          <span className="dot dot-y" />
          <span className="dot dot-g" />
          <div className="hero-dash-url">
            <ShieldCheck size={10} /> app.nexusagent.in
          </div>
        </div>

        <div className="hero-dash-body">
          <aside className="hero-dash-side">
            <div className="hero-dash-side-logo">
              <LogoMark size={20} />
            </div>
            {DEMO_AGENTS.map(a => (
              <button
                key={a.id}
                type="button"
                onClick={() => onPick(a.id)}
                className={`hero-dash-side-item ${active === a.id ? 'is-active' : ''}`}
                style={{ '--c': a.c }}
                aria-label={a.name}
                title={`${a.name} — ${a.role}`}
              >
                <a.Icon size={13} />
              </button>
            ))}
          </aside>

          <div className="hero-dash-main" key={active}>
            <div className="hero-dash-head">
              <div>
                <div className="hero-dash-eye" style={{ color: agent.c }}>{agent.role}</div>
                <div className="hero-dash-title">{agent.name} · agent</div>
              </div>
              <span className="hero-dash-pill" style={{ '--c': agent.c }}>
                <span className="pulse" /> {paused ? 'Demo' : 'Live'}
              </span>
            </div>

            {/* Live status ticker — shows what the agent is doing now */}
            <div className={`hero-dash-status hero-dash-status-${
              phase >= 3 ? 'done' : (phase === 2 ? 'ready' : 'work')
            }`} style={{ '--c': agent.c }} key={`s-${active}-${phase}`}>
              <span className="hero-dash-status-dot" />
              <span className="hero-dash-status-t">{statusText}</span>
            </div>

            <AgentDemo id={active} color={agent.c} phase={phase} agent={agent} paused={paused} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Per-agent demo views ────────────────────────────────────────────────────

function AgentDemo({ id, color, phase, agent, paused }) {
  // Hide raw content until phase >= 1, makes the "scanning" stage feel real
  const ready = phase >= 1;
  const reveal = phase >= 2;
  const approved = phase >= 3;

  // Streaming suggestion text — only types during reveal phase
  const streamed = useStream(reveal ? agent.suggestion : '', 18, [id, phase]);

  if (id === 'atlas') return (
    <>
      <div className="hero-dash-stats">
        <div className="hero-dash-stat">
          <div className="hero-dash-stat-n">12</div>
          <div className="hero-dash-stat-l">Open tasks</div>
        </div>
        <div className="hero-dash-stat hero-dash-stat-warn">
          <div className="hero-dash-stat-n">₹2.4L</div>
          <div className="hero-dash-stat-l">Overdue invoices</div>
        </div>
        <div className="hero-dash-stat hero-dash-stat-ok">
          <div className="hero-dash-stat-n">3</div>
          <div className="hero-dash-stat-l">Meetings today</div>
        </div>
      </div>
      <DemoFeed rows={[
        { c: '#0EA5E9', Icon: Mail,       n: 'Iris',  body: <>drafted reply to <em>Rohan@acme.in</em></>, t: '2m' },
        { c: '#10B981', Icon: TrendingUp, n: 'Kira',  body: <>queued 3 invoice reminders</>,             t: '11m' },
        { c: '#06B6D4', Icon: Phone,      n: 'Vox',   body: <>completed call · <em>Sharma Textiles</em></>, t: '23m' },
      ]} />
      <DemoSuggest streamed={streamed} text={agent.suggestion} phase={phase} color={color} />
    </>
  );

  if (id === 'iris') return (
    <>
      <div className="hero-dash-list">
        <div className="hero-dash-list-row">
          <div className="hero-dash-avatar" style={{ background: '#0EA5E9' }}>R</div>
          <div className="hero-dash-list-text">
            <div className="hero-dash-list-t">Rohan Kapoor · acme.in</div>
            <div className="hero-dash-list-s">Re: Q2 contract renewal — sending v3…</div>
          </div>
          <span className="hero-dash-tag" style={{ '--c': '#DC2626' }}>Urgent</span>
        </div>
        <div className="hero-dash-list-row">
          <div className="hero-dash-avatar" style={{ background: '#8B5CF6' }}>P</div>
          <div className="hero-dash-list-text">
            <div className="hero-dash-list-t">Priya Sharma · textile.in</div>
            <div className="hero-dash-list-s">Bulk order inquiry for festive season</div>
          </div>
          <span className="hero-dash-tag" style={{ '--c': '#10B981' }}>Lead</span>
        </div>
        <div className="hero-dash-list-row">
          <div className="hero-dash-avatar" style={{ background: '#F59E0B' }}>A</div>
          <div className="hero-dash-list-text">
            <div className="hero-dash-list-t">Aarav Singh · vendor</div>
            <div className="hero-dash-list-s">Invoice attached — please review</div>
          </div>
          <span className="hero-dash-tag" style={{ '--c': '#6366F1' }}>FYI</span>
        </div>
      </div>
      <DemoSuggest streamed={streamed} text={agent.suggestion} phase={phase} color={color} />
    </>
  );

  if (id === 'kira') return (
    <>
      <div className="hero-dash-list">
        <div className="hero-dash-list-row">
          <div className="hero-dash-avatar" style={{ background: '#DC2626' }}>₹</div>
          <div className="hero-dash-list-text">
            <div className="hero-dash-list-t">INV-2087 · Sharma Textiles</div>
            <div className="hero-dash-list-s">₹85,000 · 18 days overdue</div>
          </div>
          <span className="hero-dash-tag" style={{ '--c': '#DC2626' }}>2nd notice</span>
        </div>
        <div className="hero-dash-list-row">
          <div className="hero-dash-avatar" style={{ background: '#F59E0B' }}>₹</div>
          <div className="hero-dash-list-text">
            <div className="hero-dash-list-t">INV-2091 · Mehta Industries</div>
            <div className="hero-dash-list-s">₹1,20,000 · 9 days overdue</div>
          </div>
          <span className="hero-dash-tag" style={{ '--c': '#F59E0B' }}>1st notice</span>
        </div>
        <div className="hero-dash-list-row">
          <div className="hero-dash-avatar" style={{ background: '#F59E0B' }}>₹</div>
          <div className="hero-dash-list-text">
            <div className="hero-dash-list-t">INV-2094 · Singh Logistics</div>
            <div className="hero-dash-list-s">₹35,000 · 4 days overdue</div>
          </div>
          <span className="hero-dash-tag" style={{ '--c': '#F59E0B' }}>1st notice</span>
        </div>
      </div>
      <DemoSuggest streamed={streamed} text={agent.suggestion} phase={phase} color={color} btn="Send all" />
    </>
  );

  if (id === 'arjun') return (
    <>
      <div className="hero-dash-stats">
        <div className="hero-dash-stat">
          <div className="hero-dash-stat-n">24</div>
          <div className="hero-dash-stat-l">Active deals</div>
        </div>
        <div className="hero-dash-stat hero-dash-stat-warn">
          <div className="hero-dash-stat-n">7</div>
          <div className="hero-dash-stat-l">Stale &gt; 14d</div>
        </div>
        <div className="hero-dash-stat hero-dash-stat-ok">
          <div className="hero-dash-stat-n">₹14L</div>
          <div className="hero-dash-stat-l">Pipeline value</div>
        </div>
      </div>
      <DemoFeed rows={[
        { c: '#F97316', Icon: Target,  n: 'Acme Foods',     body: <>no activity for <em>16 days</em></>,           t: '!' },
        { c: '#F97316', Icon: Target,  n: 'Sharma Textiles', body: <>proposal sent · awaiting reply <em>11d</em></>, t: '!' },
        { c: '#10B981', Icon: TrendingUp, n: 'Bharat Tech',  body: <>moved to <em>Negotiation</em></>,             t: '✓' },
      ]} />
      <DemoSuggest streamed={streamed} text={agent.suggestion} phase={phase} color={color} btn="Open" />
    </>
  );

  if (id === 'sage') return (
    <>
      <div className="hero-dash-meet">
        <div className="hero-dash-meet-time">4:00 PM · today</div>
        <div className="hero-dash-meet-title">Mehta Industries — pricing call</div>
        <div className="hero-dash-meet-people">
          <span className="hero-dash-avatar" style={{ background: '#8B5CF6' }}>R</span>
          <span className="hero-dash-avatar" style={{ background: '#0EA5E9' }}>K</span>
          <span className="hero-dash-avatar" style={{ background: '#F59E0B' }}>+1</span>
          <span className="hero-dash-meet-meta">Rajesh Mehta, Kavita V., +1 other</span>
        </div>
      </div>
      <div className="hero-dash-notes">
        <div className="hero-dash-note-h">Sage's prep notes</div>
        <ul className="hero-dash-note-list">
          <li>Last contact: 14 days ago — pricing pushback on tier 2</li>
          <li>Open invoice INV-2091 (₹1.2L, 9d overdue)</li>
          <li>Mentioned competitor: Zoho — counter with local-first angle</li>
        </ul>
      </div>
      <DemoSuggest streamed={streamed} text={agent.suggestion} phase={phase} color={color} btn="Open brief" />
    </>
  );

  if (id === 'echo') return (
    <>
      <div className="hero-dash-search">
        <Brain size={11} />
        <span className="hero-dash-search-q">"acme renewal terms"</span>
        <span className="hero-dash-search-n">3 results</span>
      </div>
      <div className="hero-dash-list">
        <div className="hero-dash-list-row">
          <div className="hero-dash-avatar" style={{ background: '#EC4899' }}>1</div>
          <div className="hero-dash-list-text">
            <div className="hero-dash-list-t">Acme prefers Net-30 payment</div>
            <div className="hero-dash-list-s">From email · Rohan Kapoor · 12 days ago</div>
          </div>
        </div>
        <div className="hero-dash-list-row">
          <div className="hero-dash-avatar" style={{ background: '#EC4899' }}>2</div>
          <div className="hero-dash-list-text">
            <div className="hero-dash-list-t">Renewal needs CFO Anjali's approval</div>
            <div className="hero-dash-list-s">From call · Vox transcript · 8 days ago</div>
          </div>
        </div>
        <div className="hero-dash-list-row">
          <div className="hero-dash-avatar" style={{ background: '#EC4899' }}>3</div>
          <div className="hero-dash-list-text">
            <div className="hero-dash-list-t">Q2 contract value: ₹4.8L</div>
            <div className="hero-dash-list-s">From CRM · Deal record · 3 days ago</div>
          </div>
        </div>
      </div>
      <DemoSuggest streamed={streamed} text={agent.suggestion} phase={phase} color={color} btn="Save" />
    </>
  );

  if (id === 'vox') return (
    <>
      <div className="hero-dash-call">
        <div className="hero-dash-call-ring">
          <Phone size={16} />
        </div>
        <div className="hero-dash-call-info">
          <div className="hero-dash-call-name">Sharma Textiles · Priya</div>
          <div className="hero-dash-call-meta">Outbound · 4m 12s · ✓ completed</div>
        </div>
        <div className="hero-dash-call-wave">
          {[8,14,22,16,28,12,20,30,18,10,24,14,8].map((h,i) => (
            <span key={i} style={{ height: `${h}px`, animationDelay: `${i * 0.07}s` }} />
          ))}
        </div>
      </div>
      <div className="hero-dash-trans">
        <div className="hero-dash-trans-row">
          <span className="hero-dash-trans-who" style={{ color: '#06B6D4' }}>Vox</span>
          <span className="hero-dash-trans-t">Hi Priya, calling about INV-2087, ₹85,000…</span>
        </div>
        <div className="hero-dash-trans-row">
          <span className="hero-dash-trans-who" style={{ color: '#475569' }}>Priya</span>
          <span className="hero-dash-trans-t">Yes, we'll clear it by Friday. Confirmed.</span>
        </div>
      </div>
      <DemoSuggest streamed={streamed} text={agent.suggestion} phase={phase} color={color} btn="View" />
    </>
  );

  if (id === 'nyx') return (
    <>
      <div className="hero-dash-stats">
        <div className="hero-dash-stat hero-dash-stat-ok">
          <div className="hero-dash-stat-n">9</div>
          <div className="hero-dash-stat-l">Tasks closed</div>
        </div>
        <div className="hero-dash-stat hero-dash-stat-ok">
          <div className="hero-dash-stat-n">5</div>
          <div className="hero-dash-stat-l">Invoices sent</div>
        </div>
        <div className="hero-dash-stat">
          <div className="hero-dash-stat-n">2</div>
          <div className="hero-dash-stat-l">Deals advanced</div>
        </div>
      </div>
      <DemoFeed rows={[
        { c: '#10B981', Icon: TrendingUp, n: 'Today',    body: <>collected <em>₹1,40,000</em> in payments</>,    t: '✓' },
        { c: '#0EA5E9', Icon: Mail,       n: 'Inbox',    body: <>cleared 23 emails · 4 awaiting your review</>, t: '✓' },
        { c: '#6366F1', Icon: Moon,       n: 'Tomorrow', body: <>3 meetings scheduled · 1 prep needed</>,        t: '→' },
      ]} />
      <DemoSuggest streamed={streamed} text={agent.suggestion} phase={phase} color={color} btn="Plan day" />
    </>
  );

  return null;
}

function DemoFeed({ rows }) {
  return (
    <div className="hero-dash-feed">
      {rows.map((r, i) => (
        <div key={i} className="hero-dash-feed-row" style={{ '--c': r.c }}>
          <div className="hero-dash-feed-dot"><r.Icon size={11} /></div>
          <div className="hero-dash-feed-text">
            <strong>{r.n}</strong> {r.body}
          </div>
          <span className="hero-dash-feed-time">{r.t}</span>
        </div>
      ))}
    </div>
  );
}

function DemoSuggest({ text, streamed, btn = 'Approve', phase, color }) {
  // phase >= 3 means the agent has "clicked" approve — morph button to ✓
  const approved = phase >= 3;
  // Cursor floats in during phase 3 (the click moment) before button morphs
  const showCursor = phase === 3;
  const empty = phase < 2; // suggestion not yet revealed

  // Use streamed text when provided, fall back to static text
  const display = streamed != null ? streamed : text;

  return (
    <div
      className={`hero-dash-suggest ${empty ? 'is-empty' : ''} ${approved ? 'is-approved' : ''}`}
      style={{ '--c': color }}
    >
      <div className="hero-dash-suggest-icon">
        {approved ? <Check size={12} /> : <Brain size={12} />}
      </div>
      <div className="hero-dash-suggest-text">
        {empty ? (
          <span className="hero-dash-suggest-skel">
            <span /><span /><span />
          </span>
        ) : (
          <>
            {display}
            {!approved && display && display.length < (text?.length ?? 999) && (
              <span className="hero-dash-suggest-caret" />
            )}
          </>
        )}
      </div>
      <button className={`hero-dash-suggest-btn ${approved ? 'is-approved' : ''}`}>
        {approved ? <><Check size={11} /> Done</> : btn}
      </button>
      {showCursor && <span className="hero-dash-cursor" aria-hidden />}
    </div>
  );
}

// ── Stats Strip ──────────────────────────────────────────────────────────────

function StatsStrip() {
  const stats = [
    { n: '8',     l: 'Specialised agents',  s: 'Each focused on one job' },
    { n: '100%',  l: 'Local-first by default', s: 'Your data, your machine' },
    { n: '₹0',    l: 'Free to start',       s: 'No credit card required' },
    { n: '< 2hr', l: 'Saved per day',       s: 'On manual ops, per user' },
  ];
  return (
    <section className="stats-strip">
      <div className="container stats-grid">
        {stats.map(s => (
          <div key={s.l} className="stat-cell">
            <div className="stat-n">{s.n}</div>
            <div className="stat-l">{s.l}</div>
            <div className="stat-s">{s.s}</div>
          </div>
        ))}
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
    { role: 'Evening Digest',  Icon: Moon,       color: '#6366F1', x: 50,  y: 156 },
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
  const [active, setActive] = useState('atlas');
  const [paused, setPaused] = useState(false);

  // When a cycle finishes for the current agent, hop to the next one
  const advanceAgent = useCallback(() => {
    setActive(prev => {
      const i = DEMO_AGENTS.findIndex(a => a.id === prev);
      return DEMO_AGENTS[(i + 1) % DEMO_AGENTS.length].id;
    });
  }, []);

  const phase = useWorkPhase(active, paused, advanceAgent);
  const pickAgent = id => { setActive(id); setPaused(true); };
  const agent = DEMO_AGENTS.find(a => a.id === active);

  return (
    <section id="agents" className="section section-alt agents-section" style={{ '--c': agent.c }}>
      <div className="agents-bg" aria-hidden />
      <div className="container">
        <div className="section-header section-header-c">
          <span className="eyebrow">The team</span>
          <h2 className="section-h2">8 agents. One live demo.</h2>
          <p className="section-sub">
            Click any agent to see what it does and watch it work — live. Each one
            runs on a schedule and surfaces tasks for your review.
          </p>
        </div>

        {/* Agent chip rail — all 8 visible at once */}
        <div className="agent-chips" role="tablist">
          {DEMO_AGENTS.map(a => (
            <button
              key={a.id}
              type="button"
              role="tab"
              aria-selected={active === a.id}
              onClick={() => pickAgent(a.id)}
              className={`agent-chip ${active === a.id ? 'is-active' : ''}`}
              style={{ '--c': a.c }}
            >
              <span className="agent-chip-icon"><a.Icon size={14} /></span>
              <span className="agent-chip-text">
                <span className="agent-chip-name">{a.name}</span>
                <span className="agent-chip-role">{a.role}</span>
              </span>
            </button>
          ))}
        </div>

        <div className="agents-split">
          {/* Profile pane (left) — re-mounts on agent change to trigger animation */}
          <div className="agent-profile" key={active} style={{ '--c': agent.c }}>
            <div className="agent-profile-icon">
              <agent.Icon size={26} />
            </div>
            <div className="agent-profile-eye">{agent.role}</div>
            <h3 className="agent-profile-name">{agent.name}</h3>
            <p className="agent-profile-tag">{agent.tagline}</p>
            <p className="agent-profile-desc">{agent.desc}</p>

            <dl className="agent-profile-meta">
              <div>
                <dt><Clock size={11} /> Schedule</dt>
                <dd>{agent.schedule}</dd>
              </div>
              <div>
                <dt><ShieldCheck size={11} /> Runs on</dt>
                <dd>{agent.runsOn}</dd>
              </div>
              <div>
                <dt><Target size={11} /> Connects</dt>
                <dd>{agent.connects.join(' · ')}</dd>
              </div>
            </dl>

            <div className="agent-profile-cta-row">
              <a href={`${APP_URL}/setup`} className="btn btn-primary btn-sm">
                Try {agent.name} <ArrowRight size={12} />
              </a>
              <span className="agent-profile-hint">
                {paused ? 'Manual mode — pick another agent' : 'Auto-cycling · click to pause'}
              </span>
            </div>
          </div>

          {/* Live demo (right) */}
          <LiveDemoPanel active={active} onPick={pickAgent} paused={paused} phase={phase} />
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
  const [active,  setActive]  = useState('Pro');
  const [modal,   setModal]   = useState(null); // tier name or null
  const tier = TIERS.find(t => t.name === active);

  const handleCta = t => {
    // Razorpay-eligible tiers: hand off to the in-app pricing page with
    // ?plan=X. The /login redirect chain ensures the visitor is auth'd
    // before the Razorpay modal can open (we need a business_id on the
    // backend to attach the order to).
    if (t.plan) {
      window.location.href = `${APP_URL}/login?next=${encodeURIComponent('/pricing?plan=' + t.plan)}`;
      return;
    }
    if (t.href && t.href.startsWith('mailto:')) {
      window.location.href = t.href;
      return;
    }
    if (t.name === 'Free' || (t.href && t.href.includes('/setup'))) {
      window.location.href = t.href || `${APP_URL}/setup`;
      return;
    }
    // Fallback: legacy "early access" waitlist modal.
    setModal(t.name);
  };

  return (
    <section id="pricing" className="section">
      {modal && <EarlyAccessModal tier={modal} onClose={() => setModal(null)} />}
      <div className="container">
        <div className="section-header section-header-c">
          <span className="eyebrow">Pricing</span>
          <h2 className="section-h2">Free to start. Simple to scale.</h2>
          <p className="section-sub">
            Prices in ₹. USD available at checkout. GST as applicable.
          </p>
        </div>

        {/* Compact tier selector row */}
        <div className="pricing-selector">
          {TIERS.map(t => (
            <button
              key={t.name}
              className={`price-tab ${active === t.name ? 'price-tab-active' : ''}`}
              onClick={() => setActive(t.name)}
            >
              <span className="price-tab-name">{t.name}</span>
              <span className="price-tab-amount">{t.price}</span>
              <span className="price-tab-period">{t.period}</span>
            </button>
          ))}
        </div>

        {/* Detail panel for selected tier */}
        {tier && (
          <div className="price-detail">
            <div className="price-detail-left">
              <div className="price-detail-name">{tier.name}</div>
              <div className="price-detail-row">
                <span className="price-amount">{tier.price}</span>
                <span className="price-period">{tier.period}</span>
              </div>
              <p className="price-desc">{tier.desc}</p>
              <button className="btn btn-primary btn-lg price-detail-cta" onClick={() => handleCta(tier)}>
                {tier.cta} <ArrowRight size={14} />
              </button>
            </div>
            <div className="price-detail-divider" />
            <ul className="price-detail-list">
              {tier.items.map(item => (
                <li key={item}>
                  <CheckCircle2 size={15} className="icon-ok" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        <p className="price-fine">Prices in ₹ · GST as applicable · USD available at checkout</p>
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
          <a href={`mailto:${MAIL}?subject=Privacy Policy`}>Privacy Policy</a>
          <a href={`mailto:${MAIL}?subject=Terms of Service`}>Terms of Service</a>
          <a href={`mailto:${MAIL}?subject=Security`}>Security</a>
          <a href={`mailto:${MAIL}?subject=Data Handling`}>Data Handling</a>
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
