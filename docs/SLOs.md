## Service SLOs (Initial Draft)

### Availability
- Target 99.5% monthly for core API (sessions, adaptation, contentgen, profiles).

### Latency (p95)
- Session create: < 300ms (in-memory fallback excluded)
- Adaptation recommend-next: < 500ms (excluding model cold starts)
- Content generation (lesson) synchronous portion: < 2s

### Error Budget
- 0.5% of requests may fail outside success SLA per month.

### Rate Limit Denials
- Maintain < 1% of total POST requests (excluding intentional abusive test scenarios).

### Alert Thresholds
- Adaptation error ratio > 5% over 5m -> page.
- Encryption mode downgrade (strong required but not active) -> page.
- Sustained 429 rate > 2% over 10m -> investigate.

### Review Cadence
- Monthly SLO review & adjust thresholds based on observed traffic.

### Instrumentation Gaps
- Need explicit histogram for session create latency.
- Add counter for authz denials.
