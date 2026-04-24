import { test, expect } from '@playwright/test';
import { installMocks, seedLoggedIn } from './mocks.js';

test.describe('Keyboard shortcuts reference (?)', () => {
  test('pressing ? opens the shortcuts modal', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/');

    // Click body first so the key press doesn't land in a form field
    await page.locator('body').click();
    await page.keyboard.press('Shift+Slash');  // Shift+/ = ?

    await expect(page.getByRole('heading', { name: /Keyboard shortcuts/i }))
      .toBeVisible({ timeout: 5000 });
  });

  test('modal closes on Escape', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/');

    await page.locator('body').click();
    await page.keyboard.press('Shift+Slash');
    const heading = page.getByRole('heading', { name: /Keyboard shortcuts/i });
    await expect(heading).toBeVisible();

    await page.keyboard.press('Escape');
    await expect(heading).toBeHidden({ timeout: 3000 });
  });

  test('does NOT open when user is typing in an input', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/');

    await page.keyboard.press('Control+KeyK');
    const cmdInput = page.locator('input[placeholder*="Search" i]').first();
    await cmdInput.fill('?');

    // The shortcuts modal must NOT hijack the ? character while typing.
    await expect(page.getByRole('heading', { name: /Keyboard shortcuts/i }))
      .toHaveCount(0);
  });
});
