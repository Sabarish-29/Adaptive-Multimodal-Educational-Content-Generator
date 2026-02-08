"""
Interaction Analyzer – processes clickstream / keystroke data
to detect hesitation, confusion, and engagement patterns.
"""

from typing import List, Dict, Any
from datetime import datetime


class InteractionAnalyzer:
    """Analyses raw interaction events to produce cognitive signals."""

    def __init__(self, hesitation_threshold_ms: int = 3000):
        self.hesitation_threshold_ms = hesitation_threshold_ms

    def analyze(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a batch of interaction events.

        Expected event schema:
            {"type": "click"|"keystroke"|"scroll"|"answer",
             "timestamp": float, "metadata": {...}}
        """
        if not events:
            return {
                "hesitation_ms": 0,
                "error_rate": 0.0,
                "reread_count": 0,
                "interaction_count": 0,
            }

        timestamps = sorted(e["timestamp"] for e in events if "timestamp" in e)
        gaps = [
            (timestamps[i + 1] - timestamps[i]) * 1000
            for i in range(len(timestamps) - 1)
        ]
        max_gap = max(gaps) if gaps else 0

        answers = [e for e in events if e.get("type") == "answer"]
        wrong = sum(1 for a in answers if not a.get("metadata", {}).get("correct", True))
        error_rate = wrong / len(answers) if answers else 0.0

        scrolls = [e for e in events if e.get("type") == "scroll"]
        reread_count = sum(
            1 for s in scrolls if s.get("metadata", {}).get("direction") == "up"
        )

        return {
            "hesitation_ms": int(max_gap),
            "error_rate": round(error_rate, 3),
            "reread_count": reread_count,
            "interaction_count": len(events),
        }
