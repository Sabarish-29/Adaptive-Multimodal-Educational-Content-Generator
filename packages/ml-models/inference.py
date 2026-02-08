"""Shared inference utilities (batching, caching)."""

from typing import Any, Callable, Dict, List
from functools import lru_cache


class InferenceEngine:
    """Lightweight inference wrapper with batching support."""

    def __init__(self, model: Any, batch_size: int = 16):
        self.model = model
        self.batch_size = batch_size

    def predict_batch(self, inputs: List[Any]) -> List[Any]:
        """Run inference in batches."""
        results = []
        for i in range(0, len(inputs), self.batch_size):
            batch = inputs[i : i + self.batch_size]
            results.extend(self.model.predict(batch) if hasattr(self.model, 'predict') else batch)
        return results
