"""Privacy-preserving utilities for federated learning."""

import hashlib
import numpy as np
from typing import List


class PrivacyPreserving:
    """
    Implements differential privacy mechanisms for
    protecting student data during federated learning.
    """

    def __init__(self, epsilon: float = 1.0, delta: float = 1e-5):
        self.epsilon = epsilon
        self.delta = delta

    def add_noise(self, gradients: np.ndarray, sensitivity: float = 1.0) -> np.ndarray:
        """Add Gaussian noise for differential privacy."""
        sigma = sensitivity * np.sqrt(2 * np.log(1.25 / self.delta)) / self.epsilon
        noise = np.random.normal(0, sigma, gradients.shape)
        return gradients + noise

    def clip_gradients(self, gradients: np.ndarray, max_norm: float = 1.0) -> np.ndarray:
        """Clip gradients to bound sensitivity."""
        norm = np.linalg.norm(gradients)
        if norm > max_norm:
            gradients = gradients * (max_norm / norm)
        return gradients

    @staticmethod
    def hash_student_id(student_id: str, salt: str = "neurosync") -> str:
        """One-way hash for anonymizing student IDs in federated aggregation."""
        return hashlib.sha256(f"{salt}:{student_id}".encode()).hexdigest()[:16]
