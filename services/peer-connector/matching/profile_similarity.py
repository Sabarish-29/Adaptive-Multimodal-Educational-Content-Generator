"""Profile similarity computation using embeddings."""

from typing import Dict, List
import numpy as np


class ProfileSimilarity:
    """Vector-space similarity for student profiles."""

    def compute_embedding(self, skills: Dict[str, float]) -> np.ndarray:
        """Convert skill dict to a fixed-dim embedding."""
        # TODO: use a learned embedding model
        # For now, hash concept names to consistent indices
        dim = 64
        vec = np.zeros(dim)
        for concept, mastery in skills.items():
            idx = hash(concept) % dim
            vec[idx] += mastery
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        dot = np.dot(a, b)
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(dot / (na * nb))
