import { useState, useEffect, useCallback } from 'react';
import { ReactFlow, Background, Controls, MiniMap, addEdge, useNodesState, useEdgesState, Handle, Position, MarkerType } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Play, Plus, Trash2, Power, Save, GitBranch, Zap, Sparkles, Clock, Edit3, Code2, ArrowLeft, Check, X, BookOpen, ArrowRight } from 'lucide-react';
import { getWorkflows, getWorkflow, saveWorkflow, deleteWorkflow, toggleWorkflow, runWorkflow, getNodeTypes, getWorkflowTemplates, getWorkflowHistory, generateWorkflowFromText } from '../services/api';
import EmptyState from '../components/EmptyState';

const CAT_COLORS = { trigger: 'var(--color-accent-hover)', condition: '#7c3aed', data: 'var(--color-ok)', ai: 'var(--color-warn)', action: 'var(--color-err)', control: 'var(--color-text-dim)' };
const CAT_ICONS = { trigger: 'T', condition: '?', data: 'D', ai: 'AI', action: 'A', control: 'C' };
const CAT_LABELS = { trigger: 'Triggers', condition: 'Conditions', data: 'Data', ai: 'AI', action: 'Actions', control: 'Control' };

// ── Custom node renderer for React Flow ──────────────────────────────────────
function WorkflowNode({ data, selected }) {
  const color = CAT_COLORS[data.category] || 'var(--color-text-dim)';
  const icon = CAT_ICONS[data.category] || 'N';
  return (
    <div style={{
      padding: '10px 16px', borderRadius: 12, minWidth: 160,
      background: selected ? `${color}18` : 'var(--color-surface-2)',
      border: `2px solid ${selected ? color : 'var(--color-border-strong)'}`,
      boxShadow: selected ? `0 0 16px ${color}30` : '0 2px 8px #00000030',
    }}>
      <Handle type="target" position={Position.Left} style={{ background: color, width: 8, height: 8, border: '2px solid var(--color-surface-1)' }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
        <span style={{ fontSize: 10, fontWeight: 700, color: '#fff', background: color, padding: '2px 7px', borderRadius: 6 }}>{icon}</span>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'white' }}>{data.label}</span>
      </div>
      <div style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{data.nodeType}</div>
      {data.description && <div style={{ fontSize: 9, color: 'var(--color-text-dim)', marginTop: 3, maxWidth: 180 }}>{data.description}</div>}
      <Handle type="source" position={Position.Right} style={{ background: color, width: 8, height: 8, border: '2px solid var(--color-surface-1)' }} />
    </div>
  );
}

const nodeTypes = { workflowNode: WorkflowNode };

// ── Template card (business-user facing) ─────────────────────────────────────
function TemplateCard({ tmpl, onEnable, onOpen }) {
  const tags = tmpl.tags || [];
  return (
    <div className="panel" style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div>
        <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)', margin: 0 }}>{tmpl.name}</p>
        <p style={{ fontSize: 11, color: 'var(--color-text-muted)', margin: '4px 0 0' }}>{tmpl.description}</p>
      </div>
      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
        {tags.map((t, i) => (
          <span key={i} style={{ fontSize: 9, padding: '2px 7px', borderRadius: 4, background: 'var(--color-surface-1)', color: 'var(--color-text-dim)' }}>{t}</span>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 6, marginTop: 'auto' }}>
        <button className="btn-primary" style={{ flex: 1 }} onClick={() => onEnable(tmpl)}>
          <Play size={12} /> Use this
        </button>
        <button className="btn-ghost" onClick={() => onOpen(tmpl)}>
          <Edit3 size={12} /> Customize
        </button>
      </div>
    </div>
  );
}

// ── How-to guide ─────────────────────────────────────────────────────────────
// First-timer onboarding for the Workflows page. Explains the 4 concepts in
// the language of the product (trigger → optional condition → action), shows
// one concrete example, and points at templates. Dismissible per-user via
// localStorage so it doesn't keep appearing.
function WorkflowsGuide() {
  const KEY = 'nexus_workflows_guide_dismissed';
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(KEY) === '1');

  if (dismissed) {
    return (
      <button
        className="btn-ghost btn-sm"
        style={{ marginBottom: 12 }}
        onClick={() => { localStorage.removeItem(KEY); setDismissed(false); }}
      >
        <BookOpen size={11} /> Show how-to
      </button>
    );
  }

  const concepts = [
    { tone: 'trigger',   title: '1. Trigger',   body: 'When the workflow runs. e.g. every weekday at 9 AM, on a webhook, when an anomaly is detected.' },
    { tone: 'condition', title: '2. Condition', body: 'Optional. A filter that decides whether to continue. e.g. "only if revenue dropped more than 10%."' },
    { tone: 'action',    title: '3. Action',    body: 'What happens. e.g. send Slack, draft an email, generate a PDF, call an HTTP endpoint.' },
    { tone: 'control',   title: '4. Control',   body: 'Optional. Wait, branch on a result, loop over a list, or trigger another agent.' },
  ];

  const TONE_BG = {
    trigger:   'color-mix(in srgb, var(--color-accent) 14%, transparent)',
    condition: 'color-mix(in srgb, #a78bfa 14%, transparent)',
    action:    'color-mix(in srgb, var(--color-warn) 14%, transparent)',
    control:   'var(--color-surface-3)',
  };
  const TONE_FG = {
    trigger:   'var(--color-accent)',
    condition: '#c4b5fd',
    action:    'var(--color-warn)',
    control:   'var(--color-text-muted)',
  };

  return (
    <div className="panel" style={{
      padding: 16, marginBottom: 16,
      background: 'linear-gradient(135deg, var(--color-surface-2), var(--color-surface-1))',
      border: '1px solid var(--color-border-strong)',
      position: 'relative',
    }}>
      <button
        onClick={() => { localStorage.setItem(KEY, '1'); setDismissed(true); }}
        title="Hide this guide"
        style={{
          position: 'absolute', top: 8, right: 10,
          background: 'transparent', border: 'none', cursor: 'pointer',
          color: 'var(--color-text-dim)',
        }}
      >
        <X size={14} />
      </button>

      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
        <BookOpen size={15} color="var(--color-accent)" />
        <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>
          How workflows work
        </span>
      </div>
      <p style={{ fontSize: 12, color: 'var(--color-text-muted)', margin: '0 0 12px', maxWidth: 720, lineHeight: 1.55 }}>
        A workflow is a chain of steps that runs on its own. You wire them in this order:
        <strong style={{ color: 'var(--color-text)' }}> trigger</strong> →
        <strong style={{ color: 'var(--color-text)' }}> condition (optional)</strong> →
        <strong style={{ color: 'var(--color-text)' }}> action</strong>. Use a template, describe one in plain English, or build from scratch.
      </p>

      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: 8, marginBottom: 12,
      }}>
        {concepts.map((c) => (
          <div key={c.title} style={{
            padding: 10,
            background: 'var(--color-surface-2)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--r-md)',
          }}>
            <span style={{
              display: 'inline-block',
              fontSize: 10, fontWeight: 700, letterSpacing: 0.5, textTransform: 'uppercase',
              padding: '2px 8px', borderRadius: 'var(--r-pill)',
              background: TONE_BG[c.tone], color: TONE_FG[c.tone],
              marginBottom: 6,
            }}>
              {c.title}
            </span>
            <div style={{ fontSize: 11.5, color: 'var(--color-text-muted)', lineHeight: 1.5 }}>
              {c.body}
            </div>
          </div>
        ))}
      </div>

      {/* Worked example */}
      <div style={{
        padding: 10,
        background: 'var(--color-surface-1)',
        border: '1px dashed var(--color-border-strong)',
        borderRadius: 'var(--r-md)',
        fontSize: 11.5, color: 'var(--color-text-muted)', lineHeight: 1.6,
      }}>
        <strong style={{ color: 'var(--color-text)' }}>Worked example.</strong>{' '}
        <em>Daily sales report.</em> <strong style={{ color: TONE_FG.trigger }}>Trigger:</strong> 9 AM weekdays
        <ArrowRight size={10} style={{ verticalAlign: 'middle', margin: '0 4px', color: 'var(--color-text-dim)' }} />
        <strong style={{ color: TONE_FG.condition }}>Action:</strong> SQL "yesterday's revenue"
        <ArrowRight size={10} style={{ verticalAlign: 'middle', margin: '0 4px', color: 'var(--color-text-dim)' }} />
        <strong style={{ color: TONE_FG.action }}>Action:</strong> Summarize → build PDF → email it. The "Daily sales report" template below is exactly this.
      </div>
    </div>
  );
}


// ── Main page ────────────────────────────────────────────────────────────────
export default function Workflows() {
  const [workflows, setWorkflows] = useState([]);
  const [nodeTypeDefs, setNodeTypeDefs] = useState({});
  const [templates, setTemplates] = useState([]);
  const [history, setHistory] = useState([]);

  const [view, setView] = useState('gallery'); // gallery | my | history | builder
  const [msg, setMsg] = useState('');
  const [enablingName, setEnablingName] = useState('');

  // Builder state
  const [wfId, setWfId] = useState(null);
  const [wfName, setWfName] = useState('New Workflow');
  const [wfEnabled, setWfEnabled] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);
  const [nlPrompt, setNlPrompt] = useState('');
  const [nlBusy, setNlBusy] = useState(false);

  const refresh = useCallback(() => {
    getWorkflows().then(setWorkflows).catch(() => {});
    getWorkflowHistory().then(setHistory).catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
    getNodeTypes().then(setNodeTypeDefs).catch(() => {});
    getWorkflowTemplates().then(setTemplates).catch(() => {});
  }, [refresh]);

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(''), 2500); };

  // ── Gallery: one-click enable a template ────────────────────────────────────
  const enableTemplate = async (tmpl) => {
    setEnablingName(tmpl.name);
    try {
      // Clone the template with a fresh id so user can have multiple copies
      const payload = { ...tmpl, id: null, enabled: true };
      delete payload.id;
      const saved = await saveWorkflow(payload);
      await toggleWorkflow(saved.id, true);
      flash(`"${tmpl.name}" enabled — it will run on its schedule.`);
      refresh();
    } catch (e) {
      flash(`Failed: ${e.message}`);
    } finally {
      setEnablingName('');
    }
  };

  // ── Builder: React Flow state helpers ───────────────────────────────────────
  const onConnect = useCallback((params) => {
    setRfEdges(eds => addEdge({ ...params, animated: true, style: { stroke: 'var(--color-accent)', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--color-accent)' } }, eds));
    setDirty(true);
  }, [setRfEdges]);

  const onNodeClick = useCallback((_, node) => { setSelectedNodeId(node.id); }, []);

  const wfToRf = (wf) => {
    const nodes = (wf.nodes || []).map(n => {
      const ndef = nodeTypeDefs[n.type] || {};
      return {
        id: n.id, type: 'workflowNode',
        position: { x: n.x || 0, y: n.y || 0 },
        data: { label: n.name, nodeType: n.type, category: ndef.category || 'control', description: ndef.description?.substring(0, 60), config: n.config || {} },
      };
    });
    const edges = (wf.edges || []).map((e, i) => ({
      id: `e-${i}`, source: e.source, target: e.target,
      label: e.label || '', animated: true,
      style: { stroke: 'color-mix(in srgb, var(--color-accent) 50%, transparent)', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--color-accent)' },
      labelStyle: { fill: 'var(--color-text-muted)', fontSize: 10, fontWeight: 500 },
    }));
    return { nodes, edges };
  };

  const rfToWf = () => {
    const nodes = rfNodes.map(n => ({
      id: n.id, type: n.data.nodeType, name: n.data.label,
      config: n.data.config || {}, x: Math.round(n.position.x), y: Math.round(n.position.y),
    }));
    const edges = rfEdges.map(e => ({ source: e.source, target: e.target, label: e.label || '' }));
    return { id: wfId, name: wfName, nodes, edges, enabled: wfEnabled };
  };

  const openBuilderForNew = () => {
    setWfId(null); setWfName('New Workflow'); setWfEnabled(false);
    setRfNodes([]); setRfEdges([]); setDirty(true);
    setRunResult(null); setSelectedNodeId(null);
    setView('builder');
  };

  const openBuilderFromTemplate = (tmpl) => {
    setWfId(null); setWfName(tmpl.name); setWfEnabled(false);
    const { nodes, edges } = wfToRf(tmpl);
    setRfNodes(nodes); setRfEdges(edges);
    setDirty(true); setRunResult(null); setSelectedNodeId(null);
    setView('builder');
  };

  const openBuilderForWorkflow = async (id) => {
    const wf = await getWorkflow(id);
    setWfId(wf.id); setWfName(wf.name); setWfEnabled(wf.enabled || false);
    const { nodes, edges } = wfToRf(wf);
    setRfNodes(nodes); setRfEdges(edges);
    setDirty(false); setRunResult(null); setSelectedNodeId(null);
    setView('builder');
  };

  const handleSave = async () => {
    try {
      const wf = rfToWf();
      const res = await saveWorkflow(wf);
      setWfId(res.id); setDirty(false);
      flash('Saved');
      refresh();
    } catch (e) {
      flash(`Save failed: ${e.message}`);
    }
  };

  const handleRun = async () => {
    if (!wfId) { flash('Save the workflow first'); return; }
    flash('Running...');
    try { const res = await runWorkflow(wfId); setRunResult(res); flash(''); }
    catch (e) { flash(`Error: ${e.message}`); }
  };

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete workflow "${name}"?`)) return;
    try {
      await deleteWorkflow(id);
      flash('Deleted');
      refresh();
    } catch (e) {
      flash(`Failed: ${e.message}`);
    }
  };

  const handleToggleEnabled = async (id, next) => {
    try {
      await toggleWorkflow(id, next);
      flash(next ? 'Enabled' : 'Disabled');
      refresh();
    } catch (e) {
      flash(`Failed: ${e.message}`);
    }
  };

  // ── Node palette for builder ────────────────────────────────────────────────
  const categories = {};
  for (const [type, def] of Object.entries(nodeTypeDefs)) {
    const cat = def.category || 'control';
    if (!categories[cat]) categories[cat] = [];
    categories[cat].push({ type, ...def });
  }

  const addNode = (type) => {
    const ndef = nodeTypeDefs[type] || {};
    const config = {};
    for (const [k, v] of Object.entries(ndef.config || {})) config[k] = v.default ?? '';
    // crypto.randomUUID is available in every modern browser; fall back to
    // a random string if the context is non-secure (unlikely in our app).
    const id = `node-${
      (typeof crypto !== 'undefined' && crypto.randomUUID)
        ? crypto.randomUUID().slice(0, 8)
        : Math.random().toString(36).slice(2, 10)
    }`;
    setRfNodes(nds => [...nds, {
      id, type: 'workflowNode',
      position: { x: 200 + nds.length * 250, y: 200 + (nds.length % 3) * 80 },
      data: { label: ndef.name || type, nodeType: type, category: ndef.category || 'control', description: ndef.description?.substring(0, 60), config },
    }]);
    setSelectedNodeId(id); setDirty(true);
  };

  const removeNode = (nid) => {
    setRfNodes(nds => nds.filter(n => n.id !== nid));
    setRfEdges(eds => eds.filter(e => e.source !== nid && e.target !== nid));
    if (selectedNodeId === nid) setSelectedNodeId(null);
    setDirty(true);
  };

  const updateNodeData = (nid, updates) => {
    setRfNodes(nds => nds.map(n => n.id === nid ? { ...n, data: { ...n.data, ...updates } } : n));
    setDirty(true);
  };

  const selectedNode = rfNodes.find(n => n.id === selectedNodeId);

  // ── Render ──────────────────────────────────────────────────────────────────
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Workflows</h1>
          <p>Automations that run on a schedule, on triggers, or on demand</p>
        </div>
        {view !== 'builder' && (
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="btn-ghost" onClick={openBuilderForNew}>
              <Code2 size={14} /> Build custom
            </button>
          </div>
        )}
        {view === 'builder' && (
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="btn-ghost" onClick={() => setView('my')}>
              <ArrowLeft size={14} /> Back
            </button>
            <button className="btn-ghost" onClick={handleSave}>
              <Save size={14} /> {dirty ? 'Save *' : 'Save'}
            </button>
            {wfId && <button className="btn-primary" onClick={handleRun}><Play size={14} /> Run</button>}
          </div>
        )}
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: 'var(--color-info)' }}>{msg}</div>}

      {/* Tab bar (hidden in builder) */}
      {view !== 'builder' && (
        <div style={{ display: 'flex', gap: 6, padding: '0 24px 8px', borderBottom: '1px solid var(--color-surface-2)' }}>
          {[
            ['gallery', 'Templates', Sparkles],
            ['my', `My Workflows (${workflows.length})`, GitBranch],
            ['history', 'Run History', Clock],
          ].map(([key, label, Icon]) => (
            <button
              key={key}
              onClick={() => setView(key)}
              className={view === key ? 'btn-primary' : 'btn-ghost'}
              style={{ fontSize: 11 }}
            >
              <Icon size={12} /> {label}
            </button>
          ))}
        </div>
      )}

      {/* GALLERY */}
      {view === 'gallery' && (
        <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
          {/* How-to guide — first-timer onboarding. Dismissible & persisted. */}
          <WorkflowsGuide />

          {/* AI-assisted builder */}
          <div className="panel" style={{ padding: 16, marginBottom: 16, background: 'linear-gradient(135deg, var(--color-bg), var(--color-surface-2))', border: '1px solid color-mix(in srgb, var(--color-ok) 19%, transparent)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Sparkles size={16} color="var(--color-ok)" />
              <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>Describe an automation in plain English</span>
            </div>
            <p style={{ fontSize: 11, color: 'var(--color-text-muted)', margin: '0 0 10px' }}>
              e.g. <em>"Every Monday at 9am, post a Slack summary of last week's sales"</em> or
              <em> "When a new deal reaches proposal stage, create a follow-up task for me in 3 days"</em>
            </p>
            <div style={{ display: 'flex', gap: 6 }}>
              <input
                className="field-input"
                placeholder="Describe what you want..."
                value={nlPrompt}
                onChange={(e) => setNlPrompt(e.target.value)}
                onKeyDown={async (e) => {
                  if (e.key !== 'Enter' || !nlPrompt.trim() || nlBusy) return;
                  setNlBusy(true);
                  try {
                    const wf = await generateWorkflowFromText(nlPrompt);
                    openBuilderFromTemplate(wf);
                    setNlPrompt('');
                    flash('Generated — review and save.');
                  } catch (err) {
                    flash(`Failed: ${err.message}`);
                  }
                  setNlBusy(false);
                }}
                style={{ flex: 1, fontSize: 12 }}
                disabled={nlBusy}
              />
              <button
                className="btn-primary"
                disabled={nlBusy || !nlPrompt.trim()}
                onClick={async () => {
                  setNlBusy(true);
                  try {
                    const wf = await generateWorkflowFromText(nlPrompt);
                    openBuilderFromTemplate(wf);
                    setNlPrompt('');
                    flash('Generated — review and save.');
                  } catch (err) {
                    flash(`Failed: ${err.message}`);
                  }
                  setNlBusy(false);
                }}
              >
                {nlBusy ? 'Thinking...' : 'Generate'}
              </button>
            </div>
          </div>

          <p style={{ fontSize: 12, color: 'var(--color-text-dim)', marginBottom: 16 }}>
            Or pick a ready-made template. Click <strong style={{ color: 'var(--color-ok)' }}>Use this</strong> to turn one on with one click,
            or <strong style={{ color: 'var(--color-text)' }}>Customize</strong> to tweak it first.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
            {templates.map((t, i) => (
              <TemplateCard
                key={i}
                tmpl={t}
                onEnable={enableTemplate}
                onOpen={openBuilderFromTemplate}
              />
            ))}
            {enablingName && (
              <div className="panel" style={{ gridColumn: '1/-1', color: 'var(--color-info)', fontSize: 12 }}>
                Enabling "{enablingName}"...
              </div>
            )}
          </div>
        </div>
      )}

      {/* MY WORKFLOWS */}
      {view === 'my' && (
        <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
          {workflows.length === 0 ? (
            <EmptyState
              icon={GitBranch}
              title="No workflows yet"
              description="Enable a pre-built template in one click, or build a custom flow in the drag-and-drop editor."
              primaryLabel="Browse templates"
              onPrimary={() => setView('templates')}
              secondaryLabel="Build custom"
              onSecondary={() => setView('builder')}
            />
          ) : (
            <div style={{ display: 'grid', gap: 10 }}>
              {workflows.map(wf => (
                <div key={wf.id} className="panel" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--color-text)' }}>{wf.name}</span>
                      <span style={{
                        fontSize: 9, padding: '2px 8px', borderRadius: 10, fontWeight: 600,
                        background: wf.enabled ? 'color-mix(in srgb, var(--color-ok) 13%, transparent)' : 'var(--color-border-strong)',
                        color: wf.enabled ? 'var(--color-ok)' : 'var(--color-text-muted)',
                      }}>
                        {wf.enabled ? 'ON' : 'OFF'}
                      </span>
                    </div>
                    <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 2 }}>
                      {wf.nodes?.length || 0} steps
                      {wf.last_run && <> · last run: {wf.last_run.substring(0, 16)} ({wf.last_status})</>}
                      {wf.run_count > 0 && <> · runs: {wf.run_count}</>}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                    <button className="btn-ghost" onClick={() => handleToggleEnabled(wf.id, !wf.enabled)} title={wf.enabled ? 'Disable' : 'Enable'}>
                      <Power size={13} /> {wf.enabled ? 'Disable' : 'Enable'}
                    </button>
                    <button className="btn-ghost" onClick={() => openBuilderForWorkflow(wf.id)}>
                      <Edit3 size={13} /> Edit
                    </button>
                    <button className="btn-ghost" style={{ color: 'var(--color-err)' }} onClick={() => handleDelete(wf.id, wf.name)}>
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* HISTORY */}
      {view === 'history' && (
        <div style={{ flex: 1, overflow: 'auto', padding: 20 }}>
          {history.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-dim)', fontSize: 13 }}>No run history yet</div>
          ) : (
            <div className="table-panel">
              <div className="table-panel-header">Recent Runs</div>
              <table className="data-table">
                <thead><tr><th>Workflow</th><th>Status</th><th>Duration</th><th>Finished</th></tr></thead>
                <tbody>{history.map((h, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{h.workflow_name}</td>
                    <td style={{ color: h.status === 'success' ? 'var(--color-ok)' : 'var(--color-err)' }}>{h.status}</td>
                    <td>{h.duration_ms}ms</td>
                    <td>{h.finished_at?.substring(0, 16)}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* BUILDER (advanced) */}
      {view === 'builder' && (
        <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
          <div style={{ width: 220, borderRight: '1px solid var(--color-surface-2)', display: 'flex', flexDirection: 'column', overflow: 'hidden', flexShrink: 0 }}>
            <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
              <div className="conv-label">Add a step</div>
              {Object.entries(categories).map(([cat, nodes]) => (
                <div key={cat} style={{ marginBottom: 6 }}>
                  <div style={{ fontSize: 9, color: CAT_COLORS[cat], fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, padding: '4px 0', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span style={{ background: CAT_COLORS[cat], color: '#fff', padding: '1px 5px', borderRadius: 4, fontSize: 8 }}>{CAT_ICONS[cat]}</span>
                    {CAT_LABELS[cat] || cat}
                  </div>
                  {nodes.map(n => (
                    <button key={n.type} onClick={() => addNode(n.type)}
                      title={n.description}
                      style={{ display: 'block', width: '100%', textAlign: 'left', padding: '5px 8px', fontSize: 11, color: 'var(--color-text-muted)', background: 'transparent', border: 'none', cursor: 'pointer', borderRadius: 6 }}
                      onMouseOver={e => { e.target.style.background = 'var(--color-surface-2)'; e.target.style.color = 'white'; }}
                      onMouseOut={e => { e.target.style.background = 'transparent'; e.target.style.color = 'var(--color-text-muted)'; }}>
                      {n.name || n.type}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>

          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 16px', borderBottom: '1px solid var(--color-surface-2)' }}>
              <input value={wfName} onChange={e => { setWfName(e.target.value); setDirty(true); }}
                style={{ background: 'transparent', border: '1px solid var(--color-border-strong)', borderRadius: 6, padding: '4px 10px', color: 'white', fontSize: 13, fontWeight: 500, flex: 1, outline: 'none' }}
                placeholder="Workflow name" />
              {wfId && (
                <button className="btn-ghost" onClick={() => handleToggleEnabled(wfId, !wfEnabled).then(() => setWfEnabled(!wfEnabled))}>
                  <Power size={12} /> {wfEnabled ? 'Enabled' : 'Disabled'}
                </button>
              )}
            </div>

            {rfNodes.length === 0 ? (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', color: 'var(--color-text-dim)' }}>
                <Zap size={36} style={{ marginBottom: 12, opacity: 0.4 }} />
                <p style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>Empty workflow</p>
                <p style={{ fontSize: 12, textAlign: 'center' }}>Add steps from the left panel, connect them by dragging between handles.</p>
              </div>
            ) : (
              <div style={{ flex: 1 }}>
                <ReactFlow
                  nodes={rfNodes} edges={rfEdges}
                  onNodesChange={(...args) => { onNodesChange(...args); setDirty(true); }}
                  onEdgesChange={(...args) => { onEdgesChange(...args); setDirty(true); }}
                  onConnect={onConnect}
                  onNodeClick={onNodeClick}
                  onPaneClick={() => setSelectedNodeId(null)}
                  nodeTypes={nodeTypes}
                  fitView
                  style={{ background: 'var(--color-bg)' }}
                  defaultEdgeOptions={{ animated: true, style: { stroke: 'color-mix(in srgb, var(--color-accent) 50%, transparent)', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--color-accent)' } }}
                >
                  <Background color="var(--color-surface-2)" gap={20} size={1} />
                  <Controls showInteractive={false} style={{ background: 'var(--color-surface-2)', borderRadius: 8, border: '1px solid var(--color-border-strong)' }} />
                  <MiniMap nodeColor={(n) => CAT_COLORS[n.data?.category] || 'var(--color-text-dim)'} style={{ background: 'var(--color-surface-1)', border: '1px solid var(--color-surface-2)', borderRadius: 8 }} />
                </ReactFlow>
              </div>
            )}

            {runResult && (
              <div style={{ padding: '8px 16px', borderTop: '1px solid var(--color-surface-2)', background: 'var(--color-bg)', maxHeight: 150, overflow: 'auto' }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: runResult.status === 'success' ? 'var(--color-ok)' : 'var(--color-err)', marginBottom: 4 }}>
                  Run: {runResult.status?.toUpperCase()} — {runResult.duration_ms}ms
                </div>
                {runResult.steps?.map((s, i) => (
                  <div key={i} style={{ display: 'flex', gap: 10, fontSize: 10, padding: '2px 0', color: 'var(--color-text-muted)' }}>
                    <span style={{ minWidth: 100, fontWeight: 500 }}>{s.node_name}</span>
                    <span style={{ color: s.status === 'success' ? 'var(--color-ok)' : 'var(--color-err)', minWidth: 50 }}>{s.status}</span>
                    <span style={{ color: 'var(--color-text-dim)', minWidth: 50 }}>{s.duration_ms}ms</span>
                    <span style={{ color: 'var(--color-text-dim)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{String(s.output || '').substring(0, 100)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ width: 260, borderLeft: '1px solid var(--color-surface-2)', padding: 12, overflow: 'auto', flexShrink: 0 }}>
            {selectedNode ? (() => {
              const nd = selectedNode.data;
              const typeDef = nodeTypeDefs[nd.nodeType] || {};
              const color = CAT_COLORS[nd.category] || 'var(--color-text-dim)';
              return (
                <>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                    <span style={{ fontSize: 10, fontWeight: 700, color: '#fff', background: color, padding: '2px 7px', borderRadius: 6 }}>{CAT_ICONS[nd.category]}</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'white' }}>Step Settings</span>
                  </div>
                  <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginBottom: 8 }}>Type: {nd.nodeType}</div>

                  <label style={{ fontSize: 10, color: 'var(--color-text-dim)', display: 'block', marginBottom: 2 }}>Name</label>
                  <input className="field-input" value={nd.label} style={{ marginBottom: 10, fontSize: 12 }}
                    onChange={e => updateNodeData(selectedNode.id, { label: e.target.value })} />

                  {typeDef.description && (
                    <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginBottom: 10, padding: 8, background: 'var(--color-surface-1)', borderRadius: 6 }}>
                      {typeDef.description}
                    </div>
                  )}

                  {Object.entries(typeDef.config || {}).map(([key, def]) => (
                    <div key={key} style={{ marginBottom: 8 }}>
                      <label style={{ fontSize: 10, color: 'var(--color-text-dim)', display: 'block', marginBottom: 2 }}>{def.label || key}</label>
                      {def.type === 'select' ? (
                        <select className="field-select" style={{ width: '100%' }}
                          value={nd.config?.[key] ?? def.default ?? ''}
                          onChange={e => updateNodeData(selectedNode.id, { config: { ...nd.config, [key]: e.target.value } })}>
                          {(def.options || []).map(o => <option key={o} value={o}>{o}</option>)}
                        </select>
                      ) : def.type === 'boolean' ? (
                        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--color-text-muted)', cursor: 'pointer' }}>
                          <input type="checkbox" checked={!!nd.config?.[key]}
                            onChange={e => updateNodeData(selectedNode.id, { config: { ...nd.config, [key]: e.target.checked } })} />
                          {nd.config?.[key] ? 'Enabled' : 'Disabled'}
                        </label>
                      ) : def.type === 'number' ? (
                        <input type="number" className="field-input" style={{ fontSize: 12 }}
                          value={nd.config?.[key] ?? def.default ?? 0} min={def.min} max={def.max}
                          onChange={e => updateNodeData(selectedNode.id, { config: { ...nd.config, [key]: parseInt(e.target.value) || 0 } })} />
                      ) : def.type === 'textarea' ? (
                        <textarea className="field-input" style={{ fontSize: 11, minHeight: 70, resize: 'vertical' }}
                          value={nd.config?.[key] || ''}
                          onChange={e => updateNodeData(selectedNode.id, { config: { ...nd.config, [key]: e.target.value } })} />
                      ) : (
                        <input className="field-input" style={{ fontSize: 12 }}
                          value={nd.config?.[key] || ''}
                          onChange={e => updateNodeData(selectedNode.id, { config: { ...nd.config, [key]: e.target.value } })} />
                      )}
                    </div>
                  ))}

                  {typeDef.outputs?.length > 0 && (
                    <div style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 6, padding: 6, background: 'var(--color-surface-1)', borderRadius: 4 }}>
                      Outputs: {typeDef.outputs.join(', ')}
                    </div>
                  )}

                  <div style={{ borderTop: '1px solid var(--color-surface-2)', paddingTop: 10, marginTop: 10 }}>
                    <button className="btn-ghost" style={{ width: '100%', justifyContent: 'center', color: 'var(--color-err)' }}
                      onClick={() => removeNode(selectedNode.id)}>
                      <Trash2 size={13} /> Delete step
                    </button>
                  </div>
                </>
              );
            })() : (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'var(--color-text-dim)', textAlign: 'center', padding: 16 }}>
                <Check size={24} style={{ marginBottom: 8, opacity: 0.4 }} />
                <p style={{ fontSize: 12, fontWeight: 500, marginBottom: 4 }}>Step Inspector</p>
                <p style={{ fontSize: 11 }}>Click a step on the canvas to configure it.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
