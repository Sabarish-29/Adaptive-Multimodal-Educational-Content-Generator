"""
Integration tests for inter-agent communication.

These tests verify that agents can communicate with each other
through the orchestrator's HTTP-based protocol.

Requires all services to be running (or uses mocks).
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_URLS = {
    "orchestrator": "http://localhost:8010",
    "cognitive_guardian": "http://localhost:8011",
    "content_architect": "http://localhost:8012",
    "tutor_agent": "http://localhost:8013",
    "intervention_agent": "http://localhost:8014",
    "progress_analyst": "http://localhost:8015",
    "peer_connector": "http://localhost:8016",
}


def is_service_up(url: str) -> bool:
    """Check if a service is reachable."""
    try:
        r = httpx.get(f"{url}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestAgentHealthChecks:
    """Verify all agents expose /health endpoints."""

    @pytest.mark.parametrize("agent,url", list(BASE_URLS.items()))
    def test_health_endpoint(self, agent, url):
        if not is_service_up(url):
            pytest.skip(f"{agent} not running at {url}")

        r = httpx.get(f"{url}/health")
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") in ("ok", "healthy")


@pytest.mark.integration
class TestOrchestratorToAgents:
    """Test orchestrator → agent communication."""

    def test_cognitive_guardian_assess(self):
        url = BASE_URLS["cognitive_guardian"]
        if not is_service_up(url):
            pytest.skip("cognitive-guardian not running")

        payload = {
            "session_id": "test-session",
            "student_id": "test-student",
            "interactions": [],
        }
        r = httpx.post(f"{url}/v1/assess", json=payload, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert "cognitive_load" in data

    def test_content_architect_generate(self):
        url = BASE_URLS["content_architect"]
        if not is_service_up(url):
            pytest.skip("content-architect not running")

        payload = {
            "concept": "derivatives",
            "cognitive_load": 0.5,
            "mastery": 0.3,
            "preferred_modality": None,
        }
        r = httpx.post(f"{url}/v1/generate", json=payload, timeout=30)
        assert r.status_code == 200

    def test_tutor_agent_teach(self):
        url = BASE_URLS["tutor_agent"]
        if not is_service_up(url):
            pytest.skip("tutor-agent not running")

        payload = {
            "student_id": "test-student",
            "concept": "algebra",
            "question": "What is 2x = 6?",
            "cognitive_load": 0.4,
        }
        r = httpx.post(f"{url}/v1/teach", json=payload, timeout=15)
        assert r.status_code == 200


@pytest.mark.integration
class TestEventSchemas:
    """Test event schema serialisation/deserialisation."""

    def test_session_started_event(self):
        try:
            from packages.event_schemas.student_events import SessionStarted
        except ImportError:
            pytest.skip("event-schemas not importable")

        event = SessionStarted(
            session_id="s1",
            student_id="st1",
            topic="mathematics",
        )
        data = event.model_dump()
        assert data["session_id"] == "s1"
        assert data["event_type"] == "session_started"

    def test_cognitive_load_event(self):
        try:
            from packages.event_schemas.cognitive_events import CognitiveLoadUpdated
        except ImportError:
            pytest.skip("event-schemas not importable")

        event = CognitiveLoadUpdated(
            session_id="s1",
            student_id="st1",
            cognitive_load=0.75,
            signals={"hesitation": 0.5, "errors": 0.8},
        )
        data = event.model_dump()
        assert data["cognitive_load"] == 0.75
