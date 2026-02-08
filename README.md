<div align="center">

# NeuroSync AI

### Multi-Agent Cognitive Learning Ecosystem

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)
[![License](https://img.shields.io/badge/license-Apache--2.0-orange.svg)](LICENSE)

*An AI-powered adaptive education platform that uses specialised agents to monitor cognitive load in real-time, generate personalised multimodal content, and deliver intelligent interventions — transforming how students learn.*

</div>

---

## What is NeuroSync AI?

NeuroSync AI replaces traditional monolithic adaptive learning with a **network of 6 specialised AI agents** coordinated by a LangGraph-based orchestrator. Each agent handles one aspect of the learning experience:

| Agent | Port | Responsibility |
|-------|------|---------------|
| **Cognitive Guardian** | 8011 | Real-time cognitive load monitoring, attention tracking, fatigue estimation |
| **Content Architect** | 8012 | Multi-modal content generation, knowledge graph, RAG pipeline |
| **Tutor Agent** | 8013 | Socratic teaching, progressive hints, answer evaluation |
| **Intervention Agent** | 8014 | DQN-based intervention selection, break scheduling |
| **Progress Analyst** | 8015 | Bayesian mastery tracking, learning velocity, constellation visualisation |
| **Peer Connector** | 8016 | Intelligent peer matching, federated learning with differential privacy |

The **Orchestrator** (port 8010) coordinates the agents via a LangGraph state machine that loops until mastery > 0.85, routing to the Intervention Agent when cognitive load exceeds 0.7.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Frontend (Next.js 14)                  │
│         Constellation UI · Learning Interface       │
└────────────────────┬────────────────────────────────┘
                     │ REST / WebSocket / SSE
                     ▼
┌─────────────────────────────────────────────────────┐
│              API Gateway (FastAPI :9090)             │
└────────────────────┬────────────────────────────────┘
                     ▼
          ┌── Orchestrator (8010) ──┐
          │   LangGraph Engine      │
          └─┬──┬──┬──┬──┬──┬───────┘
            │  │  │  │  │  │
  ┌─────────┘  │  │  │  │  └─────────┐
  ▼            ▼  ▼  ▼  ▼            ▼
Cognitive   Content Tutor Inter-  Progress  Peer
Guardian    Architect Agent vention Analyst  Connector
(8011)      (8012)  (8013) (8014)  (8015)   (8016)
  │            │       │      │       │        │
  └────────────┴───────┴──┬───┴───────┴────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   Kafka (events)   Neo4j (knowledge)  Qdrant (vectors)
        │
   MongoDB · Redis · MinIO
```

## Quick Start

### Prerequisites

- Python 3.11+, Node.js 20+, Docker & Docker Compose v2

### 1. Clone & configure

```bash
git clone <repo-url>
cd Adaptive-Multimodal-Educational-Content-Generator
cp configs/environments/development.env .env
# Edit .env → set OPENAI_API_KEY
```

### 2. Start infrastructure

```bash
# Core data stores
docker compose -f infrastructure/compose/docker-compose.yml up -d

# AI infrastructure (Kafka, Neo4j, Qdrant, monitoring)
docker compose -f infrastructure/compose/docker-compose.infra.yml up -d
```

### 3. Initialise databases

```bash
pip install motor neo4j
python scripts/setup/init_databases.py
python scripts/setup/seed_knowledge_graph.py
```

### 4. Start agents

```bash
# Option A: Docker Compose (recommended)
docker compose -f infrastructure/compose/docker-compose.agents.yml up --build

# Option B: Local development (each in separate terminal)
uvicorn services.orchestrator.main:app --port 8010 --reload
uvicorn services.cognitive_guardian.main:app --port 8011 --reload
uvicorn services.content_architect.main:app --port 8012 --reload
uvicorn services.tutor_agent.main:app --port 8013 --reload
uvicorn services.intervention_agent.main:app --port 8014 --reload
uvicorn services.progress_analyst.main:app --port 8015 --reload
uvicorn services.peer_connector.main:app --port 8016 --reload
```

### 5. Verify

```bash
curl http://localhost:8010/health   # Orchestrator
curl http://localhost:8011/health   # Cognitive Guardian
# ... all agents should return {"status": "ok"}
```

### 6. Run legacy services (optional)

```bash
powershell scripts/run_all_services.ps1
```

### 7. Frontend

```bash
cd apps/web && npm install && npm run dev
# Visit http://localhost:3000
```

## Project Structure

```
├── services/
│   ├── orchestrator/         # LangGraph-based agent coordinator (8010)
│   ├── cognitive-guardian/    # Cognitive load monitoring (8011)
│   ├── content-architect/    # Multi-modal content generation (8012)
│   ├── tutor-agent/          # Socratic teaching + hints (8013)
│   ├── intervention-agent/   # RL-based intervention selection (8014)
│   ├── progress-analyst/     # Mastery tracking + visualisation (8015)
│   ├── peer-connector/       # Peer matching + federated learning (8016)
│   ├── legacy/               # Preserved v1 services
│   ├── adaptation/           # Legacy adaptation service (8001)
│   ├── sessions/             # Legacy sessions service (8002)
│   └── ...                   # Other legacy services
├── packages/
│   ├── ml-models/            # Shared ML model abstractions
│   ├── event-schemas/        # Pydantic event schemas (Kafka)
│   └── agent-sdk/            # Agent communication SDK
├── infrastructure/
│   ├── compose/              # Docker Compose files
│   └── docker/               # Base Dockerfiles
├── configs/
│   ├── agents/               # Per-agent YAML configuration
│   ├── models/               # ML model hyper-parameters
│   └── environments/         # Environment files (dev/staging/prod)
├── ml/
│   └── training/             # ML training pipelines
│       ├── cognitive_load_lstm/
│       ├── knowledge_graph_gnn/
│       └── teaching_policy_dqn/
├── apps/
│   ├── api-gateway/          # FastAPI gateway (:9090)
│   └── web/                  # Next.js 14 frontend
├── tests/
│   ├── unit/                 # Agent unit tests
│   ├── integration/          # Inter-agent communication tests
│   └── e2e/                  # Full learning session tests
├── docs/
│   ├── architecture/         # Architecture documentation
│   └── development/          # Setup & development guides
└── scripts/
    └── setup/                # Database init, KG seeding, Kafka topics
```

## ML Models

| Model | Type | Purpose |
|-------|------|---------|
| Cognitive Load LSTM | PyTorch LSTM | Predict future cognitive load |
| Knowledge Graph GNN | PyTorch Geometric GCN | Infer mastery for unobserved concepts |
| Teaching Policy DQN | PyTorch DQN | Learn optimal intervention strategies |

Train models:
```bash
python ml/training/cognitive_load_lstm/train.py --epochs 50
python ml/training/teaching_policy_dqn/train.py --epochs 200
```

## Testing

```bash
pytest tests/unit/ -v                          # Unit tests
pytest tests/integration/ -v -m integration    # Integration (services required)
pytest tests/e2e/ -v -m e2e                    # End-to-end
```

## Monitoring

- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3001 (admin/admin)

All agents expose `/metrics` endpoints scraped by Prometheus.

## Documentation

- [Architecture Overview](docs/architecture/01-overview.md)
- [Agent Reference](docs/architecture/02-agents.md)
- [Data Flow](docs/architecture/03-data-flow.md)
- [ML Models](docs/architecture/04-ml-models.md)
- [Setup Guide](docs/development/setup-guide.md)
- [Agent Development](docs/development/agent-development.md)
- [Testing Guide](docs/development/testing-guide.md)

---

## Legacy System

The original adaptive learning platform services remain under `services/` and are fully functional. Legacy services include profiles (8000), adaptation (8001), sessions (8002), content generation (8003), RAG (8005), curriculum (8006), admin (8007), and analytics (8008). See [README.legacy.md](README.legacy.md) for the original documentation including feature flags, encryption, rate limiting, circuit breakers, and SSE.

## Makefile

```bash
make ns-up          # Start full NeuroSync stack
make ns-down        # Stop everything
make ns-agents      # Start only agents
make ns-infra       # Start only infrastructure
make ns-test        # Run all tests
make ns-lint        # Lint Python code
make ns-train-all   # Train all ML models
```

## License

Apache-2.0
