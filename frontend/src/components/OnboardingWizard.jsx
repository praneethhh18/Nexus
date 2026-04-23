import { useState, useEffect } from 'react';
import { Briefcase, Users, CheckSquare, Receipt, X, ArrowRight, Sparkles } from 'lucide-react';
import { getCurrentBusiness, setBusinessId } from '../services/auth';
import { createBusiness, listBusinesses } from '../services/businesses';
import { createContact } from '../services/crm';
import { createTask } from '../services/tasks';

const ONBOARDING_KEY = 'nexus_onboarding_done';

export default function OnboardingWizard({ onClose }) {
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [bizName, setBizName] = useState('');
  const [bizIndustry, setBizIndustry] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [firstTask, setFirstTask] = useState('');
  const current = getCurrentBusiness();

  const steps = ['welcome', 'business', 'contact', 'task', 'done'];
  const total = steps.length;

  const finish = () => {
    localStorage.setItem(ONBOARDING_KEY, '1');
    onClose();
  };

  const doBusiness = async () => {
    if (!bizName.trim()) { setStep(step + 1); return; }
    setBusy(true);
    try {
      const biz = await createBusiness({ name: bizName, industry: bizIndustry });
      const fresh = await listBusinesses();
      setBusinessId(biz.id);
      window.dispatchEvent(new CustomEvent('nexus-business-changed', { detail: biz.id }));
      setStep(step + 1);
    } catch (e) {
      alert(`Failed: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const doContact = async () => {
    if (!contactName.trim()) { setStep(step + 1); return; }
    setBusy(true);
    try {
      const [first, ...rest] = contactName.trim().split(/\s+/);
      await createContact({
        first_name: first,
        last_name: rest.join(' '),
        email: contactEmail,
      });
      setStep(step + 1);
    } catch (e) {
      alert(`Failed: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const doTask = async () => {
    if (!firstTask.trim()) { setStep(step + 1); return; }
    setBusy(true);
    try {
      await createTask({ title: firstTask, priority: 'normal' });
      setStep(step + 1);
    } catch (e) {
      alert(`Failed: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const skip = () => setStep(step + 1);

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', zIndex: 500, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{
        background: '#0c1222', border: '1px solid #1e293b', borderRadius: 14,
        padding: 32, width: 480, boxShadow: '0 20px 60px rgba(0,0,0,0.7)',
      }}>
        {/* Progress bar */}
        <div style={{ display: 'flex', gap: 4, marginBottom: 20 }}>
          {steps.map((_, i) => (
            <div key={i} style={{
              flex: 1, height: 3, borderRadius: 2,
              background: i <= step ? '#22c55e' : '#1e293b',
              transition: 'background 0.2s',
            }} />
          ))}
        </div>

        <button onClick={finish} style={{ position: 'absolute', top: 16, right: 16, background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
          <X size={16} />
        </button>

        {step === 0 && (
          <>
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <Sparkles size={40} color="#22c55e" style={{ marginBottom: 12 }} />
              <h2 style={{ fontSize: 20, fontWeight: 700, color: '#e2e8f0', margin: 0 }}>Welcome to NexusAgent</h2>
              <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>Your 360° business assistant. Let's get you set up in under a minute.</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10, marginBottom: 20 }}>
              {[
                { icon: Briefcase, label: 'Multiple businesses', desc: 'Manage them all from one place' },
                { icon: Users, label: 'CRM', desc: 'Contacts, companies & deals' },
                { icon: CheckSquare, label: 'Tasks', desc: 'Track what needs doing' },
                { icon: Receipt, label: 'Invoices', desc: 'Create & track payments' },
              ].map(({ icon: Icon, label, desc }, i) => (
                <div key={i} style={{ padding: 12, background: '#0f172a', borderRadius: 8 }}>
                  <Icon size={16} color="#60a5fa" style={{ marginBottom: 6 }} />
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#e2e8f0' }}>{label}</div>
                  <div style={{ fontSize: 10, color: '#64748b' }}>{desc}</div>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between' }}>
              <button onClick={finish} className="btn-ghost">Skip onboarding</button>
              <button onClick={() => setStep(1)} className="btn-primary">Get started <ArrowRight size={13} /></button>
            </div>
          </>
        )}

        {step === 1 && (
          <>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: '#e2e8f0', marginBottom: 6 }}>Your business</h2>
            <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 16 }}>
              You already have <strong style={{ color: '#e2e8f0' }}>{current?.name || 'a business'}</strong>.
              Want to rename it or create another? Leave blank to keep things as they are.
            </p>
            <input
              className="field-input" placeholder="Another business name (optional)"
              value={bizName} onChange={(e) => setBizName(e.target.value)} maxLength={120}
              style={{ marginBottom: 10 }} autoFocus
            />
            <input
              className="field-input" placeholder="Industry (optional)"
              value={bizIndustry} onChange={(e) => setBizIndustry(e.target.value)} maxLength={80}
            />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between', marginTop: 16 }}>
              <button onClick={skip} className="btn-ghost">Skip</button>
              <button onClick={doBusiness} disabled={busy} className="btn-primary">{busy ? '...' : 'Next'} <ArrowRight size={13} /></button>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: '#e2e8f0', marginBottom: 6 }}>Add your first contact</h2>
            <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 16 }}>This is optional — you can add contacts any time from the CRM tab.</p>
            <input
              className="field-input" placeholder="Full name" value={contactName}
              onChange={(e) => setContactName(e.target.value)} maxLength={160}
              style={{ marginBottom: 10 }} autoFocus
            />
            <input
              className="field-input" type="email" placeholder="Email (optional)"
              value={contactEmail} onChange={(e) => setContactEmail(e.target.value)} maxLength={200}
            />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between', marginTop: 16 }}>
              <button onClick={skip} className="btn-ghost">Skip</button>
              <button onClick={doContact} disabled={busy} className="btn-primary">{busy ? '...' : 'Next'} <ArrowRight size={13} /></button>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <h2 style={{ fontSize: 18, fontWeight: 600, color: '#e2e8f0', marginBottom: 6 }}>Your first task</h2>
            <p style={{ fontSize: 12, color: '#94a3b8', marginBottom: 16 }}>What's something on your plate right now?</p>
            <input
              className="field-input" placeholder="e.g. Call Acme on Friday"
              value={firstTask} onChange={(e) => setFirstTask(e.target.value)} maxLength={200}
              autoFocus
            />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'space-between', marginTop: 16 }}>
              <button onClick={skip} className="btn-ghost">Skip</button>
              <button onClick={doTask} disabled={busy} className="btn-primary">{busy ? '...' : 'Next'} <ArrowRight size={13} /></button>
            </div>
          </>
        )}

        {step === 4 && (
          <>
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <div style={{
                width: 56, height: 56, borderRadius: '50%', background: '#22c55e22', color: '#22c55e',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 12,
              }}>
                <CheckSquare size={28} />
              </div>
              <h2 style={{ fontSize: 18, fontWeight: 600, color: '#e2e8f0', margin: 0 }}>You're all set</h2>
              <p style={{ fontSize: 13, color: '#94a3b8', marginTop: 8 }}>
                Open the Chat tab and try asking: <em style={{ color: '#60a5fa' }}>"What are my tasks today?"</em>
                <br />or head to Workflows to enable a ready-made automation.
              </p>
            </div>
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <button onClick={finish} className="btn-primary">Jump into my dashboard</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export function shouldShowOnboarding() {
  return localStorage.getItem(ONBOARDING_KEY) !== '1';
}
