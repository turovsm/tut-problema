import { test, expect } from '@playwright/test';

test('should load the map page correctly', async ({ page }) => {
  // Move to main page
  await page.goto('/');

  // Check logo
  await expect(page.locator('.logo__text')).toContainText('ТутПроблема');

  // Check if map is rendered
  await expect(page.locator('#map')).toBeVisible();
});
