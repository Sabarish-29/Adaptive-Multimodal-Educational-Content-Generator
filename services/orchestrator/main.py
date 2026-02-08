"""
NeuroSync AI - Orchestrator Service
Coordinates all 6 AI agents using LangGraph
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uvicorn
from datetime import datetime

app = FastAPI(
    title="NeuroSync AI - Orchestrator",
    description="Multi-Agent Learning Orchestration System",
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


class AgentState(BaseModel):
    """Shared state across all agents"""

    student_id: str
    session_id: str
    current_concept: str
    cognitive_load: int = 0
    emotional_state: str = "neutral"
    mastery_level: float = 0.0
    messages: List[Dict[str, Any]] = []
    next_action: Optional[str] = None
    timestamp: datetime = datetime.utcnow()


class LearningRequest(BaseModel):
    student_id: str
    concept: str
    preferences: Optional[Dict[str, Any]] = {}


class LearningResponse(BaseModel):
    session_id: str
    content: Dict[str, Any]
    interventions: List[str]
    metrics: Dict[str, float]


# ============================================================================
# AGENT COMMUNICATION LAYER
# ============================================================================


class AgentClient:
    """HTTP client for communicating with agent services"""

    def __init__(self):
        self.agents = {
            "cognitive_guardian": "http://cognitive-guardian:8011",
            "content_architect": "http://content-architect:8012",
            "tutor": "http://tutor-agent:8013",
            "intervention": "http://intervention-agent:8014",
            "progress": "http://progress-analyst:8015",
            "peer": "http://peer-connector:8016",
        }

    async def call_agent(
        self, agent_name: str, endpoint: str, data: Dict
    ) -> Dict:
        """Call an agent service via HTTP"""
        # TODO: Implement with httpx async client
        return {"agent": agent_name, "status": "placeholder", "data": data}


agent_client = AgentClient()


# ============================================================================
# LANGGRAPH WORKFLOW (deferred import – installed separately)
# ============================================================================


def create_learning_workflow():
    """
    Create LangGraph workflow for learning sessions.

    The workflow routes through agents in this order:
      cognitive_guardian → (intervention | content_architect) → tutor → progress
    and loops until mastery_level > 0.85.
    """

    try:
        from langgraph.graph import StateGraph, END
    except ImportError:
        # Graceful degradation – return a simple pass-through callable
        class _Noop:
            async def ainvoke(self, state):
                return state

        return _Noop()

    workflow = StateGraph(dict)

    # -- node functions -------------------------------------------------------
    async def cognitive_guardian_node(state: Dict) -> Dict:
        result = await agent_client.call_agent(
            "cognitive_guardian",
            "/v1/assess",
            {
                "student_id": state["student_id"],
                "session_id": state["session_id"],
            },
        )
        state["cognitive_load"] = result.get("cognitive_load", 0)
        state["emotional_state"] = result.get("emotional_state", "neutral")
        return state

    async def content_architect_node(state: Dict) -> Dict:
        result = await agent_client.call_agent(
            "content_architect",
            "/v1/generate",
            {
                "concept": state["current_concept"],
                "cognitive_load": state["cognitive_load"],
                "student_id": state["student_id"],
            },
        )
        state["messages"].append(
            {"type": "content", "data": result.get("content", {})}
        )
        return state

    async def tutor_node(state: Dict) -> Dict:
        result = await agent_client.call_agent(
            "tutor",
            "/v1/teach",
            {
                "student_id": state["student_id"],
                "concept": state["current_concept"],
                "context": state["messages"],
            },
        )
        state["messages"].append(
            {"type": "tutor_message", "data": result.get("response", "")}
        )
        return state

    async def intervention_node(state: Dict) -> Dict:
        result = await agent_client.call_agent(
            "intervention",
            "/v1/intervene",
            {
                "cognitive_load": state["cognitive_load"],
                "emotional_state": state["emotional_state"],
                "student_id": state["student_id"],
            },
        )
        if result.get("intervention_needed"):
            state["messages"].append(
                {"type": "intervention", "data": result.get("intervention", {})}
            )
        return state

    async def progress_node(state: Dict) -> Dict:
        result = await agent_client.call_agent(
            "progress",
            "/v1/analyze",
            {
                "student_id": state["student_id"],
                "concept": state["current_concept"],
                "session_data": state["messages"],
            },
        )
        state["mastery_level"] = result.get("mastery_level", 0.0)
        return state

    # -- build graph ----------------------------------------------------------
    workflow.add_node("cognitive_guardian", cognitive_guardian_node)
    workflow.add_node("content_architect", content_architect_node)
    workflow.add_node("tutor", tutor_node)
    workflow.add_node("intervention", intervention_node)
    workflow.add_node("progress", progress_node)

    workflow.set_entry_point("cognitive_guardian")

    def should_intervene(state: Dict) -> str:
        if state.get("cognitive_load", 0) > 80:
            return "intervention"
        return "content_architect"

    workflow.add_conditional_edges("cognitive_guardian", should_intervene)
    workflow.add_edge("intervention", "cognitive_guardian")
    workflow.add_edge("content_architect", "tutor")
    workflow.add_edge("tutor", "progress")

    def should_continue(state: Dict) -> str:
        if state.get("mastery_level", 0) > 0.85:
            return END
        return "cognitive_guardian"

    workflow.add_conditional_edges("progress", should_continue)

    return workflow.compile()


learning_workflow = create_learning_workflow()


# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "orchestrator",
        "version": "1.0.0",
        "agents_connected": len(agent_client.agents),
    }


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/v1/session/start", response_model=LearningResponse)
async def start_learning_session(request: LearningRequest):
    """Start a new learning session orchestrated across all agents."""
    try:
        initial_state = {
            "student_id": request.student_id,
            "session_id": f"session_{datetime.utcnow().timestamp()}",
            "current_concept": request.concept,
            "cognitive_load": 0,
            "emotional_state": "neutral",
            "mastery_level": 0.0,
            "messages": [],
            "next_action": None,
        }

        final_state = await learning_workflow.ainvoke(initial_state)

        return LearningResponse(
            session_id=final_state["session_id"],
            content={"messages": final_state.get("messages", [])},
            interventions=[
                msg["data"]
                for msg in final_state.get("messages", [])
                if msg.get("type") == "intervention"
            ],
            metrics={
                "cognitive_load": final_state.get("cognitive_load", 0),
                "mastery_level": final_state.get("mastery_level", 0),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/agents/status")
async def get_agents_status():
    """Get status of all connected agents."""
    status = {}
    for agent_name, url in agent_client.agents.items():
        try:
            status[agent_name] = {
                "url": url,
                "status": "registered",
                "last_check": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            status[agent_name] = {
                "url": url,
                "status": "disconnected",
                "error": str(e),
            }
    return status


# ============================================================================
# LIFECYCLE
# ============================================================================


@app.on_event("startup")
async def startup_event():
    print("🚀 Orchestrator starting up...")
    print(f"📡 Registered {len(agent_client.agents)} agents")
    print("✅ Orchestrator ready!")


@app.on_event("shutdown")
async def shutdown_event():
    print("👋 Orchestrator shutting down...")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True, log_level="info")
