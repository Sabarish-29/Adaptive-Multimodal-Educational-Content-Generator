"""Cognitive monitoring Kafka event schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional


class CognitiveLoadUpdated(BaseModel):
    """Emitted when cognitive load is reassessed."""
    event_type: str = "cognitive.load.updated"
    student_id: str
    session_id: str
    cognitive_load: int
    emotional_state: str
    attention_level: int
    fatigue_index: int
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class InterventionTriggered(BaseModel):
    """Emitted when an intervention is triggered."""
    event_type: str = "cognitive.intervention.triggered"
    student_id: str
    session_id: str
    intervention_type: str
    urgency: str  # critical | warning | info
    details: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AttentionAlert(BaseModel):
    """Emitted when attention drops below threshold."""
    event_type: str = "cognitive.attention.alert"
    student_id: str
    session_id: str
    attention_level: int
    threshold: int = 50
    duration_below_s: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
