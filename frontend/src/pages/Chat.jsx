import { useState, useRef, useEffect } from 'react';
import { Send, Plus, Download, Sparkles } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { sendMessage, getConversation, exportMarkdown } from '../services/api';

const TOOL_CLASS = { rag: 'tool-rag', sql: 'tool-sql', action: 'tool-action', report: 'tool-report', whatif: 'tool-whatif' };

const QUICK = [
  { label: 'Revenue by Region', query: 'Show me revenue by region' },
  { label: 'Company Policy', query: 'What does our company policy say about remote work?' },
  { label: 'Sales Report', query: 'Generate a sales performance report' },
  { label: 'What-If Analysis', query: 'What if revenue drops 20%?' },
];

export default function Chat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [convId, setConvId] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, loading]);

  useEffect(() => {
    const onLoad = async (e) => {
      try { const data = await getConversation(e.detail); setMessages(data.messages || []); setConvId(e.detail); } catch {}
    };
    const onNew = () => { setMessages([]); setConvId(null); inputRef.current?.focus(); };
    window.addEventListener('nexus-load-conv', onLoad);
    window.addEventListener('nexus-new-chat', onNew);
    return () => { window.removeEventListener('nexus-load-conv', onLoad); window.removeEventListener('nexus-new-chat', onNew); };
  }, []);

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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div><h1>Chat</h1><p>Ask about your business data, documents, or operations</p></div>
        {messages.length > 0 && (
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="action-btn" onClick={doExport}><Download size={13} /> Export</button>
            <button className="action-btn" onClick={() => { setMessages([]); setConvId(null); }}><Plus size={13} /> New</button>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="chat-area">
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

      {/* Input */}
      <div className="chat-input-bar">
        <div className="chat-input-wrap">
          <input ref={inputRef} type="text" value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask about data, documents, or operations..." disabled={loading} />
          <button className="send-btn" onClick={() => send()} disabled={loading || !input.trim()}>
            <Send size={15} />
          </button>
        </div>
        <div className="chat-footer">NexusAgent v2.0 &middot; 100% Local &middot; Zero API Cost</div>
      </div>
    </div>
  );
}
