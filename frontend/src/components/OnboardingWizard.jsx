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
import { listPersonas, runAgent } from '../services/agents';
import { createContact } from '../services/crm';
import { getCurrentBusiness } from '../services/auth';
import { comingSoonForIndustry, roadmapTitleSetForIndustry } from '../services/comingSoon';
import BrandMark from './BrandMark';

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
  'Other',
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
  // Step 3 (data source): inline CSV upload state.
  const [csvName, setCsvName] = useState('');
  const [csvRows, setCsvRows] = useState(0);
  // Step 5 (first run): inline agent picker state.
  const [personas, setPersonas] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [runningKey, setRunningKey] = useState('');
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
    customGoal: '',   // populated only when primaryGoal === 'Other'
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
    if (profile.primaryGoal === 'Other' && !profile.customGoal?.trim()) {
      validation.primaryGoal = "Write a one-line goal so we know what to set up.";
    }
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
      const goalForSave = profile.primaryGoal === 'Other'
        ? `Other — ${profile.customGoal.trim()}`
        : profile.primaryGoal;
      const description = [
        `Business type: ${profile.businessType}`,
        `Company size: ${profile.companySize}`,
        `Primary goal: ${goalForSave}`,
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
          primary_goal:  goalForSave,
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
      // Same UX as Step 3: refresh state but stay on this step so the
      // user actually sees the "Uploaded foo.pdf" confirmation in the
      // drop zone. They click Continue when ready.
      await refreshState();
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

  // Step 3 inline upload — parse the CSV in-browser and create contacts via
  // the proper contacts API. We CAN'T use /api/database/import because that
  // endpoint blocks writes to nexus_* "system" tables; instead we map known
  // columns to contact fields and stash every extra column inside
  // custom_fields JSON so power users with rich CSVs don't lose data.
  const uploadContactsCsv = async (file) => {
    if (!file) return;
    setBusy(true);
    setErr('');
    setCsvName(file.name);
    try {
      const text = await file.text();
      const rows = parseCsv(text);
      if (rows.length === 0) {
        throw new Error('That CSV looks empty — make sure the first row has column headers.');
      }
      const KNOWN = new Set(['first_name', 'last_name', 'email', 'phone', 'title', 'notes', 'tags', 'company']);
      // Canonicalise headers: lower, snake_case, common aliases collapse to
      // first/last name etc. so "First Name" and "FirstName" both map.
      const headers = Object.keys(rows[0]).map(h => ({
        raw: h,
        canon: canonHeader(h),
      }));
      let ok = 0;
      let failed = 0;
      for (const row of rows) {
        const body = { first_name: '', last_name: '', email: '', phone: '', title: '', notes: '', tags: '' };
        const extras = {};
        for (const h of headers) {
          const v = (row[h.raw] ?? '').trim();
          if (!v) continue;
          if (KNOWN.has(h.canon)) {
            if (h.canon === 'company') {
              // No company column on contacts table — surface in custom_fields.
              extras.company = v;
            } else {
              body[h.canon] = v;
            }
          } else {
            extras[h.raw] = v;
          }
        }
        if (!body.first_name && !body.last_name) continue;
        body.custom_fields = JSON.stringify(extras);
        try {
          await createContact(body);
          ok += 1;
        } catch {
          failed += 1;
        }
      }
      if (ok === 0) {
        throw new Error(`Couldn't import any rows. Check headers include first_name + last_name (any case).${failed ? ` ${failed} rows failed.` : ''}`);
      }
      setCsvRows(ok);
      await completeOnboardingStep('data_source');
      // Refresh state so the timeline / nav button reflect `done`, but
      // DON'T auto-jump to the next step. The user just dropped a file —
      // they need to see the green "Imported N rows from foo.csv"
      // confirmation before they're moved on, or they'll think nothing
      // happened. The Continue button picks it up from here.
      await refreshState();
    } catch (e) {
      setErr(e.message || 'Could not import this CSV — check the column headers.');
    } finally {
      setBusy(false);
    }
  };

  // Step 5 inline persona load + run.
  //
  // Some agents can't be safely sample-run from the wizard:
  //   - outbound_caller (Vox) — places real phone calls; needs a contact
  //     with a phone number + Twilio setup before it can do anything
  //   - memory_consolidate (Memory) — a weekly digest job, nothing
  //     interesting to show on a brand-new workspace with no history
  // Filter them out so the picker only offers agents that produce a
  // meaningful sample result inline.
  const FIRST_RUN_BLOCKLIST = new Set(['outbound_caller', 'memory_consolidate']);
  useEffect(() => {
    if (currentKey !== 'first_run' || personas !== null) return;
    let cancelled = false;
    listPersonas()
      .then((data) => {
        if (cancelled) return;
        const arr = Array.isArray(data) ? data : (data?.personas || []);
        const filtered = arr.filter(p => !FIRST_RUN_BLOCKLIST.has(p.agent_key));
        setPersonas(filtered.slice(0, 6));
      })
      .catch(() => { if (!cancelled) setPersonas([]); });
    return () => { cancelled = true; };
  }, [currentKey, personas]);

  const runFirstAgent = async (key) => {
    setBusy(true);
    setErr('');
    setRunningKey(key);
    setRunResult(null);
    try {
      const res = await runAgent(key);
      setRunResult({ key, summary: res?.summary || res?.output || 'Agent finished — check the dashboard for output.' });
      await completeOnboardingStep('first_run');
      const fresh = await refreshState();
      const next = fresh.steps.findIndex(s => !s.done);
      // Don't auto-advance — let the user see the run result for a moment.
      // The "Continue" button on the right will move on.
      setRunningKey('');
      if (next === -1) {
        // already at last step; do nothing
      }
    } catch (e) {
      setErr(e.message || 'Agent could not start. Try another or skip for now.');
      setRunningKey('');
    } finally {
      setBusy(false);
    }
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
      <FullScreenShell onSkip={canClose ? onClose : null}>
        <div className="onb-rail" />
        <main className="onb-pane">
          <div className="onb-pane-inner">
            <div className="onb-error">{err}</div>
          </div>
        </main>
      </FullScreenShell>
    );
  }
  // While the initial onboarding state is being fetched, render the
  // full-screen shell with skeleton content. We MUST cover the dashboard
  // immediately — returning null here used to let the half-loaded sidebar
  // + greeting + KPIs flash through behind the future wizard, which is
  // what the user was seeing on the left after email verification.
  if (!state || !currentStep) {
    return (
      <FullScreenShell onSkip={null}>
        <aside className="onb-rail">
          <div className="onb-rail-top">
            <div className="onb-brand">
              <BrandMark size={44} />
              <div>
                <div className="onb-brand-name">NexusAgent</div>
                <div className="onb-brand-sub">Workspace setup</div>
              </div>
            </div>
            <div className="onb-skeleton-stack">
              {[0,1,2,3,4,5].map(i => (
                <div key={i} className="onb-skeleton-row">
                  <div className="onb-skeleton-dot" />
                  <div className="onb-skeleton-line" style={{ width: `${60 + (i*5)%30}%` }} />
                </div>
              ))}
            </div>
          </div>
        </aside>
        <main className="onb-pane">
          <div className="onb-pane-inner">
            <div className="onb-skeleton-eyebrow" />
            <div className="onb-skeleton-title" />
            <div className="onb-skeleton-desc" />
            <div className="onb-skeleton-desc" style={{ width: '70%' }} />
          </div>
        </main>
      </FullScreenShell>
    );
  }

  const Icon = STEP_ICONS[currentKey] || Sparkles;

  return (
    <FullScreenShell onSkip={canClose ? fullySkip : null}>
      <LeftRail
        steps={steps}
        currentIndex={step}
        currentKey={currentKey}
        selectedIndustry={selectedIndustry}
        canJump={true}
        onJump={(i) => setStep(i)}
      />

      <main className="onb-pane">
        <div className="onb-pane-inner">
          <div className="onb-step-meta">
            <span className="onb-step-eyebrow">Step {step + 1} of {total}</span>
            <h1 className="onb-step-title">{currentStep.title}</h1>
            <p className="onb-step-desc">{currentStep.description}</p>
          </div>

          {err && (
            <div className="onb-error">
              {err}
            </div>
          )}

          {/* Step body — keyed on currentKey so React unmounts/remounts on
              step change. The CSS keyframe on .onb-step-body then replays
              the fade+slide-in animation, giving every step a calm entry. */}
          <div key={currentKey} className="onb-step-body">
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
              <DocumentStep
                busy={busy}
                uploadedName={uploadedName}
                done={currentStep.done}
                onUpload={uploadStarterDoc}
              />
            )}

            {currentKey === 'data_source' && (
              <DataSourceStep
                busy={busy}
                csvName={csvName}
                csvRows={csvRows}
                done={currentStep.done}
                onUpload={uploadContactsCsv}
              />
            )}

            {currentKey === 'first_run' && (
              <FirstRunStep
                personas={personas}
                runningKey={runningKey}
                runResult={runResult}
                busy={busy}
                onRun={runFirstAgent}
              />
            )}

            {currentKey === 'celebrated' && (
              <CelebrationBlock industry={selectedIndustry} />
            )}
          </div>

          <div className="onb-nav">
            <button
              onClick={goPrev}
              disabled={step === 0}
              className="onb-btn onb-btn-ghost"
            >
              <ArrowLeft size={13} /> Back
            </button>
            <div className="onb-nav-spacer" />

            {currentKey === 'profile' && (
              <button onClick={saveProfile} className="onb-btn onb-btn-primary" disabled={busy}>
                {busy ? 'Saving…' : 'Save business setup'} <ArrowRight size={13} />
              </button>
            )}

            {currentKey === 'agents' && (
              <button onClick={acceptRecommendations} className="onb-btn onb-btn-primary" disabled={busy}>
                {busy ? 'Applying…' : 'Apply this setup'} <ArrowRight size={13} />
              </button>
            )}

            {currentKey === 'document' && (
              <button
                onClick={() => { completeStep('document').then(() => goNext()); }}
                className="onb-btn onb-btn-primary" disabled={busy}
              >
                {busy ? 'Working…'
                  : currentStep.done ? 'Continue'
                  : 'Do this later'} <ArrowRight size={13} />
              </button>
            )}

            {currentKey === 'data_source' && (
              <button
                onClick={() => { completeStep('data_source').then(() => goNext()); }}
                className="onb-btn onb-btn-primary" disabled={busy}
              >
                {currentStep.done ? 'Continue' : 'Do this later'} <ArrowRight size={13} />
              </button>
            )}

            {currentKey === 'first_run' && (
              <button
                onClick={() => { completeStep('first_run').then(() => goNext()); }}
                className="onb-btn onb-btn-primary" disabled={busy}
              >
                {currentStep.done ? 'Continue' : 'Do this later'} <ArrowRight size={13} />
              </button>
            )}

            {currentKey !== 'profile' && currentKey !== 'agents'
              && currentKey !== 'document' && currentKey !== 'data_source'
              && currentKey !== 'first_run' && currentKey !== 'celebrated' && (
              <button onClick={() => { completeStep(currentKey).then(() => goNext()); }} className="onb-btn onb-btn-primary" disabled={busy}>
                {busy ? 'Saving…' : 'Mark done'} <ArrowRight size={13} />
              </button>
            )}

            {currentKey === 'celebrated' && (
              <button
                onClick={() => { completeStep('celebrated').then(() => onClose()); }}
                className="onb-btn onb-btn-primary onb-btn-celebrate"
                disabled={busy}
              >
                {busy ? 'Saving…' : 'Enter my workspace'} <ArrowRight size={13} />
              </button>
            )}
          </div>
        </div>
      </main>
    </FullScreenShell>
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
        {/* "Other" surfaces a free-text box so workspaces that don't fit one of
            the 6 templates can still tell us what they need. The value is
            stored back into primaryGoal so the rest of the flow (saveProfile,
            IndustryStep's goal highlight) keeps reading one field. */}
        {profile.primaryGoal === 'Other' && (
          <input
            className="field-input"
            style={{ marginTop: 8 }}
            placeholder="Describe what you'd like NexusAgent to do for you…"
            value={profile.customGoal || ''}
            onChange={(e) => update('customGoal', e.target.value)}
            maxLength={140}
            autoFocus
          />
        )}
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

// ── Step 3: data source (inline CSV upload, no navigation) ──────────────────
function DataSourceStep({ busy, csvName, csvRows, done, onUpload }) {
  const success = done && csvName;
  return (
    <div style={{ display: 'grid', gap: 14 }}>
      <label style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        gap: 10, minHeight: 170,
        border: `2px dashed ${success ? 'var(--color-ok)' : 'var(--color-border)'}`,
        borderRadius: 'var(--r-md)',
        background: success
          ? 'color-mix(in srgb, var(--color-ok) 6%, var(--color-surface-1))'
          : 'var(--color-surface-1)',
        cursor: busy ? 'wait' : 'pointer', textAlign: 'center', padding: 24,
        transition: 'border-color 180ms, background 180ms',
      }}>
        <input
          type="file"
          disabled={busy}
          accept=".csv,text/csv"
          style={{ display: 'none' }}
          onChange={(e) => onUpload(e.target.files?.[0])}
        />
        {success
          ? <CheckCircle2 size={26} color="var(--color-ok)" />
          : <Database size={26} color="var(--color-text-dim)" />}
        <div style={{ fontSize: 14, color: 'var(--color-text)', fontWeight: 600 }}>
          {busy
            ? `Importing ${csvName || 'CSV'}…`
            : success
              ? `Imported ${csvRows || 'your'} rows from ${csvName}`
              : 'Drop a contacts CSV or click to choose'}
        </div>
        <div style={{ fontSize: 11.5, color: 'var(--color-text-dim)', maxWidth: 400, lineHeight: 1.5 }}>
          {success
            ? 'Atlas will use these in your CRM. You can import more from Database later.'
            : 'Any spreadsheet with name + email + phone columns works. We auto-detect the rest.'}
        </div>
      </label>
      <div className="onb-info-card" style={{ fontSize: 12 }}>
        Expected headers (any order): <strong>first_name, last_name, email, phone, company</strong>. Skip this if you'd rather start from a blank pipeline.
      </div>
    </div>
  );
}

// ── Step 5: pick an agent + run it inline ───────────────────────────────────
function FirstRunStep({ personas, runningKey, runResult, busy, onRun }) {
  if (personas === null) {
    return (
      <div className="onb-info-card" style={{ textAlign: 'center', padding: 24 }}>
        Loading your agent line-up…
      </div>
    );
  }
  if (personas.length === 0) {
    return (
      <div className="onb-info-card">
        We couldn't load your agent presets right now — you can skip this step and start an agent from the Agents page after setup.
      </div>
    );
  }
  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{
        display: 'grid', gap: 10,
        gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
      }}>
        {personas.map((p) => {
          // Backend returns `agent_key` (see api/routers/agents.py and
          // agents/personas.py). Falling back to other keys for robustness.
          const key = p.agent_key || p.key || p.id;
          const isRunning = runningKey === key;
          const isDone = runResult && runResult.key === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => !busy && onRun(key)}
              disabled={busy}
              style={{
                textAlign: 'left',
                padding: '14px 14px',
                borderRadius: 12,
                background: isDone
                  ? 'color-mix(in srgb, var(--color-ok) 8%, var(--color-surface-1))'
                  : 'var(--color-surface-1)',
                border: `1px solid ${isDone
                  ? 'color-mix(in srgb, var(--color-ok) 35%, var(--color-border))'
                  : 'var(--color-border)'}`,
                cursor: busy ? 'wait' : 'pointer',
                display: 'flex', flexDirection: 'column', gap: 6,
                transition: 'transform 140ms, border-color 180ms, background 180ms',
              }}
              onMouseEnter={(e) => !busy && (e.currentTarget.style.transform = 'translateY(-1px)')}
              onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{
                  width: 28, height: 28, borderRadius: 8,
                  background: 'color-mix(in srgb, var(--color-accent) 14%, transparent)',
                  color: 'var(--color-accent)',
                  display: 'grid', placeItems: 'center',
                }}>
                  {isDone ? <CheckCircle2 size={14} /> : <Bot size={14} />}
                </div>
                <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--color-text)' }}>
                  {p.name || key}
                </div>
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
                {p.description || p.role_tag || 'Tap to run a quick sample task.'}
              </div>
              <div style={{
                fontSize: 11, fontWeight: 600, marginTop: 2,
                color: isRunning ? 'var(--color-accent)'
                      : isDone   ? 'var(--color-ok)'
                                 : 'var(--color-text-dim)',
              }}>
                {isRunning ? 'Running…' : isDone ? 'Finished ✓' : 'Run sample task →'}
              </div>
            </button>
          );
        })}
      </div>

      {runResult && (
        <div style={{
          padding: 14, borderRadius: 12,
          background: 'color-mix(in srgb, var(--color-ok) 7%, var(--color-surface-1))',
          border: '1px solid color-mix(in srgb, var(--color-ok) 25%, var(--color-border))',
          fontSize: 12.5, color: 'var(--color-text)', lineHeight: 1.55,
        }}>
          <div style={{
            fontSize: 10.5, fontWeight: 700, letterSpacing: 0.5, textTransform: 'uppercase',
            color: 'var(--color-ok)', marginBottom: 6,
          }}>
            Run complete
          </div>
          {String(runResult.summary).slice(0, 320)}
        </div>
      )}
    </div>
  );
}

function DocumentStep({ busy, uploadedName, done, onUpload }) {
  // success = the step is marked done on the server AND we have a name
  // to display. Treats the post-upload state with the same loud green
  // border + check that the data-source step uses, so the user gets a
  // clear confirmation before clicking Continue.
  const success = done && uploadedName;
  return (
    <div style={{ display: 'grid', gap: 14 }}>
      <label style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        gap: 10, minHeight: 170,
        border: `2px dashed ${success ? 'var(--color-ok)' : 'var(--color-border)'}`,
        borderRadius: 'var(--r-md)',
        background: success
          ? 'color-mix(in srgb, var(--color-ok) 6%, var(--color-surface-1))'
          : 'var(--color-surface-1)',
        cursor: busy ? 'wait' : 'pointer', textAlign: 'center', padding: 24,
        transition: 'border-color 180ms, background 180ms',
      }}>
        <input
          type="file"
          disabled={busy}
          accept=".pdf,.txt,.md,.docx,text/plain,application/pdf"
          style={{ display: 'none' }}
          onChange={(e) => onUpload(e.target.files?.[0])}
        />
        {success
          ? <CheckCircle2 size={26} color="var(--color-ok)" />
          : <Upload size={26} color="var(--color-text-dim)" />}
        <div style={{ fontSize: 14, color: 'var(--color-text)', fontWeight: 600 }}>
          {busy
            ? `Uploading ${uploadedName || 'document'}…`
            : success
              ? `Uploaded ${uploadedName}`
              : 'Drop a PDF / DOCX or click to choose'}
        </div>
        <div style={{ fontSize: 11.5, color: 'var(--color-text-dim)', maxWidth: 400, lineHeight: 1.5 }}>
          {success
            ? 'Indexed in your workspace. The AI will use it as safe context for first answers.'
            : 'Policies, product catalogs, service guides, pricing sheets, FAQs, or onboarding docs.'}
        </div>
      </label>
      <div className="onb-info-card" style={{ fontSize: 12 }}>
        Optional but recommended — one company doc is enough to seed the AI with safe context. You can upload more later from the Documents page.
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

// ─────────────────────────────────────────────────────────────────────────
// Full-screen shell
// ─────────────────────────────────────────────────────────────────────────
// The wizard is the first-ever screen a new account sees. We render it as
// a full-viewport split layout instead of a small centered modal so the
// experience feels like part of the product, not an interrupt over it.
//
// Layout: left rail (brand + vertical step timeline) + right pane (the
// step content). The styles live next to the component as an injected
// <style> tag so this file stays self-contained — no app-wide CSS edits.

function FullScreenShell({ children, onSkip }) {
  return (
    <>
      <OnboardingStyles />
      <div className="onb-shell" role="dialog" aria-modal="true" aria-label="Workspace setup">
        {/* Ambient gradient orbs in the background — pure CSS, no JS. */}
        <div className="onb-orb onb-orb-1" aria-hidden />
        <div className="onb-orb onb-orb-2" aria-hidden />

        {onSkip && (
          <button
            className="onb-skip"
            onClick={onSkip}
            title="Skip the rest of setup — you can finish later from Settings"
          >
            Skip for now <X size={13} />
          </button>
        )}

        {children}
      </div>
    </>
  );
}

// Left rail — brand + vertical step timeline. Clicking a step jumps to it
// (the wizard already supported step skipping; we just reuse the handler).
function LeftRail({ steps, currentIndex, currentKey, selectedIndustry, canJump, onJump }) {
  return (
    <aside className="onb-rail">
      <div className="onb-rail-top">
        <div className="onb-brand">
          <BrandMark size={44} />
          <div>
            <div className="onb-brand-name">NexusAgent</div>
            <div className="onb-brand-sub">Workspace setup</div>
          </div>
        </div>

        <ol className="onb-timeline" role="list">
          {steps.map((s, i) => {
            const StepIcon = STEP_ICONS[s.key] || Sparkles;
            const isActive = i === currentIndex;
            const isDone = s.done;
            return (
              <li
                key={s.key}
                className={`onb-tl-item${isActive ? ' is-active' : ''}${isDone ? ' is-done' : ''}`}
                onClick={canJump ? () => onJump(i) : undefined}
              >
                <div className="onb-tl-dot">
                  {isDone ? <CheckCircle2 size={14} /> : <StepIcon size={13} />}
                </div>
                <div className="onb-tl-text">
                  <div className="onb-tl-title">{s.title}</div>
                  <div className="onb-tl-step">Step {i + 1}</div>
                </div>
              </li>
            );
          })}
        </ol>
      </div>

      <div className="onb-rail-foot">
        <div className="onb-rail-tip">
          {currentKey === 'profile' && (
            <>Your answers tune sample data, agent priorities and email templates — pick what's true today, you can refine later.</>
          )}
          {currentKey === 'agents' && (
            <>We pre-shape the workspace for <strong>{selectedIndustry.toLowerCase()}</strong>. Every other agent stays one click away in the sidebar.</>
          )}
          {currentKey === 'document' && (
            <>One company doc is enough to start. The AI uses it as safe context for first answers — no hallucinated specs.</>
          )}
          {currentKey === 'celebrated' && (
            <>You're all set. Your dashboard, agents and sample data are waiting on the next click.</>
          )}
          {currentKey !== 'profile' && currentKey !== 'agents'
            && currentKey !== 'document' && currentKey !== 'celebrated' && (
            <>Quick step — most teams take under 2 minutes to finish setup.</>
          )}
        </div>
      </div>
    </aside>
  );
}

function CelebrationBlock({ industry }) {
  return (
    <div className="onb-celebrate">
      <div className="onb-celebrate-burst" aria-hidden>
        <Sparkles size={26} />
      </div>
      <h3 className="onb-celebrate-h3">Your NexusAgent workspace is ready.</h3>
      <p className="onb-celebrate-sub">
        Tuned for {industry.toLowerCase()} — your sidebar, sample data and agent priorities reflect what your day actually looks like.
      </p>
    </div>
  );
}

function OnboardingStyles() {
  return (
    <style>{`
      .onb-shell {
        position: fixed; inset: 0; z-index: 1000;
        display: grid;
        grid-template-columns: minmax(320px, 420px) 1fr;
        background:
          radial-gradient(1200px 600px at 0% 0%,   rgba(99,102,241,0.10), transparent 60%),
          radial-gradient(900px 500px at 100% 100%, rgba(16,185,129,0.07), transparent 55%),
          var(--color-bg);
        color: var(--color-text);
        overflow: hidden;
        animation: onb-fade-in 360ms cubic-bezier(.2,.7,.3,1);
      }
      .onb-orb {
        position: absolute; border-radius: 50%; pointer-events: none;
        filter: blur(60px); opacity: 0.55;
        animation: onb-orb-drift 16s ease-in-out infinite alternate;
      }
      .onb-orb-1 {
        width: 360px; height: 360px;
        background: radial-gradient(circle, rgba(139,92,246,0.45), transparent 70%);
        top: -80px; left: -80px;
      }
      .onb-orb-2 {
        width: 460px; height: 460px;
        background: radial-gradient(circle, rgba(16,185,129,0.35), transparent 70%);
        bottom: -120px; right: -120px;
        animation-delay: -8s;
      }
      @keyframes onb-orb-drift {
        0%   { transform: translate(0, 0)     scale(1); }
        100% { transform: translate(40px, 20px) scale(1.06); }
      }

      /* ── Left rail ───────────────────────────────────────────────────── */
      .onb-rail {
        position: relative; z-index: 1;
        display: flex; flex-direction: column; justify-content: space-between;
        padding: 40px 32px;
        background: linear-gradient(165deg,
          rgba(15, 18, 30, 0.85) 0%,
          rgba(20, 24, 40, 0.75) 50%,
          rgba(15, 18, 30, 0.85) 100%);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255,255,255,0.06);
      }
      [data-theme="light"] .onb-rail {
        background: linear-gradient(165deg, #0c1224 0%, #131b34 60%, #0c1224 100%);
      }
      .onb-rail-top { display: flex; flex-direction: column; gap: 36px; }
      .onb-brand { display: flex; align-items: center; gap: 12px; }
      .onb-brand-mark {
        width: 44px; height: 44px; border-radius: 12px;
        background: linear-gradient(135deg, #10b981 0%, #6366f1 60%, #8b5cf6 100%);
        display: grid; place-items: center;
        color: white; font-size: 20px; font-weight: 800;
        box-shadow: 0 0 0 1px rgba(99,102,241,0.25), 0 8px 24px rgba(99,102,241,0.18);
      }
      .onb-brand-name {
        font-size: 15px; font-weight: 700; letter-spacing: -0.01em;
        color: #e6e8ef;
      }
      .onb-brand-sub {
        font-size: 11px; color: #6b7280; margin-top: 2px; letter-spacing: 0.3px;
      }

      .onb-timeline { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
      .onb-tl-item {
        position: relative;
        display: grid; grid-template-columns: 32px 1fr; gap: 12px; align-items: center;
        padding: 10px 10px 10px 6px; border-radius: 10px;
        cursor: pointer; transition: background 180ms ease;
      }
      .onb-tl-item:hover { background: rgba(255,255,255,0.03); }
      /* Vertical connector line between dots */
      .onb-tl-item:not(:last-child)::after {
        content: ""; position: absolute;
        left: 21px; top: 36px; bottom: -4px;
        width: 2px; border-radius: 1px;
        background: rgba(255,255,255,0.06);
        transition: background 240ms ease;
      }
      .onb-tl-item.is-done:not(:last-child)::after { background: rgba(16,185,129,0.5); }

      .onb-tl-dot {
        width: 32px; height: 32px; border-radius: 50%;
        display: grid; place-items: center;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        color: #6b7280;
        transition: all 240ms cubic-bezier(.2,.7,.3,1);
      }
      .onb-tl-item.is-active .onb-tl-dot {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border-color: rgba(139,92,246,0.6);
        color: white;
        transform: scale(1.06);
        box-shadow: 0 0 0 4px rgba(99,102,241,0.18);
      }
      .onb-tl-item.is-done .onb-tl-dot {
        background: rgba(16,185,129,0.18);
        border-color: rgba(16,185,129,0.5);
        color: #10b981;
      }

      .onb-tl-text { min-width: 0; }
      .onb-tl-title {
        font-size: 13px; font-weight: 600;
        color: #c0c4d0;
        transition: color 200ms ease;
      }
      .onb-tl-item.is-active .onb-tl-title { color: #ffffff; }
      .onb-tl-item.is-done .onb-tl-title { color: #d3d6df; }
      .onb-tl-step {
        font-size: 10.5px; color: #5a6072; margin-top: 1px;
        letter-spacing: 0.4px; text-transform: uppercase;
      }

      .onb-rail-foot {}
      .onb-rail-tip {
        padding: 14px 16px; border-radius: 12px;
        background: rgba(255,255,255,0.035);
        border: 1px solid rgba(255,255,255,0.06);
        font-size: 12.5px; color: #9aa0b0; line-height: 1.6;
      }
      .onb-rail-tip strong { color: #d3d6df; font-weight: 600; }

      /* ── Right pane ──────────────────────────────────────────────────── */
      .onb-pane {
        position: relative; z-index: 1;
        overflow-y: auto;
        display: flex; align-items: center; justify-content: center;
        padding: 56px 40px;
      }
      .onb-pane-inner {
        width: 100%;
        max-width: 640px;
        display: flex; flex-direction: column; gap: 28px;
      }

      .onb-skip {
        position: absolute; top: 22px; right: 28px;
        display: inline-flex; align-items: center; gap: 6px;
        padding: 7px 13px; border-radius: 999px;
        background: transparent;
        border: 1px solid var(--color-border);
        color: var(--color-text-dim);
        font-size: 12px; font-weight: 500; cursor: pointer;
        transition: all 180ms ease;
        z-index: 2;
      }
      .onb-skip:hover {
        color: var(--color-text);
        border-color: var(--color-text-dim);
        background: var(--color-surface-1);
      }

      .onb-step-meta { display: flex; flex-direction: column; gap: 8px; }
      .onb-step-eyebrow {
        font-size: 11px; font-weight: 700; letter-spacing: 0.8px;
        text-transform: uppercase;
        background: linear-gradient(90deg, #10b981, #8b5cf6);
        -webkit-background-clip: text; background-clip: text;
        -webkit-text-fill-color: transparent; color: transparent;
      }
      .onb-step-title {
        margin: 0; font-size: 28px; font-weight: 700;
        letter-spacing: -0.02em; line-height: 1.15;
        color: var(--color-text);
      }
      .onb-step-desc {
        margin: 0; font-size: 14.5px; color: var(--color-text-muted);
        line-height: 1.55; max-width: 60ch;
      }

      .onb-error {
        padding: 10px 14px; border-radius: 10px;
        background: color-mix(in srgb, var(--color-err) 8%, transparent);
        border: 1px solid color-mix(in srgb, var(--color-err) 26%, transparent);
        color: var(--color-err); font-size: 12.5px; line-height: 1.5;
      }

      /* Step body — replays the fade+slide entrance on every step switch
         because the parent component remounts it via the React key prop. */
      .onb-step-body { animation: onb-step-enter 320ms cubic-bezier(.2,.7,.3,1); }
      @keyframes onb-step-enter {
        0%   { opacity: 0; transform: translateY(8px); }
        100% { opacity: 1; transform: translateY(0);   }
      }
      @keyframes onb-fade-in {
        0%   { opacity: 0; }
        100% { opacity: 1; }
      }

      .onb-info-card {
        padding: 14px 16px; border-radius: 12px;
        background: var(--color-surface-1);
        border: 1px solid var(--color-border);
        font-size: 13px; color: var(--color-text-muted); line-height: 1.6;
      }
      .onb-info-card strong { color: var(--color-text); font-weight: 600; }

      /* ── Celebration block ──────────────────────────────────────────── */
      .onb-celebrate {
        text-align: center; padding: 32px 24px;
        border-radius: 16px;
        background:
          radial-gradient(80% 80% at 50% 0%, rgba(16,185,129,0.10), transparent 70%),
          var(--color-surface-1);
        border: 1px solid color-mix(in srgb, var(--color-ok) 22%, var(--color-border));
      }
      .onb-celebrate-burst {
        width: 56px; height: 56px; border-radius: 50%;
        margin: 0 auto 14px;
        display: grid; place-items: center;
        background: linear-gradient(135deg, rgba(16,185,129,0.18), rgba(99,102,241,0.18));
        color: #10b981;
        animation: onb-pulse 2.4s ease-in-out infinite;
      }
      @keyframes onb-pulse {
        0%, 100% { transform: scale(1);    box-shadow: 0 0 0 0 rgba(16,185,129,0.20); }
        50%      { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(16,185,129,0.00); }
      }
      .onb-celebrate-h3 {
        margin: 0 0 6px; font-size: 18px; font-weight: 700;
        color: var(--color-text); letter-spacing: -0.01em;
      }
      .onb-celebrate-sub {
        margin: 0; font-size: 13.5px; color: var(--color-text-muted); line-height: 1.6;
      }

      /* ── Nav row ─────────────────────────────────────────────────────── */
      .onb-nav {
        display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
        padding-top: 8px;
      }
      .onb-nav-spacer { flex: 1; }
      .onb-btn {
        display: inline-flex; align-items: center; justify-content: center; gap: 8px;
        padding: 11px 18px; border-radius: 10px;
        font-size: 13.5px; font-weight: 600; letter-spacing: 0.01em;
        cursor: pointer; border: 1px solid transparent;
        transition: transform 140ms ease, box-shadow 180ms ease,
                    background 180ms ease, color 180ms ease, border-color 180ms ease;
      }
      .onb-btn:disabled { opacity: 0.55; cursor: not-allowed; }
      .onb-btn-ghost {
        background: transparent;
        border-color: var(--color-border);
        color: var(--color-text-muted);
      }
      .onb-btn-ghost:hover:not(:disabled) {
        color: var(--color-text);
        border-color: var(--color-text-dim);
        background: var(--color-surface-1);
      }
      .onb-btn-primary {
        background: linear-gradient(135deg, #10b981 0%, #6366f1 100%);
        color: #fff;
        box-shadow: 0 6px 20px rgba(99,102,241,0.22);
      }
      .onb-btn-primary:hover:not(:disabled) {
        transform: translateY(-1px);
        box-shadow: 0 10px 28px rgba(99,102,241,0.32);
      }
      .onb-btn-primary:active:not(:disabled) { transform: translateY(0); }
      .onb-btn-celebrate {
        padding: 13px 22px; font-size: 14px;
        background: linear-gradient(135deg, #10b981 0%, #8b5cf6 100%);
      }

      /* ── Skeleton placeholders (state-loading window) ────────────────── */
      .onb-skeleton-stack { display: flex; flex-direction: column; gap: 14px; }
      .onb-skeleton-row { display: flex; align-items: center; gap: 12px; padding: 6px 0; }
      .onb-skeleton-dot {
        width: 32px; height: 32px; border-radius: 50%;
        background: rgba(255,255,255,0.05);
        animation: onb-shimmer 1.6s ease-in-out infinite;
      }
      .onb-skeleton-line {
        height: 10px; border-radius: 4px;
        background: rgba(255,255,255,0.05);
        animation: onb-shimmer 1.6s ease-in-out infinite;
      }
      .onb-skeleton-eyebrow {
        width: 80px; height: 11px; border-radius: 4px; margin-bottom: 14px;
        background: var(--color-surface-2);
        animation: onb-shimmer 1.6s ease-in-out infinite;
      }
      .onb-skeleton-title {
        width: 60%; height: 28px; border-radius: 6px; margin-bottom: 18px;
        background: var(--color-surface-2);
        animation: onb-shimmer 1.6s ease-in-out infinite;
      }
      .onb-skeleton-desc {
        width: 90%; height: 12px; border-radius: 4px; margin-bottom: 10px;
        background: var(--color-surface-2);
        animation: onb-shimmer 1.6s ease-in-out infinite;
      }
      @keyframes onb-shimmer {
        0%, 100% { opacity: 0.6; }
        50%      { opacity: 1; }
      }

      /* ── Responsive ──────────────────────────────────────────────────── */
      @media (max-width: 900px) {
        .onb-shell { grid-template-columns: 1fr; grid-template-rows: auto 1fr; }
        .onb-rail { padding: 24px 22px; }
        .onb-rail-top { gap: 20px; }
        .onb-rail-foot { display: none; }
        .onb-timeline { flex-direction: row; gap: 0; overflow-x: auto; }
        .onb-tl-item { grid-template-columns: 28px auto; padding: 6px 10px; }
        .onb-tl-item:not(:last-child)::after {
          left: auto; right: -2px; top: 50%; bottom: auto;
          transform: translateY(-50%);
          width: 16px; height: 2px;
        }
        .onb-tl-step { display: none; }
        .onb-tl-title { font-size: 12px; }
        .onb-pane { padding: 32px 22px; }
        .onb-step-title { font-size: 22px; }
      }
    `}</style>
  );
}

// ── CSV helpers (kept tiny, no dependency) ──────────────────────────────────
// Handles quoted fields, escaped quotes ("" inside ""), and CRLF/LF newlines.
// We intentionally don't pull in PapaParse for this — onboarding ships a
// minimal contact import, power users can use the full Database page later.
function parseCsv(text) {
  const rows = [];
  let i = 0;
  const len = text.length;
  let row = [];
  let field = '';
  let inQuotes = false;
  while (i < len) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') { field += '"'; i += 2; continue; }
        inQuotes = false; i++; continue;
      }
      field += c; i++; continue;
    }
    if (c === '"') { inQuotes = true; i++; continue; }
    if (c === ',') { row.push(field); field = ''; i++; continue; }
    if (c === '\r') { i++; continue; }
    if (c === '\n') { row.push(field); rows.push(row); row = []; field = ''; i++; continue; }
    field += c; i++;
  }
  if (field !== '' || row.length) { row.push(field); rows.push(row); }
  if (rows.length === 0) return [];
  const headers = rows[0].map(h => h.trim());
  return rows.slice(1)
    .filter(r => r.some(c => c.trim() !== ''))
    .map(r => Object.fromEntries(headers.map((h, idx) => [h, r[idx] ?? ''])));
}

function canonHeader(h) {
  const s = String(h || '').toLowerCase().trim().replace(/\s+|-/g, '_');
  // Common aliases the user might use in their export.
  if (s === 'firstname' || s === 'given_name')   return 'first_name';
  if (s === 'lastname'  || s === 'surname' || s === 'family_name') return 'last_name';
  if (s === 'fullname'  || s === 'name')         return 'first_name';
  if (s === 'mobile'    || s === 'phone_number') return 'phone';
  if (s === 'mail'      || s === 'email_address')return 'email';
  if (s === 'job_title' || s === 'role')         return 'title';
  if (s === 'organization' || s === 'org' || s === 'company_name') return 'company';
  return s;
}

const ONBOARDING_KEY = 'nexus_onboarding_done';

// Onboarding is per-business. Without this, finishing the wizard for
// business A would suppress it for business B (same browser → same
// localStorage flag). Each business gets its own ":<bizId>" key, so
// a freshly-created business still triggers Step 1.
function _bizKey() {
  try {
    return getCurrentBusiness()?.id || 'unknown';
  } catch {
    return 'unknown';
  }
}

export function shouldShowOnboarding() {
  // Backward-compat: if the legacy single-key flag is set AND no
  // per-business key exists yet, treat that as "done" for the current
  // business too (so users who finished onboarding pre-multi-tenant
  // don't get an unexpected wizard).
  const bizId = _bizKey();
  const perBiz = localStorage.getItem(`${ONBOARDING_KEY}:${bizId}`);
  if (perBiz === '1') return false;
  if (perBiz === null && localStorage.getItem(ONBOARDING_KEY) === '1') {
    return false;
  }
  return true;
}

export function markOnboardingSeen() {
  localStorage.setItem(`${ONBOARDING_KEY}:${_bizKey()}`, '1');
  // Keep the legacy key set too — harmless, prevents flapping if a
  // caller reads the un-suffixed key directly.
  localStorage.setItem(ONBOARDING_KEY, '1');
}

// Called by Layout's handleCreateBiz to ensure the wizard re-opens for
// the brand-new business even on a browser that completed it earlier.
export function clearOnboardingForBusiness(bizId) {
  if (!bizId) return;
  try {
    localStorage.removeItem(`${ONBOARDING_KEY}:${bizId}`);
  } catch { /* private mode */ }
}
