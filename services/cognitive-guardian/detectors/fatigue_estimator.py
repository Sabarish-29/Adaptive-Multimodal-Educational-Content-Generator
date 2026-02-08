"""
Fatigue Estimator – time-on-task and circadian adjustments.
"""

from datetime import datetime


class FatigueEstimator:
    """Estimate fatigue from session duration and time-of-day."""

    def estimate(self, session_duration_minutes: int, current_hour: int | None = None) -> int:
        """
        Returns a fatigue index 0–100.

        - Increases after 20 min
        - Adds circadian penalty for late-night sessions
        """
        if current_hour is None:
            current_hour = datetime.utcnow().hour

        # Base fatigue from duration
        if session_duration_minutes < 20:
            base = 0
        elif session_duration_minutes < 40:
            base = (session_duration_minutes - 20) * 2
        else:
            base = min(40 + (session_duration_minutes - 40) * 5, 100)

        # Circadian penalty (late night / early morning)
        circadian = 0
        if current_hour >= 23 or current_hour < 5:
            circadian = 15
        elif current_hour >= 21:
            circadian = 8

        return min(base + circadian, 100)
