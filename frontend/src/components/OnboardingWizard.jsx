/**
 * First-run setup wizard — six steps matching the onboarding roadmap.
 *
 * State is server-backed via /api/onboarding so the wizard resumes across
 * devices and browsers. Each step has a Skip button and can also be
 * auto-completed if the user already accomplished the underlying task
 * (e.g. uploaded a document before ever opening the wizard).
 */
import { useState, useEffect } from 'react';
import {
  Sparkles, Briefcase, Users, Database, FileType2, Bot, PartyPopper,
  X, ArrowRight, ArrowLeft, CheckCircle2, Circle,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  getOnboardingState, completeOnboardingStep, skipOnboarding,
} from '../services/onboarding';

const STEP_ICONS = {
  profile:     Briefcase,
  agents:      Bot,
  data_source: Database,
  document:    FileType2,
  first_run:   Users,
  celebrated:  PartyPopper,
};

export default function OnboardingWizard({ onClose }) {
  const [state, setState] = useState(null);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const navigate = useNavigate();

  // Load server state once on open
  useEffect(() => {
    let cancelled = false;
    getOnboardingState()
      .then((s) => {
        if (cancelled) return;
        setState(s);
        // Jump to the first undone step so returning users don't start over.
        const firstUndone = (s.steps || []).findIndex(x => !x.done);
        setStep(firstUndone === -1 ? (s.steps.length - 1) : firstUndone);
      })
      .catch((e) => setErr(e.message || 'Could not load onboarding'));
    return () => { cancelled = true; };
  }, []);

  if (err) {
    return (
      <Overlay onClose={onClose}>
        <div style={{ color: 'var(--color-err)', fontSize: 12 }}>{err}</div>
      </Overlay>
    );
  }
  if (!state) return <Overlay onClose={onClose}>Loading…</Overlay>;

  const steps = state.steps;
  const current = steps[step];
  const total = steps.length;

  const saveDone = async (stepKey) => {
    setBusy(true); setErr('');
    try {
      const fresh = await completeOnboardingStep(stepKey);
      setState(fresh);
      return fresh;
    } catch (e) {
      setErr(e.message || 'Could not save progress');
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

  const skipStep = () => goNext();

  const completeAndNext = async () => {
    await saveDone(current.key);
    goNext();
  };

  const finishAndClose = async () => {
    await saveDone('celebrated');
    onClose();
  };

  const doAction = (route) => {
    // Let the user accomplish the step in-app; the widget on the dashboard
    // will show it as done after autodetection picks it up.
    onClose();
    navigate(route);
  };

  const fullySkip = async () => {
    try { await skipOnboarding(); } catch {}
    onClose();
  };

  const Icon = STEP_ICONS[current.key] || Sparkles;

  return (
    <Overlay onClose={fullySkip}>
      {/* Progress indicator */}
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
              transition: 'background 0.2s',
            }}
          />
        ))}
      </div>

      <button
        onClick={fullySkip}
        style={{
          position: 'absolute', top: 16, right: 16,
          background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer',
        }}
        title="Skip onboarding entirely"
      >
        <X size={16} />
      </button>

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 'var(--r-md)',
          background: current.done
            ? 'color-mix(in srgb, var(--color-ok) 15%, transparent)'
            : 'color-mix(in srgb, var(--color-accent) 15%, transparent)',
          color: current.done ? 'var(--color-ok)' : 'var(--color-accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {current.done ? <CheckCircle2 size={20} /> : <Icon size={20} />}
        </div>
        <div>
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)', letterSpacing: 0.5, textTransform: 'uppercase' }}>
            Step {step + 1} of {total}
          </div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600, color: 'var(--color-text)' }}>
            {current.title}
          </h2>
        </div>
      </div>

      <p style={{
        fontSize: 13, color: 'var(--color-text-muted)',
        margin: '10px 0 18px', lineHeight: 1.55,
      }}>
        {current.description}
      </p>

      {/* Step body — celebration step is special */}
      {current.key === 'celebrated' ? (
        <div style={{
          padding: 18, borderRadius: 'var(--r-md)',
          background: 'color-mix(in srgb, var(--color-ok) 8%, transparent)',
          border: '1px solid color-mix(in srgb, var(--color-ok) 25%, transparent)',
          textAlign: 'center',
        }}>
          <Sparkles size={28} color="var(--color-ok)" />
          <h3 style={{ margin: '8px 0 4px', fontSize: 15, color: 'var(--color-text)' }}>
            Your workspace is ready
          </h3>
          <p style={{ fontSize: 12, color: 'var(--color-text-muted)', margin: 0 }}>
            Try asking the AI: <em style={{ color: 'var(--color-accent)' }}>"what are my tasks today?"</em>
          </p>
        </div>
      ) : (
        <div style={{
          padding: 14, borderRadius: 'var(--r-md)',
          background: 'var(--color-surface-1)',
          border: '1px solid var(--color-border)',
          fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.6,
        }}>
          When you're ready, click <strong style={{ color: 'var(--color-text)' }}>{current.cta}</strong> and finish this step inside the app. The wizard resumes where you left off.
          <br />
          Already done? Use <strong style={{ color: 'var(--color-text)' }}>Mark done</strong>.
        </div>
      )}

      {/* Actions */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        marginTop: 18, flexWrap: 'wrap',
      }}>
        <button
          onClick={goPrev}
          disabled={step === 0}
          className="btn-ghost"
          style={{ opacity: step === 0 ? 0.4 : 1 }}
        >
          <ArrowLeft size={12} /> Back
        </button>
        <div style={{ flex: 1 }} />
        {current.key !== 'celebrated' && (
          <>
            <button onClick={skipStep} className="btn-ghost" disabled={busy}>Skip</button>
            <button
              onClick={() => doAction(current.route)}
              className="btn-ghost"
              disabled={busy}
            >
              {current.cta}
            </button>
            <button
              onClick={completeAndNext}
              className="btn-primary"
              disabled={busy}
            >
              {busy ? 'Saving…' : 'Mark done'} <ArrowRight size={12} />
            </button>
          </>
        )}
        {current.key === 'celebrated' && (
          <button onClick={finishAndClose} className="btn-primary" disabled={busy}>
            {busy ? 'Saving…' : 'Jump to dashboard'} <ArrowRight size={12} />
          </button>
        )}
      </div>
    </Overlay>
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
          width: 'min(520px, 94vw)', position: 'relative',
          boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
        }}
      >
        {children}
      </div>
    </div>
  );
}

// ── Legacy localStorage check retained for the old Layout call site ────────
// The React app decides whether to open the wizard based on the server state;
// if the call fails (e.g. offline or logged out) we fall back to localStorage
// so a fresh browser on a first-time user still sees the wizard.
const ONBOARDING_KEY = 'nexus_onboarding_done';

export function shouldShowOnboarding() {
  return localStorage.getItem(ONBOARDING_KEY) !== '1';
}

export function markOnboardingSeen() {
  localStorage.setItem(ONBOARDING_KEY, '1');
}
