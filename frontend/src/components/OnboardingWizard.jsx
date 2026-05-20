/**
 * First-run business setup wizard.
 *
 * The backend still owns progress via /api/onboarding, but the first steps are
 * now product onboarding rather than a passive checklist: collect business
 * profile, tune by industry, and ask for starter company documents.
 */
import { useState, useEffect } from 'react';
import {
  Sparkles, Briefcase, Users, Database, FileType2, Bot, PartyPopper,
  X, ArrowRight, ArrowLeft, CheckCircle2, Upload, Building2, ShieldCheck,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  getOnboardingState, completeOnboardingStep, skipOnboarding, applyIndustrySetup,
  getIndustryPreset, saveProfileExtras,
} from '../services/onboarding';
import { updateBusiness } from '../services/businesses';
import { uploadDocument } from '../services/api';
import { getCurrentBusiness } from '../services/auth';
import { comingSoonForIndustry, roadmapTitleSetForIndustry } from '../services/comingSoon';

// Tool names listed in the wizard's "industry workspace" preview that are
// genuinely roadmap (not in v1). Phase G items show with a 'Soon' badge so
// new signups don't expect to find them immediately.
const ROADMAP_TOOL_HINTS = [
  'live fleet tracking', 'driver app', 'lr tracking', 'fleet visibility',
  'route optimisation', 'route optimization', 'geofence',
  'driver coordination',  // we list this in PRESETS but full coordination is post-v1
];

const INDUSTRIES = [
  // Global categories
  'Healthcare',
  'Real estate',
  'Education',
  'Legal',
  'Ecommerce',
  'Finance',
  'SaaS',
  'Manufacturing',
  'Hospitality',
  'Local services',
  'Consulting',
  // Indian SMB additions — common business types we encountered
  // most often in early customer conversations
  'Tutoring / coaching',
  'Restaurant / cafe',
  'Beauty / salon / wellness',
  'Garment / textile retail',
  'Logistics / transport',
  'Construction / contracting',
  'Auto repair / garage',
  'Photography / event services',
  'Travel / tour operator',
  'Real estate broker',
  'Other',
];

const BUSINESS_TYPES = [
  'Startup',
  'Small business',
  'Agency',
  'Enterprise team',
  'Independent professional',
  'Non-profit',
];

const COMPANY_SIZES = ['1-5', '6-20', '21-50', '51-200', '201-500', '500+'];

const GOALS = [
  'Sales and CRM',
  'Customer support',
  'Operations automation',
  'Document intelligence',
  'Finance and invoices',
  'Team productivity',
];

const FALLBACK_INDUSTRY_TOOLS = {
  Healthcare:                    ['Patient intake', 'Policy knowledge base', 'Appointment follow-ups', 'Privacy review'],
  'Real estate':                 ['Lead capture', 'Property documents', 'Buyer follow-ups', 'Deal pipeline'],
  Education:                     ['Admissions support', 'Course FAQ', 'Student follow-ups', 'Reports'],
  Legal:                         ['Client intake', 'Document Q&A', 'Case task tracking', 'Secure audit trail'],
  Ecommerce:                     ['Product catalog', 'Returns support', 'Order follow-ups', 'Customer inbox'],
  Finance:                       ['Client onboarding', 'Invoice reminders', 'Compliance docs', 'Secure reporting'],
  SaaS:                          ['Pipeline CRM', 'Support triage', 'Churn signals', 'Product knowledge base'],
  Manufacturing:                 ['Vendor docs', 'Order follow-ups', 'Operations tasks', 'Reports'],
  Hospitality:                   ['Booking support', 'Guest FAQs', 'Review follow-ups', 'Shift tasks'],
  'Local services':              ['Lead intake', 'Job scheduling', 'Quote follow-ups', 'Invoice reminders'],
  Consulting:                    ['Client briefs', 'Proposal docs', 'Meeting prep', 'Project tasks'],
  // Indian SMB additions
  'Tutoring / coaching':         ['Inquiry intake', 'Trial-class scheduler', 'Fee reminders', 'Parent WhatsApp'],
  'Restaurant / cafe':           ['Reservation desk', 'Catering inquiries', 'Reviews + reputation', 'Daily-special broadcast'],
  'Beauty / salon / wellness':   ['Appointment desk', 'Loyalty + rebooking', 'WhatsApp reminders', 'Stylist preferences'],
  'Garment / textile retail':    ['Inventory tracking', 'Wholesale buyer CRM', 'WhatsApp catalog broadcast', 'GST invoicing'],
  'Logistics / transport':       ['Booking + dispatch', 'LR tracking', 'Driver coordination', 'Invoice reminders'],
  'Construction / contracting':  ['Site inquiries', 'Quote builder', 'Project milestones', 'Subcontractor tracking'],
  'Auto repair / garage':        ['Service desk', 'Parts orders', 'Pickup + drop coordination', 'Service reminders'],
  'Photography / event services':['Inquiry intake', 'Package builder', 'Booking calendar', 'Delivery + gallery'],
  'Travel / tour operator':      ['Itinerary builder', 'Booking + payment tracking', 'Traveler WhatsApp', 'Reviews + repeat travel'],
  'Real estate broker':          ['Rental + resale inquiries', 'Owner + tenant CRM', 'Site visit scheduler', 'Commission tracking'],
  Other:                         ['Business knowledge base', 'CRM pipeline', 'Task automation', 'Reports'],
};

const STEP_ICONS = {
  profile: Briefcase,
  agents: Bot,
  data_source: Database,
  document: FileType2,
  first_run: Users,
  celebrated: PartyPopper,
};

export default function OnboardingWizard({ onClose }) {
  const [state, setState] = useState(null);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [uploadedName, setUploadedName] = useState('');
  const [industryPreset, setIndustryPreset] = useState(null);
  // Per-field validation messages for the profile step. Keyed by the
  // field name in `profile` (name / businessType / industry / companySize /
  // primaryGoal). Cleared field-by-field as the user fixes each.
  const [fieldErrors, setFieldErrors] = useState({});
  const current = getCurrentBusiness();
  const [profile, setProfile] = useState(() => ({
    name: current?.name || '',
    industry: current?.industry || '',
    businessType: '',
    companySize: '',
    primaryGoal: '',
  }));
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;
    getOnboardingState()
      .then((s) => {
        if (cancelled) return;
        setState(s);
        const firstUndone = (s.steps || []).findIndex(x => !x.done);
        setStep(firstUndone === -1 ? Math.max(0, s.steps.length - 1) : firstUndone);
      })
      .catch((e) => setErr(e.message || 'Could not load onboarding'));
    return () => { cancelled = true; };
  }, []);

  const steps = state?.steps || [];
  const currentStep = steps[step];
  const total = steps.length || 1;
  const currentKey = currentStep?.key;
  const requiredProfileIncomplete = !!steps.find(s => s.key === 'profile' && !s.done);
  const canClose = !requiredProfileIncomplete;
  const selectedIndustry = profile.industry || current?.industry || 'Other';
  const presetTools = industryPreset?.tools || FALLBACK_INDUSTRY_TOOLS[selectedIndustry] || FALLBACK_INDUSTRY_TOOLS.Other;

  useEffect(() => {
    if (currentKey !== 'agents') return;
    let cancelled = false;
    getIndustryPreset()
      .then((preset) => {
        if (!cancelled) setIndustryPreset(preset);
      })
      .catch(() => {
        if (!cancelled) setIndustryPreset(null);
      });
    return () => { cancelled = true; };
  }, [currentKey, selectedIndustry]);

  const refreshState = async () => {
    const fresh = await getOnboardingState();
    setState(fresh);
    return fresh;
  };

  const completeStep = async (stepKey) => {
    setBusy(true);
    setErr('');
    try {
      const fresh = await completeOnboardingStep(stepKey);
      setState(fresh);
      return fresh;
    } catch (e) {
      setErr(e.message || 'Could not save progress');
      return null;
    } finally {
      setBusy(false);
    }
  };

  const goNext = () => {
    if (step < total - 1) setStep(step + 1);
    else onClose();
  };

  const goPrev = () => {
    if (step > 0) setStep(step - 1);
  };

  const saveProfile = async () => {
    if (!current) {
      setErr('No active business found. Sign in again and retry.');
      return;
    }
    // Inline validation — show per-field error, not a single banner.
    const validation = {};
    if (!profile.name.trim())     validation.name         = 'Enter the business name your customers know.';
    if (!profile.businessType)    validation.businessType = 'Pick the closest match.';
    if (!profile.industry.trim()) validation.industry     = 'Industry tunes terminology + sample data.';
    if (!profile.companySize)     validation.companySize  = 'Choose a size band.';
    if (!profile.primaryGoal)     validation.primaryGoal  = "Tell us what to focus on first.";
    if (Object.keys(validation).length) {
      setFieldErrors(validation);
      setErr('A few fields still need answers.');
      return;
    }
    setFieldErrors({});
    setBusy(true);
    setErr('');
    try {
      // Keep the legacy human-readable description for back-compat with
      // anywhere in the product that already parses it. The structured
      // version lives in settings.profile via saveProfileExtras below.
      const description = [
        `Business type: ${profile.businessType}`,
        `Company size: ${profile.companySize}`,
        `Primary goal: ${profile.primaryGoal}`,
      ].join('\n');
      await updateBusiness(current.id, {
        name: profile.name.trim(),
        industry: profile.industry.trim(),
        description,
      });
      // Write the structured fields. Failure here MUST NOT block the
      // wizard — they're enrichment, not load-bearing for first-run.
      try {
        await saveProfileExtras({
          business_type: profile.businessType,
          company_size:  profile.companySize,
          primary_goal:  profile.primaryGoal,
        });
      } catch (e) {
        // eslint-disable-next-line no-console
        console.warn('[Onboarding] profile-extras save failed (non-fatal):', e?.message);
      }
      window.dispatchEvent(new CustomEvent('nexus-business-changed', { detail: current.id }));
      await completeOnboardingStep('profile');
      setIndustryPreset(null);
      const fresh = await refreshState();
      const next = fresh.steps.findIndex(s => !s.done);
      setStep(next === -1 ? step + 1 : next);
    } catch (e) {
      setErr(e.message || 'Could not save business profile');
    } finally {
      setBusy(false);
    }
  };

  const acceptRecommendations = async () => {
    setBusy(true);
    setErr('');
    try {
      const result = await applyIndustrySetup();
      if (result?.onboarding) setState(result.onboarding);
      goNext();
    } catch (e) {
      setErr(e.message || 'Could not apply industry setup');
    } finally {
      setBusy(false);
    }
  };

  const uploadStarterDoc = async (file) => {
    if (!file) return;
    setBusy(true);
    setErr('');
    setUploadedName(file.name);
    try {
      await uploadDocument(file);
      await completeOnboardingStep('document');
      const fresh = await refreshState();
      const next = fresh.steps.findIndex(s => !s.done);
      setStep(next === -1 ? step + 1 : next);
    } catch (e) {
      setErr(e.message || 'Could not upload document');
    } finally {
      setBusy(false);
    }
  };

  const doAction = (route) => {
    onClose();
    navigate(route);
  };

  const fullySkip = async () => {
    if (!canClose) {
      setErr('Business profile and industry are required before entering the workspace.');
      return;
    }
    try { await skipOnboarding(); } catch {}
    onClose();
  };

  if (err && !state) {
    return (
      <Overlay onClose={canClose ? onClose : undefined}>
        <div style={{ color: 'var(--color-err)', fontSize: 12 }}>{err}</div>
      </Overlay>
    );
  }
  // Render nothing while the initial onboarding state is fetched.
  // The previous "Loading..." overlay flashed for a few hundred ms between
  // PlanWelcomeModal and the actual wizard, making the post-signup sequence
  // look like three stacked modals instead of one continuous flow.
  if (!state || !currentStep) return null;

  const Icon = STEP_ICONS[currentKey] || Sparkles;

  return (
    <Overlay onClose={canClose ? fullySkip : undefined}>
      <div style={{ display: 'flex', gap: 4, marginBottom: 18 }}>
        {steps.map((s, i) => (
          <div
            key={s.key}
            onClick={() => setStep(i)}
            title={s.title}
            style={{
              flex: 1, height: 3, borderRadius: 2, cursor: 'pointer',
              background: s.done
                ? 'var(--color-ok)'
                : (i === step ? 'var(--color-accent)' : 'var(--color-surface-2)'),
            }}
          />
        ))}
      </div>

      {canClose && (
        <button
          onClick={fullySkip}
          style={{
            position: 'absolute', top: 16, right: 16,
            background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer',
          }}
          title="Skip remaining onboarding"
        >
          <X size={16} />
        </button>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 'var(--r-md)',
          background: currentStep.done
            ? 'color-mix(in srgb, var(--color-ok) 15%, transparent)'
            : 'color-mix(in srgb, var(--color-accent) 15%, transparent)',
          color: currentStep.done ? 'var(--color-ok)' : 'var(--color-accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {currentStep.done ? <CheckCircle2 size={20} /> : <Icon size={20} />}
        </div>
        <div>
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)', letterSpacing: 0.5, textTransform: 'uppercase' }}>
            Step {step + 1} of {total}
          </div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: 'var(--color-text)' }}>
            {currentStep.title}
          </h2>
        </div>
      </div>

      <p style={{ fontSize: 13, color: 'var(--color-text-muted)', margin: '10px 0 18px', lineHeight: 1.55 }}>
        {currentStep.description}
      </p>

      {err && (
        <div style={{
          padding: '8px 10px', marginBottom: 12, borderRadius: 'var(--r-sm)',
          color: 'var(--color-err)', fontSize: 12,
          background: 'color-mix(in srgb, var(--color-err) 8%, transparent)',
          border: '1px solid color-mix(in srgb, var(--color-err) 24%, transparent)',
        }}>
          {err}
        </div>
      )}

      {currentKey === 'profile' && (
        <ProfileStep profile={profile} setProfile={setProfile} errors={fieldErrors} />
      )}

      {currentKey === 'agents' && (
        <IndustryStep
          industry={industryPreset?.industry || selectedIndustry}
          preset={presetTools}
          primaryGoal={profile.primaryGoal}
          companySize={profile.companySize}
        />
      )}

      {currentKey === 'document' && (
        <DocumentStep busy={busy} uploadedName={uploadedName} onUpload={uploadStarterDoc} />
      )}

      {currentKey !== 'profile' && currentKey !== 'agents' && currentKey !== 'document' && currentKey !== 'celebrated' && (
        <div style={{
          padding: 14, borderRadius: 'var(--r-md)',
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
          fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.6,
        }}>
          Open <strong style={{ color: 'var(--color-text)' }}>{currentStep.cta}</strong> to finish this step inside the app.
        </div>
      )}

      {currentKey === 'celebrated' && (
        <div style={{
          padding: 18, borderRadius: 'var(--r-md)',
          background: 'color-mix(in srgb, var(--color-ok) 8%, transparent)',
          border: '1px solid color-mix(in srgb, var(--color-ok) 25%, transparent)',
          textAlign: 'center',
        }}>
          <Sparkles size={28} color="var(--color-ok)" />
          <h3 style={{ margin: '8px 0 4px', fontSize: 15, color: 'var(--color-text)' }}>
            Your NexusAgent workspace is ready
          </h3>
          <p style={{ fontSize: 12, color: 'var(--color-text-muted)', margin: 0 }}>
            Your first screen is shaped around {selectedIndustry.toLowerCase()} work.
          </p>
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 18, flexWrap: 'wrap' }}>
        <button onClick={goPrev} disabled={step === 0} className="btn-ghost" style={{ opacity: step === 0 ? 0.4 : 1 }}>
          <ArrowLeft size={12} /> Back
        </button>
        <div style={{ flex: 1 }} />

        {currentKey === 'profile' && (
          <button onClick={saveProfile} className="btn-primary" disabled={busy}>
            {busy ? 'Saving...' : 'Save business setup'} <ArrowRight size={12} />
          </button>
        )}

        {currentKey === 'agents' && (
          <button onClick={acceptRecommendations} className="btn-primary" disabled={busy}>
            {busy ? 'Saving...' : 'Use these recommendations'} <ArrowRight size={12} />
          </button>
        )}

        {currentKey === 'document' && (
          <>
            <button onClick={() => doAction('/documents')} className="btn-ghost" disabled={busy}>
              Open Documents
            </button>
            <button onClick={() => { completeStep('document').then(() => goNext()); }} className="btn-ghost" disabled={busy}>
              Do this later
            </button>
          </>
        )}

        {currentKey !== 'profile' && currentKey !== 'agents' && currentKey !== 'document' && currentKey !== 'celebrated' && (
          <>
            <button onClick={() => doAction(currentStep.route)} className="btn-ghost" disabled={busy}>
              {currentStep.cta}
            </button>
            <button onClick={() => { completeStep(currentKey).then(() => goNext()); }} className="btn-primary" disabled={busy}>
              {busy ? 'Saving...' : 'Mark done'} <ArrowRight size={12} />
            </button>
          </>
        )}

        {currentKey === 'celebrated' && (
          <button onClick={() => { completeStep('celebrated').then(() => onClose()); }} className="btn-primary" disabled={busy}>
            {busy ? 'Saving...' : 'Jump to dashboard'} <ArrowRight size={12} />
          </button>
        )}
      </div>
    </Overlay>
  );
}

// ── Industry auto-detection from the business name ───────────────────────
// Lightweight heuristic. Doesn't replace the user's choice — only suggests
// when the dropdown is still on "Choose industry". Keywords were picked
// from common business-name patterns in the seed data.
const INDUSTRY_HINTS = [
  { match: /hospital|clinic|dental|diagnostic|pharma|medic|wellness/i,   industry: 'Healthcare' },
  { match: /school|coaching|tutor|academy|institute|class(es)?|kg|prep/i, industry: 'Tutoring / coaching' },
  { match: /restaurant|cafe|kitchen|bistro|biryani|dhab(a|ha)|bake/i,    industry: 'Restaurant / cafe' },
  { match: /salon|spa|beauty|parlou?r|hair|nail|mehndi/i,                industry: 'Beauty / salon / wellness' },
  { match: /saree|kurt|textile|fashion|garment|fabric|boutique/i,        industry: 'Garment / textile retail' },
  { match: /cargo|roadlines|transport|movers|logistic|freight|shipping/i,industry: 'Logistics / transport' },
  { match: /construct|builders|civil|contractor|interior|reno|architect/i,industry: 'Construction / contracting' },
  { match: /garage|auto|motors|car care|service centre|repair/i,         industry: 'Auto repair / garage' },
  { match: /photo|studio|films|frames|capture|moments/i,                  industry: 'Photography / event services' },
  { match: /tour|travel|holiday|trip|adventures|wanderlust/i,             industry: 'Travel / tour operator' },
  { match: /realty|estate|properties|broker|housing/i,                    industry: 'Real estate broker' },
  { match: /tech|labs|ai|software|cloud|analytics|saas|app/i,             industry: 'SaaS' },
  { match: /\b(college|university|edu)\b/i,                               industry: 'Education' },
  { match: /law|legal|advoc|attorney|chambers/i,                          industry: 'Legal' },
  { match: /tax|chartered|accountant|wealth|advisor|insurance/i,          industry: 'Finance' },
  { match: /hotel|stays|resort|villa|inn|lodge|rooms/i,                   industry: 'Hospitality' },
  { match: /mart|store|shop|wholesale|trading|retail/i,                   industry: 'Ecommerce' },
  { match: /electric|plumb|paint|carpent|pest|clean(ing)?/i,              industry: 'Local services' },
  { match: /factory|industries|works|engineering|metal|steel|food proc/i, industry: 'Manufacturing' },
];

function detectIndustryFromName(name) {
  if (!name) return null;
  for (const rule of INDUSTRY_HINTS) {
    if (rule.match.test(name)) return rule.industry;
  }
  return null;
}


function ProfileStep({ profile, setProfile, errors }) {
  const update = (key, value) => setProfile((p) => ({ ...p, [key]: value }));
  // Industry hint based on what the user typed. Only shown when the
  // industry dropdown hasn't been chosen yet — never overrides the user.
  const detected = detectIndustryFromName(profile.name);
  const showHint = !!detected && !profile.industry;

  const applyHint = () => update('industry', detected);

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      {/* Responsive grid — 2 cols on tablet+, 1 col on phones */}
      <div className="onb-grid-2col">
        <Field label="Business name" hint="The trading name your customers know you by." error={errors?.name}>
          <input
            className="field-input"
            value={profile.name}
            onChange={(e) => update('name', e.target.value)}
            placeholder="e.g. Apollo Family Clinic"
            maxLength={120}
            autoFocus
          />
          {showHint && (
            <div style={{
              marginTop: 6, padding: '6px 10px', fontSize: 11.5,
              background: 'color-mix(in srgb, var(--color-accent) 8%, transparent)',
              border: '1px solid color-mix(in srgb, var(--color-accent) 22%, var(--color-border))',
              borderRadius: 6, color: 'var(--color-text)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8,
            }}>
              <span>Looks like a <strong>{detected}</strong> business?</span>
              <button
                type="button"
                onClick={applyHint}
                style={{
                  fontSize: 11, padding: '3px 8px', borderRadius: 4,
                  border: '1px solid var(--color-accent)',
                  background: 'transparent', color: 'var(--color-accent)',
                  cursor: 'pointer', fontWeight: 600,
                }}
              >Use this</button>
            </div>
          )}
        </Field>
        <Field label="Business type" hint="Single founder, agency, enterprise team — used to tune feature defaults." error={errors?.businessType}>
          <select className="field-select" value={profile.businessType} onChange={(e) => update('businessType', e.target.value)}>
            <option value="">Choose type</option>
            {BUSINESS_TYPES.map(x => <option key={x} value={x}>{x}</option>)}
          </select>
        </Field>
        <Field label="Industry" hint="Drives terminology + sample data. You can change this later." error={errors?.industry}>
          <select className="field-select" value={profile.industry} onChange={(e) => update('industry', e.target.value)}>
            <option value="">Choose industry</option>
            {INDUSTRIES.map(x => <option key={x} value={x}>{x}</option>)}
          </select>
        </Field>
        <Field label="Company size" hint="We hide team-invite prompts for solo founders + emphasise SSO/roles for 50+." error={errors?.companySize}>
          <select className="field-select" value={profile.companySize} onChange={(e) => update('companySize', e.target.value)}>
            <option value="">Choose size</option>
            {COMPANY_SIZES.map(x => <option key={x} value={x}>{x}</option>)}
          </select>
        </Field>
      </div>
      <Field label="Main goal" hint="What you want NexusAgent to focus on first — we'll pin those agents to the top of your sidebar." error={errors?.primaryGoal}>
        <select className="field-select" value={profile.primaryGoal} onChange={(e) => update('primaryGoal', e.target.value)}>
          <option value="">What should NexusAgent help with first?</option>
          {GOALS.map(x => <option key={x} value={x}>{x}</option>)}
        </select>
      </Field>
      <div style={{
        display: 'flex', gap: 10, padding: 12, borderRadius: 'var(--r-md)',
        background: 'var(--color-surface-1)', border: '1px solid var(--color-border)',
        color: 'var(--color-text-muted)', fontSize: 12, lineHeight: 1.55,
      }}>
        <ShieldCheck size={18} color="var(--color-ok)" style={{ flexShrink: 0 }} />
        <span>This setup scopes the workspace to the business and keeps documents inside the active tenant.</span>
      </div>
    </div>
  );
}

// Goal → agent emphasis. Used to call out which agents the user's chosen
// goal will surface in the first-run experience. Keeps the wizard
// honest — the inputs collected on the profile step actually shape the
// step that follows.
const GOAL_AGENT_HIGHLIGHTS = {
  'Sales and CRM':              { focus: 'Atlas + Vox + Stale-deal watcher', why: 'so leads never go cold and outbound calls go out daily' },
  'Customer support':           { focus: 'Inbox + WhatsApp',                  why: 'so every customer message gets a draft reply within minutes' },
  'Operations automation':      { focus: 'Workflows + Morning briefing',      why: 'so recurring ops run on autopilot and you wake up to a plan' },
  'Document intelligence':      { focus: 'Documents + Forge',                 why: 'so company docs become a queryable knowledge base' },
  'Finance and invoices':       { focus: 'Kira + Invoice reminders',          why: 'so overdue invoices get chased without you remembering' },
  'Team productivity':          { focus: 'Tasks + Meeting prep',              why: 'so the team starts each day with prepped briefs + a clean to-do' },
};

function IndustryStep({ industry, preset, primaryGoal, companySize }) {
  const goalHighlight = GOAL_AGENT_HIGHLIGHTS[primaryGoal];
  // Roadmap teaser — only renders for industries with at least one
  // planned feature (Logistics, Travel, Real-estate broker, Local
  // services, Auto repair). Sets honest expectations + collects demand
  // signal without us shipping vapourware.
  const upcoming = comingSoonForIndustry(industry);
  // For very small teams (1-5) we don't want to overpromise enterprise
  // features. For larger teams (51+) we explicitly call out SSO + roles.
  const sizeBand = companySize === '1-5'
    ? "Single-founder workspace — team-invite prompts hidden until you grow."
    : companySize && ['51-200','201-500','500+'].includes(companySize)
      ? "Team workspace — SSO, roles, and audit log surfaced for compliance."
      : null;

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 10, padding: 12,
        background: 'var(--color-surface-1)', border: '1px solid var(--color-border)',
        borderRadius: 'var(--r-md)',
      }}>
        <Building2 size={18} color="var(--color-accent)" />
        <div>
          <div style={{ fontSize: 13, color: 'var(--color-text)', fontWeight: 600 }}>{industry} workspace</div>
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>These tools stay available, but the first experience is focused.</div>
        </div>
      </div>
      <div className="onb-grid-2col" style={{ gap: 8 }}>
        {preset.map((item) => {
          const lower = item.toLowerCase();
          const isRoadmap = ROADMAP_TOOL_HINTS.some(k => lower.includes(k));
          return (
            <div key={item} style={{
              padding: 10, borderRadius: 'var(--r-sm)',
              background: isRoadmap
                ? 'color-mix(in srgb, var(--color-warn) 5%, var(--color-surface-1))'
                : 'color-mix(in srgb, var(--color-accent) 7%, var(--color-surface-1))',
              border: isRoadmap
                ? '1px dashed color-mix(in srgb, var(--color-warn) 30%, var(--color-border))'
                : '1px solid color-mix(in srgb, var(--color-accent) 20%, var(--color-border))',
              fontSize: 12, color: 'var(--color-text)',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              {isRoadmap
                ? <span style={{ fontSize: 14 }}>🚧</span>
                : <CheckCircle2 size={14} color="var(--color-ok)" />}
              <span style={{ flex: 1 }}>{item}</span>
              {isRoadmap && (
                <span style={{
                  fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 4,
                  background: 'color-mix(in srgb, var(--color-warn) 20%, transparent)',
                  color: 'var(--color-warn)', textTransform: 'uppercase', letterSpacing: 0.5,
                }}>Soon</span>
              )}
            </div>
          );
        })}
      </div>

      {goalHighlight && (
        <div style={{
          padding: 12, borderRadius: 'var(--r-sm)',
          background: 'color-mix(in srgb, var(--color-info) 7%, var(--color-surface-1))',
          border: '1px solid color-mix(in srgb, var(--color-info) 25%, var(--color-border))',
          fontSize: 12, color: 'var(--color-text)', lineHeight: 1.5,
        }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-info)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>
            Because your goal is {primaryGoal}
          </div>
          We'll pin <strong>{goalHighlight.focus}</strong> {goalHighlight.why}.
        </div>
      )}

      {sizeBand && (
        <div style={{
          padding: 10, borderRadius: 'var(--r-sm)',
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
          fontSize: 11.5, color: 'var(--color-text-muted)', lineHeight: 1.5,
        }}>
          {sizeBand}
        </div>
      )}

      {upcoming.length > 0 && (
        <div style={{
          padding: 12, borderRadius: 'var(--r-sm)',
          background: 'color-mix(in srgb, var(--color-warn) 5%, var(--color-surface-1))',
          border: '1px dashed color-mix(in srgb, var(--color-warn) 30%, var(--color-border))',
          fontSize: 12, color: 'var(--color-text)', lineHeight: 1.55,
        }}>
          <div style={{
            fontSize: 11, fontWeight: 700, letterSpacing: 0.5, textTransform: 'uppercase',
            color: 'var(--color-warn)', marginBottom: 8,
          }}>
            🚧 Coming next for {industry}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {upcoming.map((f) => (
              <div key={f.id} style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                <span style={{
                  flexShrink: 0,
                  fontSize: 10, fontWeight: 600,
                  padding: '2px 6px', borderRadius: 4,
                  background: 'color-mix(in srgb, var(--color-warn) 18%, transparent)',
                  color: 'var(--color-warn)', whiteSpace: 'nowrap', marginTop: 1,
                }}>{f.eta}</span>
                <span>
                  <strong>{f.title}</strong> — {f.blurb}
                </span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 8, fontSize: 11, color: 'var(--color-text-dim)' }}>
            Reply to any onboarding email to register early interest — we ship to interested workspaces first.
          </div>
        </div>
      )}

      <div style={{
        padding: 10,
        borderRadius: 'var(--r-sm)',
        background: 'var(--color-surface-1)',
        border: '1px solid var(--color-border)',
        fontSize: 11.5,
        color: 'var(--color-text-muted)',
        lineHeight: 1.55,
      }}>
        This will tune priority agents, schedules, and starter email templates. All other NexusAgent features remain available from the sidebar.
      </div>
    </div>
  );
}

function DocumentStep({ busy, uploadedName, onUpload }) {
  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <label style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        gap: 8, minHeight: 150, border: '2px dashed var(--color-border)',
        borderRadius: 'var(--r-md)', background: 'var(--color-surface-1)',
        cursor: busy ? 'wait' : 'pointer', textAlign: 'center', padding: 20,
      }}>
        <input
          type="file"
          disabled={busy}
          accept=".pdf,.txt,.md,.docx,text/plain,application/pdf"
          style={{ display: 'none' }}
          onChange={(e) => onUpload(e.target.files?.[0])}
        />
        <Upload size={24} color="var(--color-text-dim)" />
        <div style={{ fontSize: 13, color: 'var(--color-text)', fontWeight: 600 }}>
          {busy ? `Uploading ${uploadedName || 'document'}...` : 'Upload company documents'}
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-dim)', maxWidth: 360, lineHeight: 1.5 }}>
          Policies, product catalogs, service guides, pricing sheets, FAQs, or onboarding docs.
        </div>
      </label>
      <div style={{ fontSize: 11, color: 'var(--color-text-dim)', lineHeight: 1.55 }}>
        This is optional for entry, but strongly recommended because it gives the AI safe company context before the user starts asking questions.
      </div>
    </div>
  );
}

function Field({ label, children, hint, error }) {
  // Label + tooltip helper. `hint` is the explanatory text shown muted
  // below the label; appears whenever the user is looking at this field.
  // `error` is the inline validation message — shown ONLY when set, in
  // red, replacing the hint. Keeps the form chrome stable as the user
  // types (the row height doesn't jump between hint and error).
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 600 }}>{label}</span>
      {children}
      {error ? (
        <span style={{ fontSize: 11, color: 'var(--color-err)', marginTop: 2 }}>
          {error}
        </span>
      ) : hint ? (
        <span style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 2, lineHeight: 1.4 }}>
          {hint}
        </span>
      ) : null}
    </label>
  );
}

function Overlay({ children, onClose }) {
  // Heavier backdrop + blur than a normal modal: the wizard is the user's
  // first-ever screen after signup and we want the dashboard underneath to
  // disappear, not bleed through. Without the blur, a half-loaded dashboard
  // (skeleton KPIs, sidebar, greeting) was visible behind the wizard.
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0,
        background: 'rgba(8, 10, 18, 0.92)',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
        zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: 20,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)',
          borderRadius: 'var(--r-lg)', padding: 28,
          width: 'min(620px, 94vw)', position: 'relative',
          boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
        }}
      >
        {children}
      </div>
    </div>
  );
}

const ONBOARDING_KEY = 'nexus_onboarding_done';

export function shouldShowOnboarding() {
  return localStorage.getItem(ONBOARDING_KEY) !== '1';
}

export function markOnboardingSeen() {
  localStorage.setItem(ONBOARDING_KEY, '1');
}
