## Release {{VERSION}} ({{DATE}})

### Summary
Concise overview (1–3 sentences) of major changes.

### Features
-

### Fixes
-

### Breaking Changes
- (List migrations / env var changes)

### Upgrade Steps
1. Backup DB / verify backup.
2. Apply migrations (if any).
3. Deploy services (order if required).
4. Verify health endpoints & metrics.

### Post-Deployment Validation
- Check Prometheus: rate_limit_denied_total recent values.
- Verify encryption_mode gauge == strong (if strong required).
- Run smoke tests (list).

### Rollback Plan
1. Redeploy previous tag.
2. Restore schema if incompatible.
3. Re-run smoke tests.

### Known Issues / Follow-ups
-
