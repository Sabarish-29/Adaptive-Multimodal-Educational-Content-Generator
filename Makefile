PY=python

# ============================================================
# NeuroSync AI Commands
# ============================================================

ns-up: ns-infra ns-agents
	@echo "NeuroSync AI stack is up"

ns-down:
	docker compose -f infrastructure/compose/docker-compose.agents.yml down
	docker compose -f infrastructure/compose/docker-compose.infra.yml down
	docker compose -f infrastructure/compose/docker-compose.yml down

ns-infra:
	docker compose -f infrastructure/compose/docker-compose.yml up -d
	docker compose -f infrastructure/compose/docker-compose.infra.yml up -d

ns-agents:
	docker compose -f infrastructure/compose/docker-compose.agents.yml up -d --build

ns-agents-logs:
	docker compose -f infrastructure/compose/docker-compose.agents.yml logs -f --tail=200

ns-init-db:
	$(PY) scripts/setup/init_databases.py
	$(PY) scripts/setup/seed_knowledge_graph.py

ns-test:
	$(PY) -m pytest tests/unit/ -v

ns-test-integration:
	$(PY) -m pytest tests/integration/ -v -m integration

ns-test-e2e:
	$(PY) -m pytest tests/e2e/ -v -m e2e

ns-test-all:
	$(PY) -m pytest tests/ -v

ns-lint:
	ruff check services/ packages/ ml/ scripts/

ns-format:
	ruff format services/ packages/ ml/ scripts/

ns-train-all:
	$(PY) ml/training/cognitive_load_lstm/train.py --epochs 50
	$(PY) ml/training/teaching_policy_dqn/train.py --epochs 200

ns-train-lstm:
	$(PY) ml/training/cognitive_load_lstm/train.py --epochs 50

ns-train-dqn:
	$(PY) ml/training/teaching_policy_dqn/train.py --epochs 200

# ============================================================
# Legacy Commands
# ============================================================

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
