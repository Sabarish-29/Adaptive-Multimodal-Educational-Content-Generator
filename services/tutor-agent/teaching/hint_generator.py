"""Hint generator – progressive hints from subtle to explicit."""

from typing import Dict, Any


class HintGenerator:
    """Generates progressively more explicit hints."""

    async def generate(
        self, concept: str, problem: str, attempt: int
    ) -> Dict[str, Any]:
        levels = {
            1: f"Think about the core definition of {concept}.",
            2: f"Consider how {concept} relates to the variables in the problem.",
            3: f"Try applying the main formula for {concept} step by step: identify what you know, what you need, and plug in.",
        }
        level = min(attempt + 1, 3)
        return {
            "hint": levels[level],
            "level": level,
            "max_level": 3,
        }
