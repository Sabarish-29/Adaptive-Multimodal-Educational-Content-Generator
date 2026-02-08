"""
NeuroSync AI – Progress Analyst Agent
Learning analytics, skill graph (GNN), and visualization.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
from datetime import datetime

app = FastAPI(
    title="Progress Analyst Agent",
    description="Learning analytics with GNN-based skill graphs and constellation visualizations",
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


class AnalyzeRequest(BaseModel):
    student_id: str
    concept: str
    session_data: List[Dict[str, Any]] = []
    time_spent_minutes: int = 0
    accuracy: float = 0.0


class SkillNode(BaseModel):
    concept: str
    mastery: float = 0.0  # 0-1
    velocity: float = 0.0  # learning speed
    last_practiced: Optional[datetime] = None


class ProgressReport(BaseModel):
    student_id: str
    overall_mastery: float
    skills: List[SkillNode]
    learning_velocity: float  # concepts per hour
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    streak_days: int = 0
    total_time_hours: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConstellationData(BaseModel):
    """Data for the constellation visualization."""
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    clusters: List[Dict[str, Any]]


# ============================================================================
# ANALYTICS ENGINE
# ============================================================================


class AnalyticsEngine:
    """Computes learning analytics and skill mastery."""

    def __init__(self):
        self._student_history: Dict[str, List[SkillNode]] = {}

    async def analyze(self, request: AnalyzeRequest) -> Dict[str, Any]:
        """Analyze a learning interaction and update skill graph."""
        # Compute mastery from accuracy and time
        # Simple Bayesian update (placeholder for GNN)
        prior_mastery = self._get_mastery(request.student_id, request.concept)
        evidence = request.accuracy
        posterior = prior_mastery * 0.7 + evidence * 0.3

        # Update storage
        self._update_mastery(request.student_id, request.concept, posterior)

        return {
            "mastery_level": round(posterior, 3),
            "concept": request.concept,
            "delta": round(posterior - prior_mastery, 3),
            "velocity": self._compute_velocity(request.student_id),
        }

    def _get_mastery(self, student_id: str, concept: str) -> float:
        skills = self._student_history.get(student_id, [])
        for s in skills:
            if s.concept == concept:
                return s.mastery
        return 0.3  # default prior

    def _update_mastery(self, student_id: str, concept: str, mastery: float):
        if student_id not in self._student_history:
            self._student_history[student_id] = []
        for s in self._student_history[student_id]:
            if s.concept == concept:
                s.mastery = mastery
                s.last_practiced = datetime.utcnow()
                return
        self._student_history[student_id].append(
            SkillNode(concept=concept, mastery=mastery, last_practiced=datetime.utcnow())
        )

    def _compute_velocity(self, student_id: str) -> float:
        skills = self._student_history.get(student_id, [])
        if not skills:
            return 0.0
        avg_mastery = sum(s.mastery for s in skills) / len(skills)
        return round(avg_mastery * len(skills), 2)

    async def get_report(self, student_id: str) -> ProgressReport:
        skills = self._student_history.get(student_id, [])
        if not skills:
            return ProgressReport(
                student_id=student_id,
                overall_mastery=0.0,
                skills=[],
                learning_velocity=0.0,
                strengths=[],
                weaknesses=[],
                recommendations=["Start your first lesson!"],
            )

        overall = sum(s.mastery for s in skills) / len(skills)
        sorted_skills = sorted(skills, key=lambda s: s.mastery, reverse=True)
        strengths = [s.concept for s in sorted_skills if s.mastery > 0.7]
        weaknesses = [s.concept for s in sorted_skills if s.mastery < 0.4]
        recommendations = [f"Review {w}" for w in weaknesses[:3]]

        return ProgressReport(
            student_id=student_id,
            overall_mastery=round(overall, 3),
            skills=skills,
            learning_velocity=self._compute_velocity(student_id),
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )


analytics_engine = AnalyticsEngine()


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "progress-analyst",
        "version": "1.0.0",
        "capabilities": [
            "skill_graph",
            "learning_velocity",
            "progress_report",
            "constellation_visualization",
        ],
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/v1/analyze")
async def analyze_progress(request: AnalyzeRequest):
    """Analyze a learning interaction."""
    return await analytics_engine.analyze(request)


@app.get("/v1/report/{student_id}", response_model=ProgressReport)
async def get_report(student_id: str):
    """Get a comprehensive progress report."""
    return await analytics_engine.get_report(student_id)


@app.get("/v1/constellation/{student_id}", response_model=ConstellationData)
async def get_constellation(student_id: str):
    """Get constellation visualization data for skill graph."""
    skills = analytics_engine._student_history.get(student_id, [])
    nodes = [
        {
            "id": s.concept,
            "label": s.concept,
            "size": s.mastery * 30 + 5,
            "color": _mastery_color(s.mastery),
        }
        for s in skills
    ]
    # TODO: edges from knowledge graph
    return ConstellationData(nodes=nodes, edges=[], clusters=[])


def _mastery_color(mastery: float) -> str:
    if mastery > 0.8:
        return "#10b981"  # green
    elif mastery > 0.5:
        return "#f59e0b"  # amber
    else:
        return "#ef4444"  # red


# ============================================================================
# LIFECYCLE
# ============================================================================


@app.on_event("startup")
async def startup_event():
    print("📊 Progress Analyst starting up...")
    print("✅ Progress Analyst ready!")


@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Progress Analyst shutting down...")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8015, reload=True, log_level="info")
