/**
 * Settings hub — top-of-page navigation grid that surfaces every admin /
 * workspace area in one place.
 *
 * Why: the old sidebar had 22 flat items, half of which were settings-y
 * things the SMB owner touches once a month (Team, Memory, Security,
 * Privacy Mode, Audit log, Metrics, History). They all moved into this
 * hub so the daily sidebar shrunk to 7 + 6 + 2 visible items.
 *
 * Every card links to an EXISTING route URL — no new pages were created.
 * Direct deep-links (bookmarks, support emails) keep working. The hub is
 * just a discoverable index.
 *
 * Sections mirror the mental model:
 *   Account            → things scoped to the logged-in user
 *   Workspace          → things scoped to the business
 *   Privacy & Security → audit, sessions, 2FA, privacy mode
 *   Billing            → plan + payment history
 */
import { Link } from 'react-router-dom';
import {
  Users, Mail, Brain, Bell, Plug, Briefcase, Shield, ShieldCheck,
  Activity, Clock, BarChart3, Sparkles, Receipt, ArrowRight,
} from 'lucide-react';

const SECTIONS = [
  {
    title: 'Account',
    description: 'Profile, notifications, memory — scoped to you.',
    items: [
      { to: '#profile',        icon: Briefcase, label: 'Business profile',     blurb: 'Name, industry, type, size, goal' },
      { to: '#notifications',  icon: Bell,      label: 'Notifications',        blurb: 'Email + in-app alert preferences' },
      { to: '/memory',         icon: Brain,     label: 'AI memory',            blurb: 'Long-term facts your agents remember' },
      { to: '/history',        icon: Clock,     label: 'Activity history',     blurb: 'Recent runs, edits, and AI actions' },
    ],
  },
  {
    title: 'Workspace',
    description: 'Settings that affect the whole business.',
    items: [
      { to: '/team',           icon: Users,      label: 'Team',                blurb: 'Members, roles, invitations' },
      { to: '/integrations',   icon: Plug,       label: 'Connections',         blurb: 'Gmail, Calendar, WhatsApp, Razorpay' },
      { to: '/email-templates',icon: Mail,       label: 'Email templates',     blurb: 'Industry-tuned reply templates' },
      { to: '/admin/metrics',  icon: BarChart3,  label: 'Workspace metrics',   blurb: 'Usage, token spend, agent activity' },
    ],
  },
  {
    title: 'Privacy & Security',
    description: 'Where your data goes and who can access it.',
    items: [
      { to: '/settings/privacy-mode', icon: ShieldCheck, label: 'Privacy Mode',      blurb: 'Run sensitive prompts on-device' },
      { to: '/security',              icon: Shield,      label: 'Security + 2FA',    blurb: 'Sessions, recovery codes, password' },
      { to: '/audit',                 icon: Activity,    label: 'Activity log',      blurb: 'Every privileged action recorded' },
    ],
  },
  {
    title: 'Billing',
    description: 'Subscription + invoices NexusAgent has charged you.',
    items: [
      { to: '/pricing',        icon: Sparkles,  label: 'Plan & billing',       blurb: 'Upgrade, downgrade, trial status' },
      { to: '/pricing#history',icon: Receipt,   label: 'Payment history',      blurb: 'Razorpay invoices + GST receipts' },
    ],
  },
];

export default function SettingsHub() {
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: 'var(--color-text)' }}>
          Workspace settings
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: 13, color: 'var(--color-text-muted)' }}>
          Everything that affects your account, team, and how the AI agents behave.
        </p>
      </div>

      {SECTIONS.map((section) => (
        <div key={section.title} style={{ marginBottom: 18 }}>
          <div style={{
            display: 'flex', alignItems: 'baseline', justifyContent: 'space-between',
            marginBottom: 10,
          }}>
            <h3 style={{ margin: 0, fontSize: 12, fontWeight: 700, letterSpacing: 0.6,
              textTransform: 'uppercase', color: 'var(--color-text-dim)' }}>
              {section.title}
            </h3>
            <span style={{ fontSize: 11.5, color: 'var(--color-text-muted)' }}>
              {section.description}
            </span>
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))',
            gap: 10,
          }}>
            {section.items.map((it) => {
              const Icon = it.icon;
              const Wrap = it.to.startsWith('#')
                ? ({ children }) => <a href={it.to} style={{ textDecoration: 'none' }}>{children}</a>
                : ({ children }) => <Link to={it.to} style={{ textDecoration: 'none' }}>{children}</Link>;
              return (
                <Wrap key={it.to}>
                  <div
                    className="settings-hub-card"
                    style={{
                      display: 'flex', alignItems: 'flex-start', gap: 11,
                      padding: '13px 14px',
                      background: 'var(--color-surface-1)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 10,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <div style={{
                      flexShrink: 0,
                      width: 32, height: 32, borderRadius: 8,
                      background: 'color-mix(in srgb, var(--color-accent) 12%, transparent)',
                      color: 'var(--color-accent)',
                      display: 'grid', placeItems: 'center',
                    }}>
                      <Icon size={16} />
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        fontSize: 13, fontWeight: 600, color: 'var(--color-text)',
                        marginBottom: 2,
                      }}>{it.label}</div>
                      <div style={{
                        fontSize: 11.5, color: 'var(--color-text-muted)', lineHeight: 1.45,
                      }}>{it.blurb}</div>
                    </div>
                    <ArrowRight size={13} style={{
                      flexShrink: 0, color: 'var(--color-text-dim)', marginTop: 3,
                    }} />
                  </div>
                </Wrap>
              );
            })}
          </div>
        </div>
      ))}

      <div style={{
        marginTop: 8, padding: '10px 14px',
        background: 'color-mix(in srgb, var(--color-info) 5%, var(--color-surface-1))',
        border: '1px dashed color-mix(in srgb, var(--color-info) 30%, var(--color-border))',
        borderRadius: 8, fontSize: 12, color: 'var(--color-text-muted)', lineHeight: 1.5,
      }}>
        Looking for general settings (LLM provider, SMTP, sample data)? They're below.
      </div>
    </div>
  );
}
