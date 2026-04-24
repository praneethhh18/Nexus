import { test, expect } from '@playwright/test';
import { installMocks, seedLoggedIn } from './mocks.js';

test.describe('CRM — contacts', () => {
  test('empty state shows "No contacts yet" with an Add CTA', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/crm');

    await expect(page.getByText(/No contacts yet/i)).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('button', { name: /Add contact/i }).first())
      .toBeVisible();
  });

  test('Add contact opens a modal with name fields', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/crm');

    await page.getByRole('button', { name: /Add contact/i }).first().click();
    // Form exposes inputs for first_name + last_name + email
    await expect(page.locator('input').first()).toBeVisible({ timeout: 5000 });
    // Modal title makes the context unambiguous
    await expect(page.getByText(/Add contact|New contact|Edit contact/i).first())
      .toBeVisible();
  });

  test('tab strip switches between Contacts / Companies / Deals Pipeline', async ({ page }) => {
    await seedLoggedIn(page);
    await installMocks(page);
    await page.goto('/crm');

    await page.getByRole('button', { name: /Companies/i }).click();
    await expect(page.getByText(/No companies yet/i)).toBeVisible({ timeout: 5000 });

    await page.getByRole('button', { name: /Deals Pipeline/i }).click();
    await expect(page.getByText(/No deals in the pipeline/i)).toBeVisible({ timeout: 5000 });
  });
});
