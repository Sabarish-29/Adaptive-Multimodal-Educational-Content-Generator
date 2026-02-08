"""
NeuroSync AI – Content Architect Agent
Multi-modal content generation with knowledge graph integration.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import uvicorn
from datetime import datetime
from enum import Enum

app = FastAPI(
    title="Content Architect Agent",
    description="Multi-modal content generation with knowledge graph planning",
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


class ContentModality(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    INTERACTIVE = "interactive"
    VIDEO = "video"
    AR = "ar"


class ContentRequest(BaseModel):
    concept: str
    student_id: str
    cognitive_load: int = 0
    preferred_modality: Optional[ContentModality] = None
    difficulty_level: Optional[str] = "intermediate"
    context: Optional[Dict[str, Any]] = {}


class ContentBlock(BaseModel):
    modality: ContentModality
    content: Any
    metadata: Dict[str, Any] = {}


class ContentResponse(BaseModel):
    concept: str
    blocks: List[ContentBlock]
    prerequisites: List[str] = []
    related_concepts: List[str] = []
    difficulty: str = "intermediate"
    estimated_time_minutes: int = 10
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ConceptNode(BaseModel):
    """Knowledge graph node."""
    concept_id: str
    name: str
    domain: str
    prerequisites: List[str] = []
    difficulty: float = 0.5
    keywords: List[str] = []


# ============================================================================
# CONTENT GENERATION ENGINE
# ============================================================================


class ContentEngine:
    """
    Generates multi-modal educational content.
    Adapts modality based on cognitive load and student preferences.
    """

    MODALITY_THRESHOLDS = {
        (0, 30): [ContentModality.TEXT, ContentModality.INTERACTIVE],
        (30, 60): [ContentModality.TEXT, ContentModality.IMAGE],
        (60, 80): [ContentModality.IMAGE, ContentModality.VOICE],
        (80, 100): [ContentModality.VOICE],
    }

    def select_modalities(
        self,
        cognitive_load: int,
        preferred: Optional[ContentModality] = None,
    ) -> List[ContentModality]:
        """Select best modalities given current cognitive load."""
        for (lo, hi), modalities in self.MODALITY_THRESHOLDS.items():
            if lo <= cognitive_load < hi:
                if preferred and preferred in modalities:
                    return [preferred] + [m for m in modalities if m != preferred]
                return modalities
        return [ContentModality.VOICE]

    async def generate(self, request: ContentRequest) -> ContentResponse:
        """Generate multi-modal content for the given concept."""
        modalities = self.select_modalities(
            request.cognitive_load, request.preferred_modality
        )

        blocks = []
        for modality in modalities:
            block = await self._generate_block(request.concept, modality, request.difficulty_level)
            blocks.append(block)

        # TODO: Query Neo4j for prerequisites and related concepts
        return ContentResponse(
            concept=request.concept,
            blocks=blocks,
            prerequisites=[],
            related_concepts=[],
            difficulty=request.difficulty_level or "intermediate",
            estimated_time_minutes=self._estimate_time(blocks),
        )

    async def _generate_block(
        self, concept: str, modality: ContentModality, difficulty: str
    ) -> ContentBlock:
        """Generate a single content block (placeholder)."""
        if modality == ContentModality.TEXT:
            return ContentBlock(
                modality=modality,
                content={
                    "title": f"Understanding {concept}",
                    "body": f"Placeholder text content for {concept} at {difficulty} level.",
                    "format": "markdown",
                },
                metadata={"generator": "text_generator", "model": "gpt-4"},
            )
        elif modality == ContentModality.IMAGE:
            return ContentBlock(
                modality=modality,
                content={
                    "url": f"/generated/images/{concept}.png",
                    "alt_text": f"Diagram illustrating {concept}",
                    "caption": f"Visual representation of {concept}",
                },
                metadata={"generator": "image_generator", "model": "sdxl"},
            )
        elif modality == ContentModality.VOICE:
            return ContentBlock(
                modality=modality,
                content={
                    "url": f"/generated/audio/{concept}.mp3",
                    "transcript": f"Audio explanation of {concept}",
                    "duration_seconds": 120,
                },
                metadata={"generator": "voice_generator", "model": "tts-1"},
            )
        else:
            return ContentBlock(
                modality=modality,
                content={"type": modality.value, "placeholder": True},
                metadata={"generator": "interactive_generator"},
            )

    def _estimate_time(self, blocks: List[ContentBlock]) -> int:
        """Rough time estimate in minutes per block type."""
        time_map = {
            ContentModality.TEXT: 5,
            ContentModality.IMAGE: 2,
            ContentModality.VOICE: 3,
            ContentModality.INTERACTIVE: 8,
            ContentModality.VIDEO: 5,
            ContentModality.AR: 10,
        }
        return sum(time_map.get(b.modality, 5) for b in blocks)


content_engine = ContentEngine()


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "content-architect",
        "version": "1.0.0",
        "capabilities": [
            "text_generation",
            "image_generation",
            "voice_generation",
            "interactive_content",
            "knowledge_graph",
        ],
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/v1/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest):
    """Generate multi-modal educational content."""
    try:
        return await content_engine.generate(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/concept/decompose")
async def decompose_concept(concept: str, depth: int = 2):
    """Break a concept into prerequisite sub-concepts."""
    # TODO: integrate with Neo4j knowledge graph
    return {
        "concept": concept,
        "sub_concepts": [
            {"name": f"{concept}_subtopic_1", "depth": 1},
            {"name": f"{concept}_subtopic_2", "depth": 1},
        ],
        "depth": depth,
    }


@app.get("/v1/concept/{concept_id}/prerequisites")
async def get_prerequisites(concept_id: str):
    """Get prerequisite chain from the knowledge graph."""
    return {"concept_id": concept_id, "prerequisites": [], "graph_source": "neo4j"}


# ============================================================================
# LIFECYCLE
# ============================================================================


@app.on_event("startup")
async def startup_event():
    print("📐 Content Architect starting up...")
    print("✅ Content Architect ready!")


@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Content Architect shutting down...")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8012, reload=True, log_level="info")
