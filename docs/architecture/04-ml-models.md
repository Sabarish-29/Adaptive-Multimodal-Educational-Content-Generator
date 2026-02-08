# NeuroSync AI – ML Models

## Model Inventory

| Model | Type | Input | Output | Service |
|-------|------|-------|--------|---------|
| Cognitive Load LSTM | LSTM (PyTorch) | 5-feature time series | Load prediction (0-1) | Cognitive Guardian |
| Knowledge Graph GNN | GCN (PyTorch Geometric) | Node features + graph | Mastery prediction | Progress Analyst |
| Teaching Policy DQN | DQN (PyTorch) | 8-dim state vector | Action index (0-6) | Intervention Agent |
| Sentence Embedder | Transformer | Text | 384-dim vector | Content Architect |
| Cross-Encoder Reranker | Transformer | Query-doc pair | Relevance score | Content Architect |

## Training Pipelines

### Cognitive Load LSTM

**Location:** `ml/training/cognitive_load_lstm/train.py`

Predicts future cognitive load from a sliding window of interaction signals.

- **Architecture:** 2-layer LSTM, 64 hidden dim, dropout 0.2
- **Input features:** hesitation, error rate, re-reading, fatigue, attention (5 dims)
- **Sequence length:** 10 time steps
- **Loss:** MSE
- **Training data:** Synthetic (for bootstrap); real data from `cognitive_states` collection

```bash
python ml/training/cognitive_load_lstm/train.py --epochs 50 --lr 0.001
```

### Knowledge Graph GNN

**Location:** `ml/training/knowledge_graph_gnn/train.py`

Predicts mastery for unobserved concepts by propagating known mastery values
through the prerequisite graph.

- **Architecture:** GCN (placeholder for GAT), 3 layers, 64 hidden dim
- **Input:** Node features from Neo4j concept graph
- **Output:** Per-node mastery regression
- **Loss:** MSE

```bash
python ml/training/knowledge_graph_gnn/train.py --epochs 20 --lr 0.001
```

### Teaching Policy DQN

**Location:** `ml/training/teaching_policy_dqn/train.py`

Learns which intervention to apply given the student's current state.

- **Architecture:** 3-layer MLP (128-128-7)
- **State space:** 8 dimensions (cognitive load, mastery, engagement, fatigue,
  error rate, time, modality, streak)
- **Action space:** 7 interventions (BREAK, SWITCH_MODALITY, SIMPLIFY,
  ENCOURAGE, GAMIFY, PEER_HELP, REVIEW)
- **Environment:** Simulated `StudentEnv` with crude transition dynamics
- **Algorithm:** DQN with experience replay, target network, epsilon-greedy

```bash
python ml/training/teaching_policy_dqn/train.py --epochs 200 --lr 0.001
```

## Model Configuration

All model hyper-parameters are centralised in:

```
configs/models/model_configs.yaml
```

## Inference

The `packages/ml-models/inference.py` module provides a generic batch
inference wrapper that works with any model implementing the `BaseModel` ABC.

## Future Models

- **Emotion Detection CNN** – Facial expression classification from webcam
- **Learning Style Classifier** – Predict VARK preferences from interaction
  patterns
- **Content Quality Scorer** – Rate generated content quality
- **Attention Prediction Transformer** – Predict when attention will drop
