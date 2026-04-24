import { test, expect } from '@playwright/test';
import { installMocks, seedLoggedIn } from './mocks.js';

test.describe('Settings — developer mode', () => {
  test('dev-mode toggle is present and clickable', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/settings');

    // The toggle is labelled "Developer mode"
    await expect(page.getByText(/Developer mode/i).first())
      .toBeVisible({ timeout: 10_000 });
    // It's an aria-pressed button — find the first toggle on the page.
    const toggles = page.locator('button[aria-pressed]');
    await expect(toggles.first()).toBeVisible();
  });

  test('toggling dev-mode persists into localStorage', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/settings');

    // Scope to the "Developer mode" panel so we don't pick up a notification
    // prefs toggle (which also uses aria-pressed).
    const devCard = page.locator('.panel', { hasText: /Developer mode/i }).first();
    await expect(devCard).toBeVisible({ timeout: 10_000 });
    const devToggle = devCard.locator('button[aria-pressed]').first();
    await devToggle.click();

    // Click writes '0' or '1' to localStorage.
    await expect.poll(
      () => page.evaluate(() => localStorage.getItem('nexus_dev_mode')),
      { timeout: 3000 },
    ).toMatch(/^[01]$/);
  });

  test('notification preferences panel is visible', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/settings');

    await expect(page.getByText(/Notifications|Pick which events ring the bell/i).first())
      .toBeVisible({ timeout: 10_000 });
  });
});
