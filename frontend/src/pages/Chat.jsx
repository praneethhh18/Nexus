import { useState, useRef, useEffect } from 'react';
import { Send, Plus, Download, Sparkles, Mic, MicOff, Upload, BarChart3 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { sendMessage, getConversation, exportMarkdown } from '../services/api';

const TOOL_CLASS = { rag: 'tool-rag', sql: 'tool-sql', action: 'tool-action', report: 'tool-report', whatif: 'tool-whatif' };

const QUICK = [
  { label: 'Revenue by Region', query: 'Show me revenue by region' },
  { label: 'Company Policy', query: 'What does our company policy say about remote work?' },
  { label: 'Sales Report', query: 'Generate a sales performance report' },
  { label: 'What-If Analysis', query: 'What if revenue drops 20%?' },
];

// ── Chart Component ──────────────────────────────────────────────────────────
function DataChart({ sqlData }) {
  if (!sqlData?.data?.length || !sqlData?.columns?.length) return null;
  const cols = sqlData.columns;
  const data = sqlData.data.slice(0, 20);

  // Find a string column (x-axis) and a numeric column (y-axis)
  let xCol = null, yCol = null;
  for (const col of cols) {
    const val = data[0]?.[col];
    if (!xCol && typeof val === 'string') xCol = col;
    if (!yCol && typeof val === 'number') yCol = col;
  }
  if (!xCol) xCol = cols[0];
  if (!yCol) yCol = cols[cols.length > 1 ? 1 : 0];

  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
        <BarChart3 size={14} color="#3b82f6" />
        <span style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8' }}>Data ({sqlData.row_count} rows)</span>
      </div>
      {/* Bar chart using CSS */}
      <div style={{ background: '#0f172a', borderRadius: 8, padding: 12, border: '1px solid #1e293b' }}>
        {data.map((row, i) => {
          const label = String(row[xCol] || '').substring(0, 20);
          const val = Number(row[yCol]) || 0;
          const maxVal = Math.max(...data.map(r => Number(r[yCol]) || 0));
          const pct = maxVal > 0 ? (val / maxVal) * 100 : 0;
          return (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
              <span style={{ fontSize: 10, color: '#94a3b8', minWidth: 80, textAlign: 'right' }}>{label}</span>
              <div style={{ flex: 1, height: 16, background: '#1e293b', borderRadius: 4, overflow: 'hidden' }}>
                <div style={{ width: `${pct}%`, height: '100%', background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)', borderRadius: 4, transition: 'width 0.3s' }} />
              </div>
              <span style={{ fontSize: 10, color: '#64748b', minWidth: 60 }}>
                {typeof val === 'number' && val > 1000 ? `$${(val / 1000).toFixed(1)}k` : val}
              </span>
            </div>
          );
        })}
      </div>
      {/* Data table */}
      <details style={{ marginTop: 6 }}>
        <summary style={{ fontSize: 10, color: '#475569', cursor: 'pointer' }}>View raw data</summary>
        <div style={{ overflowX: 'auto', marginTop: 4 }}>
          <table className="data-table">
            <thead><tr>{cols.map(c => <th key={c}>{c}</th>)}</tr></thead>
            <tbody>{data.map((row, i) => (
              <tr key={i}>{cols.map(c => <td key={c}>{String(row[c] ?? '')}</td>)}</tr>
            ))}</tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [chartData, setChartData] = useState(null); // SQL data for charts
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [convId, setConvId] = useState(null);
  const [recording, setRecording] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const mediaRecRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  useEffect(() => {
    const onLoad = async (e) => {
      try { const data = await getConversation(e.detail); setMessages(data.messages || []); setConvId(e.detail); } catch {}
    };
    const onNew = () => { setMessages([]); setConvId(null); setChartData(null); inputRef.current?.focus(); };
    const onRerun = (e) => { send(e.detail); };
    window.addEventListener('nexus-load-conv', onLoad);
    window.addEventListener('nexus-new-chat', onNew);
    window.addEventListener('nexus-rerun', onRerun);
    return () => { window.removeEventListener('nexus-load-conv', onLoad); window.removeEventListener('nexus-new-chat', onNew); window.removeEventListener('nexus-rerun', onRerun); };
  }, []);

  // ── Voice Recording ────────────────────────────────────────────────────────
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      const chunks = [];
      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) chunks.push(e.data); };
      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setRecording(false);
        // Send to transcription API
        const form = new FormData();
        form.append('file', blob, 'recording.webm');
        try {
          const res = await fetch('/api/voice/transcribe', { method: 'POST', body: form });
          const data = await res.json();
          if (data.text) {
            setInput(data.text);
            inputRef.current?.focus();
          }
        } catch (err) {
          console.error('Transcription failed:', err);
        }
      };
      mediaRecRef.current = mediaRecorder;
      mediaRecorder.start();
      setRecording(true);
      // Auto-stop after 5 seconds
      setTimeout(() => { if (mediaRecorder.state === 'recording') mediaRecorder.stop(); }, 5000);
    } catch (err) {
      console.error('Mic access denied:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecRef.current?.state === 'recording') mediaRecRef.current.stop();
  };

  const send = async (text = input) => {
    if (!text.trim() || loading) return;
    const q = text.trim(); setInput('');
    const ts = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { role: 'user', content: q, tools_used: [], timestamp: ts }]);
    setLoading(true);
    try {
      const res = await sendMessage(q, convId);
      if (!convId && res.conversation_id) setConvId(res.conversation_id);
      setMessages(prev => [...prev, res.message]);
      // Store chart data if SQL results exist
      if (res.state?.sql_results?.data?.length) setChartData(res.state.sql_results);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}. Make sure the API server and Ollama are running.`, tools_used: [], timestamp: ts }]);
    }
    setLoading(false);
  };

  const doExport = async () => {
    try {
      const res = await exportMarkdown(messages);
      const blob = new Blob([res.markdown], { type: 'text/markdown' });
      const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = `nexus_chat_${Date.now()}.md`; a.click();
    } catch {}
  };

  // ── Document Upload ────────────────────────────────────────────────────────
  const handleDocUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    try {
      const res = await fetch('/api/knowledge/upload', { method: 'POST', body: form });
      const data = await res.json();
      if (data.chunks_added) {
        send(`I just uploaded ${file.name}. What's in this document?`);
      }
    } catch (err) {
      console.error('Upload failed:', err);
    }
    e.target.value = '';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div><h1>Chat</h1><p>Ask about your business data, documents, or operations</p></div>
        <div style={{ display: 'flex', gap: 6 }}>
          {/* Document upload button */}
          <label className="action-btn" style={{ cursor: 'pointer' }}>
            <Upload size={13} /> Upload Doc
            <input type="file" accept=".pdf,.txt,.docx" onChange={handleDocUpload} style={{ display: 'none' }} />
          </label>
          {messages.length > 0 && (
            <>
              <button className="action-btn" onClick={doExport}><Download size={13} /> Export</button>
              <button className="action-btn" onClick={() => { setMessages([]); setConvId(null); setChartData(null); }}><Plus size={13} /> New</button>
            </>
          )}
        </div>
      </div>

      {/* Messages + Chart sidebar */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Chat */}
        <div className="chat-area" style={{ flex: 1 }}>
          {messages.length === 0 && !loading && (
            <div className="welcome">
              <div className="welcome-icon"><Sparkles size={24} color="#60a5fa" /></div>
              <h2>Welcome to NexusAgent</h2>
              <p>Your AI business assistant. Ask about data, documents, generate reports, or run scenarios.</p>
              <div className="quick-grid">
                {QUICK.map((qa, i) => (
                  <button key={i} className="quick-btn" onClick={() => send(qa.query)}>
                    <div className="title">{qa.label}</div>
                    <div className="desc">{qa.query}</div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`msg-row ${msg.role === 'user' ? 'user' : ''}`}>
              {msg.role === 'assistant' && <div className="msg-avatar bot">N</div>}
              <div className={`msg-bubble ${msg.role === 'user' ? 'user' : 'bot'}`}>
                <div className="chat-markdown"><ReactMarkdown>{msg.content}</ReactMarkdown></div>
                {msg.tools_used?.length > 0 && (
                  <div className="msg-tools">
                    {msg.tools_used.map((t, j) => <span key={j} className={`tool-badge ${TOOL_CLASS[t] || ''}`}>{t.replace(/_/g, ' ')}</span>)}
                  </div>
                )}
                {msg.multi_agent && msg.agents_used?.length > 0 && (
                  <div style={{ marginTop: 6, fontSize: 10, color: '#a78bfa', background: '#8b5cf610', border: '1px solid #8b5cf620', borderRadius: 12, padding: '2px 8px', display: 'inline-block' }}>
                    Multi-Agent: {msg.agents_used.map(a => a.replace('Agent', '')).join(', ')}
                  </div>
                )}
                {msg.sources_used?.length > 0 && (
                  <div className="msg-sources">{msg.sources_used.map((s, j) => <div key={j} className="msg-source">{s}</div>)}</div>
                )}
                {msg.timestamp && <div className="msg-time">{msg.timestamp}</div>}
              </div>
              {msg.role === 'user' && <div className="msg-avatar human">U</div>}
            </div>
          ))}

          {loading && (
            <div className="msg-row">
              <div className="msg-avatar bot">N</div>
              <div className="msg-bubble bot">
                <div className="thinking">
                  <div className="thinking-dot" /><div className="thinking-dot" /><div className="thinking-dot" />
                  <span style={{ fontSize: 11, color: '#64748b', marginLeft: 6 }}>Thinking...</span>
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Right panel — Chart */}
        {chartData && (
          <div style={{ width: 320, borderLeft: '1px solid #1e293b', padding: 12, overflow: 'auto', flexShrink: 0 }}>
            <DataChart sqlData={chartData} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="chat-input-bar">
        <div className="chat-input-wrap">
          {/* Voice button */}
          <button onClick={recording ? stopRecording : startRecording}
            style={{
              padding: 6, borderRadius: 8, border: 'none', cursor: 'pointer', transition: 'all 0.15s',
              background: recording ? '#ef444420' : 'transparent',
              color: recording ? '#ef4444' : '#64748b',
            }}>
            {recording ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
          <input ref={inputRef} type="text" value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder={recording ? 'Listening... (5 sec)' : 'Ask about data, documents, or operations...'}
            disabled={loading} />
          <button className="send-btn" onClick={() => send()} disabled={loading || !input.trim()}>
            <Send size={15} />
          </button>
        </div>
        <div className="chat-footer">NexusAgent v2.0 &middot; 100% Local &middot; Zero API Cost</div>
      </div>
    </div>
  );
}
