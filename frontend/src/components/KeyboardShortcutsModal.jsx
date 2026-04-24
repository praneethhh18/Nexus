/**
 * Keyboard shortcut reference — opens on `?`. Single source of truth for
 * which shortcuts actually work in the app. If you add a new shortcut, add
 * a row here too so it stays discoverable.
 */
import { useState, useEffect } from 'react';
import { X, Command as CommandIcon } from 'lucide-react';

const GROUPS = [
  {
    label: 'Global',
    shortcuts: [
      { keys: ['Ctrl', 'K'],      description: 'Open command palette (search anything)' },
      { keys: ['?'],              description: 'Show this keyboard shortcuts reference' },
      { keys: ['Esc'],            description: 'Close any modal, drawer, or palette' },
      { keys: ['Ctrl', 'D'],      description: 'Jump to Dashboard' },
      { keys: ['Ctrl', 'N'],      description: 'New item (context-aware per page)' },
      { keys: ['Ctrl', '/'],      description: 'Focus the chat input' },
      { keys: ['Ctrl', 'B'],      description: 'Toggle sidebar' },
    ],
  },
  {
    label: 'Chat',
    shortcuts: [
      { keys: ['/'],              description: 'Open slash-command menu' },
      { keys: ['Enter'],          description: 'Send message' },
      { keys: ['Shift', 'Enter'], description: 'New line without sending' },
      { keys: ['Ctrl', 'Enter'],  description: 'Submit the current form' },
    ],
  },
  {
    label: 'Command palette',
    shortcuts: [
      { keys: ['↑'],              description: 'Previous result' },
      { keys: ['↓'],              description: 'Next result' },
      { keys: ['Enter'],          description: 'Open selected result' },
    ],
  },
];

function isMac() {
  return typeof navigator !== 'undefined' && /Mac|iPod|iPhone|iPad/.test(navigator.platform);
}

function keyLabel(key) {
  if (key === 'Ctrl' && isMac()) return '⌘';
  if (key === 'Shift') return '⇧';
  return key;
}

export default function KeyboardShortcutsModal() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const handler = (e) => {
      // Don't fire when typing in an input
      const t = e.target;
      const isTyping = t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable);
      if (e.key === '?' && !isTyping && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        setOpen(true);
      }
      if (e.key === 'Escape' && open) {
        setOpen(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open]);

  if (!open) return null;

  return (
    <div
      onClick={() => setOpen(false)}
      style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.55)',
        zIndex: 450, display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)',
          borderRadius: 'var(--r-lg)', width: 'min(560px, 94vw)', maxHeight: '80vh',
          overflow: 'hidden', display: 'flex', flexDirection: 'column',
          boxShadow: '0 24px 80px rgba(0,0,0,0.6)',
        }}
      >
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          padding: '14px 18px', borderBottom: '1px solid var(--color-surface-2)',
        }}>
          <CommandIcon size={16} color="var(--color-accent)" />
          <h2 style={{ margin: 0, fontSize: 14, fontWeight: 600, color: 'var(--color-text)' }}>
            Keyboard shortcuts
          </h2>
          <span style={{ fontSize: 10, color: 'var(--color-text-dim)', marginLeft: 'auto' }}>
            Press <Kbd>?</Kbd> anywhere to open this
          </span>
          <button
            onClick={() => setOpen(false)}
            className="btn-ghost"
            style={{ padding: 4 }}
            title="Close (Esc)"
          >
            <X size={14} />
          </button>
        </div>

        <div style={{ padding: 18, overflow: 'auto' }}>
          {GROUPS.map((group) => (
            <div key={group.label} style={{ marginBottom: 18 }}>
              <div style={{
                fontSize: 10, fontWeight: 700, textTransform: 'uppercase',
                letterSpacing: 0.8, color: 'var(--color-text-dim)',
                marginBottom: 8,
              }}>
                {group.label}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {group.shortcuts.map((s, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '6px 10px', borderRadius: 'var(--r-sm)',
                    background: 'var(--color-surface-1)',
                  }}>
                    <span style={{ fontSize: 12, color: 'var(--color-text-muted)' }}>
                      {s.description}
                    </span>
                    <span style={{ display: 'inline-flex', gap: 4 }}>
                      {s.keys.map((k, ki) => (
                        <Kbd key={ki}>{keyLabel(k)}</Kbd>
                      ))}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function Kbd({ children }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      minWidth: 20, height: 20, padding: '0 6px',
      fontSize: 11, fontFamily: 'var(--font-mono)',
      color: 'var(--color-text)', background: 'var(--color-surface-2)',
      border: '1px solid var(--color-border-strong)', borderRadius: 4,
      boxShadow: 'inset 0 -1px 0 var(--color-border)',
    }}>
      {children}
    </span>
  );
}
