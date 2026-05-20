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

    // The deals-tab label is industry-aware (services/industryTerms.js):
    // 'Deal pipeline' for generic workspaces, 'Sales pipeline' for SaaS,
    // 'Bookings pipeline' for Hospitality, 'Listing pipeline' for Real
    // estate, etc. Match any tab whose label ends in 'pipeline' so the
    // test stays green across all 22 industry presets.
    await page.getByRole('button', { name: /pipeline/i }).first().click();
    // Empty state copy is also industry-tuned. Match the generic
    // "no deals" / "no leads" / "no listings" pattern.
    await expect(
      page.getByText(/no (deals|leads|listings|bookings|appointments|orders).*pipeline|pipeline.*empty|nothing in your pipeline/i)
    ).toBeVisible({ timeout: 5000 });
  });
});
