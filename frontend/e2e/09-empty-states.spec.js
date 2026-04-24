import { test, expect } from '@playwright/test';
import { installMocks, seedLoggedIn } from './mocks.js';

test.describe('Empty states across the product', () => {
  test.beforeEach(async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
  });

  test('Invoices shows the "No invoices yet" panel', async ({ page }) => {
    await page.goto('/invoices');
    await expect(page.getByText(/No invoices yet/i)).toBeVisible({ timeout: 10_000 });
    // Primary CTA
    await expect(page.getByRole('button', { name: /New invoice/i }).first())
      .toBeVisible();
  });

  test('Workflows — "My Workflows" tab shows the empty state', async ({ page }) => {
    await page.goto('/workflows');
    // Default view is the Templates gallery — jump to the My Workflows tab
    // to trigger the EmptyState card.
    await page.getByRole('button', { name: /My Workflows/i }).click();
    await expect(page.getByText(/No workflows yet/i)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('button', { name: /Browse templates/i })).toBeVisible();
  });

  test('Inbox shows the all-caught-up panel', async ({ page }) => {
    await page.goto('/inbox');
    await expect(page.getByText(/You're all caught up/i)).toBeVisible({ timeout: 10_000 });
  });
});
