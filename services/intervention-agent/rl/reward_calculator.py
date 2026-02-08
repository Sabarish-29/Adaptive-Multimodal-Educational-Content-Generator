"""
Reward Calculator – computes RL reward signal from intervention outcomes.
"""


class RewardCalculator:
    """
    Calculates reward for the DQN policy based on post-intervention metrics.
    """

    def calculate(
        self,
        pre_load: int,
        post_load: int,
        accepted: bool,
        student_rating: int = 0,
    ) -> float:
        """
        Compute reward.

        Positive for: load reduction, acceptance, good ratings.
        Negative for: load increase, rejection, session abandonment.
        """
        reward = 0.0

        # Load reduction (normalized)
        load_delta = pre_load - post_load
        reward += load_delta / 100.0 * 2.0  # max ±2.0

        # Acceptance bonus
        reward += 1.0 if accepted else -0.5

        # Rating bonus (1-5 scale)
        if student_rating > 0:
            reward += (student_rating - 3) / 2.0  # maps [1,5] → [-1, 1]

        return round(reward, 3)
