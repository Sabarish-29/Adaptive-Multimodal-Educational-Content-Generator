"""
Intervention Trigger – determines when to fire interventions
based on predicted cognitive load trajectory.
"""

from typing import List, Tuple


class InterventionTrigger:
    """Rule-based trigger with planned RL-policy upgrade path."""

    def __init__(
        self,
        immediate_threshold: int = 90,
        warning_threshold: int = 75,
        trend_window: int = 3,
    ):
        self.immediate_threshold = immediate_threshold
        self.warning_threshold = warning_threshold
        self.trend_window = trend_window

    def evaluate(
        self,
        current_load: int,
        predicted_loads: List[int],
        emotional_state: str = "calm",
    ) -> Tuple[bool, str, str]:
        """
        Returns (trigger, urgency, action).

        urgency: "critical" | "warning" | "none"
        action: recommended intervention type
        """
        # Immediate triggers
        if current_load >= self.immediate_threshold:
            return True, "critical", "suggest_break"

        if emotional_state in ("frustrated", "confused") and current_load > 70:
            return True, "critical", "encourage_and_simplify"

        # Predictive triggers
        if predicted_loads and max(predicted_loads[: self.trend_window]) > self.immediate_threshold:
            return True, "warning", "switch_modality"

        if current_load >= self.warning_threshold:
            return True, "warning", "simplify_content"

        return False, "none", "continue"
