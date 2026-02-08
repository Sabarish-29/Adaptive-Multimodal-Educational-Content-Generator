"""
NeuroSync AI – Base Agent abstraction.

Every agent service inherits from BaseAgent to guarantee
a consistent interface for the orchestrator.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Abstract base for all NeuroSync AI agents."""

    name: str = "base"
    version: str = "1.0.0"

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return updated state."""
        ...

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        """Return agent health information."""
        ...

    def __repr__(self) -> str:
        return f"<Agent {self.name} v{self.version}>"
