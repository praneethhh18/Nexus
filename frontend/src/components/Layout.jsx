import { useState, useEffect, useCallback, useRef } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Database, TrendingUp, FileText, Clock, Settings, Plus, Trash2, ChevronLeft, ChevronRight, GitBranch, Bell, LogOut, Terminal, Sun, Moon, Command, Briefcase, ChevronDown, Check, Users, CheckSquare, Receipt, FileType2, ShieldCheck, Brain, BarChart3, Shield, Activity, Search } from 'lucide-react';
import { getConversations, deleteConversation, getHealth, getNotifications, markAllNotificationsRead, listBusinesses, createBusiness } from '../services/api';
import { approvalsPendingCount } from '../services/agent';
import { getUser, logout, getBusinesses, getBusinessId, switchBusiness, getCurrentBusiness } from '../services/auth';
import OnboardingWizard, { shouldShowOnboarding } from './OnboardingWizard';
import CommandPalette from './CommandPalette';

const NAV_MAIN = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/crm', icon: Users, label: 'CRM' },
  { to: '/tasks', icon: CheckSquare, label: 'Tasks' },
  { to: '/invoices', icon: Receipt, label: 'Invoices' },
  { to: '/documents', icon: FileType2, label: 'Documents' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/workflows', icon: GitBranch, label: 'Workflows' },
  { to: '/approvals', icon: ShieldCheck, label: 'Approvals', badge: 'approvals' },
  { to: '/team', icon: Users, label: 'Team' },
  { to: '/memory', icon: Brain, label: 'Memory' },
  { to: '/security', icon: Shield, label: 'Security' },
  { to: '/audit', icon: Activity, label: 'Audit log' },
  { to: '/history', icon: Clock, label: 'History' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

const NAV_DEV = [
  { to: '/database', icon: Database, label: 'Database' },
  { to: '/sql', icon: Terminal, label: 'SQL Editor' },
  { to: '/whatif', icon: TrendingUp, label: 'What-If' },
];

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [health, setHealth] = useState(null);
  const [notifData, setNotifData] = useState({ notifications: [], unread_count: 0 });
  const [showNotifs, setShowNotifs] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('nexus_theme') || 'dark');
  const [businesses, setBusinessesState] = useState(getBusinesses());
  const [currentBizId, setCurrentBizId] = useState(getBusinessId());
  const [showBizMenu, setShowBizMenu] = useState(false);
  const [showNewBiz, setShowNewBiz] = useState(false);
  const [newBizName, setNewBizName] = useState('');
  const [newBizIndustry, setNewBizIndustry] = useState('');
  const [devMode, setDevMode] = useState(localStorage.getItem('nexus_dev_mode') === '1');
  const [showOnboarding, setShowOnboarding] = useState(shouldShowOnboarding());
  const [pendingApprovals, setPendingApprovals] = useState(0);
  const bizRef = useRef(null);
  const user = getUser();
  const navigate = useNavigate();
  const current = getCurrentBusiness();

  const reloadAll = useCallback(() => {
    getConversations().then(setConversations).catch(() => {});
    getNotifications().then(setNotifData).catch(() => {});
    getHealth().then(setHealth).catch(() => {});
    approvalsPendingCount().then((d) => setPendingApprovals(d.pending_count || 0)).catch(() => {});
  }, []);

  useEffect(() => {
    reloadAll();
    listBusinesses().then(setBusinessesState).catch(() => {});
    const iv = setInterval(() => {
      getConversations().then(setConversations).catch(() => {});
      getNotifications().then(setNotifData).catch(() => {});
      approvalsPendingCount().then((d) => setPendingApprovals(d.pending_count || 0)).catch(() => {});
    }, 15000);
    const onBizChange = (e) => {
      setCurrentBizId(e.detail);
      setBusinessesState(getBusinesses());
      reloadAll();
    };
    const onDevModeChange = () => {
      setDevMode(localStorage.getItem('nexus_dev_mode') === '1');
    };
    window.addEventListener('nexus-business-changed', onBizChange);
    window.addEventListener('nexus-devmode-changed', onDevModeChange);
    return () => {
      clearInterval(iv);
      window.removeEventListener('nexus-business-changed', onBizChange);
      window.removeEventListener('nexus-devmode-changed', onDevModeChange);
    };
  }, [reloadAll]);

  // Close biz menu on outside click
  useEffect(() => {
    const onClick = (e) => {
      if (bizRef.current && !bizRef.current.contains(e.target)) setShowBizMenu(false);
    };
    window.addEventListener('mousedown', onClick);
    return () => window.removeEventListener('mousedown', onClick);
  }, []);

  const handleSwitchBiz = (bizId) => {
    switchBusiness(bizId);
    setCurrentBizId(bizId);
    setShowBizMenu(false);
  };

  const handleCreateBiz = async (e) => {
    e.preventDefault();
    if (!newBizName.trim()) return;
    try {
      const biz = await createBusiness({ name: newBizName, industry: newBizIndustry });
      const fresh = await listBusinesses();
      setBusinessesState(fresh);
      switchBusiness(biz.id);
      setCurrentBizId(biz.id);
      setShowNewBiz(false);
      setNewBizName('');
      setNewBizIndustry('');
    } catch (err) {
      alert(`Failed to create business: ${err.message}`);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      // Ctrl+K is owned by the CommandPalette component
      // (it opens a global search overlay — more useful than "jump to chat")
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') { e.preventDefault(); navigate('/chat'); window.dispatchEvent(new Event('nexus-new-chat')); }
      if ((e.ctrlKey || e.metaKey) && e.key === 'd') { e.preventDefault(); navigate('/'); }
      if (e.key === 'Escape') { setShowNotifs(false); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [navigate]);

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('nexus_theme', next);
    document.documentElement.setAttribute('data-theme', next);
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    await deleteConversation(id).catch(() => {});
    setConversations(c => c.filter(x => x.conversation_id !== id));
  };

  const handleClearNotifs = async () => {
    await markAllNotificationsRead().catch(() => {});
    setNotifData(d => ({ ...d, unread_count: 0, notifications: d.notifications.map(n => ({ ...n, read: 1 })) }));
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

        {/* Business switcher */}
        {!collapsed && (
          <div ref={bizRef} style={{ padding: '8px 12px', borderBottom: '1px solid #1e293b', position: 'relative' }}>
            <button
              onClick={() => setShowBizMenu(v => !v)}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                padding: '8px 10px', background: '#111827', border: '1px solid #1f2937',
                borderRadius: 8, color: '#e2e8f0', cursor: 'pointer', fontSize: 12,
              }}
              title="Switch business"
            >
              <Briefcase size={14} style={{ color: '#22c55e', flexShrink: 0 }} />
              <span style={{ flex: 1, textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {current?.name || 'Select business'}
              </span>
              <ChevronDown size={12} style={{ color: '#64748b' }} />
            </button>

            {showBizMenu && (
              <div style={{
                position: 'absolute', top: 'calc(100% - 2px)', left: 12, right: 12, zIndex: 50,
                background: '#0c1222', border: '1px solid #1e293b', borderRadius: 8,
                boxShadow: '0 8px 24px rgba(0,0,0,0.4)', maxHeight: 280, overflow: 'auto',
              }}>
                {businesses.length === 0 && (
                  <div style={{ padding: 12, fontSize: 11, color: '#64748b' }}>No businesses yet</div>
                )}
                {businesses.map(b => (
                  <div
                    key={b.id}
                    onClick={() => handleSwitchBiz(b.id)}
                    style={{
                      padding: '8px 12px', cursor: 'pointer', fontSize: 12,
                      display: 'flex', alignItems: 'center', gap: 8,
                      background: b.id === currentBizId ? '#1e293b' : 'transparent',
                      color: '#e2e8f0',
                    }}
                    onMouseEnter={(e) => { if (b.id !== currentBizId) e.currentTarget.style.background = '#111827'; }}
                    onMouseLeave={(e) => { if (b.id !== currentBizId) e.currentTarget.style.background = 'transparent'; }}
                  >
                    <Briefcase size={12} style={{ color: '#64748b', flexShrink: 0 }} />
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.name}</span>
                    {b.id === currentBizId && <Check size={12} style={{ color: '#22c55e' }} />}
                  </div>
                ))}
                <div style={{ borderTop: '1px solid #1e293b' }}>
                  <div
                    onClick={() => { setShowBizMenu(false); setShowNewBiz(true); }}
                    style={{ padding: '8px 12px', cursor: 'pointer', fontSize: 12, color: '#22c55e', display: 'flex', alignItems: 'center', gap: 8 }}
                  >
                    <Plus size={12} /> New business
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        <nav className="nav-section">
          {NAV_MAIN.map(({ to, icon: Icon, label, badge }) => {
            const count = badge === 'approvals' ? pendingApprovals : 0;
            return (
              <NavLink key={to} to={to} end={to === '/'} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                style={collapsed ? { justifyContent: 'center', padding: '10px' } : {}} title={label}>
                <Icon size={18} />
                {!collapsed && <span style={{ flex: 1 }}>{label}</span>}
                {count > 0 && !collapsed && (
                  <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 10, background: '#f59e0b', color: '#0c1222', minWidth: 18, textAlign: 'center' }}>{count}</span>
                )}
                {count > 0 && collapsed && (
                  <span style={{ position: 'absolute', top: 4, right: 4, width: 7, height: 7, borderRadius: '50%', background: '#f59e0b' }} />
                )}
              </NavLink>
            );
          })}
          {devMode && (
            <>
              {!collapsed && (
                <div style={{ padding: '8px 12px 4px', fontSize: 9, color: '#475569', textTransform: 'uppercase', letterSpacing: 1 }}>
                  Developer
                </div>
              )}
              {NAV_DEV.map(({ to, icon: Icon, label }) => (
                <NavLink key={to} to={to} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                  style={collapsed ? { justifyContent: 'center', padding: '10px' } : {}} title={label}>
                  <Icon size={18} />
                  {!collapsed && <span>{label}</span>}
                </NavLink>
              ))}
            </>
          )}
        </nav>

        {/* Conversations */}
        {!collapsed && (
          <div className="conv-section hide-mobile">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 8px', marginBottom: 4 }}>
              <span className="conv-label">Chats</span>
              <button onClick={() => { navigate('/chat'); window.dispatchEvent(new Event('nexus-new-chat')); }}
                style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                <Plus size={14} />
              </button>
            </div>
            {conversations.slice(0, 15).map(c => (
              <div key={c.conversation_id} className="conv-item"
                onClick={() => { navigate('/chat'); window.dispatchEvent(new CustomEvent('nexus-load-conv', { detail: c.conversation_id })); }}>
                <MessageSquare size={12} style={{ opacity: 0.4, flexShrink: 0 }} />
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.title}</span>
                <button className="del" onClick={(e) => handleDelete(e, c.conversation_id)}>
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Bottom: user + status */}
        <div style={{ borderTop: '1px solid #1e293b', padding: collapsed ? '8px' : '8px 12px' }}>
          {/* Notification bell */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, justifyContent: collapsed ? 'center' : 'flex-start' }}>
            <button onClick={() => setShowNotifs(!showNotifs)} style={{ position: 'relative', background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 4 }}>
              <Bell size={16} />
              {notifData.unread_count > 0 && (
                <span style={{ position: 'absolute', top: -2, right: -4, width: 14, height: 14, borderRadius: '50%', background: '#ef4444', color: 'white', fontSize: 8, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {notifData.unread_count}
                </span>
              )}
            </button>
            {!collapsed && (
              <>
                <button onClick={toggleTheme} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 4 }}>
                  {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
                </button>
                <button onClick={logout} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', padding: 4 }} title="Logout">
                  <LogOut size={14} />
                </button>
              </>
            )}
          </div>

          {/* Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: collapsed ? 'center' : 'flex-start' }}>
            <div className={`status-dot ${health?.ollama?.online ? 'online' : 'offline'}`} />
            {!collapsed && <span style={{ fontSize: 10, color: '#475569' }}>{user?.name || 'User'}</span>}
          </div>
        </div>
      </aside>

      {/* Notification panel */}
      {showNotifs && (
        <div style={{ position: 'fixed', top: 0, right: 0, width: 340, height: '100vh', background: '#0c1222', borderLeft: '1px solid #1e293b', zIndex: 100, display: 'flex', flexDirection: 'column', boxShadow: '-4px 0 24px rgba(0,0,0,0.4)' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #1e293b', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: 'white' }}>Notifications</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={handleClearNotifs} style={{ fontSize: 11, color: '#64748b', background: 'none', border: 'none', cursor: 'pointer' }}>Mark all read</button>
              <button onClick={() => setShowNotifs(false)} style={{ fontSize: 16, color: '#64748b', background: 'none', border: 'none', cursor: 'pointer' }}>x</button>
            </div>
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
            {notifData.notifications.length === 0 ? (
              <p style={{ textAlign: 'center', padding: 40, color: '#475569', fontSize: 12 }}>No notifications</p>
            ) : notifData.notifications.map((n, i) => (
              <div key={i} style={{
                padding: '10px 12px', borderRadius: 8, marginBottom: 4, cursor: 'pointer',
                background: n.read ? 'transparent' : '#1e293b',
                borderLeft: `3px solid ${{ critical: '#ef4444', warning: '#f59e0b', success: '#22c55e', info: '#3b82f6' }[n.severity] || '#64748b'}`,
              }}>
                <p style={{ fontSize: 12, fontWeight: n.read ? 400 : 600, color: '#e2e8f0' }}>{n.title}</p>
                <p style={{ fontSize: 10, color: '#64748b', marginTop: 2 }}>{n.message}</p>
                <p style={{ fontSize: 9, color: '#475569', marginTop: 2 }}>{n.created_at?.substring(0, 16)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* New Business Modal */}
      {showNewBiz && (
        <div
          onClick={() => setShowNewBiz(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
        >
          <form
            onClick={(e) => e.stopPropagation()}
            onSubmit={handleCreateBiz}
            style={{ background: '#0c1222', border: '1px solid #1e293b', borderRadius: 12, padding: 24, width: 380, boxShadow: '0 16px 48px rgba(0,0,0,0.6)' }}
          >
            <h3 style={{ fontSize: 16, fontWeight: 600, color: '#e2e8f0', margin: '0 0 4px' }}>Create a new business</h3>
            <p style={{ fontSize: 11, color: '#64748b', margin: '0 0 16px' }}>Each business has isolated data, contacts, workflows, and reports.</p>
            <label style={{ display: 'block', fontSize: 11, color: '#94a3b8', marginBottom: 4 }}>Business name *</label>
            <input
              autoFocus
              value={newBizName}
              onChange={(e) => setNewBizName(e.target.value)}
              placeholder="e.g. Acme Corp"
              required
              maxLength={120}
              style={{ width: '100%', padding: '8px 10px', background: '#111827', border: '1px solid #1f2937', borderRadius: 6, color: '#e2e8f0', fontSize: 13, marginBottom: 12 }}
            />
            <label style={{ display: 'block', fontSize: 11, color: '#94a3b8', marginBottom: 4 }}>Industry (optional)</label>
            <input
              value={newBizIndustry}
              onChange={(e) => setNewBizIndustry(e.target.value)}
              placeholder="e.g. SaaS, Retail, Consulting"
              maxLength={80}
              style={{ width: '100%', padding: '8px 10px', background: '#111827', border: '1px solid #1f2937', borderRadius: 6, color: '#e2e8f0', fontSize: 13, marginBottom: 20 }}
            />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button type="button" onClick={() => setShowNewBiz(false)} style={{ padding: '6px 14px', fontSize: 12, background: 'transparent', border: '1px solid #1f2937', borderRadius: 6, color: '#94a3b8', cursor: 'pointer' }}>Cancel</button>
              <button type="submit" style={{ padding: '6px 14px', fontSize: 12, background: '#22c55e', border: 'none', borderRadius: 6, color: '#0c1222', fontWeight: 600, cursor: 'pointer' }}>Create</button>
            </div>
          </form>
        </div>
      )}

      {showOnboarding && <OnboardingWizard onClose={() => setShowOnboarding(false)} />}

      <CommandPalette />

      {/* Main */}
      <main className="main-content">
        <Outlet />
      </main>

      {/* Keyboard shortcut hint */}
      <div style={{ position: 'fixed', bottom: 8, right: 12, display: 'flex', gap: 8, opacity: 0.3 }}>
        <span style={{ fontSize: 9, color: '#475569' }}><Command size={9} style={{ display: 'inline', verticalAlign: 'middle' }} />+K Search</span>
        <span style={{ fontSize: 9, color: '#475569' }}><Command size={9} style={{ display: 'inline', verticalAlign: 'middle' }} />+N New chat</span>
        <span style={{ fontSize: 9, color: '#475569' }}><Command size={9} style={{ display: 'inline', verticalAlign: 'middle' }} />+D Dashboard</span>
      </div>
    </>
  );
}
