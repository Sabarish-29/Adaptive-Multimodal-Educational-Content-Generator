# Adaptive Multimodal Educational Content Generator

Version: 1.1 (August 18, 2025)

An accessibility-first, adaptive, multimodal educational platform for neurodiverse learners. This monorepo contains frontend (Next.js), backend microservices (FastAPI), model adapters, RAG pipeline, contextual bandit adaptation, evaluation & safety, and analytics — all backed by MongoDB.

## Architecture (Quick View)
### Streaming Generation (Phase 11)
Frontend now supports experimental streaming lesson generation mode (toggle "Stream"). It expects a backend endpoint `POST /v1/generate/lesson/stream` returning newline-delimited JSON objects:
```
{"part":"Introduction ..."}
{"part":"Section 1 ..."}
...
{"part":"Summary ...","done":true}
```
Each line must be a standalone JSON object; `part` is appended in order. Final object SHOULD include `done:true`. Errors should terminate the response early; client emits `gen.stream.error` telemetry.

```
UI (Next.js) --> API Services (FastAPI) --> MongoDB / Redis / MinIO
							   |             \- Vector / RAG (hash-embed stub)
							   \-> Model Adapters (LLM/VLM/TTS stubs)
```

## Quickstart (Local)

Prereqs: Docker, Docker Compose, Node 18+, Python 3.11+, Make (optional on Windows via `make.exe` or use npm scripts), GPU (optional) for model services.

1. Copy env templates:
```
cp .env.example .env
```
2. Start stack:
```
docker compose -f infra/compose/docker-compose.dev.yml up -d --build
```
3. Seed demo data:
```
python data/seeds/seed_demo.py
```
4. Run demo flow (optional):
```
python scripts/demo_flow.py
```
5. Visit web app: http://localhost:3000

SSE Recommendations (sessions) stream every 5s after starting a session (see demo_flow or UI integration forthcoming).

### Integration Smoke Test
Run a fast cross-service validation (health, session create, adaptation, SSE optional, metrics):
```
python scripts/integration_smoke.py --sse-events 2
```
Skip SSE for quicker CI baseline:
```
python scripts/integration_smoke.py --skip-sse
```
Exit code is non-zero on failure, so this can gate PRs. Use `--out-json report.json` to archive results.

Fallback Behavior (ContentGen): If legacy `contentgen.main` fails to import (e.g. path issues), the boot wrapper loads a minimal module (`contentgen_minimal`) providing `/healthz`, `/metrics`, and `POST /v1/generate/lesson` so the smoke test still passes. Health JSON will include `"mode":"minimal"` in this case.

### Feature Flags
Set in environment (`.env`) to toggle optional components:
	- Optional: set `FIELD_ENCRYPTION_KEY` (base64 32 bytes) to enable AES-GCM instead of placeholder if `cryptography` installed.
	- Optional: `PII_HASH_SALT` for stable HMAC-SHA256 hashing of identifiers.
	- Optional: `REQUIRE_STRONG_ENCRYPTION=true` to fail startup if AES-GCM not active while feature enabled.
### Feature Flags
Set in environment (`.env`) to toggle optional components:
- `FEATURE_CAPTION=true` enable caption endpoint & asset generation
- `FEATURE_TTS=true` enable TTS synthesis endpoint & audio asset
- `FEATURE_FIELD_ENCRYPTION=true` enables pluggable field encryption subsystem.
	- Key sourcing priority:
		1. Static local key: `FIELD_ENCRYPTION_KEY` (base64 16/24/32 raw bytes) -> AES-GCM (encryption_mode=2)
		2. AWS KMS data key: set `ENCRYPTION_PROVIDER=aws_kms` and `AWS_KMS_KEY_ID=<arn|alias/...>` -> generates and caches an AES_256 data key via `GenerateDataKey` (encryption_mode=3)
		3. Placeholder fallback: XOR/base64 `SimpleObfuscator` (encryption_mode=1)
	- Rotation (KMS): refresh interval via `ENCRYPTION_KMS_DATA_KEY_TTL_SECONDS` (default 3600) – process-local cache (lightweight, not envelope per record yet).
	- Hashing: `PII_HASH_SALT` for deterministic HMAC-SHA256 of identifiers (non-reversible, for joins/metrics).
	- Enforcement: `REQUIRE_STRONG_ENCRYPTION=true` forces import-time failure unless either a valid `FIELD_ENCRYPTION_KEY` *or* a usable KMS config is present when feature is enabled.
	- Future hardening (not yet implemented): persist ciphertext data key, dual-key rotation window, per-record envelope keys.

### Testing / Performance Env Vars
These variables accelerate local & CI test runs without altering production behavior:


Encryption enforcement:

### Local Testing Speedups

| Concern | Default Behavior | FAST / Fallback Behavior |
|---------|------------------|--------------------------|
| Sessions SSE stream | Calls adaptation service each interval (HTTP) | Synthetic recommendations inline when `FAST_TEST_MODE=true` |
| Mongo connection | Driver waits up to several seconds for server selection | If connection fails within `MONGODB_TIMEOUT_MS`, in-memory stub DB is used (sessions) |
| Adaptation call timeout | 5.0s HTTP client timeout | 1.5s (or value from `RECOMMEND_HTTP_TIMEOUT`) in fast mode |

Example fast test run:
```bash
FAST_TEST_MODE=true MONGODB_TIMEOUT_MS=200 pytest -q
```

To test strong encryption success path:
```bash
export FEATURE_FIELD_ENCRYPTION=true REQUIRE_STRONG_ENCRYPTION=true
export FIELD_ENCRYPTION_KEY=$(python - <<'PY'
import os, base64; print(base64.b64encode(os.urandom(32)).decode())
PY
)
pytest -q tests/test_encryption_roundtrip.py
```

To verify enforcement failure (should raise at import):
Generate a strong (32-byte) encryption key quickly:
```bash
python scripts/gen_field_key.py 32
# or without length (defaults 32)
python scripts/gen_field_key.py > key.txt
```
```bash
export FEATURE_FIELD_ENCRYPTION=true REQUIRE_STRONG_ENCRYPTION=true
unset FIELD_ENCRYPTION_KEY
pytest -q tests/test_rate_limit_denied_metric.py::test_require_strong_encryption_enforced
```

### Request Correlation
Clients may send `X-Request-ID` (otherwise generated). Propagated in responses & logs for cross-service tracing. Frontend demo attaches a per-page UUID; SSE includes `rid` query param fallback.

### Rate Limiting
Redis-backed sliding window (falls back to in-memory) limiting for mutating endpoints (POST/PUT/PATCH):
	- fine-grained: `SESSIONS_CREATE_RATE_PER_MIN` (session creation) and `SESSIONS_EVENT_RATE_PER_MIN` (event ingestion) if provided
Returns `429` with `{ "detail": "rate_limit_exceeded" }` and includes `X-RateLimit-Remaining` header on successful requests.

SSE tuning (sessions service):
- `SESSIONS_SSE_HEARTBEAT_SECONDS` (default 15) periodic heartbeat event interval.
- `SESSIONS_SSE_MAX_EVENTS_PER_SEC` (0 = unlimited) throttles recommendation events to mitigate client backpressure or burst CPU.

### Caching
Disable by omitting Redis or leaving `aioredis` uninstalled.

### Metrics (Prometheus)
Core sessions-related:
- `sessions_recommendation_events_total{source="synthetic"|"http"}`
- `adaptation_call_latency_seconds{status="ok"|"unavailable"|"error"}` (Histogram optional)
- `sessions_adaptation_circuit_state` (Gauge 0=closed,1=open,2=half_open) & `sessions_adaptation_circuit_open_total`
- `sessions_sse_heartbeats_total`
- `sessions_sse_disconnects_total`
Scrape each service `/metrics` endpoint.

### Dev Tooling
- Coverage enforced via `.coveragerc` (current fail-under 80%; raise incrementally after sustained green).
- Load tests: see `loadtests/` (`sessions_recommend.js`, `sessions_adaptation_mix.js`) and baseline results in `docs/perf/`.
- Secret scanning via `gitleaks` (config: `.gitleaks.toml`).
- Dependency policy + vulnerability gate: `scripts/dependency_policy.py` (allowlists: `.dependency-allowlist`, `.vuln-allowlist`).

### Circuit Breaker / Adaptive Retry (Sessions -> Adaptation)
Environment variables:
- `SESSIONS_ADAPTATION_CB_FAILURE_THRESHOLD` (default 3)
- `SESSIONS_ADAPTATION_CB_RESET_SECONDS` (default 30)
- `SESSIONS_ADAPTATION_RETRY_BACKOFF_BASE` (default 0.5)
- `SESSIONS_ADAPTATION_RETRY_BACKOFF_MAX` (default 5.0)

Metrics:
- `sessions_adaptation_circuit_state` (0=closed,1=open,2=half_open)
- `sessions_adaptation_circuit_open_total`

### RL Placeholders
Endpoints under `/v1/rl/*` return 501 (except status) pending future reinforcement learning phase.

## Key Services (Phase 0)

## Documentation
### Continuous Integration Overview
GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

To emulate CI fast suite locally:
```bash
FAST_TEST_MODE=true MONGODB_TIMEOUT_MS=150 pytest -q tests/test_sessions_memory_fallback.py tests/test_sse_fast_mode.py tests/test_rate_limit_denied_metric.py::test_require_strong_encryption_enforced
```
Runbooks: see `docs/runbooks/*` (redis_outage, rate_limit_spike, encryption_key_rotation).
Schema & Migrations scaffold: `scripts/migrations/` and `schema_version` field on new writes.
Architecture / Security / Operations docs in `docs/` for deeper details.

### Load Testing & Performance Regression

K6 script `loadtest/k6_sessions.js` exercises session creation and single event ingest per iteration.

Establish a baseline (store artifact under version control or artifact storage):

```bash
k6 run --vus 10 --duration 1m --summary-export results/baseline.json loadtest/k6_sessions.js
```

Run a comparison load and export current results:

```bash
k6 run --vus 10 --duration 1m --summary-export results/latest.json loadtest/k6_sessions.js
```

Check for p95 regression (>20% increase by default) using the regression script:

```bash
python scripts/perf_regression.py --current results/latest.json --baseline results/baseline.json --max-p95-increase 0.2
```

Integrate into nightly CI: run k6, then perf_regression; fail job on regression to surface early performance drift.

## License
Apache-2.0 (placeholder)

## Frontend ↔ Backend Integration (Local Dev)

1. Start Python services with hot reload:
	- `pwsh scripts/run_all_services.ps1` (adaptation :8001, contentgen :8002, sessions :8003, profiles :8004, rag :8005)
2. Frontend env file `apps/web/.env.local` (added) maps these service URLs via `NEXT_PUBLIC_*` vars consumed in `src/lib/api.ts`.
3. Run Next.js dev: `cd apps/web; npm run dev` and visit http://localhost:3000.
4. CORS: Sessions & Adaptation now include permissive dev CORS (origin `FRONTEND_ORIGIN` env or http://localhost:3000). For production prefer a gateway or same-origin deployment and remove broad CORS.
5. SSE: Session recommendations stream through `/v1/sessions/{id}/live` (Server-Sent Events). If/when auth is enforced, use cookie-based auth or a signed query token—EventSource cannot add custom Authorization headers.
6. Optional Gateway: Minimal FastAPI gateway at `apps/api-gateway/main.py` can unify routes under one origin (run `uvicorn apps.api-gateway.main:app --reload --port 9000`). Frontend can then switch to relative `/api/...` calls (future refactor: introduce a single `NEXT_PUBLIC_API_BASE`).
7. Request Correlation: Frontend adds `X-Request-ID`; SSE includes `rid` parameter for linkage; keep this for distributed tracing.
8. Rate Limit Feedback: Frontend should detect HTTP 429 and surface a retry-after message (TODO UI enhancement).

Security Note: Dev mock auth still issues an unsigned base64 token; replace with real JWT + HttpOnly cookie before moving beyond local prototyping.
