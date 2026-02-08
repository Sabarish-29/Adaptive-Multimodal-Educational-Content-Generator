"""Base agent class for the Agent SDK."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Base class all NeuroSync AI agents inherit from."""

    name: str = "unnamed"
    version: str = "1.0.0"

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming state and return updated state."""
        ...

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """Return health/readiness information."""
        ...

    def capabilities(self) -> list:
        """List agent capabilities."""
        return []

    def __repr__(self):
        return f"<Agent:{self.name} v{self.version}>"
