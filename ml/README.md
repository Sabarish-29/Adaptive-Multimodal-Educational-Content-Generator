# NeuroSync AI – ML Training Pipelines

This directory contains training pipelines for the core ML models used by NeuroSync AI agents.

## Models

| Model | Agent | Framework | Status |
|-------|-------|-----------|--------|
| Cognitive Load LSTM | Cognitive Guardian | PyTorch | Skeleton |
| Knowledge Graph GNN | Progress Analyst | PyTorch Geometric | Skeleton |
| Teaching Policy DQN | Intervention Agent | PyTorch + Gymnasium | Skeleton |

## Directory Structure

```
ml/
├── datasets/          # Training data (gitignored)
├── training/
│   ├── cognitive_load_lstm/   # LSTM for cognitive load prediction
│   ├── knowledge_graph_gnn/   # GNN for skill mastery inference
│   └── teaching_policy_dqn/   # DQN for intervention policy
├── notebooks/         # Jupyter notebooks for exploration
└── experiments/       # MLflow / W&B experiment logs
```

## Getting Started

```bash
cd ml/training/cognitive_load_lstm
pip install -r requirements.txt
python train.py --config config.yaml
```
