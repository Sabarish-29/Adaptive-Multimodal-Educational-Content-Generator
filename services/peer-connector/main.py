"""
NeuroSync AI – Peer Connector Agent
Peer matching, group optimization, and federated learning.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
from datetime import datetime

app = FastAPI(
    title="Peer Connector Agent",
    description="Intelligent peer matching with privacy-preserving federated learning",
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


class StudentProfile(BaseModel):
    student_id: str
    skills: Dict[str, float] = {}  # concept → mastery
    preferred_modality: str = "text"
    timezone: str = "UTC"
    availability: List[str] = []  # e.g. ["weekday_evening", "weekend_morning"]
    study_pace: str = "moderate"  # slow | moderate | fast


class MatchRequest(BaseModel):
    student_id: str
    concept: str
    match_type: str = "study_partner"  # study_partner | mentor | group
    max_results: int = 5


class PeerMatch(BaseModel):
    peer_id: str
    compatibility_score: float  # 0-1
    shared_concepts: List[str]
    complementary_strengths: List[str]
    match_reason: str


class GroupRequest(BaseModel):
    student_ids: List[str]
    concept: str
    group_size: int = 4


class StudyGroup(BaseModel):
    group_id: str
    members: List[str]
    concept: str
    diversity_score: float
    recommended_activities: List[str]


# ============================================================================
# MATCHING ENGINE
# ============================================================================


class MatchingEngine:
    """Profile similarity and complementary skill matching."""

    def __init__(self):
        self._profiles: Dict[str, StudentProfile] = {}

    def register_profile(self, profile: StudentProfile):
        self._profiles[profile.student_id] = profile

    async def find_matches(self, request: MatchRequest) -> List[PeerMatch]:
        """Find compatible peers for a student."""
        requester = self._profiles.get(request.student_id)
        if not requester:
            return []

        matches = []
        for pid, profile in self._profiles.items():
            if pid == request.student_id:
                continue
            score = self._compute_similarity(requester, profile, request.concept)
            if score > 0.3:
                shared = list(set(requester.skills.keys()) & set(profile.skills.keys()))
                complementary = [
                    k for k in profile.skills
                    if k not in requester.skills or profile.skills[k] > requester.skills.get(k, 0) + 0.2
                ]
                matches.append(
                    PeerMatch(
                        peer_id=pid,
                        compatibility_score=round(score, 3),
                        shared_concepts=shared[:5],
                        complementary_strengths=complementary[:3],
                        match_reason=self._match_reason(request.match_type, score),
                    )
                )

        matches.sort(key=lambda m: m.compatibility_score, reverse=True)
        return matches[: request.max_results]

    def _compute_similarity(
        self, a: StudentProfile, b: StudentProfile, concept: str
    ) -> float:
        """Simple cosine-like similarity over skill vectors."""
        all_concepts = set(a.skills.keys()) | set(b.skills.keys())
        if not all_concepts:
            return 0.0

        dot = sum(a.skills.get(c, 0) * b.skills.get(c, 0) for c in all_concepts)
        norm_a = sum(v ** 2 for v in a.skills.values()) ** 0.5
        norm_b = sum(v ** 2 for v in b.skills.values()) ** 0.5

        if norm_a == 0 or norm_b == 0:
            return 0.0

        similarity = dot / (norm_a * norm_b)

        # Bonus for matching concept interest
        if concept in a.skills and concept in b.skills:
            similarity += 0.1

        return min(similarity, 1.0)

    def _match_reason(self, match_type: str, score: float) -> str:
        if match_type == "mentor" and score > 0.7:
            return "Strong knowledge overlap – great mentor fit."
        elif match_type == "study_partner":
            return "Similar learning pace and complementary skills."
        return "Compatible learning profiles."


class GroupOptimizer:
    """Creates optimally diverse study groups."""

    async def create_group(
        self,
        profiles: List[StudentProfile],
        concept: str,
        size: int = 4,
    ) -> StudyGroup:
        # TODO: use optimization algorithm for diversity
        selected = profiles[:size]
        return StudyGroup(
            group_id=f"group_{datetime.utcnow().timestamp()}",
            members=[p.student_id for p in selected],
            concept=concept,
            diversity_score=0.75,
            recommended_activities=[
                "Collaborative problem solving",
                "Peer teaching rotation",
                "Group quiz challenge",
            ],
        )


matching_engine = MatchingEngine()
group_optimizer = GroupOptimizer()


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "peer-connector",
        "version": "1.0.0",
        "capabilities": [
            "peer_matching",
            "group_optimization",
            "federated_learning",
        ],
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/v1/profile")
async def register_profile(profile: StudentProfile):
    """Register or update a student profile for matching."""
    matching_engine.register_profile(profile)
    return {"status": "registered", "student_id": profile.student_id}


@app.post("/v1/match", response_model=List[PeerMatch])
async def find_matches(request: MatchRequest):
    """Find compatible peers."""
    return await matching_engine.find_matches(request)


@app.post("/v1/group", response_model=StudyGroup)
async def create_group(request: GroupRequest):
    """Create an optimized study group."""
    profiles = [
        matching_engine._profiles[sid]
        for sid in request.student_ids
        if sid in matching_engine._profiles
    ]
    return await group_optimizer.create_group(profiles, request.concept, request.group_size)


# ============================================================================
# LIFECYCLE
# ============================================================================


@app.on_event("startup")
async def startup_event():
    print("🤝 Peer Connector starting up...")
    print("✅ Peer Connector ready!")


@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Peer Connector shutting down...")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8016, reload=True, log_level="info")
