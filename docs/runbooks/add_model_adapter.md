# Runbook: Add a New Model Adapter

## Goal
Integrate a new model (LLM/TTS/Caption) behind adapter interface.

## Steps
1. Create adapter class implementing interface in `packages/model_adapters/adaptive_model_adapters/<new>.py`.
2. Register class in `factory.py` ADAPTERS dict.
3. Expose model name via env var `MODEL_LLM_NAME` (or appropriate kind).
4. Rebuild contentgen service (Docker) or install package locally.
5. Smoke test generation endpoint.

## Validation
- Verify provenance hash changes only with prompt/model id.
- Confirm deterministic stub replaced by real output.

## Rollback
- Set env var back to previous adapter name and redeploy.
