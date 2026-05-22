/**
 * Trial banner, persistent strip at the top of the app showing how many
 * days are left on the current trial + a CTA to upgrade.
 *
 * Renders nothing when:
 *   - User isn't logged in
 *   - Backend says is_trial=false (paid customers, free users, expired)
 *
 * Reads /api/billing/subscription on mount + once an hour. Cached in
 * sessionStorage to avoid hammering the API on every route change.
 *
 * Visual hierarchy:
 *   - Days >= 7  → calm purple (informational)
 *   - Days 3-6   → amber (heads-up)
 *   - Days 0-2   → red (urgent)
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Sparkles, ArrowRight, X } from 'lucide-react';
import { isLoggedIn } from '../services/auth';

const POLL_INTERVAL_MS = 60 * 60 * 1000;   // 1 hour
const DISMISS_KEY = 'nexus_trial_banner_dismissed_until';
const CACHE_KEY = 'nexus_subscription_summary';

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

export default function TrialBanner() {
  const [sub, setSub] = useState(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!isLoggedIn()) return;

    // Check dismissed-until, user clicked the X today, leave them alone
    // until tomorrow morning.
    try {
      const until = sessionStorage.getItem(DISMISS_KEY);
      if (until && Number(until) > Date.now()) {
        setDismissed(true);
        return;
      }
    } catch { /* sessionStorage may be disabled */ }

    // Hydrate from cache instantly (no flash of empty banner), refresh in BG.
    try {
      const cached = sessionStorage.getItem(CACHE_KEY);
      if (cached) setSub(JSON.parse(cached));
    } catch { /* ignore parse errors */ }

    let mounted = true;
    fetchSubscription().then((s) => {
      if (!mounted) return;
      if (s) {
        setSub(s);
        try { sessionStorage.setItem(CACHE_KEY, JSON.stringify(s)); } catch { /* full storage */ }
      }
    });
    const interval = setInterval(() => {
      fetchSubscription().then((s) => {
        if (mounted && s) setSub(s);
      });
    }, POLL_INTERVAL_MS);
    return () => { mounted = false; clearInterval(interval); };
  }, []);

  const handleDismiss = () => {
    setDismissed(true);
    // Snooze for 24h, banner reappears tomorrow.
    try {
      sessionStorage.setItem(DISMISS_KEY, String(Date.now() + 24 * 60 * 60 * 1000));
    } catch { /* full storage */ }
  };

  if (!sub || !sub.is_trial || dismissed) return null;
  const days = sub.trial_days_remaining;
  if (days === null || days === undefined) return null;

  // Tone by urgency.
  const tone =
    days >= 7 ? { bg: 'linear-gradient(90deg, #6366F1 0%, #8B5CF6 100%)', fg: '#fff', accent: '#fff' } :
    days >= 3 ? { bg: 'linear-gradient(90deg, #F59E0B 0%, #FB923C 100%)', fg: '#fff', accent: '#fff' } :
                { bg: 'linear-gradient(90deg, #DC2626 0%, #EF4444 100%)', fg: '#fff', accent: '#fff' };

  const dayLabel = days === 0 ? 'today' : days === 1 ? 'tomorrow' : `in ${days} days`;
  const planLabel = sub.label || 'Pro';

  return (
    <div
      role="status"
      style={{
        background: tone.bg,
        color: tone.fg,
        padding: '8px 16px',
        display: 'flex', alignItems: 'center', gap: 12,
        fontSize: 13, fontWeight: 500,
        flexShrink: 0,
        boxShadow: 'inset 0 -1px 0 rgba(0,0,0,0.08)',
      }}
    >
      <Sparkles size={14} style={{ flexShrink: 0 }} />
      <span style={{ flex: 1 }}>
        <strong>{planLabel} trial</strong> ends {dayLabel}.{' '}
        <span style={{ opacity: 0.9 }}>
          Subscribe now and your remaining trial days are added on top , 
          you don't lose them.
        </span>
      </span>
      <Link
        to="/pricing"
        style={{
          display: 'inline-flex', alignItems: 'center', gap: 4,
          background: 'rgba(255,255,255,0.18)',
          color: tone.accent,
          padding: '4px 12px', borderRadius: 999,
          textDecoration: 'none',
          fontSize: 12, fontWeight: 600,
          flexShrink: 0,
        }}
      >
        Upgrade <ArrowRight size={12} />
      </Link>
      <button
        onClick={handleDismiss}
        aria-label="Dismiss for 24 hours"
        title="Hide for 24 hours"
        style={{
          background: 'transparent', border: 'none', color: tone.fg,
          cursor: 'pointer', padding: 4, opacity: 0.7,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          borderRadius: 6, flexShrink: 0,
        }}
      >
        <X size={14} />
      </button>
    </div>
  );
}
