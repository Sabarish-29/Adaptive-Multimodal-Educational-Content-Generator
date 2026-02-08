"""
Cognitive Load LSTM Predictor – placeholder for the trained LSTM model
that predicts cognitive load trajectory.
"""

from typing import List
import numpy as np


class LoadPredictor:
    """
    LSTM-based cognitive load predictor.

    Takes a sequence of recent cognitive load readings and predicts
    the next N values so the system can intervene proactively.

    Model will be trained via ml/training/cognitive_load_lstm/.
    """

    def __init__(self, model_path: str | None = None):
        self._model = None
        if model_path:
            self._load(model_path)

    def _load(self, path: str):
        """Load a trained PyTorch LSTM model."""
        try:
            import torch
            self._model = torch.load(path, map_location="cpu")
            self._model.eval()
        except Exception:
            self._model = None

    def predict(self, history: List[int], horizon: int = 5) -> List[int]:
        """
        Predict future cognitive load from recent history.

        Args:
            history: list of recent cognitive load readings (0-100)
            horizon: how many future steps to predict

        Returns:
            List of predicted cognitive load values
        """
        if self._model is None:
            # Heuristic fallback: linear extrapolation
            if len(history) < 2:
                return [history[-1]] * horizon if history else [50] * horizon
            slope = history[-1] - history[-2]
            predictions = []
            last = history[-1]
            for _ in range(horizon):
                last = max(0, min(100, last + slope))
                predictions.append(int(last))
            return predictions

        # TODO: real inference with self._model
        return [50] * horizon
