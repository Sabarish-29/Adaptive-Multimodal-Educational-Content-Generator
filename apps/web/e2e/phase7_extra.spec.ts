import { test, expect } from '@playwright/test';

const base = 'http://localhost:3000';

test.describe('Phase 7 Additional Flows', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(base + '/login');
    await page.getByLabel('Username').fill('inst_admin');
    await page.getByLabel('Password').fill('pass');
    await page.click('button:has-text("Login")');
  });

  test('submit negative feedback with comment', async ({ page }) => {
    // Stubs
    await page.route('**/v1/generate/lesson', route => route.fulfill({ status:200, body: JSON.stringify({ bundle_id:'bundle_neg', items: [] }) }));
    await page.route('**/v1/feedback', route => {
      if(route.request().method()==='POST') return route.fulfill({ status:201, body: JSON.stringify({ stored:true }) });
      return route.continue();
    });
    await page.goto(base + '/');
    await page.locator('button:has-text("Generate")').first().click();
    const down = page.locator('button[aria-label="Thumbs down"]');
    await down.waitFor({ state:'visible' });
    await down.click();
    await expect(page.locator('text=Content Feedback')).toBeVisible();
    await page.locator('textarea').fill('Needs improvement.');
    await page.locator('button:has-text("Submit")').click();
    await expect(page.locator('text=Thanks! Saved.')).toBeVisible();
  });

  test('recommendations disable persists across reload', async ({ page }) => {
    await page.goto(base + '/');
    const checkbox = page.locator('label:has-text("Disable") input[type="checkbox"]');
    await checkbox.waitFor();
    const wasChecked = await checkbox.isChecked();
    // Toggle
    await checkbox.click();
    const newState = !wasChecked; // after click
    await page.reload();
    await expect(page.locator('label:has-text("Disable") input[type="checkbox"]')).toHaveJSProperty('checked', newState);
  });

  test('live session start success path (stub)', async ({ page }) => {
    // Stub sessions endpoint
    await page.route('**/v1/sessions', route => {
      if(route.request().method()==='POST'){
        return route.fulfill({ status:200, body: JSON.stringify({ session_id: 'sess123' }) });
      }
      return route.continue();
    });
    await page.goto(base + '/');
    const start = page.locator('button:has-text("Start")');
    await start.click();
    await expect(page.locator('text=Session: sess123')).toBeVisible();
  });

  test('telemetry page loads (stubbed data)', async ({ page }) => {
    // Stub telemetry endpoints
    await page.route('**/v1/telemetry/stats', r=> r.fulfill({ status:200, body: JSON.stringify({ types:[{ type:'feedback.submit', count:5, avgDur:12.3, p95Dur:30.1, maxDur:55.2 }] }) }));
    await page.route('**/v1/telemetry/latest*', r=> r.fulfill({ status:200, body: JSON.stringify({ events: [{ _id:'e1', type:'feedback.submit', data:{ itemId:'bundle1' }, durMs: 10.2 }] }) }));
    await page.route('**/v1/telemetry/rollups/hourly*', r=> r.fulfill({ status:200, body: JSON.stringify({ rollups:[{ hourStart: new Date().toISOString(), types:{ 'feedback.submit': { count:5 } } }] }) }));
    await page.route('**/v1/recommendations/metrics', r=> r.fulfill({ status:200, body: JSON.stringify({ windowMinutes:30, overall:{ fetches:10, clicks:2, ctr:0.2, acceptance:0.5 }, variants:[] }) }));
    await page.goto(base + '/telemetry');
    await expect(page.locator('text=Telemetry Dashboard')).toBeVisible();
  // Assert the event type appears in the Event Types card (first occurrence)
  const eventTypeHeading = page.locator('section:has-text("Event Types"), div').locator('h4:has-text("feedback.submit")').first();
  await expect(eventTypeHeading).toBeVisible();
  });
});
