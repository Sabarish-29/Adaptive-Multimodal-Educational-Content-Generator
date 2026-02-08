"""
Unit tests for Intervention Agent.
"""

import pytest


class TestStrategyEngine:
    """Test intervention strategy selection."""

    def test_high_load_selects_break_or_simplify(self):
        try:
            from services.intervention_agent.main import StrategyEngine
        except ImportError:
            pytest.skip("intervention-agent not importable")

        engine = StrategyEngine()
        strategy = engine.select(cognitive_load=0.9, engagement=0.5, fatigue=0.3)
        assert strategy in ("BREAK", "SIMPLIFY", "SWITCH_MODALITY")

    def test_low_engagement_selects_gamify(self):
        try:
            from services.intervention_agent.main import StrategyEngine
        except ImportError:
            pytest.skip("intervention-agent not importable")

        engine = StrategyEngine()
        strategy = engine.select(cognitive_load=0.3, engagement=0.1, fatigue=0.2)
        assert strategy in ("GAMIFY", "PEER_HELP", "ENCOURAGE")


class TestRewardCalculator:
    """Test RL reward computation."""

    def test_positive_reward_on_load_reduction(self):
        try:
            from services.intervention_agent.rl.reward_calculator import RewardCalculator
        except ImportError:
            pytest.skip("reward_calculator not importable")

        calc = RewardCalculator()
        reward = calc.compute(
            load_before=0.8, load_after=0.5,
            accepted=True, rating=4,
        )
        assert reward > 0

    def test_negative_reward_on_load_increase(self):
        try:
            from services.intervention_agent.rl.reward_calculator import RewardCalculator
        except ImportError:
            pytest.skip("reward_calculator not importable")

        calc = RewardCalculator()
        reward = calc.compute(
            load_before=0.5, load_after=0.8,
            accepted=False, rating=1,
        )
        assert reward < 0


class TestBreakSuggester:
    """Test Pomodoro-based break scheduling."""

    def test_break_duration(self):
        try:
            from services.intervention_agent.strategies.break_suggester import BreakSuggester
        except ImportError:
            pytest.skip("break_suggester not importable")

        bs = BreakSuggester()
        suggestion = bs.suggest(session_duration_minutes=30, break_count=0)
        assert isinstance(suggestion, dict)
        assert "duration_minutes" in suggestion
        assert suggestion["duration_minutes"] > 0
