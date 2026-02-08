"""
End-to-end tests for NeuroSync AI learning session flow.

These tests simulate a complete learning session through
the orchestrator, verifying the full agent pipeline.
"""

import pytest
import httpx

ORCHESTRATOR_URL = "http://localhost:8010"


def orchestrator_available() -> bool:
    try:
        r = httpx.get(f"{ORCHESTRATOR_URL}/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


@pytest.mark.e2e
@pytest.mark.skipif(not orchestrator_available(), reason="Orchestrator not running")
class TestLearningSessionE2E:
    """Full learning session end-to-end flow."""

    def test_start_session(self):
        payload = {
            "student_id": "e2e-student",
            "topic": "algebra",
            "concept": "linear_equations",
        }
        r = httpx.post(f"{ORCHESTRATOR_URL}/v1/session/start", json=payload, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert "session_id" in data

    def test_session_assess_and_teach_cycle(self):
        # Start
        start = httpx.post(
            f"{ORCHESTRATOR_URL}/v1/session/start",
            json={"student_id": "e2e-student", "topic": "algebra", "concept": "linear_equations"},
            timeout=30,
        )
        assert start.status_code == 200
        session_id = start.json()["session_id"]

        # Submit an interaction
        interact = httpx.post(
            f"{ORCHESTRATOR_URL}/v1/session/{session_id}/interact",
            json={
                "student_id": "e2e-student",
                "interaction_type": "answer",
                "data": {"answer": "x = 3", "correct": True},
            },
            timeout=30,
        )
        assert interact.status_code == 200

    def test_session_progress(self):
        r = httpx.get(
            f"{ORCHESTRATOR_URL}/v1/progress/e2e-student",
            timeout=10,
        )
        # May be 200 or 404 depending on state
        assert r.status_code in (200, 404)
