/**
 * Self-hosted setup wizard.
 *
 * Lives at `/setup` and is reachable without auth. Walks a first-time user
 * through:
 *
 *   1. Platform check  — OS / RAM / disk / Python
 *   2. Ollama reachable  — if not, show the install link + re-check
 *   3. Pick a model  — recommended default based on detected RAM
 *   4. Pull the model  — Ollama's cold pull can take minutes; we poll status
 *   5. Finish  — marks setup complete, redirects to /login
 *
 * Each step is a pure function of the `status` snapshot; re-polling after
 * every action keeps the UI honest without bespoke state choreography.
 */
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle2, AlertCircle, Loader2, Download, Sparkles, ExternalLink,
  Cpu, HardDrive, MemoryStick, Server,
} from 'lucide-react';
import {
  getSetupStatus, pullSetupModel, chooseSetupModel, completeSetup,
} from '../services/setup';


export default function Setup() {
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [err, setErr] = useState('');
  const [pulling, setPulling] = useState(null);     // model name being pulled
  const [finishing, setFinishing] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const s = await getSetupStatus();
      setStatus(s);
      if (!selectedModel) setSelectedModel(s.models?.default_model || null);
      setErr('');
      return s;
    } catch (e) {
      setErr(String(e.message || e));
    }
  }, [selectedModel]);

  useEffect(() => { refresh(); }, [refresh]);

  // Once setup is already marked complete, kick the user to the real app.
  useEffect(() => {
    if (status?.completed) {
      const t = setTimeout(() => navigate('/login'), 1200);
      return () => clearTimeout(t);
    }
  }, [status?.completed, navigate]);

  // While a pull is running, poll status every 8s so the "installed" chip
  // flips to green without a manual refresh.
  useEffect(() => {
    if (!pulling) return;
    const iv = setInterval(refresh, 8000);
    return () => clearInterval(iv);
  }, [pulling, refresh]);

  const pull = async (name) => {
    setPulling(name); setErr('');
    try {
      await pullSetupModel(name);
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setPulling(null);
      refresh();
    }
  };

  const choose = async (name) => {
    setSelectedModel(name);
    try { await chooseSetupModel(name); } catch {}
  };

  const finish = async () => {
    setFinishing(true);
    try {
      await completeSetup();
      navigate('/login');
    } catch (e) {
      setErr(String(e.message || e));
    } finally {
      setFinishing(false);
    }
  };

  if (!status) {
    return (
      <Shell>
        <div style={{ textAlign: 'center', color: 'var(--color-text-dim)', padding: 40 }}>
          <Loader2 size={20} style={{ animation: 'spin 1s linear infinite' }} /> Loading…
        </div>
      </Shell>
    );
  }

  const { platform, ollama, models, can_finish: canFinish, completed } = status;

  return (
    <Shell>
      <div style={{ marginBottom: 16 }}>
        <Sparkles size={20} color="var(--color-accent)" />
        <h1 style={{ margin: '6px 0 4px', fontSize: 20 }}>Welcome to NexusAgent</h1>
        <p style={{ margin: 0, fontSize: 13, color: 'var(--color-text-muted)' }}>
          Three quick checks and you're ready. Your workspace stays local.
        </p>
      </div>

      {err && (
        <div style={{
          padding: 10, marginBottom: 14, borderRadius: 'var(--r-sm)',
          background: 'color-mix(in srgb, var(--color-err) 10%, transparent)',
          color: 'var(--color-err)', fontSize: 12,
        }}>
          <AlertCircle size={12} style={{ verticalAlign: 'middle' }} /> {err}
        </div>
      )}

      {completed && (
        <Step kind="ok" title="Setup complete — redirecting to sign in…">
          If you're not taken there in a moment, <a href="/login" style={{ color: 'var(--color-info)' }}>click here</a>.
        </Step>
      )}

      {/* ── Step 1: Platform ─────────────────────────────────────────────── */}
      <Step kind="ok" title="Your machine">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, marginTop: 8 }}>
          <InfoCell icon={Server}      label="OS"     value={`${platform.os} ${platform.release}`} />
          <InfoCell icon={Cpu}         label="Arch"   value={`${platform.arch} · py ${platform.python}`} />
          <InfoCell icon={MemoryStick} label="RAM"    value={platform.ram_gb ? `${platform.ram_gb} GB` : 'unknown'} />
          <InfoCell icon={HardDrive}   label="Disk free" value={platform.disk_free_gb ? `${platform.disk_free_gb} GB` : 'unknown'} />
        </div>
      </Step>

      {/* ── Step 2: Ollama ───────────────────────────────────────────────── */}
      {ollama.online ? (
        <Step kind="ok" title="Ollama is running">
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
            {ollama.models?.length || 0} model(s) already installed at <code>{ollama.host}</code>
          </span>
        </Step>
      ) : (
        <Step kind="error" title="Ollama not detected">
          <p style={{ fontSize: 12, margin: '4px 0 10px', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
            NexusAgent needs a local Ollama daemon for private inference. Install it from{' '}
            <a href={models.install_hint_url} target="_blank" rel="noreferrer"
               style={{ color: 'var(--color-info)' }}>
              ollama.com/download <ExternalLink size={10} />
            </a>, start it (<code>ollama serve</code>), then click Re-check.
          </p>
          <button className="btn-primary" onClick={refresh} style={{ fontSize: 12 }}>
            Re-check
          </button>
        </Step>
      )}

      {/* ── Step 3: Model selection ──────────────────────────────────────── */}
      {ollama.online && (
        <Step kind={models.suitable.some(m => m.installed) ? 'ok' : 'pending'} title="Pick a model">
          <p style={{ fontSize: 11, color: 'var(--color-text-muted)', margin: '4px 0 8px', lineHeight: 1.5 }}>
            Choose a model that fits your RAM. You can change this later in Settings.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {models.suitable.map(m => {
              const isChosen = selectedModel === m.name;
              return (
                <div
                  key={m.name}
                  onClick={() => choose(m.name)}
                  style={{
                    display: 'flex', alignItems: 'flex-start', gap: 10,
                    padding: 10, borderRadius: 'var(--r-md)', cursor: 'pointer',
                    background: isChosen
                      ? 'color-mix(in srgb, var(--color-accent) 10%, transparent)'
                      : 'var(--color-surface-1)',
                    border: `1px solid ${isChosen ? 'color-mix(in srgb, var(--color-accent) 40%, transparent)' : 'var(--color-border)'}`,
                  }}
                >
                  <input
                    type="radio" checked={isChosen} onChange={() => choose(m.name)}
                    style={{ accentColor: 'var(--color-accent)', marginTop: 3 }}
                  />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-text)', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                      {m.label}
                      {m.recommended && (
                        <span style={{
                          fontSize: 9, padding: '1px 6px', borderRadius: 'var(--r-pill)',
                          background: 'var(--color-accent-soft)', color: 'var(--color-accent)',
                        }}>Recommended</span>
                      )}
                      {m.installed
                        ? <span style={{ fontSize: 9, color: 'var(--color-ok)' }}>✓ installed</span>
                        : <span style={{ fontSize: 9, color: 'var(--color-text-dim)' }}>not installed</span>}
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 2 }}>
                      Needs ≈ {m.size_gb} GB disk · ≥ {m.min_ram_gb} GB RAM
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--color-text-muted)', marginTop: 3 }}>
                      {m.note}
                    </div>
                  </div>
                  {!m.installed && (
                    <button
                      onClick={(e) => { e.stopPropagation(); pull(m.name); }}
                      disabled={pulling === m.name}
                      className="btn-ghost"
                      style={{ fontSize: 11, padding: '4px 10px' }}
                    >
                      {pulling === m.name
                        ? <><Loader2 size={11} style={{ animation: 'spin 1s linear infinite' }} /> Pulling…</>
                        : <><Download size={11} /> Pull</>}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
          {pulling && (
            <p style={{ fontSize: 11, color: 'var(--color-text-dim)', marginTop: 8 }}>
              The first pull can take several minutes depending on your connection. You can keep this page open — it will refresh automatically.
            </p>
          )}
        </Step>
      )}

      {/* ── Finish ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 18 }}>
        <button
          onClick={finish}
          disabled={!canFinish || finishing}
          className="btn-primary"
          style={{ fontSize: 13, padding: '8px 18px' }}
        >
          {finishing
            ? <Loader2 size={12} style={{ animation: 'spin 1s linear infinite' }} />
            : <CheckCircle2 size={12} />}
          {canFinish ? 'Finish setup' : 'Waiting for Ollama + a model'}
        </button>
      </div>
    </Shell>
  );
}


function Shell({ children }) {
  return (
    <div style={{
      minHeight: '100vh', background: 'var(--color-bg)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
    }}>
      <div style={{
        width: 'min(680px, 96vw)',
        padding: 24, borderRadius: 'var(--r-lg)',
        background: 'var(--color-surface-2)', border: '1px solid var(--color-border-strong)',
        boxShadow: '0 20px 48px rgba(0,0,0,0.35)',
      }}>
        {children}
      </div>
    </div>
  );
}


function Step({ kind = 'pending', title, children }) {
  const color = {
    ok:      'var(--color-ok)',
    pending: 'var(--color-warn)',
    error:   'var(--color-err)',
  }[kind];
  const Icon = kind === 'ok' ? CheckCircle2
             : kind === 'error' ? AlertCircle
             : Loader2;
  return (
    <div style={{
      padding: 14, marginBottom: 12, borderRadius: 'var(--r-md)',
      background: 'var(--color-surface-1)',
      borderLeft: `3px solid ${color}`,
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8,
        fontSize: 13, fontWeight: 600, color: 'var(--color-text)',
      }}>
        <Icon size={14} color={color} />
        {title}
      </div>
      <div style={{ marginTop: 4 }}>{children}</div>
    </div>
  );
}


function InfoCell({ icon: Icon, label, value }) {
  return (
    <div style={{
      padding: '8px 10px', borderRadius: 'var(--r-sm)',
      background: 'var(--color-bg)', border: '1px solid var(--color-border)',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6,
                    fontSize: 9, color: 'var(--color-text-dim)',
                    textTransform: 'uppercase', letterSpacing: 0.8 }}>
        <Icon size={10} />
        {label}
      </div>
      <div style={{ fontSize: 12, color: 'var(--color-text)', marginTop: 2 }}>{value}</div>
    </div>
  );
}
