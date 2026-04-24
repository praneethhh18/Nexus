import { test, expect } from '@playwright/test';
import { installMocks, seedLoggedIn } from './mocks.js';

test.describe('Chat — slash command menu', () => {
  test('typing "/" in the chat input reveals the typeahead menu', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/chat');

    // The chat composer uses a textarea; find it and type the slash.
    const composer = page.locator('textarea, input[placeholder*="ask" i], input[placeholder*="message" i]').first();
    await expect(composer).toBeVisible({ timeout: 10_000 });
    await composer.click();
    await composer.fill('/');

    // At least one slash command label is rendered by the menu
    await expect(page.getByText(/\/remind|\/task|\/deal|\/invoice|\/brief/i).first())
      .toBeVisible({ timeout: 3000 });
  });

  test('clearing the slash hides the menu', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/chat');

    const composer = page.locator('textarea, input[placeholder*="ask" i], input[placeholder*="message" i]').first();
    await composer.fill('/');
    await expect(page.getByText(/\/remind/).first()).toBeVisible({ timeout: 3000 });
    await composer.fill('');
    await expect(page.getByText(/\/remind/)).toHaveCount(0);
  });
});
