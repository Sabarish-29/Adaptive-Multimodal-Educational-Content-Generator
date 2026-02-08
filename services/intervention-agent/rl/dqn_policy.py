"""
DQN Policy – Deep Q-Network for intervention selection.
Placeholder; will be trained via ml/training/teaching_policy_dqn/.
"""

from typing import List, Optional
import numpy as np


class DQNPolicy:
    """
    Deep Q-Network that learns the optimal intervention strategy
    from (state, action, reward, next_state) transitions.
    """

    ACTIONS = [
        "suggest_break",
        "switch_modality",
        "simplify_content",
        "encourage_and_hint",
        "gamify",
        "peer_help",
        "review_prerequisites",
        "continue",
    ]

    def __init__(self, state_dim: int = 6, hidden_dim: int = 64):
        self.state_dim = state_dim
        self.hidden_dim = hidden_dim
        self._model = None  # PyTorch model loaded after training

    def select_action(self, state: List[float], epsilon: float = 0.0) -> str:
        """Select action using epsilon-greedy policy."""
        if self._model is None or np.random.random() < epsilon:
            return np.random.choice(self.ACTIONS)

        # TODO: forward pass through DQN
        return self.ACTIONS[0]

    def state_vector(
        self,
        cognitive_load: int,
        emotional_state_id: int,
        fatigue: int,
        attention: int,
        mastery: float,
        duration: int,
    ) -> List[float]:
        """Convert metrics to a normalized state vector."""
        return [
            cognitive_load / 100.0,
            emotional_state_id / 5.0,
            fatigue / 100.0,
            attention / 100.0,
            mastery,
            min(duration / 120.0, 1.0),
        ]
