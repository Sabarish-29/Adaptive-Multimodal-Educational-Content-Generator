import { test, expect } from '@playwright/test';

const base = 'http://localhost:3000';

// Collect telemetry batches and assert vital + page view emitted.
// Uses window.__telemetry_flush exposed by telemetry lib to force send.

test.describe('Telemetry Web Vitals', () => {
  test('captures web_vital and page.view events', async ({ page }) => {
    const batches: any[] = [];
    await page.route('**/v1/telemetry/events', async route => {
      const req = route.request();
      if(req.method()==='POST'){
        try {
          const body = req.postData();
          if(body){
            batches.push(JSON.parse(body));
          }
        } catch {}
        await route.fulfill({ status:200, body: JSON.stringify({ ok: true }) });
      } else {
        await route.continue();
      }
    });

    await page.goto(base + '/');

    // Loop attempting flush until we see vitals or timeout (~6s)
    const start = Date.now();
    let foundVital = false;
    while(Date.now() - start < 6000 && !foundVital){
      await page.waitForTimeout(500);
      await page.evaluate(() => { (window as any).__telemetry_flush && (window as any).__telemetry_flush(); });
      foundVital = batches.some(b => (b.events||[]).some((e:any)=> e.type==='web_vital'));
    }

    // Consolidate all events
    const events = batches.flatMap(b => b.events || []);
    expect(events.some(e=>e.type==='page.view')).toBeTruthy();
    expect(events.some(e=>e.type==='web_vital')).toBeTruthy();
  });
});
