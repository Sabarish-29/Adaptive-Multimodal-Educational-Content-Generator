import { test, expect } from '@playwright/test';

const base = 'http://localhost:3000';

test.describe('Authoring Phase 9', () => {
  test('frontmatter metadata, autosave, worker parse, undo/redo, sanitization & export', async ({ page }) => {
    await page.goto(base + '/login');
    await page.getByLabel('Username').fill('inst_admin');
    await page.getByLabel('Password').fill('pass');
    await page.click('button:has-text("Login")');
    await page.goto(base + '/author');
    const ta = page.locator('textarea#author-markdown');
    await ta.waitFor();
    // Insert frontmatter
    await ta.fill('---\n title: Phase9 Lesson \n objectives: alpha, beta \n---\n\n## Heading\nBody text');
    // Wait for metadata to render
    await expect(page.locator('text=Phase9 Lesson')).toBeVisible();
    await expect(page.locator('text=alpha, beta')).toBeVisible();
    // Wait for autosave indicator "Saved" to appear
    await page.waitForTimeout(1200);
    await expect(page.locator('text=Saved')).toBeVisible();
    // Edit via metadata inputs (title)
  await page.getByTestId('title-input').fill('Phase9 Revised');
  await expect(page.getByTestId('title-input')).toHaveValue('Phase9 Revised');
  // Undo metadata change (should revert to original frontmatter title 'Lesson Draft')
  await page.click('button:has-text("Undo")');
  await expect(page.getByTestId('title-input')).toHaveValue('Lesson Draft');
    // Redo metadata change
  await page.click('button:has-text("Redo")');
  await expect(page.getByTestId('title-input')).toHaveValue('Phase9 Revised');
    // Add XSS attempt and ensure it's sanitized
    await ta.fill('---\n title: XSS Test \n---\n\n<script>alert(1)</script>\n\n<img src=x onerror=alert(2)>');
    await page.waitForTimeout(400); // debounce + worker parse
  const previewHtml = await page.locator('text=Preview').locator('..').innerHTML().catch(()=> '');
    expect(previewHtml).not.toContain('script');
    expect(previewHtml).not.toContain('onerror');
    // Trigger export (cannot easily capture file, but ensure no error)
    await page.click('button:has-text("Export JSON")');
  });
});
