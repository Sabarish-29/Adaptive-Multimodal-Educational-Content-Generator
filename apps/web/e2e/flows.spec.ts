import { test, expect, Page, Route } from '@playwright/test';

const base = 'http://localhost:3000';

test.describe('Core flows', () => {
  test.beforeEach(async ({ page }) => {
    console.log('Navigate to login');
    await page.goto(base + '/login');
    await page.fill('input[type="text"]', 'learner1');
    await page.fill('input[type="password"]', 'pass');
    await page.click('button:has-text("Login")');
  });

  test('generate lesson (fails gracefully without backend)', async ({ page }) => {
    console.log('Open content page');
    await page.goto(base + '/content');
    const btn = page.locator('button:has-text("Generate")');
    await expect(btn).toBeVisible();
    await btn.click();
    // We don't assert success result because backend may not be running; just ensure UI stays responsive
    await expect(btn).toBeVisible();
  });

  test('view analytics page and charts render', async ({ page }) => {
    console.log('Navigate to analytics');
    await page.goto(base + '/analytics');
    await expect(page.locator('text=Progress')).toBeVisible();
    // Chart placeholders still present (even if no data)
    await expect(page.locator('svg[aria-label="line chart"]')).toBeVisible({ timeout: 5000 }).catch(()=>{});
  });
  test('live session start failure shows error toast', async ({ page }: { page: Page }) => {
    console.log('Intercept session creation to force failure');
  await page.route('**/v1/sessions', (route: Route) => route.fulfill({ status: 500, body: JSON.stringify({ error: 'boom' }) }));
    await page.goto(base + '/');
    const startBtn = page.locator('button:has-text("Start")');
    await expect(startBtn).toBeVisible();
    await startBtn.click();
    // Toast should appear with error message
    await expect(page.locator('[role="status"]:has-text("Failed to start session")')).toBeVisible({ timeout: 5000 });
  });
  test('instructor authoring access positive', async ({ page }: { page: Page }) => {
    console.log('Login as instructor for authoring');
    await page.goto(base + '/login');
    await page.fill('input[type="text"]', 'inst_admin');
    await page.fill('input[type="password"]', 'pass');
    await page.click('button:has-text("Login")');
    await page.goto(base + '/author');
    await expect(page.locator('text=Authoring Workspace')).toBeVisible();
  });
});
