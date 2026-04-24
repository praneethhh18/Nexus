import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for NexusAgent E2E.
 *
 * Tests run against the Vite dev server boot via `npm run dev`. The backend
 * is not started — every /api/* request is intercepted by `e2e/mocks.js`
 * so the suite runs in any environment (CI or local) without a live
 * uvicorn + Ollama + ChromaDB stack.
 *
 * The `webServer` block starts Vite before the first test and tears it
 * down after the run.
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },
  fullyParallel: false,            // specs share local storage + stubs; serialize to avoid flakes
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: process.env.CI ? [['github'], ['list']] : 'list',

  use: {
    baseURL: 'http://localhost:5173',
    trace:   'retain-on-failure',
    video:   'retain-on-failure',
    screenshot: 'only-on-failure',
  },

  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
    stdout: 'ignore',
    stderr: 'pipe',
  },
});
