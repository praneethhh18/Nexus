import { test, expect } from '@playwright/test';
import { installMocks, seedLoggedIn } from './mocks.js';

test.describe('Tasks CRUD', () => {
  test('empty state is shown when there are no tasks', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/tasks');

    // The EmptyState component renders "No tasks here" as the title.
    await expect(page.getByText(/No tasks here/i)).toBeVisible({ timeout: 10_000 });
  });

  test('Add task button opens the modal', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/tasks');

    await page.getByRole('button', { name: /Add task/i }).first().click();
    await expect(page.locator('input[placeholder], label:has-text("Title")').first())
      .toBeVisible({ timeout: 5000 });
  });

  test('submitting a task triggers the create endpoint', async ({ page }) => {
    let createCalled = false;
    await seedLoggedIn(page);
    await installMocks(page, {
      'POST /api/tasks': () => {
        createCalled = true;
        return {
          status: 200, contentType: 'application/json',
          body: JSON.stringify({
            id: 'tk-1', title: 'Call Alice', status: 'open', priority: 'normal',
            created_at: '2026-04-24T10:00:00', tags: '',
          }),
        };
      },
    });
    await page.goto('/tasks');

    await page.getByRole('button', { name: /Add task/i }).first().click();
    // The modal's Title input has `required` + `autoFocus` — fill it.
    const title = page.locator('input[required]').first();
    await title.fill('Call Alice');
    // Submit via Enter on the required field — avoids ambiguity with the
    // page header's "Add task" button which also matches /Add Task/i.
    await title.press('Enter');

    await expect.poll(() => createCalled, { timeout: 5000 }).toBe(true);
  });
});
