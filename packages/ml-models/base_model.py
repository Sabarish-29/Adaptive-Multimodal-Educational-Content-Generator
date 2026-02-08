"""Base ML model abstraction for all NeuroSync AI models."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path


class BaseMLModel(ABC):
    """
    Abstract base class for all ML models in NeuroSync AI.
    Provides consistent interface for loading, inference, and versioning.
    """

    name: str = "base"
    version: str = "1.0.0"

    def __init__(self, model_path: Optional[str] = None):
        self._model = None
        self._device = "cpu"
        if model_path and Path(model_path).exists():
            self.load(model_path)

    @abstractmethod
    def load(self, path: str) -> None:
        """Load model weights from disk."""
        ...

    @abstractmethod
    def predict(self, inputs: Any) -> Any:
        """Run inference."""
        ...

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return model metadata (name, version, params, etc.)."""
        ...

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def to_device(self, device: str = "cpu"):
        self._device = device
        if self._model is not None:
            try:
                self._model = self._model.to(device)
            except AttributeError:
                pass
