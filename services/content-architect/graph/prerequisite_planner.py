"""Prerequisite Planner – computes optimal learning paths via the KG."""

from typing import List, Dict
from .knowledge_graph import KnowledgeGraph


class PrerequisitePlanner:
    """Builds topologically sorted learning paths from the knowledge graph."""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg

    async def compute_learning_path(self, target_concept: str) -> List[str]:
        """Return ordered list of concepts to learn before target_concept."""
        prereqs = await self.kg.get_prerequisites(target_concept)
        # TODO: full topological sort using recursive prerequisite lookup
        return prereqs + [target_concept]
