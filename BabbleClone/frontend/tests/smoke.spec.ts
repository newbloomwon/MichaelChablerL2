import { test, expect } from '@playwright/test';

test('smoke: home loads', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await expect(page).toHaveTitle(/BabbleClone|BabbelClone|Vite/);
  // Check for the custom header with BabbelClone branding
  const header = await page.locator('header');
  await expect(header.getByText('BabbelClone')).toBeVisible();
});
