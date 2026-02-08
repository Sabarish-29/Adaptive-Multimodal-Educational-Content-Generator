"""
NeuroSync AI – Cognitive Guardian Agent
Real-time cognitive state monitoring and prediction.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import uvicorn
from datetime import datetime

app = FastAPI(
    title="Cognitive Guardian Agent",
    description="Real-time cognitive load detection and emotion analysis",
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


class SessionMetrics(BaseModel):
    """Real-time session metrics from the frontend."""

    session_id: str
    student_id: str
    hesitation_ms: int = 0
    error_rate: float = 0.0
    reread_count: int = 0
    session_duration_minutes: int = 0
    interaction_count: int = 0


class CognitiveAssessment(BaseModel):
    """Cognitive state assessment result."""

    session_id: str
    cognitive_load: int = Field(..., ge=0, le=100)
    emotional_state: str
    attention_level: int = Field(..., ge=0, le=100)
    fatigue_index: int = Field(..., ge=0, le=100)
    intervention_needed: bool
    recommended_action: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AttentionFrame(BaseModel):
    """Single frame of attention data from webcam."""

    session_id: str
    timestamp: float
    face_detected: bool
    eye_gaze_x: Optional[float] = None
    eye_gaze_y: Optional[float] = None
    head_pitch: Optional[float] = None
    head_yaw: Optional[float] = None
    blink_detected: bool = False


# ============================================================================
# COGNITIVE LOAD CALCULATION
# ============================================================================


class CognitiveLoadCalculator:
    """Multi-signal cognitive load estimator."""

    def __init__(self):
        self.weights = {
            "hesitation": 0.25,
            "errors": 0.35,
            "rereads": 0.20,
            "fatigue": 0.15,
            "attention": 0.05,
        }

    def calculate(
        self,
        metrics: SessionMetrics,
        attention_data: Optional[List[AttentionFrame]] = None,
    ) -> int:
        hesitation_score = min(metrics.hesitation_ms / 100, 100)
        error_score = metrics.error_rate * 100
        reread_score = min(metrics.reread_count * 15, 100)
        fatigue_score = self._calculate_fatigue(metrics.session_duration_minutes)
        attention_score = self._calculate_attention_penalty(attention_data)

        load = (
            self.weights["hesitation"] * hesitation_score
            + self.weights["errors"] * error_score
            + self.weights["rereads"] * reread_score
            + self.weights["fatigue"] * fatigue_score
            + self.weights["attention"] * attention_score
        )
        return int(min(load, 100))

    def _calculate_fatigue(self, duration_minutes: int) -> int:
        if duration_minutes < 20:
            return 0
        elif duration_minutes < 40:
            return (duration_minutes - 20) * 2
        else:
            return min(40 + (duration_minutes - 40) * 5, 100)

    def _calculate_attention_penalty(
        self, attention_data: Optional[List[AttentionFrame]]
    ) -> int:
        if not attention_data:
            return 0
        poor = sum(
            1
            for f in attention_data
            if not f.face_detected
            or (f.eye_gaze_x is not None and abs(f.eye_gaze_x) > 0.4)
            or (f.head_yaw is not None and abs(f.head_yaw) > 30)
        )
        return int(poor / len(attention_data) * 100)


# ============================================================================
# EMOTION DETECTION (placeholder – will integrate Wav2Vec2)
# ============================================================================


class EmotionDetector:
    EMOTIONS = ["calm", "frustrated", "confused", "excited", "tired"]

    def detect(self, metrics: SessionMetrics, cognitive_load: int) -> str:
        if cognitive_load > 85:
            return "frustrated"
        elif metrics.error_rate > 0.7:
            return "confused"
        elif metrics.session_duration_minutes > 45:
            return "tired"
        return "calm"


# ============================================================================
# INTERVENTION RULES
# ============================================================================


def determine_intervention(
    cognitive_load: int, emotional_state: str, fatigue: int
) -> tuple:
    if cognitive_load > 90:
        return True, "suggest_break"
    elif cognitive_load > 80:
        return True, "switch_modality"
    elif cognitive_load > 70:
        return True, "simplify_content"
    elif emotional_state == "frustrated":
        return True, "encourage_and_hint"
    elif fatigue > 80:
        return True, "suggest_break"
    return False, "continue"


# ============================================================================
# GLOBALS
# ============================================================================

calculator = CognitiveLoadCalculator()
emotion_detector = EmotionDetector()

attention_buffer: Dict[str, List[AttentionFrame]] = {}
MAX_BUFFER_SIZE = 100


# ============================================================================
# ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "cognitive-guardian",
        "version": "1.0.0",
        "capabilities": [
            "cognitive_load_assessment",
            "emotion_detection",
            "attention_tracking",
            "intervention_recommendation",
        ],
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/v1/assess", response_model=CognitiveAssessment)
async def assess_cognitive_state(metrics: SessionMetrics):
    attention_data = attention_buffer.get(metrics.session_id, [])
    cognitive_load = calculator.calculate(metrics, attention_data)
    emotional_state = emotion_detector.detect(metrics, cognitive_load)
    attention_level = 100 - calculator._calculate_attention_penalty(attention_data)
    fatigue_index = calculator._calculate_fatigue(metrics.session_duration_minutes)
    intervention_needed, recommended_action = determine_intervention(
        cognitive_load, emotional_state, fatigue_index
    )
    confidence = 0.85 if len(attention_data) > 10 else 0.5

    return CognitiveAssessment(
        session_id=metrics.session_id,
        cognitive_load=cognitive_load,
        emotional_state=emotional_state,
        attention_level=attention_level,
        fatigue_index=fatigue_index,
        intervention_needed=intervention_needed,
        recommended_action=recommended_action,
        confidence=confidence,
    )


@app.websocket("/v1/attention/stream/{session_id}")
async def attention_stream(websocket: WebSocket, session_id: str):
    """WebSocket for streaming attention frames from the frontend."""
    await websocket.accept()
    if session_id not in attention_buffer:
        attention_buffer[session_id] = []
    try:
        while True:
            data = await websocket.receive_json()
            frame = AttentionFrame(session_id=session_id, **data)
            attention_buffer[session_id].append(frame)
            if len(attention_buffer[session_id]) > MAX_BUFFER_SIZE:
                attention_buffer[session_id].pop(0)
            await websocket.send_json(
                {
                    "status": "received",
                    "buffer_size": len(attention_buffer[session_id]),
                }
            )
    except WebSocketDisconnect:
        attention_buffer.pop(session_id, None)


@app.get("/v1/attention/{session_id}")
async def get_attention_metrics(session_id: str):
    if session_id not in attention_buffer:
        return {"session_id": session_id, "frames_collected": 0, "attention_score": None}
    frames = attention_buffer[session_id]
    total = len(frames)
    with_face = sum(1 for f in frames if f.face_detected)
    return {
        "session_id": session_id,
        "frames_collected": total,
        "attention_score": int(with_face / total * 100) if total else 0,
        "face_detection_rate": with_face / total if total else 0,
    }


# ============================================================================
# LIFECYCLE
# ============================================================================


@app.on_event("startup")
async def startup_event():
    print("🧠 Cognitive Guardian starting up...")
    print("✅ Cognitive Guardian ready!")


@app.on_event("shutdown")
async def shutdown_event():
    attention_buffer.clear()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8011, reload=True, log_level="info")
