# NeuroSync AI – Data Flow

## Learning Session Flow

A typical learning session follows this sequence through the agent network:

```
Student opens session
        │
        ▼
┌─── Orchestrator ───────────────────────────────────────────┐
│                                                            │
│  1. build_initial_state(student, topic, concept)           │
│                                                            │
│  ┌──────────────── Loop until mastery > 0.85 ────────────┐ │
│  │                                                        │ │
│  │  2. Cognitive Guardian → assess cognitive state         │ │
│  │     • Receives interaction data                        │ │
│  │     • Returns: cognitive_load, fatigue, attention       │ │
│  │     • Emits: CognitiveLoadUpdated event                │ │
│  │                                                        │ │
│  │  3. Decision: cognitive_load > 0.7?                    │ │
│  │     ├── YES → Intervention Agent                       │ │
│  │     │         • Selects strategy (DQN or rule-based)   │ │
│  │     │         • Emits: InterventionTriggered event     │ │
│  │     │         └── Returns to step 2                    │ │
│  │     └── NO  → Content Architect                        │ │
│  │               • Selects modality based on load         │ │
│  │               • Queries knowledge graph (Neo4j)        │ │
│  │               • RAG retrieval from Qdrant              │ │
│  │               • Generates adapted content              │ │
│  │               • Emits: ContentGenerated event          │ │
│  │                                                        │ │
│  │  4. Tutor Agent                                        │ │
│  │     • Socratic teaching or direct explanation          │ │
│  │     • Progressive hints on request                     │ │
│  │     • Evaluates student answers                        │ │
│  │                                                        │ │
│  │  5. Progress Analyst                                   │ │
│  │     • Bayesian mastery update                          │ │
│  │     • Learning velocity computation                    │ │
│  │     • Constellation update                             │ │
│  │     • Emits: ConceptMastered event (if threshold met)  │ │
│  │                                                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                            │
│  6. Session end → emit SessionEnded event                  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Kafka Event Topics

| Topic | Publisher(s) | Consumer(s) | Schema |
|-------|-------------|-------------|--------|
| `neurosync.sessions` | Orchestrator | Analytics, Progress | SessionStarted, SessionEnded |
| `neurosync.cognitive` | Cognitive Guardian | Intervention, Analytics | CognitiveLoadUpdated, AttentionAlert |
| `neurosync.content` | Content Architect | Analytics, Cache | ContentGenerated, ContentFeedback |
| `neurosync.interventions` | Intervention Agent | Analytics, Progress | InterventionTriggered |
| `neurosync.progress` | Progress Analyst | Frontend (via SSE) | ConceptMastered |
| `neurosync.peer` | Peer Connector | Analytics | PeerMatched, GroupFormed |
| `neurosync.events.dead-letter` | All | Ops team | Failed events |

## Data Stores

| Store | Used By | Purpose |
|-------|---------|---------|
| **MongoDB** | All services | Student profiles, sessions, cognitive states, interventions |
| **Redis** | Tutor Agent, Orchestrator | Conversation memory, caching, rate limiting |
| **Neo4j** | Content Architect, Progress Analyst | Knowledge graph (concepts, prerequisites, skills) |
| **Qdrant** | Content Architect | Vector embeddings for RAG retrieval |
| **MinIO** | Content Architect | Generated media files (images, audio, video) |
| **Kafka** | All agents | Event streaming and async communication |
