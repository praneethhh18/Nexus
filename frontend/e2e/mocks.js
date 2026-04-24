/**
 * API mocking helpers for the E2E suite.
 *
 * The real backend isn't started in tests — we intercept every /api/* request
 * at the network layer and return canned JSON. This keeps the suite fast
 * (no Ollama, no ChromaDB) and reproducible across environments.
 *
 * Each spec calls `await installMocks(page, { ...overrides })` at the top
 * of its test to set the common routes, plus any per-test overrides.
 */

const DEFAULT_USER = {
  id: 'user-e2e',
  email: 'e2e@example.com',
  name:  'E2E Tester',
};

const DEFAULT_BUSINESS = {
  id:       'biz-e2e',
  name:     'E2E Test Co',
  industry: 'Testing',
  is_active: 1,
};


// ── Pre-auth helpers ────────────────────────────────────────────────────────
/**
 * Seed localStorage so the app boots as a logged-in user. Must be called
 * BEFORE `page.goto()` so the storage is present on first render.
 */
export async function seedLoggedIn(page, {
  user = DEFAULT_USER,
  business = DEFAULT_BUSINESS,
} = {}) {
  await page.addInitScript(({ user, business }) => {
    localStorage.setItem('nexus_token', 'e2e-test-token');
    localStorage.setItem('nexus_user',  JSON.stringify(user));
    localStorage.setItem('nexus_business_id', business.id);
    localStorage.setItem('nexus_businesses', JSON.stringify([business]));
    // Hide the onboarding wizard by default; opt-in tests flip this back.
    localStorage.setItem('nexus_onboarding_done', '1');
  }, { user, business });
}


// ── Route table ────────────────────────────────────────────────────────────
function json(body, status = 200) {
  return { status, contentType: 'application/json', body: JSON.stringify(body) };
}

/**
 * Install the common set of mocks. `overrides` lets a spec replace a specific
 * route with its own handler. Unmatched /api/* routes fall through to a 200
 * empty-object stub so the UI renders its "no data" state without erroring.
 */
export async function installMocks(page, overrides = {}) {
  const routes = {
    // ── Health + auth ────────────────────────────────────────────────────
    'GET /api/health':       () => json({ status: 'ok', provider: 'ollama', model: 'llama3' }),
    'GET /api/health/deep':  () => json({ ok: true, checks: {} }),
    'GET /api/auth/me':      () => json(DEFAULT_USER),

    // ── Businesses ───────────────────────────────────────────────────────
    'GET /api/businesses':             () => json([DEFAULT_BUSINESS]),
    'GET /api/businesses/current':     () => json(DEFAULT_BUSINESS),

    // ── Notifications ────────────────────────────────────────────────────
    'GET /api/notifications':          () => json({ notifications: [], unread_count: 0 }),
    'GET /api/notifications/prefs':    () => json({ agent_completed: true }),
    'POST /api/notifications':         () => json({ ok: true }),

    // ── Onboarding (server-backed) ───────────────────────────────────────
    'GET /api/onboarding':             () => json({
      steps: [
        { key: 'profile',     title: 'Business profile',          description: '',       cta: 'Open', route: '/settings', done: true },
        { key: 'agents',      title: 'Choose your team',           description: '',       cta: 'Open', route: '/agents',   done: true },
        { key: 'data_source', title: 'Connect data',               description: '',       cta: 'Open', route: '/database', done: true },
        { key: 'document',    title: 'Upload document',            description: '',       cta: 'Open', route: '/documents', done: true },
        { key: 'first_run',   title: 'Run first agent',            description: '',       cta: 'Open', route: '/agents',   done: true },
        { key: 'celebrated',  title: "You're all set",             description: '',       cta: 'Finish', route: '/',        done: true },
      ],
      skipped: false, all_done: true, celebrated: true,
    }),

    // ── Agents ───────────────────────────────────────────────────────────
    'GET /api/agents/personas':    () => json([]),
    'GET /api/agents/background':  () => json({ jobs: [] }),
    'GET /api/agents/activity':    () => json([]),
    'GET /api/agents/nudges':      () => json([]),
    'GET /api/agents/schedule':    () => json({ schedule: [], presets: [5, 15, 60, 1440] }),
    'GET /api/agents/runs':        () => json({ runs: [] }),
    'GET /api/approvals/pending-count': () => json({ pending_count: 0 }),

    // ── CRM ──────────────────────────────────────────────────────────────
    'GET /api/crm/overview':    () => json({ contacts: 0, companies: 0, open_deals_count: 0, open_deals_value: 0, won_this_month: 0 }),
    'GET /api/crm/contacts':    () => json([]),
    'GET /api/crm/companies':   () => json([]),
    'GET /api/crm/deals':       () => json([]),
    'GET /api/crm/pipeline':    () => json({ by_stage: {}, stages: [] }),

    // ── Tasks ────────────────────────────────────────────────────────────
    'GET /api/tasks':          () => json([]),
    'GET /api/tasks/summary':  () => json({ overdue: 0, today: 0, upcoming: 0, open_total: 0, done_today: 0 }),

    // ── Invoices ─────────────────────────────────────────────────────────
    'GET /api/invoices':          () => json([]),
    'GET /api/invoices/summary':  () => json({ outstanding: 0, paid: 0, draft: 0, overdue: { count: 0, total: 0 } }),

    // ── Documents ────────────────────────────────────────────────────────
    'GET /api/documents/templates': () => json([]),
    'GET /api/documents':           () => json([]),

    // ── Tags ─────────────────────────────────────────────────────────────
    'GET /api/tags':                () => json([]),
    'POST /api/tags/bulk-for/task':    () => json({}),
    'POST /api/tags/bulk-for/contact': () => json({}),
    'POST /api/tags/bulk-for/company': () => json({}),
    'POST /api/tags/bulk-for/deal':    () => json({}),

    // ── Integrations ─────────────────────────────────────────────────────
    'GET /api/integrations/providers': () => json({ providers: [], categories: {} }),
    'GET /api/integrations':           () => json([]),

    // ── Workflows ────────────────────────────────────────────────────────
    'GET /api/workflows':            () => json([]),
    'GET /api/workflows/templates':  () => json([]),
    'GET /api/workflows/node-types': () => json([]),
    'GET /api/workflows/history':    () => json([]),

    // ── Misc ─────────────────────────────────────────────────────────────
    'GET /api/stats':         () => json({ conversations: 0 }),
    'GET /api/briefing/latest': () => json(null),
    'GET /api/calendar/status': () => json({ connected: false }),
    'GET /api/calendar/events': () => json([]),
    'GET /api/conversations':   () => json([]),
    'GET /api/agent/tools':     () => json([]),

    ...overrides,
  };

  await page.route(/\/api\//, async (route) => {
    const req = route.request();
    const key = `${req.method()} ${new URL(req.url()).pathname}`;
    const handler = routes[key];
    if (handler) {
      const result = await handler(route);
      await route.fulfill(result);
      return;
    }
    // Unknown /api/* — return an empty OK so the UI falls to its empty state
    // rather than lighting up red with network errors.
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
  });
}


/**
 * Convenience: record every request/response that hits an /api/ endpoint so
 * specs can assert against what the UI actually called.
 */
export function trackApiCalls(page) {
  const calls = [];
  page.on('request', (req) => {
    const url = req.url();
    if (url.includes('/api/')) {
      calls.push({ method: req.method(), url: new URL(url).pathname, postData: req.postData() });
    }
  });
  return calls;
}
