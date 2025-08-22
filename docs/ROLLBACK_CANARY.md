## Rollback & Canary Playbook

### Goals
Minimize impact of faulty deployment by gradually shifting traffic and enabling rapid safe rollback.

### Preconditions
- Previous release image/tag retained.
- Migrations backward compatible or gated by feature flags.
- Health metrics & alerting active (latency, error ratio, 429 rate, encryption_mode).

### Canary Deployment Steps
1. Deploy new version to canary (5–10% traffic).
2. Verify /health and /metrics.
3. Monitor error & latency metrics; run smoke tests.
4. Hold 15 min; if stable, increase to 25%, 50%, 100%.

### Promotion Criteria
- Error ratio <2%.
- Latency p95 within SLO.
- No abnormal spike in rate_limit_denied_total.

### Rollback Triggers
- Error ratio ≥5% for 5m.
- adaptation_call_latency_seconds p95 >2x baseline.
- encryption_mode downgrade when strong required.

### Rollback Steps
1. Route traffic back to previous version.
2. If incompatible schema: run rollback script / restore snapshot.
3. Clear inconsistent caches (targeted Redis keys).
4. Run smoke tests.
5. Post-mortem & remediation tasks.

### Post-Rollback Actions
- Incident report.
- Add regression tests.
- Improve canary checks if gap found.
