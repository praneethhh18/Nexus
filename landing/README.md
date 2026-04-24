# NexusAgent — Landing page

Public marketing site. Separate from the main React app so it can deploy
independently to Vercel / Netlify / Cloudflare Pages.

## Dev

```bash
npm install
npm run dev      # runs at http://localhost:4000
```

## Build

```bash
npm run build    # outputs to dist/
```

## Deploy

- **Vercel**: point the project's root to `landing/`, framework preset Vite.
- **Netlify**: publish directory `landing/dist`, build `npm run build` inside `landing/`.
- **Cloudflare Pages**: same as Netlify.

### App URL

The CTA buttons ("Start free", "Sign in") link to `APP_URL` — defaults to
`/app`. Set the Vite env variable to wherever the real app lives:

```bash
VITE_APP_URL=https://app.nexusagent.yourdomain.com npm run build
```

For local testing with the full stack:

```bash
VITE_APP_URL=http://localhost:5173 npm run dev
```

## Sections

1. **Nav + hero** — tagline, CTA to `/setup`, privacy pill.
2. **Problem** — "scattered across seven tools".
3. **Agents** — the six-agent grid.
4. **Privacy** — the four-layer defence (the actual differentiator).
5. **Features** — 8-tile feature grid.
6. **Pricing** — 4 tiers (Free / Pro / Business / Self-hosted).
7. **FAQ** — 6 questions that address the usual objections.
8. **CTA + footer** — last chance to convert.

## Non-goals for this first cut

- Testimonials (add after beta)
- Video demo (Loom recording is a follow-up)
- Analytics + A/B testing (Phase 11 — Plausible/PostHog hooks go here later)
- Email capture / waitlist (needs a backend endpoint; CTA goes straight to `/setup` for now)
