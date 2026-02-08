"""Break suggestion strategy."""

from typing import Dict, Any


class BreakSuggester:
    """Suggests micro-breaks based on fatigue and session duration."""

    BREAK_SCHEDULE = {
        25: 5,   # after 25 min → 5 min break (Pomodoro)
        50: 10,  # after 50 min → 10 min break
        90: 15,  # after 90 min → 15 min break
    }

    def suggest(
        self, session_duration_minutes: int, fatigue_index: int
    ) -> Dict[str, Any]:
        # Find appropriate break duration
        duration = 5
        for threshold, break_len in sorted(self.BREAK_SCHEDULE.items()):
            if session_duration_minutes >= threshold:
                duration = break_len

        # Increase break for high fatigue
        if fatigue_index > 80:
            duration = max(duration, 10)

        return {
            "type": "break",
            "duration_minutes": duration,
            "message": f"Great work! Take a {duration}-minute break to recharge.",
            "activities": ["stretch", "hydrate", "look away from screen"],
        }
