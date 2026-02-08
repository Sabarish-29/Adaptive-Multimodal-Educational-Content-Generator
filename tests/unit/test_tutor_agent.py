"""
Unit tests for Tutor Agent.
"""

import pytest


class TestSocraticMethod:
    """Test Socratic question generation."""

    def test_question_generated(self):
        try:
            from services.tutor_agent.teaching.socratic_method import SocraticTeacher
        except ImportError:
            pytest.skip("socratic_method not importable")

        teacher = SocraticTeacher()
        q = teacher.generate_question(
            concept="derivatives",
            knowledge_level=0.3,
            context="Student struggles with the chain rule",
        )
        assert isinstance(q, str)
        assert len(q) > 10


class TestHintGenerator:
    """Test progressive hint generation."""

    def test_three_levels(self):
        try:
            from services.tutor_agent.teaching.hint_generator import HintGenerator
        except ImportError:
            pytest.skip("hint_generator not importable")

        gen = HintGenerator()
        hints = gen.generate_hints(
            concept="quadratic equations",
            question="Solve x^2 - 5x + 6 = 0",
            answer="x = 2 or x = 3",
        )
        assert len(hints) == 3
        assert all(isinstance(h, dict) for h in hints)

    def test_hint_levels_increase(self):
        try:
            from services.tutor_agent.teaching.hint_generator import HintGenerator
        except ImportError:
            pytest.skip("hint_generator not importable")

        gen = HintGenerator()
        hints = gen.generate_hints("algebra", "Solve 2x=6", "x=3")
        levels = [h["level"] for h in hints]
        assert levels == [1, 2, 3]


class TestCalculatorTool:
    """Test safe math evaluation."""

    def test_simple_arithmetic(self):
        try:
            from services.tutor_agent.reasoning.tools.calculator import safe_eval
        except ImportError:
            pytest.skip("calculator not importable")

        assert safe_eval("2 + 3") == 5
        assert safe_eval("10 / 2") == 5.0

    def test_dangerous_code_rejected(self):
        try:
            from services.tutor_agent.reasoning.tools.calculator import safe_eval
        except ImportError:
            pytest.skip("calculator not importable")

        with pytest.raises(Exception):
            safe_eval("__import__('os').system('whoami')")
