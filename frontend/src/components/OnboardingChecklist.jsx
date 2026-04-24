/**
 * Dashboard checklist widget — shows remaining onboarding steps with a CTA
 * for each one, and hides itself once all steps are done or the user has
 * explicitly skipped.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, Circle, ArrowRight, Sparkles, X } from 'lucide-react';
import {
  getOnboardingState, completeOnboardingStep, skipOnboarding,
} from '../services/onboarding';

export default function OnboardingChecklist() {
  const [state, setState] = useState(null);
  const [dismissing, setDismissing] = useState(false);
  const navigate = useNavigate();

  const load = useCallback(() => {
    getOnboardingState().then(setState).catch(() => {});
  }, []);

  useEffect(() => {
    load();
    // Refresh when the user returns to the tab — they may have just completed
    // a step elsewhere in the app.
    const onFocus = () => load();
    window.addEventListener('focus', onFocus);
    return () => window.removeEventListener('focus', onFocus);
  }, [load]);

  if (!state) return null;
  if (state.skipped) return null;
  if (state.all_done && state.celebrated) return null;

  const total = state.steps.length;
  const doneCount = state.steps.filter(s => s.done).length;
  const pct = Math.round((doneCount / total) * 100);

  const markDone = async (key) => {
    try { setState(await completeOnboardingStep(key)); } catch {}
  };

  const dismiss = async () => {
    setDismissing(true);
    try { await skipOnboarding(); setState({ ...state, skipped: true }); } catch {}
    setDismissing(false);
  };

  return (
    <div className="panel" style={{
      padding: 18, display: 'flex', flexDirection: 'column', gap: 12,
      borderColor: 'color-mix(in srgb, var(--color-accent) 30%, var(--color-border))',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: 36, height: 36, borderRadius: 'var(--r-md)',
          background: 'color-mix(in srgb, var(--color-accent) 15%, transparent)',
          color: 'var(--color-accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <Sparkles size={18} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>
            Finish setting up NexusAgent
          </div>
          <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 2 }}>
            {doneCount} of {total} steps done · {pct}% complete
          </div>
        </div>
        <button
          onClick={dismiss}
          disabled={dismissing}
          className="btn-ghost"
          style={{ fontSize: 11 }}
          title="Hide this panel until you reopen it from Settings"
        >
          <X size={12} />
        </button>
      </div>

      <div style={{
        height: 4, borderRadius: 2, background: 'var(--color-surface-2)', overflow: 'hidden',
      }}>
        <div style={{
          height: '100%', width: `${pct}%`,
          background: 'linear-gradient(90deg, var(--color-accent), var(--color-ok))',
          transition: 'width 0.4s ease',
        }} />
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
        {state.steps.map((step) => (
          <div
            key={step.key}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 10px', borderRadius: 'var(--r-sm)',
              background: step.done
                ? 'color-mix(in srgb, var(--color-ok) 5%, transparent)'
                : 'transparent',
              opacity: step.done ? 0.7 : 1,
            }}
          >
            {step.done
              ? <CheckCircle2 size={14} color="var(--color-ok)" />
              : <Circle size={14} color="var(--color-text-dim)" />}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontSize: 12, fontWeight: 500,
                color: step.done ? 'var(--color-text-muted)' : 'var(--color-text)',
                textDecoration: step.done ? 'line-through' : 'none',
              }}>
                {step.title}
              </div>
              <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>
                {step.description}
              </div>
            </div>
            {!step.done && (
              <>
                <button
                  onClick={() => navigate(step.route)}
                  className="btn-ghost"
                  style={{ fontSize: 11, padding: '3px 8px' }}
                >
                  {step.cta} <ArrowRight size={10} />
                </button>
                <button
                  onClick={() => markDone(step.key)}
                  className="btn-ghost"
                  style={{ fontSize: 11, padding: '3px 8px' }}
                  title="Mark this step as done without doing it"
                >
                  Skip
                </button>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
