"""
Unit tests for shared packages: event-schemas, agent-sdk, ml-models.
"""

import pytest


# ---------------------------------------------------------------------------
# Event Schemas
# ---------------------------------------------------------------------------

class TestStudentEvents:
    def test_session_started_round_trip(self):
        try:
            from packages.event_schemas.student_events import SessionStarted
        except ImportError:
            pytest.skip("event-schemas not importable")

        evt = SessionStarted(session_id="s1", student_id="st1", topic="math")
        assert evt.event_type == "session_started"
        assert evt.model_dump()["session_id"] == "s1"

    def test_answer_submitted(self):
        try:
            from packages.event_schemas.student_events import AnswerSubmitted
        except ImportError:
            pytest.skip("event-schemas not importable")

        evt = AnswerSubmitted(
            session_id="s1", student_id="st1",
            concept="algebra", answer="42", correct=True,
        )
        assert evt.correct is True


class TestCognitiveEvents:
    def test_cognitive_load_updated(self):
        try:
            from packages.event_schemas.cognitive_events import CognitiveLoadUpdated
        except ImportError:
            pytest.skip("event-schemas not importable")

        evt = CognitiveLoadUpdated(
            session_id="s1", student_id="st1",
            cognitive_load=0.6, signals={},
        )
        assert 0 <= evt.cognitive_load <= 1

    def test_intervention_triggered(self):
        try:
            from packages.event_schemas.cognitive_events import InterventionTriggered
        except ImportError:
            pytest.skip("event-schemas not importable")

        evt = InterventionTriggered(
            session_id="s1", student_id="st1",
            intervention_type="BREAK", reason="high cognitive load",
        )
        assert evt.intervention_type == "BREAK"


# ---------------------------------------------------------------------------
# Agent SDK
# ---------------------------------------------------------------------------

class TestAgentCommunicator:
    def test_instantiation(self):
        try:
            from packages.agent_sdk.communication import AgentCommunicator
        except ImportError:
            pytest.skip("agent-sdk not importable")

        comm = AgentCommunicator(base_url="http://localhost:8010")
        assert comm.base_url == "http://localhost:8010"


# ---------------------------------------------------------------------------
# ML Models
# ---------------------------------------------------------------------------

class TestTrainingConfig:
    def test_config_defaults(self):
        try:
            from packages.ml_models.training import TrainingConfig
        except ImportError:
            pytest.skip("ml-models not importable")

        cfg = TrainingConfig(model_name="test", output_dir="/tmp/test")
        assert cfg.epochs > 0
        assert cfg.batch_size > 0
