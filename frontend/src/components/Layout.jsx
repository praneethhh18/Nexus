import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { MessageSquare, Database, TrendingUp, FileText, Clock, Settings, Plus, Trash2, ChevronLeft, ChevronRight } from 'lucide-react';
import { getConversations, deleteConversation, getHealth } from '../services/api';

const NAV = [
  { to: '/', icon: MessageSquare, label: 'Chat' },
  { to: '/database', icon: Database, label: 'Database' },
  { to: '/whatif', icon: TrendingUp, label: 'What-If' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/history', icon: Clock, label: 'History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [health, setHealth] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    getConversations().then(setConversations).catch(() => {});
    getHealth().then(setHealth).catch(() => {});
    const iv = setInterval(() => {
      getConversations().then(setConversations).catch(() => {});
    }, 10000);
    return () => clearInterval(iv);
  }, []);

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    await deleteConversation(id).catch(() => {});
    setConversations(c => c.filter(x => x.conversation_id !== id));
  };

  return (
    <>
      {/* Sidebar */}
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon">N</div>
          {!collapsed && <span>NexusAgent</span>}
          <button onClick={() => setCollapsed(!collapsed)} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        <nav className="nav-section">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              style={collapsed ? { justifyContent: 'center', padding: '10px' } : {}}>
              <Icon size={18} />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        {!collapsed && (
          <div className="conv-section hide-mobile">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 8px', marginBottom: 4 }}>
              <span className="conv-label">Conversations</span>
              <button onClick={() => { navigate('/'); window.dispatchEvent(new Event('nexus-new-chat')); }}
                style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                <Plus size={14} />
              </button>
            </div>
            {conversations.map(c => (
              <div key={c.conversation_id} className="conv-item"
                onClick={() => { navigate('/'); window.dispatchEvent(new CustomEvent('nexus-load-conv', { detail: c.conversation_id })); }}>
                <MessageSquare size={12} style={{ opacity: 0.4, flexShrink: 0 }} />
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.title}</span>
                <button className="del" onClick={(e) => handleDelete(e, c.conversation_id)}>
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
            {conversations.length === 0 && (
              <div style={{ padding: '8px', fontSize: 11, color: '#475569' }}>No conversations yet</div>
            )}
          </div>
        )}

        <div className="status-bar">
          <div className={`status-dot ${health?.ollama?.online ? 'online' : 'offline'}`} />
          {!collapsed && (
            <span style={{ fontSize: 11, color: '#64748b' }}>
              {health?.ollama?.online ? 'Ollama Online' : 'Offline'}
            </span>
          )}
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        <Outlet />
      </main>
    </>
  );
}
