"""
NeuroSync AI – Tutor Agent
Socratic teaching, ReAct reasoning, and hint generation.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
from datetime import datetime

app = FastAPI(
    title="Tutor Agent",
    description="AI tutor with Socratic method, ReAct reasoning, and tool use",
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


class TeachRequest(BaseModel):
    student_id: str
    concept: str
    question: Optional[str] = None
    context: List[Dict[str, Any]] = []
    difficulty: str = "intermediate"


class TeachResponse(BaseModel):
    response: str
    explanation_type: str  # socratic | direct | hint | example
    follow_up_questions: List[str] = []
    tools_used: List[str] = []
    confidence: float = 0.9
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HintRequest(BaseModel):
    student_id: str
    concept: str
    problem: str
    attempts: int = 0


class HintResponse(BaseModel):
    hint: str
    hint_level: int  # 1=subtle, 2=moderate, 3=explicit
    remaining_hints: int


# ============================================================================
# TEACHING ENGINE
# ============================================================================


class TeachingEngine:
    """
    Multi-strategy teaching engine.
    Selects teaching approach based on student state and question type.
    """

    async def teach(self, request: TeachRequest) -> TeachResponse:
        """Process a teaching request."""
        if request.question:
            return await self._answer_question(request)
        return await self._explain_concept(request)

    async def _explain_concept(self, request: TeachRequest) -> TeachResponse:
        """Generate a concept explanation using Socratic method."""
        # TODO: integrate with LangChain ReAct agent
        return TeachResponse(
            response=(
                f"Let's explore **{request.concept}** together.\n\n"
                f"Before we dive in, what do you already know about {request.concept}? "
                f"Think about where you might have encountered this concept before."
            ),
            explanation_type="socratic",
            follow_up_questions=[
                f"What do you think is the core idea behind {request.concept}?",
                f"Can you think of a real-world example of {request.concept}?",
                f"How might {request.concept} relate to what you learned previously?",
            ],
        )

    async def _answer_question(self, request: TeachRequest) -> TeachResponse:
        """Answer a student's question with appropriate depth."""
        # TODO: ReAct agent with tool use (calculator, web search, etc.)
        return TeachResponse(
            response=(
                f"Great question about {request.concept}! "
                f"Regarding: *{request.question}*\n\n"
                f"Let me walk you through this step by step..."
            ),
            explanation_type="direct",
            follow_up_questions=[
                "Does that make sense?",
                "Would you like me to explain any part in more detail?",
            ],
        )


class HintEngine:
    """Progressive hint system – hints get more explicit with each attempt."""

    MAX_HINTS = 3

    async def generate_hint(self, request: HintRequest) -> HintResponse:
        hint_level = min(request.attempts + 1, self.MAX_HINTS)

        if hint_level == 1:
            hint = f"Think about the fundamental principles of {request.concept}."
        elif hint_level == 2:
            hint = (
                f"Consider applying the key formula or definition related to "
                f"{request.concept}. Look at the problem structure."
            )
        else:
            hint = (
                f"Here's the approach: break the problem into smaller parts. "
                f"Start by identifying the given variables and what you need to find."
            )

        return HintResponse(
            hint=hint,
            hint_level=hint_level,
            remaining_hints=max(0, self.MAX_HINTS - hint_level),
        )


teaching_engine = TeachingEngine()
hint_engine = HintEngine()


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "tutor-agent",
        "version": "1.0.0",
        "capabilities": [
            "socratic_teaching",
            "question_answering",
            "hint_generation",
            "react_reasoning",
        ],
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/v1/teach", response_model=TeachResponse)
async def teach(request: TeachRequest):
    """Provide tutoring for a concept or answer a question."""
    try:
        return await teaching_engine.teach(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/hint", response_model=HintResponse)
async def get_hint(request: HintRequest):
    """Get a progressive hint for a problem."""
    return await hint_engine.generate_hint(request)


@app.post("/v1/evaluate")
async def evaluate_answer(
    student_id: str, concept: str, answer: str, expected: str
):
    """Evaluate a student's answer and provide feedback."""
    # TODO: semantic similarity comparison using embeddings
    is_correct = answer.strip().lower() == expected.strip().lower()
    return {
        "correct": is_correct,
        "feedback": "Correct! Well done." if is_correct else "Not quite. Let me help you understand why.",
        "score": 1.0 if is_correct else 0.0,
    }


# ============================================================================
# LIFECYCLE
# ============================================================================


@app.on_event("startup")
async def startup_event():
    print("🎓 Tutor Agent starting up...")
    print("✅ Tutor Agent ready!")


@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Tutor Agent shutting down...")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8013, reload=True, log_level="info")
