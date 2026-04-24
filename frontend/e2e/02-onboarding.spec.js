import { test, expect } from '@playwright/test';
import { installMocks, seedLoggedIn } from './mocks.js';

test.describe('Onboarding wizard', () => {
  test('shows checklist widget on dashboard when setup is incomplete', async ({ page }) => {
    // Override onboarding to return an incomplete state so the widget renders.
    await seedLoggedIn(page);
    await installMocks(page, {
      'GET /api/onboarding': () => ({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({
          steps: [
            { key: 'profile',     title: 'Business profile',  description: 'Name + details',
              cta: 'Open profile', route: '/settings',  done: false },
            { key: 'agents',      title: 'Choose your team',   description: 'Pick agents',
              cta: 'Configure',    route: '/agents',    done: false },
            { key: 'data_source', title: 'Connect data',        description: 'CSV or email',
              cta: 'Import',       route: '/database',  done: false },
            { key: 'document',    title: 'Upload document',     description: 'PDF to RAG',
              cta: 'Upload',       route: '/documents', done: false },
            { key: 'first_run',   title: 'Run first agent',     description: 'Try one',
              cta: 'Pick agent',   route: '/agents',    done: false },
            { key: 'celebrated',  title: "You're all set",      description: 'Finish',
              cta: 'Finish',       route: '/',          done: false },
          ],
          skipped: false, all_done: false, celebrated: false,
        }),
      }),
    });
    await page.goto('/');
    // The checklist card anchors on a "Finish setting up" headline.
    await expect(page.getByText(/Finish setting up/i)).toBeVisible({ timeout: 10000 });
  });

  test('checklist disappears when skipped state is returned', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page, {
      'GET /api/onboarding': () => ({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({
          steps: [], skipped: true, all_done: false, celebrated: true,
        }),
      }),
    });
    await page.goto('/');
    await page.waitForTimeout(500);
    await expect(page.getByText(/Finish setting up/i)).toHaveCount(0);
  });
});
