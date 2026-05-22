/**
 * BrandMark, the single source of truth for the NexusAgent logo across
 * the entire app. Mirrors the SVG used on the landing page (LogoMark in
 * landing/src/App.jsx) so users see the exact same identity on
 * marketing, signup, onboarding, and inside the product.
 *
 * Why a shared component instead of inlining the SVG everywhere:
 *   - When we tweak the logo (color, stroke weight, motion), one file
 *     changes, not 8.
 *   - Catches the bug where the wizard rail used a placeholder "N" tile
 *     while the landing showed the real logo. Visitors saw two different
 *     brands in the same session.
 *
 * Usage:
 *   <BrandMark size={32} />
 *   <BrandMark size={44} />
 */
export default function BrandMark({ size = 32, style }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ flexShrink: 0, ...style }}
      aria-label="NexusAgent"
    >
      <rect width="32" height="32" rx="8" fill="#1D4ED8" />
      {/* N strokes */}
      <line x1="9"  y1="8.5"  x2="9"  y2="23.5" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
      <line x1="9"  y1="8.5"  x2="23" y2="23.5" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
      <line x1="23" y1="8.5"  x2="23" y2="23.5" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
      {/* Corner nodes */}
      <circle cx="9"  cy="8.5"  r="2.6" fill="white" />
      <circle cx="9"  cy="23.5" r="2.6" fill="white" />
      <circle cx="23" cy="8.5"  r="2.6" fill="white" />
      <circle cx="23" cy="23.5" r="2.6" fill="white" />
      {/* Centre node on diagonal */}
      <circle cx="16" cy="16"   r="1.9" fill="rgba(255,255,255,0.55)" />
    </svg>
  );
}
