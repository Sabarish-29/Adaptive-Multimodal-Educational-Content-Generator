"""Conversational memory for the tutor agent."""

from typing import List, Dict, Any
from collections import defaultdict


class ConversationMemory:
    """
    Per-student conversation memory used by the tutor agent
    to maintain context across interactions.
    """

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._store: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def add(self, student_id: str, role: str, content: str):
        self._store[student_id].append({"role": role, "content": content})
        if len(self._store[student_id]) > self.max_history:
            self._store[student_id] = self._store[student_id][-self.max_history :]

    def get_history(self, student_id: str, last_n: int = 10) -> List[Dict[str, Any]]:
        return self._store[student_id][-last_n:]

    def clear(self, student_id: str):
        self._store.pop(student_id, None)
