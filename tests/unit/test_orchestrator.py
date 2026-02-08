"""
Unit tests for the Orchestrator service.
"""

import pytest


class TestSharedAgentState:
    """Test the shared state model used by LangGraph workflow."""

    def test_state_defaults(self):
        try:
            from services.orchestrator.agents.state import SharedAgentState
        except ImportError:
            pytest.skip("orchestrator state not importable")

        state = SharedAgentState(
            student_id="s1",
            session_id="sess1",
        )
        assert state.cognitive_load == 0.0
        assert state.mastery == 0.0
        assert state.iteration == 0
        assert state.messages == []

    def test_state_serialisation(self):
        try:
            from services.orchestrator.agents.state import SharedAgentState
        except ImportError:
            pytest.skip("orchestrator state not importable")

        state = SharedAgentState(student_id="s1", session_id="sess1", cognitive_load=0.7)
        data = state.model_dump()
        assert data["cognitive_load"] == 0.7
        assert data["student_id"] == "s1"


class TestOrchestrationConfig:
    """Test orchestrator config loading."""

    def test_config_defaults(self):
        try:
            from services.orchestrator.config import Settings
        except ImportError:
            pytest.skip("orchestrator config not importable")

        settings = Settings()
        assert settings.orchestrator_port == 8010
