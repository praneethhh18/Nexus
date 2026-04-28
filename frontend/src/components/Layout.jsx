import { useState, useEffect, useCallback, useRef } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Database, TrendingUp, FileText, Clock, Settings, Plus, Trash2, ChevronLeft, ChevronRight, GitBranch, Bell, LogOut, Terminal, Sun, Moon, Command, Briefcase, ChevronDown, Check, Users, CheckSquare, Receipt, FileType2, ShieldCheck, Brain, BarChart3, Shield, Activity, Search, Bot, Inbox, Plug, Sparkles } from 'lucide-react';
import { getHealth, getNotifications, markAllNotificationsRead, listBusinesses, createBusiness } from '../services/api';
import { markNotificationRead, deleteNotification } from '../services/onboarding';
import { approvalsPendingCount } from '../services/agent';
import { getUser, logout, getBusinesses, getBusinessId, switchBusiness, getCurrentBusiness } from '../services/auth';
import OnboardingWizard, { shouldShowOnboarding } from './OnboardingWizard';
import CommandPalette from './CommandPalette';
import KeyboardShortcutsModal from './KeyboardShortcutsModal';

const NAV_MAIN = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/crm', icon: Users, label: 'CRM' },
  { to: '/tasks', icon: CheckSquare, label: 'Tasks' },
  { to: '/invoices', icon: Receipt, label: 'Invoices' },
  { to: '/documents', icon: FileType2, label: 'Documents' },
  { to: '/reports', icon: FileText, label: 'Reports' },
  { to: '/workflows', icon: GitBranch, label: 'Workflows' },
  { to: '/integrations', icon: Plug, label: 'Integrations' },
  { to: '/inbox', icon: Inbox, label: 'Inbox', badge: 'approvals' },
  { to: '/agents', icon: Bot, label: 'Agents' },
  { to: '/team', icon: Users, label: 'Team' },
  { to: '/memory', icon: Brain, label: 'Memory' },
  { to: '/security', icon: Shield, label: 'Security' },
  { to: '/audit', icon: Activity, label: 'Audit log' },
  { to: '/admin/metrics', icon: BarChart3, label: 'Metrics' },
  { to: '/history', icon: Clock, label: 'History' },
  { to: '/pricing', icon: Sparkles, label: 'Plan & billing' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

const NAV_DEV = [
  { to: '/database', icon: Database, label: 'Database' },
  { to: '/sql', icon: Terminal, label: 'SQL Editor' },
  { to: '/whatif', icon: TrendingUp, label: 'What-If' },
];

export default function Layout() {
  const [collapsed, setCollapsed] = useState(false);
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
    getNotifications().then(setNotifData).catch(() => {});
    getHealth().then(setHealth).catch(() => {});
    approvalsPendingCount().then((d) => setPendingApprovals(d.pending_count || 0)).catch(() => {});
  }, []);

  useEffect(() => {
    reloadAll();
    listBusinesses().then(setBusinessesState).catch(() => {});
    const iv = setInterval(() => {
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

  // Keyboard shortcuts — owned here. Cmd+K is handled by CommandPalette,
  // `?` is handled by KeyboardShortcutsModal. Everything else lives below.
  useEffect(() => {
    const handler = (e) => {
      const t = e.target;
      const typing = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);

      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        navigate('/chat');
        window.dispatchEvent(new Event('nexus-new-chat'));
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        navigate('/');
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        setCollapsed(c => !c);
      }
      if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        navigate('/chat');
        // Focus the chat input after the page mounts
        setTimeout(() => {
          const el = document.querySelector('textarea[placeholder*="sk" i], textarea[placeholder*="message" i], input[placeholder*="ask" i]');
          if (el) el.focus();
        }, 120);
      }
      if (e.key === 'Escape' && !typing) { setShowNotifs(false); }
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
          <button onClick={() => setCollapsed(!collapsed)} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer' }}>
            {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {/* Business switcher */}
        {!collapsed && (
          <div ref={bizRef} style={{ padding: '8px 12px', borderBottom: '1px solid var(--color-surface-2)', position: 'relative' }}>
            <button
              onClick={() => setShowBizMenu(v => !v)}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 8,
                padding: '8px 10px', background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)',
                borderRadius: 8, color: 'var(--color-text)', cursor: 'pointer', fontSize: 12,
              }}
              title="Switch business"
            >
              <Briefcase size={14} style={{ color: 'var(--color-ok)', flexShrink: 0 }} />
              <span style={{ flex: 1, textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {current?.name || 'Select business'}
              </span>
              <ChevronDown size={12} style={{ color: 'var(--color-text-dim)' }} />
            </button>

            {showBizMenu && (
              <div style={{
                position: 'absolute', top: 'calc(100% - 2px)', left: 12, right: 12, zIndex: 50,
                background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 8,
                boxShadow: '0 8px 24px rgba(0,0,0,0.4)', maxHeight: 280, overflow: 'auto',
              }}>
                {businesses.length === 0 && (
                  <div style={{ padding: 12, fontSize: 11, color: 'var(--color-text-dim)' }}>No businesses yet</div>
                )}
                {businesses.map(b => (
                  <div
                    key={b.id}
                    onClick={() => handleSwitchBiz(b.id)}
                    style={{
                      padding: '8px 12px', cursor: 'pointer', fontSize: 12,
                      display: 'flex', alignItems: 'center', gap: 8,
                      background: b.id === currentBizId ? 'var(--color-surface-2)' : 'transparent',
                      color: 'var(--color-text)',
                    }}
                    onMouseEnter={(e) => { if (b.id !== currentBizId) e.currentTarget.style.background = 'var(--color-bg)'; }}
                    onMouseLeave={(e) => { if (b.id !== currentBizId) e.currentTarget.style.background = 'transparent'; }}
                  >
                    <Briefcase size={12} style={{ color: 'var(--color-text-dim)', flexShrink: 0 }} />
                    <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{b.name}</span>
                    {b.id === currentBizId && <Check size={12} style={{ color: 'var(--color-ok)' }} />}
                  </div>
                ))}
                <div style={{ borderTop: '1px solid var(--color-surface-2)' }}>
                  <div
                    onClick={() => { setShowBizMenu(false); setShowNewBiz(true); }}
                    style={{ padding: '8px 12px', cursor: 'pointer', fontSize: 12, color: 'var(--color-ok)', display: 'flex', alignItems: 'center', gap: 8 }}
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
                  <span style={{ fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 10, background: 'var(--color-warn)', color: 'var(--color-bg)', minWidth: 18, textAlign: 'center' }}>{count}</span>
                )}
                {count > 0 && collapsed && (
                  <span style={{ position: 'absolute', top: 4, right: 4, width: 7, height: 7, borderRadius: '50%', background: 'var(--color-warn)' }} />
                )}
              </NavLink>
            );
          })}
          {devMode && (
            <>
              {!collapsed && (
                <div style={{ padding: '8px 12px 4px', fontSize: 9, color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 1 }}>
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

        {/* Conversations moved into the Chat page itself */}

        {/* Bottom: user + status */}
        <div style={{ borderTop: '1px solid var(--color-surface-2)', padding: collapsed ? '8px' : '8px 12px' }}>
          {/* Notification bell */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6, justifyContent: collapsed ? 'center' : 'flex-start' }}>
            <button onClick={() => setShowNotifs(!showNotifs)} style={{ position: 'relative', background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 4 }}>
              <Bell size={16} />
              {notifData.unread_count > 0 && (
                <span style={{ position: 'absolute', top: -2, right: -4, width: 14, height: 14, borderRadius: '50%', background: 'var(--color-err)', color: 'white', fontSize: 8, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {notifData.unread_count}
                </span>
              )}
            </button>
            {!collapsed && (
              <>
                <button onClick={toggleTheme} style={{ background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 4 }}>
                  {theme === 'dark' ? <Sun size={14} /> : <Moon size={14} />}
                </button>
                <button onClick={logout} style={{ marginLeft: 'auto', background: 'none', border: 'none', color: 'var(--color-text-dim)', cursor: 'pointer', padding: 4 }} title="Logout">
                  <LogOut size={14} />
                </button>
              </>
            )}
          </div>

          {/* Status */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, justifyContent: collapsed ? 'center' : 'flex-start' }}>
            <div className={`status-dot ${health?.ollama?.online ? 'online' : 'offline'}`} />
            {!collapsed && <span style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>{user?.name || 'User'}</span>}
          </div>
        </div>
      </aside>

      {/* Notification panel */}
      {showNotifs && (
        <div style={{ position: 'fixed', top: 0, right: 0, width: 340, height: '100vh', background: 'var(--color-bg)', borderLeft: '1px solid var(--color-surface-2)', zIndex: 100, display: 'flex', flexDirection: 'column', boxShadow: '-4px 0 24px rgba(0,0,0,0.4)' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-surface-2)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: 14, fontWeight: 600, color: 'white' }}>Notifications</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button onClick={handleClearNotifs} style={{ fontSize: 11, color: 'var(--color-text-dim)', background: 'none', border: 'none', cursor: 'pointer' }}>Mark all read</button>
              <button onClick={() => setShowNotifs(false)} style={{ fontSize: 16, color: 'var(--color-text-dim)', background: 'none', border: 'none', cursor: 'pointer' }}>x</button>
            </div>
          </div>
          <div style={{ flex: 1, overflow: 'auto', padding: 8 }}>
            {notifData.notifications.length === 0 ? (
              <p style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-dim)', fontSize: 12 }}>No notifications</p>
            ) : notifData.notifications.map((n) => {
              const markOne = async () => {
                await markNotificationRead(n.id).catch(() => {});
                setNotifData(d => ({
                  ...d,
                  unread_count: Math.max(0, (d.unread_count || 0) - (n.read ? 0 : 1)),
                  notifications: d.notifications.map(x => x.id === n.id ? { ...x, read: 1 } : x),
                }));
              };
              const removeOne = async (e) => {
                e.stopPropagation();
                await deleteNotification(n.id).catch(() => {});
                setNotifData(d => ({
                  ...d,
                  unread_count: Math.max(0, (d.unread_count || 0) - (n.read ? 0 : 1)),
                  notifications: d.notifications.filter(x => x.id !== n.id),
                }));
              };
              return (
                <div
                  key={n.id}
                  onClick={markOne}
                  style={{
                    padding: '10px 12px', borderRadius: 8, marginBottom: 4, cursor: 'pointer',
                    background: n.read ? 'transparent' : 'var(--color-surface-2)',
                    borderLeft: `3px solid ${{ critical: 'var(--color-err)', warning: 'var(--color-warn)', success: 'var(--color-ok)', info: 'var(--color-accent)' }[n.severity] || 'var(--color-text-dim)'}`,
                    position: 'relative',
                  }}
                >
                  <p style={{ fontSize: 12, fontWeight: n.read ? 400 : 600, color: 'var(--color-text)', paddingRight: 20 }}>{n.title}</p>
                  <p style={{ fontSize: 10, color: 'var(--color-text-dim)', marginTop: 2 }}>{n.message}</p>
                  <p style={{ fontSize: 9, color: 'var(--color-text-dim)', marginTop: 2 }}>{n.created_at?.substring(0, 16)}</p>
                  <button
                    onClick={removeOne}
                    title="Remove this notification"
                    style={{
                      position: 'absolute', top: 6, right: 6,
                      background: 'none', border: 'none', cursor: 'pointer',
                      color: 'var(--color-text-dim)', padding: 2, opacity: 0.6,
                    }}
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
              );
            })}
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
            style={{ background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 12, padding: 24, width: 380, boxShadow: '0 16px 48px rgba(0,0,0,0.6)' }}
          >
            <h3 style={{ fontSize: 16, fontWeight: 600, color: 'var(--color-text)', margin: '0 0 4px' }}>Create a new business</h3>
            <p style={{ fontSize: 11, color: 'var(--color-text-dim)', margin: '0 0 16px' }}>Each business has isolated data, contacts, workflows, and reports.</p>
            <label style={{ display: 'block', fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 4 }}>Business name *</label>
            <input
              autoFocus
              value={newBizName}
              onChange={(e) => setNewBizName(e.target.value)}
              placeholder="e.g. Acme Corp"
              required
              maxLength={120}
              style={{ width: '100%', padding: '8px 10px', background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 6, color: 'var(--color-text)', fontSize: 13, marginBottom: 12 }}
            />
            <label style={{ display: 'block', fontSize: 11, color: 'var(--color-text-muted)', marginBottom: 4 }}>Industry (optional)</label>
            <input
              value={newBizIndustry}
              onChange={(e) => setNewBizIndustry(e.target.value)}
              placeholder="e.g. SaaS, Retail, Consulting"
              maxLength={80}
              style={{ width: '100%', padding: '8px 10px', background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 6, color: 'var(--color-text)', fontSize: 13, marginBottom: 20 }}
            />
            <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
              <button type="button" onClick={() => setShowNewBiz(false)} style={{ padding: '6px 14px', fontSize: 12, background: 'transparent', border: '1px solid var(--color-surface-2)', borderRadius: 6, color: 'var(--color-text-muted)', cursor: 'pointer' }}>Cancel</button>
              <button type="submit" style={{ padding: '6px 14px', fontSize: 12, background: 'var(--color-ok)', border: 'none', borderRadius: 6, color: 'var(--color-bg)', fontWeight: 600, cursor: 'pointer' }}>Create</button>
            </div>
          </form>
        </div>
      )}

      {showOnboarding && <OnboardingWizard onClose={() => setShowOnboarding(false)} />}

      <CommandPalette />
      <KeyboardShortcutsModal />

      {/* Main */}
      <main className="main-content">
        <Outlet />
      </main>

      {/* Keyboard shortcut hint */}
      <div style={{ position: 'fixed', bottom: 8, right: 12, display: 'flex', gap: 8, opacity: 0.3 }}>
        <span style={{ fontSize: 9, color: 'var(--color-text-dim)' }}><Command size={9} style={{ display: 'inline', verticalAlign: 'middle' }} />+K Search</span>
        <span style={{ fontSize: 9, color: 'var(--color-text-dim)' }}><Command size={9} style={{ display: 'inline', verticalAlign: 'middle' }} />+N New chat</span>
        <span style={{ fontSize: 9, color: 'var(--color-text-dim)' }}><Command size={9} style={{ display: 'inline', verticalAlign: 'middle' }} />+D Dashboard</span>
        <span style={{ fontSize: 9, color: 'var(--color-text-dim)' }}>? Shortcuts</span>
      </div>
    </>
  );
}
