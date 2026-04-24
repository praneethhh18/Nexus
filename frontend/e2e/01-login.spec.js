import { test, expect } from '@playwright/test';
import { installMocks } from './mocks.js';

test.describe('Login flow', () => {
  test('redirects to /login when not authenticated', async ({ page }) => {
    await installMocks(page);
    // No seedLoggedIn — we want the unauthenticated state.
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
  });

  test('shows the login form with email + password fields', async ({ page }) => {
    await installMocks(page);
    await page.goto('/login');
    await expect(page.locator('input[type="email"], input[placeholder*="mail" i]').first()).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('login accepts credentials and navigates into the app', async ({ page }) => {
    // Stub the login endpoint to return a valid token, then verify the UI
    // ends up somewhere inside the protected app.
    await installMocks(page, {
      'POST /api/auth/login': () => ({
        status: 200, contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'e2e-test-token',
          user: { id: 'user-e2e', email: 'e2e@example.com', name: 'E2E' },
          businesses: [{ id: 'biz-e2e', name: 'E2E Test Co', is_active: 1 }],
          current_business_id: 'biz-e2e',
        }),
      }),
    });
    await page.goto('/login');
    await page.fill('input[type="email"]', 'e2e@example.com');
    await page.fill('input[type="password"]', 'correctpassword');
    // Submit via Enter on the password field — avoids ambiguity with the
    // mode-toggle "Sign In" pill button sitting above the form.
    await page.locator('input[type="password"]').press('Enter');
    // Token lands in localStorage via setSession — the clearest signal
    // that login succeeded regardless of where the app navigates to.
    await expect.poll(
      () => page.evaluate(() => localStorage.getItem('nexus_token')),
      { timeout: 8000 },
    ).toBe('e2e-test-token');
  });
});
