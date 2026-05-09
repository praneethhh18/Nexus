/**
 * ContactPreviewLink — markdown link augmented with a hover/click preview card.
 *
 * When ReactMarkdown renders a link whose href matches /crm/contacts/<id>
 * we substitute this component instead of a plain <a>. Hover for ~250ms (or
 * focus via keyboard) → lazily fetch the contact + render a mini card with
 * name, title, phone, email, lead-score tag, and quick action buttons.
 *
 * Used in Chat.jsx + Inbox.jsx — anywhere ReactMarkdown is rendered.
 */
import { useState, useRef, useCallback } from 'react';
import { Phone, Mail, MessageSquare, ExternalLink, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { getContact } from '../services/crm';
import { prepareDialForContact } from '../services/voice_calls';

const HOVER_DELAY_MS = 250;
// In-memory cache so re-rendering the same chat scroll doesn't refetch
// the same contact 5 times. Module-scoped — wipes on full reload.
const _cache = new Map();

function extractContactId(href) {
  if (!href) return null;
  // Match /crm/contacts/<id> with or without trailing slash / query / hash
  const m = String(href).match(/\/crm\/contacts\/([^/?#\s]+)/);
  return m ? m[1] : null;
}

export default function ContactPreviewLink({ href, children, ...rest }) {
  // All hooks must be called unconditionally — React hooks rules forbid
  // early-returning before subsequent hook calls. cid drives behavior, not
  // hook ordering.
  const cid = extractContactId(href);
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [contact, setContact] = useState(cid ? (_cache.get(cid) || null) : null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const hoverTimer = useRef(null);
  const wrapRef = useRef(null);

  const load = useCallback(async () => {
    if (!cid || contact || loading) return;
    setLoading(true); setErr('');
    try {
      const c = await getContact(cid);
      _cache.set(cid, c);
      setContact(c);
    } catch (e) {
      setErr(e.message || 'Could not load contact');
    } finally {
      setLoading(false);
    }
  }, [cid, contact, loading]);

  // Plain markdown link if it's not a contact URL — passthrough. Safe to
  // early-return here because all hooks above ran unconditionally.
  if (!cid) {
    return <a href={href} {...rest}>{children}</a>;
  }

  const onEnter = () => {
    clearTimeout(hoverTimer.current);
    hoverTimer.current = setTimeout(() => { setOpen(true); load(); }, HOVER_DELAY_MS);
  };
  const onLeave = () => {
    clearTimeout(hoverTimer.current);
    hoverTimer.current = setTimeout(() => setOpen(false), 200);
  };

  return (
    <span ref={wrapRef} onMouseEnter={onEnter} onMouseLeave={onLeave}
          style={{ position: 'relative', display: 'inline-block' }}>
      <a
        href={href}
        onClick={(e) => { e.preventDefault(); navigate(href); }}
        onFocus={() => { setOpen(true); load(); }}
        onBlur={() => setTimeout(() => setOpen(false), 200)}
        style={{
          color: 'var(--color-info)', textDecoration: 'none',
          borderBottom: '1px dashed color-mix(in srgb, var(--color-info) 50%, transparent)',
          cursor: 'pointer',
        }}
        {...rest}
      >
        {children}
      </a>
      {open && (
        <PreviewCard
          contact={contact} loading={loading} err={err}
          onOpen={() => navigate(href)}
        />
      )}
    </span>
  );
}

function PreviewCard({ contact, loading, err, onOpen }) {
  const stop = (e) => e.stopPropagation();
  const score = (() => {
    if (!contact?.tags) return null;
    const m = String(contact.tags).match(/lead-score-(\d+)/i);
    return m ? parseInt(m[1], 10) : null;
  })();
  const scoreColor = (s) => s == null ? 'var(--color-text-dim)'
    : s >= 75 ? 'var(--color-err)'
    : s >= 55 ? 'var(--color-warn)'
    : s >= 35 ? 'var(--color-info)' : 'var(--color-text-dim)';

  return (
    <div
      onClick={stop}
      style={{
        position: 'absolute', top: 'calc(100% + 6px)', left: 0,
        zIndex: 50, width: 280,
        background: 'var(--color-bg)',
        border: '1px solid var(--color-border-strong)',
        borderRadius: 10,
        boxShadow: '0 12px 32px rgba(0,0,0,0.35)',
        padding: 12, fontSize: 12, color: 'var(--color-text)',
        animation: 'fade-in 0.12s ease-out',
      }}
    >
      {loading && !contact && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--color-text-dim)' }}>
          <Loader2 size={12} className="spin" /> Loading…
        </div>
      )}
      {err && <div style={{ color: 'var(--color-err)' }}>{err}</div>}
      {contact && (
        <>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 8 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontWeight: 600, fontSize: 13,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {[contact.first_name, contact.last_name].filter(Boolean).join(' ') || '(unnamed)'}
              </div>
              {contact.title && (
                <div style={{ fontSize: 11, color: 'var(--color-text-dim)' }}>{contact.title}</div>
              )}
            </div>
            {score != null && (
              <div title="Lead score" style={{
                fontSize: 11, fontWeight: 700,
                padding: '2px 8px', borderRadius: 999,
                background: `color-mix(in srgb, ${scoreColor(score)} 14%, transparent)`,
                color: scoreColor(score),
              }}>{score}</div>
            )}
          </div>
          {contact.company_name && (
            <div style={{ fontSize: 11, color: 'var(--color-text-dim)', marginBottom: 6 }}>
              @ {contact.company_name}
            </div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 8 }}>
            {contact.email && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11 }}>
                <Mail size={11} color="var(--color-info)" /> {contact.email}
              </div>
            )}
            {contact.phone && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11 }}>
                <Phone size={11} color="var(--color-ok)" /> {contact.phone}
              </div>
            )}
          </div>
          {contact.last_call_summary && (
            <div style={{
              fontSize: 11, color: 'var(--color-text-dim)',
              padding: '6px 8px', borderRadius: 6,
              background: 'var(--color-surface-2)', marginBottom: 8,
              display: '-webkit-box', WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical', overflow: 'hidden',
            }}>
              <strong>Last call:</strong> {contact.last_call_summary}
            </div>
          )}
          <div style={{ display: 'flex', gap: 4, justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', gap: 4 }}>
              {contact.phone && (
                <button
                  className="btn-ghost"
                  onClick={async (e) => {
                    e.stopPropagation();
                    try {
                      const r = await prepareDialForContact({ contact_id: contact.id, purpose: 'a quick check-in' });
                      if (r?.precall_url) window.open(r.precall_url, '_blank', 'noopener');
                    } catch {}
                  }}
                  title="Vox call"
                  style={{ padding: '4px 6px' }}
                >
                  <Phone size={11} />
                </button>
              )}
              {contact.phone && (
                <a
                  href={`https://wa.me/${contact.phone.replace(/\D/g, '')}`}
                  target="_blank" rel="noreferrer" onClick={stop}
                  className="btn-ghost"
                  title="WhatsApp"
                  style={{ padding: '4px 6px', color: 'var(--color-ok)' }}
                >
                  <MessageSquare size={11} />
                </a>
              )}
              {contact.email && (
                <a
                  href={`mailto:${contact.email}`}
                  onClick={stop}
                  className="btn-ghost"
                  title="Email"
                  style={{ padding: '4px 6px', color: 'var(--color-info)' }}
                >
                  <Mail size={11} />
                </a>
              )}
            </div>
            <button
              className="btn-ghost"
              onClick={onOpen}
              title="Open contact"
              style={{ padding: '4px 8px', fontSize: 11, display: 'inline-flex', alignItems: 'center', gap: 4 }}
            >
              Open <ExternalLink size={10} />
            </button>
          </div>
        </>
      )}
    </div>
  );
}
