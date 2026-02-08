"""Socratic method teaching strategy."""

from typing import List


class SocraticMethod:
    """
    Implements Socratic teaching by guiding students through
    a series of leading questions rather than direct answers.
    """

    async def generate_questions(
        self, concept: str, student_knowledge_level: float = 0.5
    ) -> List[str]:
        """Generate a sequence of Socratic questions."""
        if student_knowledge_level < 0.3:
            return [
                f"What comes to mind when you hear '{concept}'?",
                f"Where have you encountered something similar to {concept}?",
                f"What do you think the basic idea behind {concept} is?",
            ]
        elif student_knowledge_level < 0.7:
            return [
                f"Can you explain {concept} in your own words?",
                f"What would happen if we changed one key aspect of {concept}?",
                f"How does {concept} connect to what we discussed earlier?",
            ]
        else:
            return [
                f"Can you think of a case where {concept} doesn't apply?",
                f"How would you teach {concept} to someone else?",
                f"What are the limitations of the standard approach to {concept}?",
            ]
