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

  test('short query shows the slash-command quick-action menu', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/');

    await page.keyboard.press('Control+KeyK');
    await page.locator('input[placeholder*="Search" i]').first().fill('a');
    // Below 2 chars (and not starting with /) we now surface the slash
    // commands as a starting menu rather than a static hint. Verify the
    // group header + at least one command item are rendered.
    await expect(page.getByText(/Quick action/i).first()).toBeVisible();
    await expect(page.getByText('/call', { exact: false }).first()).toBeVisible();
  });

  test('typing "/" filters down to the matching slash commands', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/');

    await page.keyboard.press('Control+KeyK');
    await page.locator('input[placeholder*="Search" i]').first().fill('/wa');
    await expect(page.getByText('/wa', { exact: false }).first()).toBeVisible();
    // Other slash entries should NOT be present once the prefix narrows.
    await expect(page.getByText('/call').first()).toBeHidden();
  });
});
