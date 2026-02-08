"""
GNN-based skill graph for mastery prediction.
Placeholder – model trained via ml/training/knowledge_graph_gnn/.
"""

from typing import Dict, List, Any
import numpy as np


class SkillGraphGNN:
    """
    Graph Neural Network that operates on the student's skill graph.
    Predicts mastery levels for unobserved concepts based on
    related concept mastery and graph structure.
    """

    def __init__(self, model_path: str | None = None):
        self._model = None
        if model_path:
            self._load(model_path)

    def _load(self, path: str):
        try:
            import torch
            self._model = torch.load(path, map_location="cpu")
            self._model.eval()
        except Exception:
            self._model = None

    def predict_mastery(
        self, student_skills: Dict[str, float], concept: str
    ) -> float:
        """Predict mastery for a concept using GNN message passing."""
        if self._model is None:
            # Heuristic fallback: average of related skills
            if not student_skills:
                return 0.3
            return round(sum(student_skills.values()) / len(student_skills), 3)

        # TODO: real GNN inference
        return 0.5

    def find_weak_links(
        self, student_skills: Dict[str, float], threshold: float = 0.4
    ) -> List[str]:
        """Find concepts below the mastery threshold."""
        return [c for c, m in student_skills.items() if m < threshold]
