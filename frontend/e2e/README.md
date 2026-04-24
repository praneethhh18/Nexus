# E2E test suite — Playwright

Ten spec files that cover the user-visible flows:

| File                            | What it verifies |
| ------------------------------- | ---------------- |
| `01-login.spec.js`              | Unauth redirect, login form, successful sign-in |
| `02-onboarding.spec.js`         | Dashboard checklist widget shows/hides based on state |
| `03-command-palette.spec.js`    | Ctrl+K opens search overlay, Esc closes |
| `04-keyboard-shortcuts.spec.js` | `?` opens shortcut modal (and doesn't hijack inputs) |
| `05-tasks-crud.spec.js`         | Empty state, modal opens, POST /tasks fires |
| `06-crm-contact.spec.js`        | Contacts / Companies / Deals tab switching + CTAs |
| `07-bulk-actions.spec.js`       | Checkbox + BulkActionBar + bulk-delete endpoint |
| `08-chat-slash-menu.spec.js`    | Typing `/` reveals the slash typeahead |
| `09-empty-states.spec.js`       | Invoices / Workflows / Inbox empty panels |
| `10-settings-devmode.spec.js`   | Dev-mode toggle persists; notification prefs visible |

## How it works

- **Backend is not started.** Every `/api/*` call is intercepted by
  `e2e/mocks.js` and answered with a canned 200. This keeps the suite
  fast and removes the Ollama / ChromaDB / Python dependency chain.
- Each test `await seedLoggedIn(page)` before `page.goto(...)` so the
  app boots as an authenticated user. Login-specific tests skip that.
- **Vite dev server is auto-spawned** by `playwright.config.js` on port
  5173 — no manual setup.

## Run locally

```bash
cd frontend
npm install
npm run e2e:install   # one-time: downloads Chromium
npm run e2e           # headless run
npm run e2e:ui        # interactive mode with time-travel debugging
```

## CI

The `e2e` job in `.github/workflows/ci.yml` runs the suite on every PR.
Playwright `--with-deps` installs system libs chromium needs on Ubuntu.

## Adding a new spec

1. Drop a new `NN-name.spec.js` into this folder.
2. At the top of each test call `await seedLoggedIn(page)` + `await installMocks(page, {...})`.
3. Any per-test mock goes in the second arg of `installMocks`:

```js
await installMocks(page, {
  'POST /api/custom-endpoint': () => ({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ ok: true }),
  }),
});
```

Unknown `/api/*` routes return `200 {}` by default so unseeded calls
never light the UI up red.
