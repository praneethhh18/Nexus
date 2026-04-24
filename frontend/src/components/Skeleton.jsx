/**
 * Skeleton loader primitive.
 *
 *   <Skeleton width={120} height={14} />              // single bar
 *   <SkeletonText lines={3} />                        // stacked text lines
 *   <SkeletonCard />                                  // card placeholder
 *
 * Uses a CSS keyframe gradient sweep — no JS animation cost. Respects the
 * theme tokens so skeletons blend into both dark and light modes.
 */
import { useEffect } from 'react';

let _styleInjected = false;
function _ensureKeyframes() {
  if (_styleInjected || typeof document === 'undefined') return;
  const el = document.createElement('style');
  el.textContent = `
    @keyframes nexus-skeleton-shimmer {
      from { background-position: 0 0; }
      to   { background-position: -200% 0; }
    }
    .nexus-skeleton {
      background: linear-gradient(90deg,
        var(--color-surface-1) 0%,
        var(--color-surface-2) 50%,
        var(--color-surface-1) 100%);
      background-size: 200% 100%;
      animation: nexus-skeleton-shimmer 1.4s linear infinite;
      border-radius: 4px;
    }
  `;
  document.head.appendChild(el);
  _styleInjected = true;
}


export default function Skeleton({ width = '100%', height = 12, radius, style }) {
  useEffect(() => { _ensureKeyframes(); }, []);
  return (
    <div
      className="nexus-skeleton"
      style={{
        width, height,
        borderRadius: radius ?? 4,
        display: 'inline-block',
        ...style,
      }}
    />
  );
}


export function SkeletonText({ lines = 3, spacing = 6 }) {
  useEffect(() => { _ensureKeyframes(); }, []);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: spacing }}>
      {Array.from({ length: lines }, (_, i) => (
        <Skeleton
          key={i}
          height={10}
          width={i === lines - 1 ? '65%' : '100%'}
        />
      ))}
    </div>
  );
}


export function SkeletonCard({ height = 120 }) {
  useEffect(() => { _ensureKeyframes(); }, []);
  return (
    <div className="panel" style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <Skeleton width={36} height={36} radius={'var(--r-md)'} />
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
          <Skeleton width={140} height={12} />
          <Skeleton width={80}  height={10} />
        </div>
      </div>
      <SkeletonText lines={2} />
      <Skeleton width={`${height}px`} height={height} radius={8} style={{ alignSelf: 'stretch', width: '100%' }} />
    </div>
  );
}
