import { useState, useEffect, useCallback } from 'react';
import { ReactFlow, Background, Controls, MiniMap, addEdge, useNodesState, useEdgesState, Handle, Position, MarkerType } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Play, Plus, Trash2, Power, Save, GitBranch, Zap } from 'lucide-react';
import { getWorkflows, getWorkflow, saveWorkflow, deleteWorkflow, toggleWorkflow, runWorkflow, getNodeTypes, getWorkflowTemplates, getWorkflowHistory } from '../services/api';

const CAT_COLORS = { trigger: '#2563eb', condition: '#7c3aed', data: '#16a34a', ai: '#ea580c', action: '#dc2626', control: '#475569' };
const CAT_ICONS = { trigger: 'T', condition: '?', data: 'D', ai: 'AI', action: 'A', control: 'C' };
const CAT_LABELS = { trigger: 'Triggers', condition: 'Conditions', data: 'Data', ai: 'AI', action: 'Actions', control: 'Control' };

// Custom node component for React Flow
function WorkflowNode({ data, selected }) {
  const color = CAT_COLORS[data.category] || '#475569';
  const icon = CAT_ICONS[data.category] || 'N';
  return (
    <div style={{
      padding: '10px 16px', borderRadius: 12, minWidth: 160,
      background: selected ? `${color}18` : '#1e293b',
      border: `2px solid ${selected ? color : '#334155'}`,
      boxShadow: selected ? `0 0 16px ${color}30` : '0 2px 8px #00000030',
      transition: 'all 0.15s',
    }}>
      <Handle type="target" position={Position.Left} style={{ background: color, width: 8, height: 8, border: '2px solid #0f172a' }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
        <span style={{ fontSize: 10, fontWeight: 700, color: '#fff', background: color, padding: '2px 7px', borderRadius: 6 }}>{icon}</span>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'white' }}>{data.label}</span>
      </div>
      <div style={{ fontSize: 10, color: '#64748b' }}>{data.nodeType}</div>
      {data.description && <div style={{ fontSize: 9, color: '#475569', marginTop: 3, maxWidth: 180 }}>{data.description}</div>}
      <Handle type="source" position={Position.Right} style={{ background: color, width: 8, height: 8, border: '2px solid #0f172a' }} />
    </div>
  );
}

const nodeTypes = { workflowNode: WorkflowNode };

export default function Workflows() {
  const [workflows, setWorkflows] = useState([]);
  const [nodeTypeDefs, setNodeTypeDefs] = useState({});
  const [templates, setTemplates] = useState([]);
  const [wfId, setWfId] = useState(null);
  const [wfName, setWfName] = useState('New Workflow');
  const [wfEnabled, setWfEnabled] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [selectedNodeId, setSelectedNodeId] = useState(null);
  const [runResult, setRunResult] = useState(null);
  const [tab, setTab] = useState('canvas');
  const [history, setHistory] = useState([]);
  const [msg, setMsg] = useState('');

  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    getWorkflows().then(setWorkflows).catch(() => {});
    getNodeTypes().then(setNodeTypeDefs).catch(() => {});
    getWorkflowTemplates().then(setTemplates).catch(() => {});
    getWorkflowHistory().then(setHistory).catch(() => {});
  }, []);

  const onConnect = useCallback((params) => {
    setRfEdges(eds => addEdge({ ...params, animated: true, style: { stroke: '#3b82f6', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: '#3b82f6' } }, eds));
    setDirty(true);
  }, [setRfEdges]);

  const onNodeClick = useCallback((_, node) => { setSelectedNodeId(node.id); }, []);

  // Convert workflow data to React Flow format
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
      style: { stroke: '#3b82f680', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#3b82f6' },
      labelStyle: { fill: '#94a3b8', fontSize: 10, fontWeight: 500 },
    }));
    return { nodes, edges };
  };

  // Convert React Flow back to workflow format
  const rfToWf = () => {
    const nodes = rfNodes.map(n => ({
      id: n.id, type: n.data.nodeType, name: n.data.label,
      config: n.data.config || {}, x: Math.round(n.position.x), y: Math.round(n.position.y),
    }));
    const edges = rfEdges.map(e => ({ source: e.source, target: e.target, label: e.label || '' }));
    return { id: wfId, name: wfName, nodes, edges, enabled: wfEnabled };
  };

  const loadWf = async (id) => {
    const wf = await getWorkflow(id);
    setWfId(wf.id); setWfName(wf.name); setWfEnabled(wf.enabled || false);
    const { nodes, edges } = wfToRf(wf);
    setRfNodes(nodes); setRfEdges(edges);
    setDirty(false); setRunResult(null); setSelectedNodeId(null); setTab('canvas');
  };

  const newWf = () => {
    setWfId(null); setWfName('New Workflow'); setWfEnabled(false);
    setRfNodes([]); setRfEdges([]); setDirty(true); setRunResult(null); setSelectedNodeId(null); setTab('canvas');
  };

  const loadTemplate = (tmpl) => {
    setWfId(null); setWfName(tmpl.name); setWfEnabled(false);
    const { nodes, edges } = wfToRf(tmpl);
    setRfNodes(nodes); setRfEdges(edges);
    setDirty(true); setTab('canvas');
  };

  const handleSave = async () => {
    const wf = rfToWf();
    const res = await saveWorkflow(wf);
    setWfId(res.id); setDirty(false);
    setMsg('Saved!'); setTimeout(() => setMsg(''), 2000);
    getWorkflows().then(setWorkflows);
  };

  const handleRun = async () => {
    if (!wfId) { setMsg('Save the workflow first'); return; }
    setMsg('Running...');
    try { const res = await runWorkflow(wfId); setRunResult(res); setMsg(''); }
    catch (e) { setMsg(`Error: ${e.message}`); }
  };

  const addNode = (type) => {
    const ndef = nodeTypeDefs[type] || {};
    const config = {};
    for (const [k, v] of Object.entries(ndef.config || {})) config[k] = v.default ?? '';
    const id = `node-${Date.now().toString(36)}`;
    const newNode = {
      id, type: 'workflowNode',
      position: { x: 200 + rfNodes.length * 250, y: 200 + (rfNodes.length % 3) * 80 },
      data: { label: ndef.name || type, nodeType: type, category: ndef.category || 'control', description: ndef.description?.substring(0, 60), config },
    };
    setRfNodes(nds => [...nds, newNode]);
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
  const categories = {};
  for (const [type, def] of Object.entries(nodeTypeDefs)) {
    const cat = def.category || 'control';
    if (!categories[cat]) categories[cat] = [];
    categories[cat].push({ type, ...def });
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>Workflow Automation</h1>
          <p>Drag nodes, connect them, and build powerful business automations</p>
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          <button className="btn-ghost" onClick={newWf}><Plus size={14} /> New</button>
          <button className="btn-ghost" onClick={handleSave}><Save size={14} /> {dirty ? 'Save *' : 'Save'}</button>
          {wfId && <button className="btn-primary" onClick={handleRun}><Play size={14} /> Run</button>}
        </div>
      </div>

      {msg && <div style={{ padding: '4px 24px', fontSize: 12, color: '#60a5fa' }}>{msg}</div>}

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Panel */}
        <div style={{ width: 220, borderRight: '1px solid #1e293b', display: 'flex', flexDirection: 'column', overflow: 'hidden', flexShrink: 0 }}>
          {/* Saved Workflows */}
          <div style={{ padding: 8, borderBottom: '1px solid #1e293b', maxHeight: 200, overflow: 'auto' }}>
            <div className="conv-label">Saved Workflows</div>
            {workflows.map(wf => (
              <div key={wf.id} className="conv-item" onClick={() => loadWf(wf.id)}
                style={wfId === wf.id ? { background: '#3b82f615', color: '#60a5fa' } : {}}>
                <GitBranch size={12} style={{ flexShrink: 0, opacity: 0.4 }} />
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 11 }}>{wf.name}</span>
                <span style={{ fontSize: 8, color: wf.enabled ? '#4ade80' : '#475569', fontWeight: 600 }}>{wf.enabled ? 'ON' : 'OFF'}</span>
              </div>
            ))}
            {workflows.length === 0 && <div style={{ padding: 8, fontSize: 10, color: '#475569' }}>No workflows yet</div>}
          </div>

          {/* Node Palette */}
          <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
            <div className="conv-label">Drag to Add</div>
            {Object.entries(categories).map(([cat, nodes]) => (
              <div key={cat} style={{ marginBottom: 6 }}>
                <div style={{ fontSize: 9, color: CAT_COLORS[cat], fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, padding: '4px 0', display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ background: CAT_COLORS[cat], color: '#fff', padding: '1px 5px', borderRadius: 4, fontSize: 8 }}>{CAT_ICONS[cat]}</span>
                  {CAT_LABELS[cat] || cat}
                </div>
                {nodes.map(n => (
                  <button key={n.type} onClick={() => addNode(n.type)}
                    title={n.description}
                    style={{ display: 'block', width: '100%', textAlign: 'left', padding: '5px 8px', fontSize: 11, color: '#94a3b8', background: 'transparent', border: 'none', cursor: 'pointer', borderRadius: 6, transition: 'all 0.1s' }}
                    onMouseOver={e => { e.target.style.background = '#1e293b'; e.target.style.color = 'white'; }}
                    onMouseOut={e => { e.target.style.background = 'transparent'; e.target.style.color = '#94a3b8'; }}>
                    {n.name || n.type}
                  </button>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Center Canvas */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          {/* Tabs */}
          <div style={{ display: 'flex', gap: 4, padding: '4px 8px', borderBottom: '1px solid #1e293b' }}>
            {['canvas', 'templates', 'history'].map(t => (
              <button key={t} onClick={() => setTab(t)} className={tab === t ? 'btn-primary' : 'btn-ghost'} style={{ fontSize: 10, padding: '3px 10px' }}>
                {t === 'canvas' ? 'Canvas' : t === 'templates' ? 'Templates' : 'History'}
              </button>
            ))}
            {wfName && tab === 'canvas' && (
              <input value={wfName} onChange={e => { setWfName(e.target.value); setDirty(true); }}
                style={{ marginLeft: 'auto', background: 'transparent', border: '1px solid #334155', borderRadius: 6, padding: '2px 8px', color: 'white', fontSize: 12, fontWeight: 500, width: 200, outline: 'none' }} />
            )}
          </div>

          {tab === 'canvas' ? (
            rfNodes.length === 0 && !wfId ? (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', color: '#475569' }}>
                <Zap size={36} style={{ marginBottom: 12, opacity: 0.4 }} />
                <p style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>Build Your Automation</p>
                <p style={{ fontSize: 12, maxWidth: 360, textAlign: 'center' }}>
                  Add nodes from the left panel, connect them by dragging between handles, and configure each step in the right panel.
                </p>
                <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
                  <button className="btn-primary" onClick={newWf}><Plus size={14} /> New Workflow</button>
                  <button className="btn-ghost" onClick={() => setTab('templates')}>Load Template</button>
                </div>
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
                  style={{ background: '#0a0e1a' }}
                  defaultEdgeOptions={{ animated: true, style: { stroke: '#3b82f680', strokeWidth: 2 }, markerEnd: { type: MarkerType.ArrowClosed, color: '#3b82f6' } }}
                >
                  <Background color="#1e293b" gap={20} size={1} />
                  <Controls showInteractive={false} style={{ background: '#1e293b', borderRadius: 8, border: '1px solid #334155' }} />
                  <MiniMap nodeColor={(n) => CAT_COLORS[n.data?.category] || '#475569'} style={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }} />
                </ReactFlow>
              </div>
            )
          ) : tab === 'templates' ? (
            <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
              <p style={{ fontSize: 13, color: '#94a3b8', marginBottom: 16 }}>Pre-built automations — click to load, then customize and save.</p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {templates.map((tmpl, i) => (
                  <div key={i} onClick={() => loadTemplate(tmpl)} className="panel" style={{ cursor: 'pointer', transition: 'all 0.15s', borderColor: '#334155' }}
                    onMouseOver={e => e.currentTarget.style.borderColor = '#3b82f640'}
                    onMouseOut={e => e.currentTarget.style.borderColor = '#334155'}>
                    <p style={{ fontSize: 13, fontWeight: 600, color: 'white', marginBottom: 4 }}>{tmpl.name}</p>
                    <p style={{ fontSize: 11, color: '#64748b', marginBottom: 6 }}>{tmpl.description}</p>
                    <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                      {tmpl.tags?.map((t, j) => <span key={j} style={{ fontSize: 9, padding: '1px 6px', borderRadius: 4, background: '#0f172a', color: '#64748b' }}>{t}</span>)}
                      <span style={{ fontSize: 9, color: '#475569', marginLeft: 'auto' }}>{tmpl.nodes?.length} nodes</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ flex: 1, overflow: 'auto', padding: 16 }}>
              {history.length === 0 ? (
                <div style={{ textAlign: 'center', padding: 40, color: '#475569', fontSize: 13 }}>No run history yet</div>
              ) : (
                <div className="table-panel">
                  <div className="table-panel-header">Run History</div>
                  <table className="data-table">
                    <thead><tr><th>Workflow</th><th>Status</th><th>Duration</th><th>Finished</th></tr></thead>
                    <tbody>{history.map((h, i) => (
                      <tr key={i}>
                        <td style={{ fontWeight: 500 }}>{h.workflow_name}</td>
                        <td style={{ color: h.status === 'success' ? '#4ade80' : '#f87171' }}>{h.status}</td>
                        <td>{h.duration_ms}ms</td>
                        <td>{h.finished_at?.substring(0, 16)}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Run Result Bar */}
          {runResult && (
            <div style={{ padding: '8px 16px', borderTop: '1px solid #1e293b', background: '#0c1222', maxHeight: 150, overflow: 'auto' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: runResult.status === 'success' ? '#4ade80' : '#f87171', marginBottom: 4 }}>
                Run: {runResult.status?.toUpperCase()} — {runResult.duration_ms}ms
              </div>
              {runResult.steps?.map((s, i) => (
                <div key={i} style={{ display: 'flex', gap: 10, fontSize: 10, padding: '2px 0', color: '#94a3b8' }}>
                  <span style={{ minWidth: 100, fontWeight: 500 }}>{s.node_name}</span>
                  <span style={{ color: s.status === 'success' ? '#4ade80' : '#f87171', minWidth: 50 }}>{s.status}</span>
                  <span style={{ color: '#475569', minWidth: 50 }}>{s.duration_ms}ms</span>
                  <span style={{ color: '#475569', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{String(s.output || '').substring(0, 100)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Panel - Node Inspector */}
        <div style={{ width: 260, borderLeft: '1px solid #1e293b', padding: 12, overflow: 'auto', flexShrink: 0 }}>
          {selectedNode ? (() => {
            const nd = selectedNode.data;
            const typeDef = nodeTypeDefs[nd.nodeType] || {};
            const color = CAT_COLORS[nd.category] || '#475569';
            return (
              <>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: '#fff', background: color, padding: '2px 7px', borderRadius: 6 }}>{CAT_ICONS[nd.category]}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, color: 'white' }}>Node Config</span>
                </div>
                <div style={{ fontSize: 10, color: '#475569', marginBottom: 8 }}>Type: {nd.nodeType}</div>

                {/* Name */}
                <label style={{ fontSize: 10, color: '#64748b', display: 'block', marginBottom: 2 }}>Name</label>
                <input className="field-input" value={nd.label} style={{ marginBottom: 10, fontSize: 12 }}
                  onChange={e => updateNodeData(selectedNode.id, { label: e.target.value })} />

                {/* Description */}
                {typeDef.description && (
                  <div style={{ fontSize: 10, color: '#475569', marginBottom: 10, padding: 8, background: '#0f172a', borderRadius: 6 }}>
                    {typeDef.description}
                  </div>
                )}

                {/* Config fields */}
                {Object.entries(typeDef.config || {}).map(([key, def]) => (
                  <div key={key} style={{ marginBottom: 8 }}>
                    <label style={{ fontSize: 10, color: '#64748b', display: 'block', marginBottom: 2 }}>{def.label || key}</label>
                    {def.type === 'select' ? (
                      <select className="field-select" style={{ width: '100%' }}
                        value={nd.config?.[key] ?? def.default ?? ''}
                        onChange={e => updateNodeData(selectedNode.id, { config: { ...nd.config, [key]: e.target.value } })}>
                        {(def.options || []).map(o => <option key={o} value={o}>{o}</option>)}
                      </select>
                    ) : def.type === 'bool' ? (
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#94a3b8', cursor: 'pointer' }}>
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
                    {def.help && <div style={{ fontSize: 9, color: '#475569', marginTop: 1 }}>{def.help}</div>}
                  </div>
                ))}

                {/* Outputs info */}
                {typeDef.outputs?.length > 0 && (
                  <div style={{ fontSize: 10, color: '#475569', marginTop: 6, padding: 6, background: '#0f172a', borderRadius: 4 }}>
                    Outputs: {typeDef.outputs.join(', ')}
                  </div>
                )}

                <div style={{ borderTop: '1px solid #1e293b', paddingTop: 10, marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <button className="btn-ghost" style={{ width: '100%', justifyContent: 'center', color: '#f87171' }}
                    onClick={() => removeNode(selectedNode.id)}>
                    <Trash2 size={13} /> Delete Node
                  </button>
                  {wfId && (
                    <button className="btn-ghost" style={{ width: '100%', justifyContent: 'center' }}
                      onClick={async () => { await toggleWorkflow(wfId, !wfEnabled); setWfEnabled(!wfEnabled); getWorkflows().then(setWorkflows); }}>
                      <Power size={13} /> {wfEnabled ? 'Disable' : 'Enable'} Workflow
                    </button>
                  )}
                </div>
              </>
            );
          })() : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569', textAlign: 'center', padding: 16 }}>
              <GitBranch size={24} style={{ marginBottom: 8, opacity: 0.4 }} />
              <p style={{ fontSize: 12, fontWeight: 500, marginBottom: 4 }}>Node Inspector</p>
              <p style={{ fontSize: 11 }}>Click a node on the canvas to configure it. Connect nodes by dragging from one handle to another.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
