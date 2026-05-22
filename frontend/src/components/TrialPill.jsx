/**
 * Trial pill, small, non-dismissible badge in the sidebar showing
 * how many trial days are left.
 *
 * Sibling of TrialBanner. They have different jobs:
 *   - TrialBanner is a dismissible top-of-page strip with a big "Upgrade"
 *     CTA. The customer can hide it for 24 hours when they're in flow.
 *   - TrialPill is small, always-on, non-dismissible. It's the answer to
 *     "how long do I have left?", the customer can glance at the sidebar
 *     any time and know. No surprise expirations.
 *
 * Renders nothing for non-trial accounts (paid, free, expired).
 * Tone graduates from calm purple → amber (≤6 days) → red (≤2 days).
 * Clicking opens /pricing.
 *
 * Reuses TrialBanner's sessionStorage cache key so the two stay in sync
 * and we don't double-fetch on every layout mount.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles } from 'lucide-react';
import { isLoggedIn } from '../services/auth';

const CACHE_KEY = 'nexus_subscription_summary';
const POLL_INTERVAL_MS = 60 * 60 * 1000;   // 1h, same as banner

async function fetchSubscription() {
  try {
    const res = await fetch('/api/billing/subscription', {
      headers: (() => {
        const h = { 'Content-Type': 'application/json' };
        const t = localStorage.getItem('nexus_token');
        if (t) h['Authorization'] = `Bearer ${t}`;
        const b = localStorage.getItem('nexus_business_id');
        if (b) h['X-Business-Id'] = b;
        return h;
      })(),
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export default function TrialPill({ collapsed = false }) {
  const [sub, setSub] = useState(null);

  useEffect(() => {
    if (!isLoggedIn()) return;

    // Hydrate from the shared cache, TrialBanner may have already fetched.
    try {
      const cached = sessionStorage.getItem(CACHE_KEY);
      if (cached) setSub(JSON.parse(cached));
    } catch { /* ignore */ }

    let mounted = true;
    fetchSubscription().then((s) => {
      if (!mounted || !s) return;
      setSub(s);
      try { sessionStorage.setItem(CACHE_KEY, JSON.stringify(s)); } catch { /* ignore */ }
    });
    const interval = setInterval(() => {
      fetchSubscription().then((s) => { if (mounted && s) setSub(s); });
    }, POLL_INTERVAL_MS);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  if (!sub || !sub.is_trial) return null;
  const days = sub.trial_days_remaining;
  if (days === null || days === undefined) return null;

  // Urgency tones, match the banner's so the two read as one system.
  const tone =
    days >= 7 ? { bg: 'rgba(99,102,241,0.12)',  bd: 'rgba(99,102,241,0.35)', fg: '#a5b4fc' } :
    days >= 3 ? { bg: 'rgba(245,158,11,0.14)',  bd: 'rgba(245,158,11,0.40)', fg: '#fbbf24' } :
                { bg: 'rgba(239,68,68,0.16)',   bd: 'rgba(239,68,68,0.45)',  fg: '#fca5a5' };

  const dayText = days === 0 ? 'last day'
                : days === 1 ? '1 day left'
                : `${days} days left`;

  if (collapsed) {
    // Compact form when the sidebar is collapsed: just a small dot + days.
    return (
      <Link
        to="/pricing"
        title={`${sub.label || 'Pro'} trial, ${dayText}`}
        style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: 28, height: 28, borderRadius: 8,
          background: tone.bg, border: `1px solid ${tone.bd}`,
          color: tone.fg, fontSize: 10, fontWeight: 700,
          textDecoration: 'none', margin: '8px auto',
        }}
      >
        {days}
      </Link>
    );
  }

  return (
    <Link
      to="/pricing"
      title="Upgrade to lock in your trial days"
      style={{
        display: 'flex', alignItems: 'center', gap: 8,
        margin: '8px 12px 0',
        padding: '8px 11px',
        borderRadius: 8,
        background: tone.bg,
        border: `1px solid ${tone.bd}`,
        color: tone.fg,
        textDecoration: 'none',
        fontSize: 11.5, fontWeight: 500,
        transition: 'transform 140ms ease, box-shadow 180ms ease',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-1px)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; }}
    >
      <Sparkles size={12} style={{ flexShrink: 0 }} />
      <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        <strong style={{ fontWeight: 700 }}>{sub.label || 'Pro'} trial</strong>
        {' · '}{dayText}
      </span>
    </Link>
  );
}
