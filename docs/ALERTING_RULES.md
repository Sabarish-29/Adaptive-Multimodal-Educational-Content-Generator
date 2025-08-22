# Alerting Rules (Prometheus)

This document defines recommended Prometheus recording & alerting rules for the platform. It maps service metrics to SLOs / runbooks and supplies example Alertmanager annotations. Tune thresholds per environment (staging vs prod).

## Conventions
- Labels: `severity` (page|ticket|info), `service`, `component`.
- Alert name pattern: `<service>:<component>:<condition>`.
- Duration: use a short evaluation window (e.g. 1m) for fast-detect infrastructure issues; use longer windows (5m/15m) for user-experience SLO breaches to avoid flapping.
- Runbook label: `runbook` URL path relative to repository (e.g. `docs/runbooks/rate_limit_spike.md`).

## Key Metrics Reference
| Metric | Labels | Description |
|--------|--------|-------------|
| `adaptation_call_latency_seconds` (Histogram) | status | Latency of adaptation recommend-next HTTP calls from sessions. |
| `adaptation_requests_total` | method,path,status | Total adaptation requests. |
| `sessions_recommendation_events_total` | source | Count of recommendation events emitted by sessions SSE (synthetic or http). |
| `rate_limit_denied_total` | service,path | Count of 429 denials. |
| `encryption_mode` (Gauge) | - | 0 disabled, 1 placeholder, 2 AES-GCM local, 3 AES-GCM KMS. |
| `sessions_started_total` | - | Sessions created. |
| `session_events_total` | - | Events ingested per session. |
| `adaptation_recommendations_total` | cached,strategy | Adaptation server recommendations served. |

## Recording Rules (Examples)
```yaml
# prometheus/recording_rules.yml
groups:
- name: platform_recording
  interval: 30s
  rules:
  - record: job:adaptation_request_rate:5m
    expr: sum(rate(adaptation_requests_total[5m]))
  - record: job:rate_limit_denied_ratio:5m
    expr: sum(rate(rate_limit_denied_total[5m])) / sum(rate(adaptation_requests_total[5m]) + rate(session_events_total[5m]) + rate(sessions_started_total[5m]))
  - record: job:sessions_recommendation_events_rate:5m
    expr: sum(rate(sessions_recommendation_events_total[5m]))
  - record: job:adaptation_recommend_p95_latency_seconds:5m
    expr: histogram_quantile(0.95, sum(rate(adaptation_call_latency_seconds_bucket[5m])) by (le))
  - record: job:adaptation_recommend_error_ratio:5m
    expr: sum(rate(adaptation_call_latency_seconds_count{status!="ok"}[5m])) / sum(rate(adaptation_call_latency_seconds_count[5m]))
```

## Alerting Rules
```yaml
# prometheus/alert_rules.yml
groups:
- name: platform_availability
  interval: 30s
  rules:
  - alert: adaptation:recommendation:high_p95_latency
    expr: job:adaptation_recommend_p95_latency_seconds:5m > 0.8
    for: 10m
    labels:
      severity: page
      service: adaptation
      component: recommend-next
      slo: latency
      runbook: docs/runbooks/adaptation_latency.md
    annotations:
      summary: Adaptation recommend-next p95 latency high
      description: "P95 latency {{ $value }}s > 0.8s for 10m (SLO breach risk)."

  - alert: adaptation:recommendation:high_error_ratio
    expr: job:adaptation_recommend_error_ratio:5m > 0.05 and sum(rate(adaptation_call_latency_seconds_count[5m])) > 20
    for: 5m
    labels:
      severity: page
      service: adaptation
      component: recommend-next
      slo: availability
      runbook: docs/runbooks/adaptation_errors.md
    annotations:
      summary: Adaptation recommend-next error ratio high
      description: "Error ratio >5% for 5m."

  - alert: sessions:recommendation_stream:stalled
    expr: job:sessions_recommendation_events_rate:5m == 0
    for: 5m
    labels:
      severity: page
      service: sessions
      component: sse
      runbook: docs/runbooks/sse_stall.md
    annotations:
      summary: Sessions SSE stream stalled
      description: "No recommendation events emitted in last 5m."

  - alert: global:rate_limit:spike
    expr: job:rate_limit_denied_ratio:5m > 0.15
    for: 10m
    labels:
      severity: ticket
      service: platform
      component: rate-limit
      runbook: docs/runbooks/rate_limit_spike.md
    annotations:
      summary: Elevated rate limiting
      description: ">15% of requests denied for 10m; potential abuse or misconfiguration."

  - alert: security:encryption:placeholder_in_prod
    expr: (encryption_mode == 1) and on() (environment == "prod")
    for: 2m
    labels:
      severity: page
      service: platform
      component: encryption
      runbook: docs/runbooks/encryption_key_rotation.md
    annotations:
      summary: Placeholder encryption active in production
      description: "encryption_mode=1 (placeholder) detected in prod. Must be 2 (AES local) or 3 (KMS)."

  - alert: security:encryption:mode_downgrade
    expr: clamp_min(max_over_time(encryption_mode[1h]) - encryption_mode, 0) > 0
    for: 5m
    labels:
      severity: ticket
      service: platform
      component: encryption
      runbook: docs/runbooks/encryption_key_rotation.md
    annotations:
      summary: Encryption mode downgraded recently
      description: "Observed encryption_mode decreased within 1h window; investigate key or provider regression."

  - alert: sessions:creation:drop
    expr: rate(sessions_started_total[15m]) < 0.1 and on() (environment == "prod")
    for: 30m
    labels:
      severity: ticket
      service: sessions
      component: ingress
      runbook: docs/runbooks/sessions_volume_drop.md
    annotations:
      summary: Session creation volume low
      description: "Session creation rate <0.1/s for 30m (historical baseline breach)."

- name: platform_resource_protection
  interval: 30s
  rules:
  - alert: adaptation:health:excessive_429
    expr: sum(rate(rate_limit_denied_total{service="adaptation"}[5m])) > 5
    for: 10m
    labels:
      severity: info
      service: adaptation
      component: rate-limit
      runbook: docs/runbooks/rate_limit_spike.md
    annotations:
      summary: Adaptation 429 spike
      description: ">5 denials/sec for 10m."

  - alert: sessions:health:excessive_429
    expr: sum(rate(rate_limit_denied_total{service="sessions"}[5m])) > 5
    for: 10m
    labels:
      severity: info
      service: sessions
      component: rate-limit
      runbook: docs/runbooks/rate_limit_spike.md
    annotations:
      summary: Sessions 429 spike
      description: ">5 denials/sec for 10m."
```

## Environment Label Injection
Add an external rule or relabel config that sets a synthetic `environment` label (e.g. via Prometheus relabel_configs or sidecar) so production-only alerts can filter: `environment == "prod"`.

## Alertmanager Routing (Example Snippet)
```yaml
route:
  receiver: default
  routes:
  - matchers:
    - severity = page
    receiver: pagerduty
  - matchers:
    - severity = ticket
    receiver: jira
  - matchers:
    - severity = info
    receiver: slack-info

receivers:
- name: pagerduty
  pagerduty_configs:
  - routing_key: <secret>
- name: jira
  webhook_configs:
  - url: https://jira.example.com/hooks/prom
- name: slack-info
  slack_configs:
  - channel: '#alerts-info'
```

## Runbook Mapping
| Alert | Runbook |
|-------|---------|
| global:rate_limit:spike | `docs/runbooks/rate_limit_spike.md` |
| security:encryption:placeholder_in_prod | `docs/runbooks/encryption_key_rotation.md` |
| sessions:recommendation_stream:stalled | `docs/runbooks/sse_stall.md` (to create) |
| adaptation:recommendation:high_error_ratio | `docs/runbooks/adaptation_errors.md` (to create) |

Create missing runbooks as lightweight Markdown with: impact, hypotheses, diagnostics (kubectl / logs / metrics), remediation steps, and rollback criteria.

## Future Enhancements
- Add synthetic availability probe metrics (e.g. blackbox exporter for SSE endpoint).
- Incorporate burn-rate multi-window alerts (30m & 6h) for SLO compliance.
- Add per-strategy adaptation success/error ratios once instrumented.
- Integrate anomaly detection (optional) for sudden recommendation volume spikes instead of static thresholds.
