"""
NeuroSync AI – Intervention Agent
Reinforcement learning-based intervention strategies.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
from datetime import datetime
from enum import Enum

app = FastAPI(
    title="Intervention Agent",
    description="RL-based learning intervention system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# MODELS
# ============================================================================


class InterventionType(str, Enum):
    BREAK = "suggest_break"
    SWITCH_MODALITY = "switch_modality"
    SIMPLIFY = "simplify_content"
    ENCOURAGE = "encourage_and_hint"
    GAMIFY = "gamify"
    PEER_HELP = "peer_help"
    REVIEW = "review_prerequisites"


class InterventionRequest(BaseModel):
    student_id: str
    session_id: Optional[str] = None
    cognitive_load: int = 0
    emotional_state: str = "calm"
    fatigue_index: int = 0
    attention_level: int = 100
    mastery_level: float = 0.5
    session_duration_minutes: int = 0


class InterventionResponse(BaseModel):
    intervention_needed: bool
    intervention_type: Optional[InterventionType] = None
    intervention: Dict[str, Any] = {}
    confidence: float = 0.0
    reasoning: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# INTERVENTION STRATEGY ENGINE
# ============================================================================


class StrategyEngine:
    """
    Selects the best intervention strategy.
    Currently rule-based; will be replaced with DQN policy.
    """

    def select(self, request: InterventionRequest) -> InterventionResponse:
        # High cognitive load
        if request.cognitive_load > 90:
            return self._build_response(
                InterventionType.BREAK,
                {"message": "You've been working hard! Take a 5-minute break.", "duration_minutes": 5},
                confidence=0.95,
                reasoning="Cognitive load critically high (>90).",
            )

        if request.cognitive_load > 80:
            return self._build_response(
                InterventionType.SWITCH_MODALITY,
                {"message": "Let's try a different format to keep things fresh.", "suggested_modality": "voice"},
                confidence=0.88,
                reasoning="Cognitive load high (>80). Switching modality can reduce load.",
            )

        if request.cognitive_load > 70:
            return self._build_response(
                InterventionType.SIMPLIFY,
                {"message": "Let me simplify this a bit.", "new_difficulty": "beginner"},
                confidence=0.82,
                reasoning="Cognitive load elevated (>70).",
            )

        # Emotional triggers
        if request.emotional_state == "frustrated":
            return self._build_response(
                InterventionType.ENCOURAGE,
                {"message": "It's okay to find this challenging. Let me give you a hint!", "include_hint": True},
                confidence=0.85,
                reasoning="Student appears frustrated.",
            )

        if request.emotional_state == "confused":
            return self._build_response(
                InterventionType.REVIEW,
                {"message": "Let's revisit some foundations first.", "review_concept": True},
                confidence=0.80,
                reasoning="Student appears confused.",
            )

        # Fatigue
        if request.fatigue_index > 80:
            return self._build_response(
                InterventionType.BREAK,
                {"message": "You've been studying a while. A short break can boost focus!", "duration_minutes": 10},
                confidence=0.90,
                reasoning="High fatigue index.",
            )

        # No intervention needed
        return InterventionResponse(
            intervention_needed=False,
            confidence=0.75,
            reasoning="All metrics within acceptable range.",
        )

    def _build_response(
        self,
        intervention_type: InterventionType,
        intervention: Dict[str, Any],
        confidence: float,
        reasoning: str,
    ) -> InterventionResponse:
        return InterventionResponse(
            intervention_needed=True,
            intervention_type=intervention_type,
            intervention=intervention,
            confidence=confidence,
            reasoning=reasoning,
        )


strategy_engine = StrategyEngine()


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "intervention-agent",
        "version": "1.0.0",
        "capabilities": [
            "break_suggestion",
            "modality_switching",
            "content_simplification",
            "encouragement",
            "gamification",
        ],
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/v1/intervene", response_model=InterventionResponse)
async def intervene(request: InterventionRequest):
    """Determine if an intervention is needed and what type."""
    return strategy_engine.select(request)


@app.post("/v1/feedback")
async def record_feedback(
    student_id: str, intervention_type: str, accepted: bool, rating: int = 0
):
    """Record student feedback on an intervention for RL reward signal."""
    # TODO: store for DQN training
    return {
        "recorded": True,
        "student_id": student_id,
        "intervention_type": intervention_type,
        "accepted": accepted,
        "rating": rating,
    }


# ============================================================================
# LIFECYCLE
# ============================================================================


@app.on_event("startup")
async def startup_event():
    print("🛡️ Intervention Agent starting up...")
    print("✅ Intervention Agent ready!")


@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Intervention Agent shutting down...")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8014, reload=True, log_level="info")
