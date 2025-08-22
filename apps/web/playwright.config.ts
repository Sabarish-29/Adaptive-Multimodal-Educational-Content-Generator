import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  retries: 0,
  timeout: 30000,
  use: {
    headless: true,
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry'
  },
  webServer: {
    // Use production build for deterministic e2e (avoids dev overlay portals intercepting clicks)
    command: 'npm run build && npm run start',
    port: 3000,
    reuseExistingServer: true,
    timeout: 180000
  },
  reporter: [['list'], ['json', { outputFile: 'playwright-report/results.json' }]]
});
