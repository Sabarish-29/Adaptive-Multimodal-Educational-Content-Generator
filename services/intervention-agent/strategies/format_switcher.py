"""Format / modality switching strategy."""

from typing import Dict, Any, List


class FormatSwitcher:
    """Switches content modality when the current format isn't working."""

    MODALITY_ORDER = ["text", "image", "voice", "interactive", "video"]

    def suggest_switch(
        self, current_modality: str, cognitive_load: int
    ) -> Dict[str, Any]:
        """Suggest an alternative modality."""
        current_idx = (
            self.MODALITY_ORDER.index(current_modality)
            if current_modality in self.MODALITY_ORDER
            else 0
        )

        # If load is very high, prefer low-effort modalities
        if cognitive_load > 80:
            suggestions = ["voice", "image"]
        else:
            suggestions = [
                m for i, m in enumerate(self.MODALITY_ORDER)
                if i != current_idx
            ]

        return {
            "type": "switch_modality",
            "current": current_modality,
            "suggested": suggestions[0] if suggestions else "text",
            "alternatives": suggestions,
            "message": f"Let's try learning this through {suggestions[0]} instead.",
        }
