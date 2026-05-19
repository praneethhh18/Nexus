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
  getIndustryPreset,
} from '../services/onboarding';
import { updateBusiness } from '../services/businesses';
import { uploadDocument } from '../services/api';
import { getCurrentBusiness } from '../services/auth';

const INDUSTRIES = [
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
  Healthcare: ['Patient intake', 'Policy knowledge base', 'Appointment follow-ups', 'Privacy review'],
  'Real estate': ['Lead capture', 'Property documents', 'Buyer follow-ups', 'Deal pipeline'],
  Education: ['Admissions support', 'Course FAQ', 'Student follow-ups', 'Reports'],
  Legal: ['Client intake', 'Document Q&A', 'Case task tracking', 'Secure audit trail'],
  Ecommerce: ['Product catalog', 'Returns support', 'Order follow-ups', 'Customer inbox'],
  Finance: ['Client onboarding', 'Invoice reminders', 'Compliance docs', 'Secure reporting'],
  SaaS: ['Pipeline CRM', 'Support triage', 'Churn signals', 'Product knowledge base'],
  Manufacturing: ['Vendor docs', 'Order follow-ups', 'Operations tasks', 'Reports'],
  Hospitality: ['Booking support', 'Guest FAQs', 'Review follow-ups', 'Shift tasks'],
  'Local services': ['Lead intake', 'Job scheduling', 'Quote follow-ups', 'Invoice reminders'],
  Consulting: ['Client briefs', 'Proposal docs', 'Meeting prep', 'Project tasks'],
  Other: ['Business knowledge base', 'CRM pipeline', 'Task automation', 'Reports'],
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
    if (!profile.name.trim() || !profile.industry.trim() || !profile.businessType || !profile.companySize || !profile.primaryGoal) {
      setErr('Complete the business profile fields before continuing.');
      return;
    }
    setBusy(true);
    setErr('');
    try {
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
  if (!state || !currentStep) return <Overlay>Loading...</Overlay>;

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
        <ProfileStep profile={profile} setProfile={setProfile} />
      )}

      {currentKey === 'agents' && (
        <IndustryStep industry={industryPreset?.industry || selectedIndustry} preset={presetTools} />
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

function ProfileStep({ profile, setProfile }) {
  const update = (key, value) => setProfile((p) => ({ ...p, [key]: value }));
  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <Field label="Business name">
          <input className="field-input" value={profile.name} onChange={(e) => update('name', e.target.value)} placeholder="Acme Services" maxLength={120} autoFocus />
        </Field>
        <Field label="Business type">
          <select className="field-select" value={profile.businessType} onChange={(e) => update('businessType', e.target.value)}>
            <option value="">Choose type</option>
            {BUSINESS_TYPES.map(x => <option key={x} value={x}>{x}</option>)}
          </select>
        </Field>
        <Field label="Industry">
          <select className="field-select" value={profile.industry} onChange={(e) => update('industry', e.target.value)}>
            <option value="">Choose industry</option>
            {INDUSTRIES.map(x => <option key={x} value={x}>{x}</option>)}
          </select>
        </Field>
        <Field label="Company size">
          <select className="field-select" value={profile.companySize} onChange={(e) => update('companySize', e.target.value)}>
            <option value="">Choose size</option>
            {COMPANY_SIZES.map(x => <option key={x} value={x}>{x}</option>)}
          </select>
        </Field>
      </div>
      <Field label="Main goal">
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

function IndustryStep({ industry, preset }) {
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
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        {preset.map((item) => (
          <div key={item} style={{
            padding: 10, borderRadius: 'var(--r-sm)',
            background: 'color-mix(in srgb, var(--color-accent) 7%, var(--color-surface-1))',
            border: '1px solid color-mix(in srgb, var(--color-accent) 20%, var(--color-border))',
            fontSize: 12, color: 'var(--color-text)',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            <CheckCircle2 size={14} color="var(--color-ok)" /> {item}
          </div>
        ))}
      </div>
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

function Field({ label, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <span style={{ fontSize: 11, color: 'var(--color-text-muted)', fontWeight: 600 }}>{label}</span>
      {children}
    </label>
  );
}

function Overlay({ children, onClose }) {
  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)',
        zIndex: 500, display: 'flex', alignItems: 'center', justifyContent: 'center',
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
