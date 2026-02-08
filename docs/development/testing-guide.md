# NeuroSync AI – Testing Guide

## Test Categories

| Category | Directory | Marker | Dependencies |
|----------|-----------|--------|-------------|
| Unit | `tests/unit/` | _(none)_ | None (mocked) |
| Integration | `tests/integration/` | `@pytest.mark.integration` | Services running |
| End-to-End | `tests/e2e/` | `@pytest.mark.e2e` | Full stack |
| Load | `loadtests/` | _(k6/locust)_ | Full stack |

## Running Tests

```bash
# All unit tests
pytest tests/unit/ -v

# Single agent
pytest tests/unit/test_cognitive_guardian.py -v

# Integration tests (requires services)
pytest tests/integration/ -v -m integration

# E2E tests
pytest tests/e2e/ -v -m e2e

# With coverage
pytest tests/unit/ --cov=services --cov-report=html
```

## Test Structure

### Unit Tests

Each agent has a corresponding test file:

```
tests/unit/
├── test_cognitive_guardian.py
├── test_content_architect.py
├── test_tutor_agent.py
├── test_intervention_agent.py
├── test_progress_analyst.py
├── test_peer_connector.py
├── test_orchestrator.py
└── test_shared_packages.py
```

### Integration Tests

```
tests/integration/
└── test_agent_communication.py
```

Tests inter-agent HTTP communication, event schema serialisation,
and health-check contracts.

### E2E Tests

```
tests/e2e/
└── test_learning_session.py
```

Simulates a full learning session through the orchestrator.

## Writing Tests

### Agent test pattern

```python
class TestMyFeature:
    def test_happy_path(self):
        try:
            from services.my_agent.main import MyClass
        except ImportError:
            pytest.skip("agent not importable")

        instance = MyClass()
        result = instance.do_something(input_data)
        assert result == expected
```

### Mocking external services

```python
from unittest.mock import AsyncMock, patch

@patch("services.content_architect.graph.knowledge_graph.AsyncGraphDatabase")
async def test_knowledge_graph(mock_neo4j):
    mock_neo4j.driver.return_value = AsyncMock()
    # ...
```

## pytest Configuration

Add to `pyproject.toml` or `pytest.ini`:

```ini
[tool.pytest.ini_options]
markers = [
    "integration: integration tests requiring running services",
    "e2e: end-to-end tests requiring full stack",
]
testpaths = ["tests"]
asyncio_mode = "auto"
```
