import { test, expect } from '@playwright/test';
import { installMocks, seedLoggedIn } from './mocks.js';

test.describe('Bulk actions on tasks', () => {
  const seedTasks = [
    { id: 'tk-1', title: 'Alpha', status: 'open', priority: 'normal', created_at: '2026-04-24T10:00:00', tags: '', recurrence: 'none' },
    { id: 'tk-2', title: 'Bravo', status: 'open', priority: 'high',   created_at: '2026-04-24T10:00:00', tags: '', recurrence: 'none' },
    { id: 'tk-3', title: 'Charlie', status: 'open', priority: 'low',   created_at: '2026-04-24T10:00:00', tags: '', recurrence: 'none' },
  ];

  test('select-all checkbox reveals the action bar', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page, {
      'GET /api/tasks': () => ({
        status: 200, contentType: 'application/json',
        body: JSON.stringify(seedTasks),
      }),
      'GET /api/tasks/summary': () => ({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ overdue: 0, today: 0, upcoming: 0, open_total: 3, done_today: 0 }),
      }),
    });
    await page.goto('/tasks');

    // Wait for the task rows to land
    await expect(page.getByText('Alpha')).toBeVisible({ timeout: 10_000 });

    // Tick the first row's checkbox (the select-all strip is first)
    await page.locator('input[type="checkbox"]').nth(1).check();

    // The sticky BulkActionBar renders "1 selected" / "2 selected" etc.
    // Anchor the regex so we don't also match the "X of N selected" strip
    // that the redesigned Tasks page now shows above the rows.
    await expect(page.getByText(/^\d+ selected$/i)).toBeVisible({ timeout: 3000 });
  });

  test('bulk delete fires the bulk endpoint', async ({ page }) => {
    let bulkCalled = false;
    await seedLoggedIn(page);
    await installMocks(page, {
      'GET /api/tasks': () => ({
        status: 200, contentType: 'application/json',
        body: JSON.stringify(seedTasks),
      }),
      'GET /api/tasks/summary': () => ({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({ overdue: 0, today: 0, upcoming: 0, open_total: 3, done_today: 0 }),
      }),
      'POST /api/tasks/bulk-delete': () => {
        bulkCalled = true;
        return {
          status: 200, contentType: 'application/json',
          body: JSON.stringify({ deleted: 2 }),
        };
      },
    });
    // Auto-confirm the browser `confirm()` that bulk delete uses.
    page.on('dialog', (d) => d.accept());

    await page.goto('/tasks');
    await expect(page.getByText('Alpha')).toBeVisible({ timeout: 10_000 });

    await page.locator('input[type="checkbox"]').nth(1).check();
    await page.locator('input[type="checkbox"]').nth(2).check();

    await page.getByRole('button', { name: /^Delete$/i }).click();

    await expect.poll(() => bulkCalled, { timeout: 5000 }).toBe(true);
  });
});
