#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const reportPath = path.join(process.cwd(), 'playwright-report', 'results.json');
if(!fs.existsSync(reportPath)){
  console.log('[e2e-summary] No results file at', reportPath);
  process.exit(0);
}
try {
  const json = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
  const suites = json.suites || [];
  let passed=0, failed=0, skipped=0, duration=0;
  const cases = [];
  const walk = (suite) => {
    (suite.specs||[]).forEach(spec => {
      (spec.tests||[]).forEach(t => {
        const status = t.results?.[0]?.status || 'unknown';
        if(status==='passed') passed++; else if(status==='failed') failed++; else skipped++;
        duration += (t.results?.[0]?.duration || 0);
        cases.push({ title: spec.title, status, duration: t.results?.[0]?.duration || 0 });
      });
    });
    (suite.suites||[]).forEach(walk);
  };
  suites.forEach(walk);
  const summary = { passed, failed, skipped, durationMs: duration, cases };
  const outFile = path.join(process.cwd(), 'playwright-report', 'summary.json');
  fs.writeFileSync(outFile, JSON.stringify(summary, null, 2));
  console.log('[e2e-summary]', JSON.stringify(summary));
  if(failed>0) process.exit(1);
} catch (e){
  console.error('[e2e-summary] Failed to parse results:', e.message);
  process.exit(1);
}
