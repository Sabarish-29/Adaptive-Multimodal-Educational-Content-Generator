"""Shared training utilities."""

from typing import Dict, Any
import time


class TrainingConfig:
    """Common training configuration."""

    def __init__(
        self,
        epochs: int = 10,
        batch_size: int = 32,
        learning_rate: float = 1e-3,
        device: str = "cpu",
    ):
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.device = device


class TrainingLogger:
    """Simple training logger."""

    def __init__(self):
        self.history = []

    def log_epoch(self, epoch: int, metrics: Dict[str, float]):
        self.history.append({"epoch": epoch, "metrics": metrics, "timestamp": time.time()})

    def summary(self) -> Dict[str, Any]:
        if not self.history:
            return {"epochs": 0}
        last = self.history[-1]
        return {
            "epochs": len(self.history),
            "latest_metrics": last["metrics"],
            "total_time_s": self.history[-1]["timestamp"] - self.history[0]["timestamp"],
        }
