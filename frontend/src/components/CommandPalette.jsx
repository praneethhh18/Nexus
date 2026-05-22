/**
 * Global search command palette, opens with Ctrl+K / Cmd+K from anywhere.
 * Searches across contacts, companies, deals, tasks, invoices, documents,
 * memory, and recent conversations. Keyboard navigable.
 *
 * Slash commands (typed at start): /call /wa /email /task /invoice /lead
 *  /outreach /agents /agent <name>  → run a quick action or jump to a page.
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, User, Building2, Briefcase, CheckSquare, Receipt, FileType2, Brain, MessageSquare, Phone, Mail, Plus, Send, Bot, Zap } from 'lucide-react';
import { globalSearch } from '../services/security';

const KIND_META = {
  contact:      { icon: User,         color: 'var(--color-info)', label: 'Contact' },
  company:      { icon: Building2,    color: '#a78bfa', label: 'Company' },
  deal:         { icon: Briefcase,    color: 'var(--color-warn)', label: 'Deal' },
  task:         { icon: CheckSquare,  color: 'var(--color-ok)', label: 'Task' },
  invoice:      { icon: Receipt,      color: 'var(--color-info)', label: 'Invoice' },
  document:     { icon: FileType2,    color: '#a78bfa', label: 'Document' },
  memory:       { icon: Brain,        color: 'var(--color-warn)', label: 'Memory' },
  conversation: { icon: MessageSquare, color: 'var(--color-text-dim)', label: 'Chat' },
  command:      { icon: Zap,          color: 'var(--color-warn)', label: 'Quick action' },
};

// Slash commands the palette recognises. Each entry produces a synthetic
// search-result item the user can fire with Enter, same nav model as a real
// search hit, no parallel UI to maintain.
const COMMANDS = [
  { trigger: '/call',     icon: Phone,        title: 'Call …',          description: 'Vox: outbound voice call to a contact', route: '/crm?action=call' },
  { trigger: '/wa',       icon: MessageSquare, title: 'WhatsApp …',      description: 'Open WhatsApp chat with a contact',     route: '/crm?action=wa' },
  { trigger: '/email',    icon: Mail,         title: 'Email …',         description: 'Compose an email to a contact',         route: '/crm?action=email' },
  { trigger: '/task',     icon: Plus,         title: 'New task',        description: 'Create a task',                          route: '/tasks?new=1' },
  { trigger: '/invoice',  icon: Receipt,      title: 'New invoice',     description: 'Draft an invoice',                       route: '/invoices?new=1' },
  { trigger: '/lead',     icon: Search,       title: 'Find leads',      description: 'Run Lead Hunter (find new prospects)',  route: '/agents?focus=lead-hunter' },
  { trigger: '/outreach', icon: Send,         title: 'Run outreach',    description: 'Bulk message a contact segment',        route: '/agents?focus=outreach' },
  { trigger: '/agents',   icon: Bot,          title: 'Open Agents',     description: 'Manage your custom agents',              route: '/agents' },
  { trigger: '/agent',    icon: Bot,          title: 'New custom agent', description: 'Define a new scheduled agent',         route: '/agents?new=1' },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef(null);
  const navigate = useNavigate();

  // Hotkey handler, Ctrl+K / Cmd+K
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setOpen((v) => !v);
      }
      if (e.key === 'Escape' && open) {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open]);

  // Reset & focus when opening
  useEffect(() => {
    if (open) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setQuery('');
      setGroups([]);
      setSelectedIdx(0);
      setTimeout(() => inputRef.current?.focus(), 10);
    }
  }, [open]);

  // Debounced search, handles both slash commands and free-text search
  useEffect(() => {
    if (!open) return;
    const q = query.trim();

    // Slash commands take precedence, they don't need a 2-char minimum.
    if (q.startsWith('/')) {
      const matches = COMMANDS
        .filter((c) => c.trigger.startsWith(q.toLowerCase()) || c.trigger.startsWith('/' + q.toLowerCase().slice(1)))
        .map((c) => ({
          id:       c.trigger,
          title:    c.title,
          subtitle: `${c.trigger} · ${c.description}`,
          route:    c.route,
          _command: c,
        }));
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setGroups(matches.length ? [{ kind: 'command', items: matches }] : []);
      setSelectedIdx(0);
      return;
    }

    if (q.length < 2) {
      // Show all commands as a starting menu when palette is empty
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setGroups([{
        kind: 'command',
        items: COMMANDS.map((c) => ({
          id:       c.trigger,
          title:    c.title,
          subtitle: `${c.trigger} · ${c.description}`,
          route:    c.route,
          _command: c,
        })),
      }]);
      return;
    }

    const t = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await globalSearch(q, 6);
        setGroups(res.groups || []);
        setSelectedIdx(0);
      } catch {}
      setLoading(false);
    }, 180);
    return () => clearTimeout(t);
  }, [query, open]);

  // Flat list for keyboard navigation
  const flatItems = groups.flatMap((g) => g.items.map((it) => ({ ...it, _kind: g.kind })));

  const activate = useCallback((item) => {
    if (!item) return;
    navigate(item.route);
    setOpen(false);
  }, [navigate]);

  const onKeyDown = (e) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIdx((i) => Math.min(i + 1, flatItems.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIdx((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      activate(flatItems[selectedIdx]);
    }
  };

  if (!open) return null;

  let flatIdx = -1;

  return (
    <div
      onClick={() => setOpen(false)}
      style={{
        position: 'fixed', inset: 0, zIndex: 400,
        background: 'rgba(0,0,0,0.55)',
        display: 'flex', alignItems: 'flex-start', justifyContent: 'center',
        paddingTop: 90,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 600, maxWidth: '92vw', maxHeight: '70vh',
          background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)', borderRadius: 12,
          boxShadow: '0 24px 80px rgba(0,0,0,0.7)',
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', borderBottom: '1px solid var(--color-surface-2)' }}>
          <Search size={16} color="var(--color-info)" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Search contacts, deals, tasks, invoices, documents, memory..."
            style={{
              flex: 1, background: 'transparent', border: 'none', outline: 'none',
              color: 'var(--color-text)', fontSize: 15,
            }}
          />
          <span style={{ fontSize: 10, color: 'var(--color-text-dim)', padding: '2px 6px', border: '1px solid var(--color-border-strong)', borderRadius: 4 }}>ESC</span>
        </div>

        <div style={{ flex: 1, overflow: 'auto' }}>
          {query.trim().length < 2 && groups.length === 0 ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-dim)', fontSize: 12 }}>
              Type 2+ chars to search · or start with <code style={{ background: 'var(--color-surface-2)', padding: '1px 4px', borderRadius: 3 }}>/</code> for quick actions.
            </div>
          ) : loading && groups.length === 0 ? (
            <div style={{ padding: 24, textAlign: 'center', color: 'var(--color-text-dim)', fontSize: 12 }}>Searching…</div>
          ) : groups.length === 0 ? (
            <div style={{ padding: 24, textAlign: 'center', color: 'var(--color-text-dim)', fontSize: 12 }}>
              No matches for "<strong style={{ color: 'var(--color-text-muted)' }}>{query}</strong>"
            </div>
          ) : (
            groups.map((g) => {
              const meta = KIND_META[g.kind] || { icon: Search, color: 'var(--color-text-dim)', label: g.kind };
              const Icon = meta.icon;
              return (
                <div key={g.kind}>
                  <div style={{
                    padding: '8px 16px', fontSize: 10, fontWeight: 700,
                    color: 'var(--color-text-dim)', textTransform: 'uppercase', letterSpacing: 1,
                    background: 'var(--color-bg)',
                  }}>
                    {meta.label}
                  </div>
                  {g.items.map((item) => {
                    flatIdx += 1;
                    const isActive = flatIdx === selectedIdx;
                    return (
                      <div
                        key={`${g.kind}-${item.id}`}
                        onMouseEnter={() => setSelectedIdx(flatIdx)}
                        onClick={() => activate(item)}
                        style={{
                          display: 'flex', alignItems: 'center', gap: 12,
                          padding: '10px 16px', cursor: 'pointer',
                          background: isActive ? 'var(--color-surface-2)' : 'transparent',
                          borderLeft: `3px solid ${isActive ? meta.color : 'transparent'}`,
                        }}
                      >
                        <Icon size={14} color={meta.color} style={{ flexShrink: 0 }} />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{
                            fontSize: 13, color: 'var(--color-text)',
                            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                          }}>{item.title}</div>
                          {item.subtitle && (
                            <div style={{ fontSize: 10, color: 'var(--color-text-dim)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {item.subtitle}
                            </div>
                          )}
                        </div>
                        {isActive && (
                          <span style={{ fontSize: 10, color: 'var(--color-text-dim)' }}>↵</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })
          )}
        </div>

        <div style={{ padding: '6px 12px', borderTop: '1px solid var(--color-surface-2)', fontSize: 10, color: 'var(--color-text-dim)', display: 'flex', gap: 12 }}>
          <span>↑ ↓ navigate</span>
          <span>↵ open</span>
          <span>esc close</span>
          <span style={{ marginLeft: 'auto' }}>⌘/Ctrl+K</span>
        </div>
      </div>
    </div>
  );
}
