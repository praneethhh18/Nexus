/**
 * "Coming soon" feature registry.
 *
 * Phase G + later features are planned but not built. We surface them to
 * users with a "Coming soon" badge so:
 *   1. They know what's on the roadmap without us oversleeping our
 *      development commitments
 *   2. They can email/WhatsApp early interest, gives us a demand signal
 *      for which features to actually prioritise
 *   3. We don't have to lie in the marketing copy (e.g. listing "LR
 *      tracking" as if it ships today when v1 doesn't have it)
 *
 * Each entry:
 *   id          stable key, used by tracking later
 *   title       short label shown on the badge / list
 *   eta         human label for when, e.g. "Q1 2026" or "Next version"
 *   industries  which workspaces should see this teaser
 *   blurb       one-line description for the tooltip / preview
 */

export const COMING_SOON_FEATURES = [
  {
    id: 'fleet-live-tracking',
    title: 'Live fleet tracking',
    eta: 'Next version',
    industries: ['Logistics / transport', 'Travel / tour operator', 'Real estate broker', 'Local services'],
    blurb: "Live map of vehicles, ETA on consignments, AI agent answers 'where is my truck' from real-time GPS.",
  },
  {
    id: 'driver-app',
    title: 'Driver smartphone app',
    eta: 'Next version',
    industries: ['Logistics / transport', 'Travel / tour operator', 'Local services'],
    blurb: 'Drivers log in, accept jobs, post GPS pings, no hardware needed.',
  },
  {
    id: 'route-optimisation',
    title: 'Multi-stop route optimisation',
    eta: 'Soon',
    industries: ['Logistics / transport', 'Local services'],
    blurb: 'Daily route plans that minimise distance + fuel + driver hours.',
  },
  {
    id: 'geofence-alerts',
    title: 'Geofence + speed alerts',
    eta: 'Soon',
    industries: ['Logistics / transport', 'Travel / tour operator', 'Auto repair / garage'],
    blurb: "Get pinged when a vehicle leaves a zone or breaks speed limits.",
  },
  {
    id: 'fuel-reports',
    title: 'Fuel + odometer reports',
    eta: 'Soon',
    industries: ['Logistics / transport', 'Auto repair / garage'],
    blurb: 'Per-trip and per-driver fuel consumption + km efficiency analytics.',
  },
];

/**
 * Get coming-soon features that should be teased to the current workspace.
 * Returns [] for industries with nothing planned.
 *
 * Industry matching is case-insensitive, mirrors the backend
 * normalize_industry() so 'healthcare' / 'HEALTHCARE' / 'Healthcare '
 * all resolve to the same canonical industry key. Without this, a
 * workspace whose industry got stored with non-canonical casing would
 * silently see no roadmap teasers.
 */
export function comingSoonForIndustry(industry) {
  if (!industry) return [];
  const needle = industry.trim().toLowerCase();
  return COMING_SOON_FEATURES.filter((f) =>
    f.industries.some((ind) => ind.toLowerCase() === needle)
  );
}

/**
 * Lower-case set of titles a workspace's industry has planned. Used by the
 * wizard tools list to mark which tool entries are roadmap (not shipped),
 * so we don't lie about what's available today.
 */
export function roadmapTitleSetForIndustry(industry) {
  return new Set(
    comingSoonForIndustry(industry).map(f => f.title.toLowerCase())
  );
}
