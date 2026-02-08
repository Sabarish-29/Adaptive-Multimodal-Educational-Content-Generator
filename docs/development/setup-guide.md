# NeuroSync AI – Development Setup Guide

## Prerequisites

- **Python 3.11+**
- **Node.js 20+** (for the web frontend)
- **Docker & Docker Compose v2**
- **Git**

## Quick Start

### 1. Clone & enter the repository

```bash
git clone <repo-url>
cd Adaptive-Multimodal-Educational-Content-Generator
```

### 2. Copy environment variables

```bash
cp configs/environments/development.env .env
```

Edit `.env` to set your `OPENAI_API_KEY` and any other secrets.

### 3. Start infrastructure

```bash
# Core data stores (MongoDB, Redis, MinIO)
docker compose -f infrastructure/compose/docker-compose.yml up -d

# New infrastructure (Kafka, Neo4j, Qdrant, Prometheus, Grafana)
docker compose -f infrastructure/compose/docker-compose.infra.yml up -d
```

### 4. Initialise databases

```bash
pip install motor neo4j
python scripts/setup/init_databases.py
python scripts/setup/seed_knowledge_graph.py
```

### 5. Set up Kafka topics

```bash
# From inside the Kafka container:
docker exec -it ns-kafka bash scripts/setup/setup_kafka.sh kafka:29092
```

### 6. Install Python dependencies

```bash
# Create a virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux

# Install all agent requirements
pip install -r services/orchestrator/requirements.txt
pip install -r services/cognitive-guardian/requirements.txt
pip install -r services/content-architect/requirements.txt
pip install -r services/tutor-agent/requirements.txt
pip install -r services/intervention-agent/requirements.txt
pip install -r services/progress-analyst/requirements.txt
pip install -r services/peer-connector/requirements.txt
```

### 7. Run agents locally

```bash
# In separate terminals:
uvicorn services.orchestrator.main:app --port 8010 --reload
uvicorn services.cognitive_guardian.main:app --port 8011 --reload
uvicorn services.content_architect.main:app --port 8012 --reload
uvicorn services.tutor_agent.main:app --port 8013 --reload
uvicorn services.intervention_agent.main:app --port 8014 --reload
uvicorn services.progress_analyst.main:app --port 8015 --reload
uvicorn services.peer_connector.main:app --port 8016 --reload
```

Or use Docker Compose:

```bash
docker compose -f infrastructure/compose/docker-compose.agents.yml up --build
```

### 8. Run legacy services (optional)

```bash
# Use the existing scripts
powershell scripts/run_all_services.ps1
```

### 9. Verify health

```bash
# Check all agents
curl http://localhost:8010/health  # Orchestrator
curl http://localhost:8011/health  # Cognitive Guardian
curl http://localhost:8012/health  # Content Architect
curl http://localhost:8013/health  # Tutor Agent
curl http://localhost:8014/health  # Intervention Agent
curl http://localhost:8015/health  # Progress Analyst
curl http://localhost:8016/health  # Peer Connector
```

## Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requires services running)
pytest tests/integration/ -v -m integration

# End-to-end tests
pytest tests/e2e/ -v -m e2e
```

## Monitoring

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3001 (admin/admin)

## Useful Makefile Commands

```bash
make ns-up          # Start all infrastructure + agents
make ns-down        # Stop everything
make ns-agents      # Start only agents
make ns-infra       # Start only infrastructure
make ns-test        # Run all tests
make ns-lint        # Lint all Python files
```
