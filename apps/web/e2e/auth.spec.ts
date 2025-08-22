import { test, expect } from '@playwright/test';

// Assumes dev server running on localhost:3000
const base = 'http://localhost:3000';

test.describe('Auth & Guarded Routes', () => {
  test('redirects unauthenticated content page to login', async ({ page }) => {
    console.log('Visiting /content unauthenticated');
    await page.goto(base + '/content');
    await page.waitForURL('**/login');
    await expect(page.locator('text=Login')).toBeVisible();
  });

  test('login and access content', async ({ page }) => {
    console.log('Going to login page');
    await page.goto(base + '/login');
    await page.fill('input[type="text"]', 'learner1');
    await page.fill('input[type="password"]', 'pass');
    await page.click('button:has-text("Login")');
    console.log('Logged in, navigating to /content');
    await expect(page.locator('text=Logged in as')).toBeVisible();
    await page.goto(base + '/content');
    await expect(page.locator('text=Generate Lesson')).toBeVisible();
  });

  test('instructor role required for author page', async ({ page }) => {
    console.log('Login as learner');
    await page.goto(base + '/login');
    await page.fill('input[type="text"]', 'learner1');
    await page.fill('input[type="password"]', 'pass');
    await page.click('button:has-text("Login")');
    await page.goto(base + '/author');
    // should redirect because learner
    await page.waitForURL(base + '/');
    // re-login as instructor
    console.log('Re-login as instructor');
    await page.goto(base + '/login');
    await page.fill('input[type="text"]', 'inst_admin');
    await page.fill('input[type="password"]', 'pass');
    await page.click('button:has-text("Login")');
    await page.goto(base + '/author');
    await expect(page.locator('text=Authoring Workspace')).toBeVisible();
  });
});
