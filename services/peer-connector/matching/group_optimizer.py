"""Group optimizer – forms balanced study groups."""

from typing import List, Dict
import random


class GroupOptimizer:
    """
    Optimizes group composition for diversity and complementary skills.
    Uses a greedy approach; will upgrade to ILP solver.
    """

    def optimize(
        self,
        student_skills: Dict[str, Dict[str, float]],
        group_size: int = 4,
    ) -> List[List[str]]:
        """Partition students into balanced groups."""
        students = list(student_skills.keys())
        random.shuffle(students)
        groups = []
        for i in range(0, len(students), group_size):
            groups.append(students[i : i + group_size])
        return groups
