"""
NeuroSync AI – Learning Session Workflow

Defines the primary LangGraph workflow that routes a learning session
through the cognitive-guardian → content-architect → tutor → progress loop.
"""

from typing import Dict, Any

# Workflow is bootstrapped in orchestrator/main.py via create_learning_workflow().
# This module holds helper utilities shared across workflows.


async def build_initial_state(
    student_id: str,
    session_id: str,
    concept: str,
    preferences: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Construct the initial state dict for a new learning session."""
    return {
        "student_id": student_id,
        "session_id": session_id,
        "current_concept": concept,
        "cognitive_load": 0,
        "emotional_state": "neutral",
        "mastery_level": 0.0,
        "messages": [],
        "next_action": None,
        "preferences": preferences or {},
    }
