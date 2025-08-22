import { test, expect } from '@playwright/test';

const base = 'http://localhost:3000';

test.describe('Smoke', () => {
  test('home loads', async ({ page }) => {
      console.log('Navigating to home...');
      await page.goto(base + '/');
      console.log('Page loaded, checking text');
      await expect(page.locator('text=Developer Console')).toBeVisible();
      console.log('Smoke test completed');
    });
});
