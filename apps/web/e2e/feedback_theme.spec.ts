import { test, expect } from '@playwright/test';

const base = 'http://localhost:3000';

test.describe('Feedback & Theme', () => {
  test('submit positive feedback with tags', async ({ page }) => {
  await page.goto(base + '/login');
  await page.getByLabel('Username').fill('inst_admin');
  await page.getByLabel('Password').fill('pass');
    await page.click('button:has-text("Login")');
    await page.goto(base + '/');
    // Stub lesson generation API so bundle appears without backend
    await page.route('**/v1/generate/lesson', async route => {
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json', 'x-request-id': 'pw-test-rid' },
        body: JSON.stringify({ bundle_id: 'bundle_test', items: [] })
      });
    });
    // Stub analytics feedback submission so widget can show success
    await page.route('**/v1/feedback', async route => {
      const request = route.request();
      if(request.method() === 'POST') {
        await route.fulfill({
          status: 201,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ stored: true })
        });
      } else {
        await route.continue();
      }
    });
  const genBtn = page.locator('button:has-text("Generate")').first();
  await genBtn.waitFor({ state: 'visible', timeout: 5000 });
  await genBtn.click();
    // Wait for feedback widget and open modal normally
    const thumbsUp = page.locator('button[aria-label="Thumbs up"]');
    await thumbsUp.waitFor({ state: 'visible', timeout: 10000 });
    await thumbsUp.click();
    await expect(page.locator('text=Content Feedback')).toBeVisible();
    const tagBtn = page.locator('button:has-text("helpful")');
    if(await tagBtn.isVisible()) await tagBtn.click();
    const tagBtn2 = page.locator('button:has-text("engaging")');
    if(await tagBtn2.isVisible()) await tagBtn2.click();
    const submit = page.locator('button:has-text("Submit")');
    await submit.click();
  await expect(page.locator('text=Thanks! Saved.')).toBeVisible({ timeout: 8000 });
  });

  test('theme persists after toggle', async ({ page }) => {
    await page.goto(base + '/');
  // Button text shows target theme (what you'll switch to), so capture initial label
  const btn = page.locator('button:has-text("Light"), button:has-text("Dark")').first();
  await btn.waitFor({ state:'visible' });
  const initialLabel = await btn.textContent(); // 'Light' means current theme is dark
  await btn.click();
  // After click, label should flip
  const flippedLabel = initialLabel === 'Light' ? 'Dark' : 'Light';
  await expect(page.locator(`button:has-text("${flippedLabel}")`)).toBeVisible();
  await page.reload();
  // Persistence: after reload, label should remain flipped (since theme stored)
  await expect(page.locator(`button:has-text("${flippedLabel}")`)).toBeVisible();
  });
});
