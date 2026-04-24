import { test, expect } from '@playwright/test';
import { installMocks, seedLoggedIn } from './mocks.js';

test.describe('Command palette (Cmd+K)', () => {
  test('Ctrl+K opens the search overlay', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/');

    await page.keyboard.press('Control+KeyK');
    // The palette renders an input with the "Search" placeholder text.
    const input = page.locator('input[placeholder*="Search" i]').first();
    await expect(input).toBeVisible({ timeout: 5000 });
    await expect(input).toBeFocused();
  });

  test('Escape closes the palette', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/');

    await page.keyboard.press('Control+KeyK');
    const input = page.locator('input[placeholder*="Search" i]').first();
    await expect(input).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(input).toBeHidden({ timeout: 3000 });
  });

  test('typing a short query shows the "type at least 2 chars" hint', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/');

    await page.keyboard.press('Control+KeyK');
    await page.locator('input[placeholder*="Search" i]').first().fill('a');
    await expect(page.getByText(/Type at least 2 characters/i)).toBeVisible();
  });
});
