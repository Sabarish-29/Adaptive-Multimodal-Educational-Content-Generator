"""Student-related Kafka event schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional


class StudentSessionStarted(BaseModel):
    """Emitted when a student starts a learning session."""
    event_type: str = "student.session.started"
    student_id: str
    session_id: str
    concept: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}


class StudentSessionEnded(BaseModel):
    """Emitted when a student ends a learning session."""
    event_type: str = "student.session.ended"
    student_id: str
    session_id: str
    duration_minutes: int
    mastery_delta: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StudentAnswerSubmitted(BaseModel):
    """Emitted when a student submits an answer."""
    event_type: str = "student.answer.submitted"
    student_id: str
    session_id: str
    concept: str
    correct: bool
    time_taken_ms: int
    attempt: int = 1
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StudentInteraction(BaseModel):
    """Generic interaction event."""
    event_type: str = "student.interaction"
    student_id: str
    session_id: str
    interaction_type: str  # click | scroll | keystroke | navigation
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
