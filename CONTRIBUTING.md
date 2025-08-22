# Contributing Guide

## Branching Strategy
- `main`: stable baseline. PRs require passing CI.
- Feature branches: `feat/<short-topic>` (e.g. `feat/adaptation-metrics`).
- Bugfix branches: `fix/<short-topic>`.
- Docs only: `docs/<short-topic>`.

## Commit Messages
Format (Conventional Commits subset):
`type(scope): concise description`
Types: feat, fix, docs, refactor, test, chore, perf, security.

Examples:
`feat(adaptation): add posterior mean to recommendation payload`
`security(auth): enforce learner self-access restriction`

## Pull Request Checklist
- [ ] OpenAPI updated (if API change)
- [ ] Tests added or adjusted
- [ ] Lint passes (ruff)
- [ ] No debug prints left
- [ ] Docs / README / runbooks updated if needed

## Code Style
- Python: ruff lints; prefer type hints for new code.
- FastAPI endpoints: response models where stable; avoid premature over-modeling.
- Keep service `main.py` focused; extract helpers when >400 lines.

## Testing Guidelines
- Unit: algorithmic / pure logic (bandit updates, hashing).
- Integration: endpoint behavior with in-memory FastAPI + httpx AsyncClient.
- Contract: schemathesis against `docs/api/openapi.yaml` (non-501 endpoints).
- Avoid external network in tests; mock if needed.

## Feature Flags
Environment variables `FEATURE_*` gate optional capabilities (caption, tts, field_encryption). Default off in prod.

## Security Practices
- Never commit secrets (.env is example only).
- Use audit logging for security-relevant events (content generate, session events, adaptation feedback pending addition).
- Prefer fail-secure over fail-open beyond Phase 0 (currently some fail-open stubs remain).

## Performance / Observability
- Add Prometheus metrics under `/metrics` for new services when adding business-critical endpoints.
- Use structured JSON logs (middleware pattern) with `request_id` to aid correlation.

## Dependency Management
- Pin direct production dependencies with compatible (`==` or appropriate constraint) in each service `requirements.txt`.
- Add dev-only tools to root `requirements-dev.txt`.

## Adding a New Model Adapter
1. Implement Protocol in `packages/model_adapters/adaptive_model_adapters`.
2. Register key in `factory.py`.
3. Add feature flag if optional.
4. Update docs + runbook if operational.

## Adding a New Service
1. Scaffold `services/<name>/` with Dockerfile, requirements, and `main.py`.
2. Implement minimal `/healthz` and add to docker-compose.
3. Add OpenAPI endpoints to unified spec.
4. Add CI matrix include if tests.

## Release Process (Future)
1. Tag semantic version `vX.Y.Z` after changelog update.
2. Build & push docker images (multi-service) with tag + commit SHA.
3. Publish generated client SDK (if applicable).

## Questions / Issues
Open GitHub Issues with template; include service name, reproduction steps, expected vs actual behavior, logs snippet.
