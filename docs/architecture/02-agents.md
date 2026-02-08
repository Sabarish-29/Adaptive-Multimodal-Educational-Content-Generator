# NeuroSync AI – Agent Reference

Each agent is a self-contained FastAPI micro-service with its own Dockerfile,
requirements, configuration, and ML models.

---

## 1. Cognitive Guardian (port 8011)

**Purpose:** Real-time cognitive load monitoring and emotional state detection.

### Capabilities
- Multi-signal cognitive load fusion (hesitation, errors, re-reading, fatigue, attention)
- WebSocket-based attention streaming via MediaPipe FaceMesh
- Fatigue estimation using session duration + circadian rhythm
- Intervention trigger evaluation (immediate / warning / predictive)
- LSTM-based cognitive load prediction (future states)

### Key Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/assess` | Compute cognitive load from interaction data |
| GET | `/v1/state/{session_id}` | Get current cognitive state |
| WS | `/v1/attention/stream/{session_id}` | Real-time attention frames |

### Configuration
`configs/agents/cognitive-guardian.yaml`

---

## 2. Content Architect (port 8012)

**Purpose:** Multi-modal content generation adapted to cognitive state.

### Capabilities
- Modality selection based on cognitive load thresholds
- Text, image, voice, interactive, video, and AR content generation
- Knowledge graph management (Neo4j) with prerequisite planning
- RAG pipeline: Qdrant vector search → SentenceTransformer embedding → CrossEncoder reranking

### Key Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/generate` | Generate content for a concept |
| POST | `/v1/knowledge/concept` | Add concept to knowledge graph |
| POST | `/v1/search` | RAG search for relevant content |

### Configuration
`configs/agents/content-architect.yaml`

---

## 3. Tutor Agent (port 8013)

**Purpose:** Personalised tutoring with Socratic method and progressive hints.

### Capabilities
- Socratic teaching adapted to student knowledge level
- 3-level progressive hint generation
- ReAct reasoning with tool use (calculator, code executor)
- Per-student conversation memory (Redis-backed)

### Key Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/teach` | Get teaching response |
| POST | `/v1/hint` | Get progressive hint |
| POST | `/v1/evaluate` | Evaluate student answer |

### Configuration
`configs/agents/tutor-agent.yaml`

---

## 4. Intervention Agent (port 8014)

**Purpose:** Select and execute optimal learning interventions.

### Capabilities
- Rule-based intervention selection (fallback)
- DQN-based learned policy for intervention optimisation
- Pomodoro-inspired break scheduling
- Modality switching recommendations
- Feedback loop for RL reward signal

### Intervention Types
`BREAK` · `SWITCH_MODALITY` · `SIMPLIFY` · `ENCOURAGE` · `GAMIFY` · `PEER_HELP` · `REVIEW`

### Key Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/intervene` | Select intervention strategy |
| POST | `/v1/feedback` | Report intervention outcome |

### Configuration
`configs/agents/intervention-agent.yaml`

---

## 5. Progress Analyst (port 8015)

**Purpose:** Track mastery, compute learning velocity, and generate visualisations.

### Capabilities
- Bayesian mastery updates (0.7 prior + 0.3 evidence)
- GNN-based mastery prediction for unobserved concepts
- Learning velocity computation (Δmastery/Δtime)
- Constellation visualisation (circular layout, mastery-coloured nodes)

### Key Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/update` | Update mastery from new evidence |
| GET | `/v1/progress/{student_id}` | Get student skill graph |
| GET | `/v1/constellation/{student_id}` | Get constellation visualisation data |

### Configuration
`configs/agents/progress-analyst.yaml`

---

## 6. Peer Connector (port 8016)

**Purpose:** Intelligent peer matching and privacy-preserving federated learning.

### Capabilities
- Cosine similarity over skill vectors for peer matching
- Group optimisation with diversity constraints
- Flower-based federated learning client
- Differential privacy (Gaussian noise, gradient clipping, ID hashing)

### Key Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/profile` | Create/update peer profile |
| POST | `/v1/match` | Find matching peers |
| POST | `/v1/group` | Form optimised study groups |

### Configuration
`configs/agents/peer-connector.yaml`
