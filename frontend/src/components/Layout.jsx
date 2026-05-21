import { useState, useEffect, useCallback, useRef } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Database, TrendingUp, FileText, Clock, Settings, Plus, Trash2, ChevronLeft, ChevronRight, GitBranch, Bell, LogOut, Terminal, Sun, Moon, Command, Briefcase, ChevronDown, Check, Users, CheckSquare, Receipt, FileType2, ShieldCheck, Brain, BarChart3, Shield, Activity, Search, Bot, Inbox, Plug, Sparkles, Mail } from 'lucide-react';
import { getHealth, getNotifications, markAllNotificationsRead, listBusinesses, createBusiness } from '../services/api';
import { markNotificationRead, deleteNotification, getOnboardingState } from '../services/onboarding';
import { approvalsPendingCount } from '../services/agent';
import { getUser, logout, getBusinesses, getBusinessId, switchBusiness, getCurrentBusiness } from '../services/auth';
import OnboardingWizard, { shouldShowOnboarding, markOnboardingSeen, clearOnboardingForBusiness } from './OnboardingWizard';
import CommandPalette from './CommandPalette';
import KeyboardShortcutsModal from './KeyboardShortcutsModal';
import TrialBanner from './TrialBanner';
import TrialPill from './TrialPill';
import { prefetchRoute, prefetchAllRoutesIdle } from '../services/routePrefetch';
import { prefetchData } from '../services/dataPrefetch';

// ── Sidebar information architecture ─────────────────────────────────────
// 3-tier disclosure so the daily UI doesn't read like an engineering org
// chart:
//
//   Tier 1 (daily): 7 high-traffic items the SMB owner uses every login.
//   Tier 2 (weekly): grouped under a quiet "More" label — power features
//     that aren't part of the daily flow but should stay one click away.
//   Tier 3 (admin): grouped under "Workspace" — settings, billing, help.
//     Most live INSIDE the new /settings hub page; the sidebar only shows
//     the top-level entry plus billing + help for direct access.
//
// Every existing route URL is preserved — only the visual grouping and a
// few labels change. Industry-aware terminology already runs through every
// page header via useTerm(), so renaming "CRM" → "Customers" here is the
// universal default for businesses without a specific industry override.
const NAV_PRIMARY = [
  { to: '/',                icon: LayoutDashboard, label: 'Home' },
  { to: '/inbox',           icon: Inbox,           label: 'Inbox',     badge: 'approvals' },
  { to: '/crm',             icon: Users,           label: 'Customers' },
  { to: '/tasks',           icon: CheckSquare,     label: 'Tasks' },
  { to: '/invoices',        icon: Receipt,         label: 'Invoices' },
  { to: '/documents',       icon: FileType2,       label: 'Documents' },
  { to: '/chat',            icon: MessageSquare,   label: 'Chat with AI' },
];

const NAV_MORE = [
  { to: '/agents',          icon: Bot,             label: 'AI Agents' },
  { to: '/workflows',       icon: GitBranch,       label: 'Workflows' },
  { to: '/reports',         icon: FileText,        label: 'Reports' },
  { to: '/analytics',       icon: TrendingUp,      label: 'Analytics' },
  { to: '/integrations',    icon: Plug,            label: 'Integrations' },
  { to: '/email-templates', icon: Mail,            label: 'Email templates' },
];

const NAV_WORKSPACE = [
  { to: '/settings',        icon: Settings,        label: 'Settings' },
  { to: '/pricing',         icon: Sparkles,        label: 'Plan & billing' },
];

const NAV_DEV = [
  { to: '/database',        icon: Database,        label: 'Database' },
  { to: '/sql',             icon: Terminal,        label: 'SQL Editor' },
  // What-If moved into Chat as the /whatif slash command. Direct route at
  // /whatif still works for legacy bookmarks.
];

// Items moved INTO the /settings hub (their URLs still work directly for
// muscle-memory + deep links — only the sidebar entry is gone).
// Documented here so future maintainers don't think they're missing.
//   - /team             → Settings → Workspace → Team
//   - /memory           → Settings → Account → Memory
//   - /security         → Settings → Privacy & Security → Security
//   - /audit            → Settings → Privacy & Security → Activity log
//   - /admin/metrics    → Settings → Workspace → Metrics
//   - /history          → Settings → Account → History
//   - /settings/privacy-mode → Settings → Privacy & Security → Privacy Mode

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
  // Hover-intent debounce for sidebar prefetch — a 250ms threshold filters
  // out "brushing past" the sidebar while still firing ahead of a real click
  // (humans take 300-500ms between hover and click). Prevents firing 20
  // route+data prefetches as the cursor drags over the nav column.
  const hoverTimerRef = useRef(null);
  const user = getUser();
  const navigate = useNavigate();
  const current = getCurrentBusiness();

  const onNavHover = useCallback((to) => {
    // Route chunks fire immediately — they're idempotent + de-duped and the
    // Vite compile is the slow part, so earlier is better.
    prefetchRoute(to);
    if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current);
    hoverTimerRef.current = setTimeout(() => prefetchData(to), 250);
  }, []);
  const onNavLeave = useCallback(() => {
    if (hoverTimerRef.current) {
      clearTimeout(hoverTimerRef.current);
      hoverTimerRef.current = null;
    }
  }, []);

  const reloadAll = useCallback(() => {
    getNotifications().then(setNotifData).catch(() => {});
    getHealth().then(setHealth).catch(() => {});
    approvalsPendingCount().then((d) => setPendingApprovals(d.pending_count || 0)).catch(() => {});
  }, []);

  // Warm the route JS chunks (Vite compile + transfer) in the background
  // after Layout mounts. This is local CPU + network work; doesn't touch
  // the API, so it's safe to fire eagerly.
  //
  // DATA prefetching is deliberately *not* eagerly scheduled here — firing
  // ~11 extra API calls right when the dashboard is making its own 10 calls
  // overloaded a backend with no connection pool (each request opened a
  // fresh PG connection ~150ms; the pool saturated, tier-2 endpoints sat in
  // queue for minutes). Data prefetch now fires on hover intent only — that
  // way it never overlaps with the cold-start API storm.
  useEffect(() => { prefetchAllRoutesIdle(); }, []);

  useEffect(() => {
    reloadAll();
    listBusinesses().then(setBusinessesState).catch(() => {});
    getOnboardingState().then((s) => {
      const profileDone = (s.steps || []).find(x => x.key === 'profile')?.done;
      if (!profileDone || (!s.skipped && !(s.all_done && s.celebrated))) {
        setShowOnboarding(true);
      }
    }).catch(() => {});
    const iv = setInterval(() => {
      getNotifications().then(setNotifData).catch(() => {});
      approvalsPendingCount().then((d) => setPendingApprovals(d.pending_count || 0)).catch(() => {});
    }, 15000);
    const onBizChange = (e) => {
      setCurrentBizId(e.detail);
      setBusinessesState(getBusinesses());
      reloadAll();
      getOnboardingState().then((s) => {
        const profileDone = (s.steps || []).find(x => x.key === 'profile')?.done;
        setShowOnboarding(!profileDone || (!s.skipped && !(s.all_done && s.celebrated)));
      }).catch(() => {});
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
      // A brand-new business hasn't been through the wizard. Clear the
      // per-business "done" flag (no-op if it wasn't there) and re-open
      // the wizard so the new workspace gets profiled + seeded the same
      // way the very first one did.
      clearOnboardingForBusiness(biz.id);
      setShowOnboarding(true);
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
        <div
          className="sidebar-logo"
          style={collapsed ? { padding: '12px 8px', justifyContent: 'center' } : undefined}
        >
          {/* Collapsed sidebar = 60px wide. The logo "N" + label + chevron
              don't fit; we hide the icon when collapsed and let the chevron
              be the full visible affordance, since clicking it is the only
              way back to the expanded view. */}
          {!collapsed && <div className="sidebar-logo-icon">N</div>}
          {!collapsed && <span>NexusAgent</span>}
          <button
            onClick={() => setCollapsed(!collapsed)}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={collapsed ? 'Expand' : 'Collapse'}
            style={{
              marginLeft: collapsed ? 0 : 'auto',
              background: 'none', border: 'none',
              color: 'var(--color-text-dim)',
              cursor: 'pointer',
              padding: 6,
              borderRadius: 'var(--r-md)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={16} />}
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
                {/* "+ New business" was removed intentionally: one
                    subscription = one business. A customer who needs a
                    second workspace is a second sale, not a free expansion.
                    If we ship an Agency tier later, reinstate this entry
                    behind a plan check. The modal + handleCreateBiz +
                    /api/businesses POST endpoint are kept intact for
                    that future path and for admin-tool scripts. */}
              </div>
            )}
          </div>
        )}

        {/* Always-visible trial countdown. Renders nothing for paid / free /
            expired accounts. Sits right under the business switcher so it's
            in the customer's eye-line every time they look at the sidebar. */}
        <TrialPill collapsed={collapsed} />

        <nav className="nav-section">
          {/* Tier 1 — daily, no group label (these are the obvious ones) */}
          {NAV_PRIMARY.map((item) => (
            <SidebarItem
              key={item.to} item={item} collapsed={collapsed}
              pendingApprovals={pendingApprovals}
              onHover={onNavHover} onLeave={onNavLeave}
            />
          ))}

          {/* Tier 2 — weekly tools. Group label visually separates without
              hiding. On collapsed sidebar the label disappears but the
              divider stays so the visual rhythm is preserved. */}
          <div className={`nav-group ${collapsed ? 'is-collapsed' : ''}`}>
            {!collapsed && <div className="nav-group-label">More</div>}
            {collapsed && <div className="nav-group-divider" />}
            {NAV_MORE.map((item) => (
              <SidebarItem
                key={item.to} item={item} collapsed={collapsed}
                pendingApprovals={pendingApprovals}
                onHover={onNavHover} onLeave={onNavLeave}
              />
            ))}
          </div>

          {/* Tier 3 — workspace admin. Settings + Plan & billing only;
              Team / Memory / Security / Privacy / Audit / Metrics / History
              live INSIDE the Settings hub page instead of cluttering the
              sidebar. Their direct URLs still work for deep links. */}
          <div className={`nav-group ${collapsed ? 'is-collapsed' : ''}`}>
            {!collapsed && <div className="nav-group-label">Workspace</div>}
            {collapsed && <div className="nav-group-divider" />}
            {NAV_WORKSPACE.map((item) => (
              <SidebarItem
                key={item.to} item={item} collapsed={collapsed}
                pendingApprovals={pendingApprovals}
                onHover={onNavHover} onLeave={onNavLeave}
              />
            ))}
          </div>

          {/* Dev mode — only when explicitly toggled. Power tools that the
              SMB owner should never see by default. */}
          {devMode && (
            <div className={`nav-group ${collapsed ? 'is-collapsed' : ''}`}>
              {!collapsed && <div className="nav-group-label">Developer</div>}
              {collapsed && <div className="nav-group-divider" />}
              {NAV_DEV.map((item) => (
                <SidebarItem
                  key={item.to} item={item} collapsed={collapsed}
                  pendingApprovals={pendingApprovals}
                  onHover={onNavHover} onLeave={onNavLeave}
                />
              ))}
            </div>
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

      {/* Notification panel — anchored to the bell at bottom-left of the
          sidebar so the click → panel visual relationship is obvious.
          Previously the bell sat bottom-left but the panel slid in from
          the right edge of the screen, which looked disconnected. */}
      {showNotifs && (
        <>
          {/* Click-outside backdrop. */}
          <div
            onClick={() => setShowNotifs(false)}
            style={{ position: 'fixed', inset: 0, zIndex: 99, background: 'transparent' }}
          />
          <div style={{
            position: 'fixed',
            bottom: 56,
            left: collapsed ? 64 : 14,
            width: 340,
            maxHeight: 'min(560px, 70vh)',
            background: 'var(--color-bg-elev)',
            border: '1px solid var(--color-border)',
            borderRadius: 12,
            zIndex: 100,
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 18px 48px rgba(0,0,0,0.45)',
          }}>
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
        </>
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

      {showOnboarding && <OnboardingWizard onClose={() => {
        // Persist "wizard done" in localStorage so subsequent route changes
        // (e.g. clicking "Invite teammates" in the welcome modal → /team)
        // do NOT re-open the wizard on the next page load. Before this,
        // shouldShowOnboarding() stayed true forever and every navigation
        // re-mounted the wizard, making post-setup buttons feel broken.
        markOnboardingSeen();
        setShowOnboarding(false);
        // PlanWelcomeModal listens for this event and replays any welcome
        // that was deferred while the wizard was up (e.g. the trial
        // celebration after a fresh signup).
        window.dispatchEvent(new CustomEvent('nexus-onboarding-closed'));
      }} />}

      <CommandPalette />
      <KeyboardShortcutsModal />

      {/* Main */}
      <main className="main-content">
        {/* Trial countdown — renders as a strip above the route content
            when status='trial'. Self-hides for paid + free users. */}
        <TrialBanner />
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


// ── SidebarItem ─────────────────────────────────────────────────────────
// Single nav row shared across all three sidebar tiers + dev mode. Pulled
// out so the rendering logic stays one place and group sections in Layout
// remain readable.
function SidebarItem({ item, collapsed, pendingApprovals, onHover, onLeave }) {
  const { to, icon: Icon, label, badge } = item;
  const count = badge === 'approvals' ? pendingApprovals : 0;
  return (
    <NavLink
      to={to}
      end={to === '/'}
      className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
      style={collapsed ? { justifyContent: 'center', padding: '10px' } : undefined}
      title={label}
      onMouseEnter={() => onHover(to)}
      onMouseLeave={onLeave}
      onFocus={() => onHover(to)}
      onBlur={onLeave}
    >
      <Icon size={18} />
      {!collapsed && <span style={{ flex: 1 }}>{label}</span>}
      {count > 0 && !collapsed && (
        <span style={{
          fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 10,
          background: 'var(--color-warn)', color: 'var(--color-bg)',
          minWidth: 18, textAlign: 'center',
        }}>{count}</span>
      )}
      {count > 0 && collapsed && (
        <span style={{
          position: 'absolute', top: 4, right: 4,
          width: 7, height: 7, borderRadius: '50%',
          background: 'var(--color-warn)',
        }} />
      )}
    </NavLink>
  );
}
