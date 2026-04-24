/**
 * Illustrated empty state — rendered on every list page when there's no data.
 * The shape is deliberately opinionated: a soft-coloured icon tile, a concise
 * title, a one-line explanation of what the page is for, a primary CTA, and
 * an optional secondary link. Keeps every empty page feeling intentional
 * rather than broken.
 */
import { ArrowRight } from 'lucide-react';

export default function EmptyState({
  icon: Icon,
  title,
  description,
  primaryLabel,
  onPrimary,
  secondaryLabel,
  onSecondary,
  accent = 'var(--color-accent)',
  minHeight = 280,
  size = 'md',           // 'sm' = inline inside a panel; 'md' = page-level
}) {
  const iconSize = size === 'sm' ? 20 : 28;
  const tileSize = size === 'sm' ? 44 : 64;
  const titleFont = size === 'sm' ? 14 : 17;
  const descFont = size === 'sm' ? 12 : 13;

  return (
    <div
      className="panel"
      style={{
        padding: size === 'sm' ? 20 : 32,
        minHeight,
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', textAlign: 'center',
        gap: 10,
      }}
    >
      {Icon && (
        <div style={{
          width: tileSize, height: tileSize, borderRadius: 'var(--r-md)',
          background: `color-mix(in srgb, ${accent} 15%, transparent)`,
          color: accent,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          marginBottom: 4,
        }}>
          <Icon size={iconSize} />
        </div>
      )}

      <h3 style={{
        margin: 0, fontSize: titleFont, fontWeight: 600, color: 'var(--color-text)',
      }}>
        {title}
      </h3>

      {description && (
        <p style={{
          margin: 0, maxWidth: 420,
          fontSize: descFont, color: 'var(--color-text-muted)', lineHeight: 1.55,
        }}>
          {description}
        </p>
      )}

      {(primaryLabel || secondaryLabel) && (
        <div style={{
          marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap',
          justifyContent: 'center',
        }}>
          {primaryLabel && (
            <button
              onClick={onPrimary}
              className="btn-primary"
              style={{ fontSize: 12, padding: '7px 16px' }}
            >
              {primaryLabel} <ArrowRight size={11} />
            </button>
          )}
          {secondaryLabel && (
            <button
              onClick={onSecondary}
              className="btn-ghost"
              style={{ fontSize: 12, padding: '7px 14px' }}
            >
              {secondaryLabel}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
