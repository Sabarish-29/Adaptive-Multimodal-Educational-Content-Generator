# NeuroSync AI – Agent Development Guide

## Creating a New Agent

### 1. Directory Structure

```
services/your-agent/
├── __init__.py
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── Dockerfile           # Container definition
├── your_module/         # Domain-specific logic
│   ├── __init__.py
│   └── ...
└── README.md            # Agent documentation
```

### 2. Agent Template

Every agent must expose:
- `GET /health` – Returns `{"status": "ok", "service": "<name>"}`
- `POST /v1/<action>` – Primary endpoint(s)
- Prometheus metrics at `/metrics` (optional but recommended)

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load models, connect to databases
    yield
    # Shutdown: close connections

app = FastAPI(title="Your Agent", version="1.0.0", lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "your-agent"}

@app.post("/v1/action")
async def action(request: YourRequest):
    # Process and return result
    ...
```

### 3. Register with Orchestrator

1. Add the agent URL to `services/orchestrator/config.py`:
   ```python
   your_agent_url: str = "http://localhost:PORT"
   ```

2. Add a node in the LangGraph workflow
   (`services/orchestrator/workflows/learning_session.py`)

3. Add the service to `infrastructure/compose/docker-compose.agents.yml`

4. Create a config file at `configs/agents/your-agent.yaml`

### 4. Event Integration

Publish events to Kafka using the agent SDK:

```python
from packages.agent_sdk.communication import AgentCommunicator

comm = AgentCommunicator(base_url="http://localhost:8010")
await comm.emit_event("neurosync.your-topic", event_data)
```

### 5. Testing

- Unit tests: `tests/unit/test_your_agent.py`
- Integration: `tests/integration/` (with `@pytest.mark.integration`)
- E2E: `tests/e2e/`

### 6. Graceful Degradation

Every ML-based feature must have a rule-based fallback:

```python
try:
    result = ml_model.predict(input_data)
except Exception:
    result = rule_based_fallback(input_data)
```

## Best Practices

1. **Pydantic models** for all request/response schemas
2. **Async** database drivers (motor, neo4j AsyncDriver)
3. **Structured logging** with JSON format
4. **Health checks** that verify downstream dependencies
5. **Configuration** via environment variables with Pydantic Settings
6. **Timeouts** on all external calls
7. **Circuit breakers** for inter-agent communication
