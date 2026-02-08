# NeuroSync AI – Architecture Overview

## Vision

NeuroSync AI is a **multi-agent cognitive learning ecosystem** that transforms
adaptive education through real-time cognitive monitoring, personalised content
generation, and intelligent intervention. It replaces the traditional
monolithic adaptive learning approach with a network of specialised AI agents
coordinated by a central orchestrator.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js 14)                  │
│              Constellation UI  ·  Learning Interface        │
└──────────────────────┬──────────────────────────────────────┘
                       │ REST / WebSocket / SSE
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                     API Gateway (FastAPI 9090)               │
│              Authentication · Rate Limiting · Routing        │
└──────────────────────┬──────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │    Orchestrator (8010)  │
          │      LangGraph Engine  │
          └──┬──┬──┬──┬──┬──┬──────┘
             │  │  │  │  │  │
   ┌─────────┘  │  │  │  │  └─────────┐
   ▼            ▼  ▼  ▼  ▼            ▼
┌──────┐  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Cogni-│  │Cont- │ │Tutor │ │Inter-│ │Prog- │ │Peer  │
│tive  │  │ent   │ │Agent │ │vent- │ │ress  │ │Conn- │
│Guard-│  │Archi-│ │(8013)│ │ion   │ │Anal- │ │ector │
│ian   │  │tect  │ │      │ │Agent │ │yst   │ │(8016)│
│(8011)│  │(8012)│ │      │ │(8014)│ │(8015)│ │      │
└──┬───┘  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
   │         │        │        │        │        │
   └─────────┴────────┴────┬───┴────────┴────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
  │  Kafka       │ │  Neo4j       │ │  Qdrant      │
  │  Event Bus   │ │  Knowledge   │ │  Vector      │
  │              │ │  Graph       │ │  Store        │
  └──────────────┘ └──────────────┘ └──────────────┘
          │
  ┌───────┴────────────────────────────┐
  │  MongoDB · Redis · MinIO           │
  │  (data stores from legacy stack)   │
  └────────────────────────────────────┘
```

## Design Principles

1. **Agent Autonomy** – Each agent is a standalone FastAPI micro-service with
   its own models, data, and health checks. Agents can be deployed, scaled,
   and updated independently.

2. **Orchestrator-Coordinated** – The LangGraph-based Orchestrator defines
   the workflow graph. Conditional edges route to different agents based on
   the student's cognitive state.

3. **Event-Driven** – All significant state changes are published to Kafka
   topics, enabling asynchronous processing, audit trails, and future
   analytics pipelines.

4. **Privacy-First** – Differential privacy in federated learning, hashed
   student IDs, field-level encryption, and GDPR-compliant data retention.

5. **Graceful Degradation** – Every agent has rule-based fallbacks so the
   system continues to function even when ML models or external services
   are unavailable.

## Communication Patterns

| Pattern | Used Between | Protocol |
|---------|-------------|----------|
| Synchronous RPC | Orchestrator ↔ Agents | HTTP/JSON |
| Streaming | Cognitive Guardian → Frontend | WebSocket |
| Event Sourcing | All agents → Kafka | Kafka producer |
| Graph Queries | Content Architect ↔ Neo4j | Bolt |
| Vector Search | Content Architect ↔ Qdrant | gRPC / REST |

## Port Assignments

| Service | Port |
|---------|------|
| Profiles (legacy) | 8000 |
| Adaptation (legacy) | 8001 |
| Sessions (legacy) | 8002 |
| Content Gen (legacy) | 8003 |
| RAG (legacy) | 8005 |
| Curriculum (legacy) | 8006 |
| Admin | 8007 |
| Analytics | 8008 |
| API Gateway | 9090 |
| **Orchestrator** | **8010** |
| **Cognitive Guardian** | **8011** |
| **Content Architect** | **8012** |
| **Tutor Agent** | **8013** |
| **Intervention Agent** | **8014** |
| **Progress Analyst** | **8015** |
| **Peer Connector** | **8016** |
