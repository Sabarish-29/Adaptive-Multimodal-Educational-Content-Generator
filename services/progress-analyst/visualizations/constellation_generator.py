"""
Constellation Generator – creates a star-map style visualization
of the student's knowledge graph where each star is a concept.
"""

from typing import Dict, List, Any


class ConstellationGenerator:
    """
    Generates a 2D/3D constellation map of the student's skills.
    Each node (star) represents a concept; brightness = mastery level.
    Edges represent prerequisite relationships.
    """

    def generate(
        self,
        skills: Dict[str, float],
        edges: List[tuple] = None,
    ) -> Dict[str, Any]:
        """
        Generate constellation data for the frontend.
        """
        import math

        nodes = []
        for i, (concept, mastery) in enumerate(skills.items()):
            angle = (2 * math.pi * i) / max(len(skills), 1)
            radius = 1.0 - mastery * 0.3  # high mastery → closer to center
            nodes.append(
                {
                    "id": concept,
                    "x": round(math.cos(angle) * radius * 100, 2),
                    "y": round(math.sin(angle) * radius * 100, 2),
                    "brightness": round(mastery, 2),
                    "label": concept,
                    "color": self._color(mastery),
                }
            )

        edge_data = []
        if edges:
            edge_data = [
                {"source": src, "target": tgt, "weight": 1.0}
                for src, tgt in edges
            ]

        return {
            "nodes": nodes,
            "edges": edge_data,
            "center": {"x": 0, "y": 0},
        }

    @staticmethod
    def _color(mastery: float) -> str:
        if mastery > 0.8:
            return "#fbbf24"  # gold (mastered)
        elif mastery > 0.5:
            return "#60a5fa"  # blue (learning)
        else:
            return "#6b7280"  # gray (new)
