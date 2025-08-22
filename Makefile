PY=python

up:
	docker compose -f infra/compose/docker-compose.dev.yml up -d --build

down:
	docker compose -f infra/compose/docker-compose.dev.yml down

seed:
	$(PY) data/seeds/seed_demo.py

test:
	$(PY) -m pytest -q

test-fast:
	FAST_TEST_MODE=true MONGODB_TIMEOUT_MS=200 RECOMMEND_HTTP_TIMEOUT=1.0 $(PY) -m pytest -q

run-content:
	$(PY) -m uvicorn services.contentgen.contentgen.main:app --reload --port 8001

run-adaptation:
	$(PY) -m uvicorn services.adaptation.adaptation.main:app --reload --port 8002

run-profiles:
	$(PY) -m uvicorn services.profiles.profiles.main:app --reload --port 8003

lint:
	ruff check .

format:
	ruff format .

dev-up: bootstrap run-local

# Local dev (venv + run all services with reload)
bootstrap:
	powershell -ExecutionPolicy Bypass -File scripts/bootstrap_env.ps1 -Dev

run-local:
	powershell -ExecutionPolicy Bypass -File scripts/run_all_services.ps1

compose-logs:
	docker compose -f infra/compose/docker-compose.dev.yml logs -f --tail=200

sync-env:
	$(PY) scripts/sync_env.py

verify-env:
	$(PY) scripts/verify_env.py
