"""Learning velocity tracker – measures learning speed over time."""

from typing import List, Dict
from datetime import datetime, timedelta


class LearningVelocity:
    """Computes how fast a student acquires new skills."""

    def compute(
        self,
        mastery_snapshots: List[Dict],
        window_hours: int = 24,
    ) -> float:
        """
        Compute velocity = Δmastery / Δtime.

        mastery_snapshots: list of {"mastery": float, "timestamp": datetime}
        """
        if len(mastery_snapshots) < 2:
            return 0.0

        recent = sorted(mastery_snapshots, key=lambda s: s["timestamp"])
        first = recent[0]
        last = recent[-1]

        time_delta = (last["timestamp"] - first["timestamp"]).total_seconds() / 3600
        if time_delta <= 0:
            return 0.0

        mastery_delta = last["mastery"] - first["mastery"]
        return round(mastery_delta / time_delta, 4)
