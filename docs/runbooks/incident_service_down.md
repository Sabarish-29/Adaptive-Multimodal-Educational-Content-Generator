# Runbook: Service Down

## Detection
- Alerts from uptime probe / HTTP 5xx surge / missing heartbeats.

## Immediate Actions
1. Identify failing service container: `docker ps | findstr api-<service>`
2. Check logs: `docker logs <container>`
3. Health endpoint: `curl http://localhost:<port>/healthz`
4. If crash-loop: review recent deploy diff.

## Remediation Steps
- Config issue: compare env with `.env.example`.
- Dependency error: rebuild `docker compose build <service>`.
- Mongo connectivity: verify `mongodb` container healthy.

## Escalation
- If data corruption suspected: put service in maintenance (return 503) and snapshot Mongo volume.

## Postmortem Data
- Timeline, root cause, impact scope, mitigation, action items.
