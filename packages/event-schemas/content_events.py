"""Content generation Kafka event schemas."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, List


class ContentGenerated(BaseModel):
    """Emitted when content is generated for a student."""
    event_type: str = "content.generated"
    student_id: str
    session_id: str
    concept: str
    modalities: List[str]
    difficulty: str
    generation_time_ms: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ContentFeedback(BaseModel):
    """Emitted when a student reacts to content."""
    event_type: str = "content.feedback"
    student_id: str
    content_id: str
    modality: str
    rating: int  # 1-5
    helpful: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConceptMastered(BaseModel):
    """Emitted when a student masters a concept."""
    event_type: str = "content.concept.mastered"
    student_id: str
    concept: str
    mastery_level: float
    time_to_mastery_minutes: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
