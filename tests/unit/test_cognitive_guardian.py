"""
Unit tests for Cognitive Guardian agent.
"""

import pytest
from unittest.mock import AsyncMock, patch


# ---------------------------------------------------------------------------
# Cognitive Load Calculator
# ---------------------------------------------------------------------------

class TestCognitiveLoadCalculator:
    """Test the weighted fusion of cognitive signals."""

    def _make_calculator(self):
        """Import and instantiate CognitiveLoadCalculator."""
        import sys, types
        # Minimal stub so import doesn't fail without full deps
        try:
            from services.cognitive_guardian.main import CognitiveLoadCalculator
            return CognitiveLoadCalculator()
        except ImportError:
            pytest.skip("cognitive-guardian service not importable")

    def test_all_zero_signals(self):
        calc = self._make_calculator()
        signals = {
            "hesitation_score": 0.0,
            "error_pattern_score": 0.0,
            "rereading_score": 0.0,
            "fatigue_level": 0.0,
            "attention_deviation": 0.0,
        }
        result = calc.compute(signals)
        assert result == pytest.approx(0.0, abs=0.01)

    def test_all_max_signals(self):
        calc = self._make_calculator()
        signals = {
            "hesitation_score": 1.0,
            "error_pattern_score": 1.0,
            "rereading_score": 1.0,
            "fatigue_level": 1.0,
            "attention_deviation": 1.0,
        }
        result = calc.compute(signals)
        assert result == pytest.approx(1.0, abs=0.01)

    def test_weights_sum_to_one(self):
        calc = self._make_calculator()
        total = sum(calc.weights.values())
        assert total == pytest.approx(1.0, abs=1e-6)

    def test_partial_signals(self):
        calc = self._make_calculator()
        signals = {
            "hesitation_score": 0.5,
            "error_pattern_score": 0.8,
            "rereading_score": 0.0,
            "fatigue_level": 0.0,
            "attention_deviation": 0.0,
        }
        result = calc.compute(signals)
        expected = 0.25 * 0.5 + 0.35 * 0.8
        assert result == pytest.approx(expected, abs=0.01)


# ---------------------------------------------------------------------------
# Intervention Trigger
# ---------------------------------------------------------------------------

class TestInterventionTrigger:
    """Test rule-based trigger logic."""

    def test_immediate_trigger_on_high_load(self):
        """Cognitive load > 0.85 should fire an immediate trigger."""
        try:
            from services.cognitive_guardian.models.intervention_trigger import InterventionTrigger
        except ImportError:
            pytest.skip("intervention_trigger not importable")

        trigger = InterventionTrigger()
        result = trigger.evaluate(cognitive_load=0.90, consecutive_errors=0, fatigue=0.0)
        assert result is not None
        assert result["level"] == "immediate"

    def test_no_trigger_on_low_load(self):
        try:
            from services.cognitive_guardian.models.intervention_trigger import InterventionTrigger
        except ImportError:
            pytest.skip("intervention_trigger not importable")

        trigger = InterventionTrigger()
        result = trigger.evaluate(cognitive_load=0.30, consecutive_errors=0, fatigue=0.2)
        assert result is None
