"""
Unit tests for Progress Analyst agent.
"""

import pytest


class TestBayesianMastery:
    """Test Bayesian mastery update logic."""

    def test_mastery_increases_on_correct(self):
        try:
            from services.progress_analyst.main import AnalyticsEngine
        except ImportError:
            pytest.skip("progress-analyst not importable")

        engine = AnalyticsEngine()
        prior = 0.3
        updated = engine.update_mastery(prior, evidence=0.9)
        assert updated > prior

    def test_mastery_decreases_on_wrong(self):
        try:
            from services.progress_analyst.main import AnalyticsEngine
        except ImportError:
            pytest.skip("progress-analyst not importable")

        engine = AnalyticsEngine()
        prior = 0.7
        updated = engine.update_mastery(prior, evidence=0.1)
        assert updated < prior

    def test_mastery_bounded(self):
        try:
            from services.progress_analyst.main import AnalyticsEngine
        except ImportError:
            pytest.skip("progress-analyst not importable")

        engine = AnalyticsEngine()
        result = engine.update_mastery(0.99, evidence=1.0)
        assert 0.0 <= result <= 1.0


class TestLearningVelocity:
    """Test learning velocity computation."""

    def test_positive_velocity(self):
        try:
            from services.progress_analyst.analytics.learning_velocity import LearningVelocityTracker
        except ImportError:
            pytest.skip("learning_velocity not importable")

        tracker = LearningVelocityTracker()
        velocity = tracker.compute(
            mastery_history=[0.1, 0.2, 0.35, 0.5],
            time_deltas=[1.0, 1.0, 1.0],
        )
        assert velocity > 0

    def test_zero_velocity_on_plateau(self):
        try:
            from services.progress_analyst.analytics.learning_velocity import LearningVelocityTracker
        except ImportError:
            pytest.skip("learning_velocity not importable")

        tracker = LearningVelocityTracker()
        velocity = tracker.compute(
            mastery_history=[0.5, 0.5, 0.5],
            time_deltas=[1.0, 1.0],
        )
        assert velocity == pytest.approx(0.0, abs=0.01)


class TestConstellationGenerator:
    """Test constellation visualisation data generation."""

    def test_generates_nodes_and_edges(self):
        try:
            from services.progress_analyst.visualizations.constellation_generator import ConstellationGenerator
        except ImportError:
            pytest.skip("constellation_generator not importable")

        gen = ConstellationGenerator()
        skills = [
            {"id": "a", "name": "Algebra", "mastery": 0.8},
            {"id": "b", "name": "Calculus", "mastery": 0.3},
        ]
        edges = [("a", "b")]
        data = gen.generate(skills, edges)
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 2
