"""
NeuroSync AI – Shared agent state definition.

Used by LangGraph as the TypedDict / Pydantic schema flowing
through the orchestration graph.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """A single message produced by any agent."""

    type: str  # content | tutor_message | intervention | progress
    agent: str = ""
    data: Any = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SharedAgentState(BaseModel):
    """State object flowing through the LangGraph orchestration."""

    student_id: str
    session_id: str
    current_concept: str

    # Cognitive metrics
    cognitive_load: int = 0
    emotional_state: str = "neutral"
    attention_level: int = 100
    fatigue_index: int = 0

    # Learning metrics
    mastery_level: float = 0.0
    interaction_count: int = 0

    # Accumulator
    messages: List[AgentMessage] = []
    next_action: Optional[str] = None
    metadata: Dict[str, Any] = {}
