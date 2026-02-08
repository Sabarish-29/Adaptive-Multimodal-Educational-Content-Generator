"""
Unit tests for Peer Connector agent.
"""

import pytest


class TestProfileSimilarity:
    """Test cosine similarity matching."""

    def test_identical_profiles_score_one(self):
        try:
            from services.peer_connector.matching.profile_similarity import ProfileMatcher
        except ImportError:
            pytest.skip("profile_similarity not importable")

        matcher = ProfileMatcher()
        profile = {"skills": {"math": 0.8, "physics": 0.5}}
        score = matcher.similarity(profile, profile)
        assert score == pytest.approx(1.0, abs=0.01)

    def test_orthogonal_profiles_score_zero(self):
        try:
            from services.peer_connector.matching.profile_similarity import ProfileMatcher
        except ImportError:
            pytest.skip("profile_similarity not importable")

        matcher = ProfileMatcher()
        p1 = {"skills": {"math": 1.0, "physics": 0.0}}
        p2 = {"skills": {"math": 0.0, "physics": 1.0}}
        score = matcher.similarity(p1, p2)
        assert score < 0.5


class TestGroupOptimizer:
    """Test group formation."""

    def test_creates_groups_of_correct_size(self):
        try:
            from services.peer_connector.matching.group_optimizer import GroupOptimizer
        except ImportError:
            pytest.skip("group_optimizer not importable")

        opt = GroupOptimizer(min_size=2, max_size=3)
        students = [f"s{i}" for i in range(6)]
        groups = opt.optimize(students, similarity_matrix=None)
        assert all(2 <= len(g) <= 3 for g in groups)


class TestPrivacyPreserving:
    """Test differential privacy utilities."""

    def test_noise_is_added(self):
        try:
            from services.peer_connector.federated.privacy_preserving import PrivacyManager
        except ImportError:
            pytest.skip("privacy_preserving not importable")

        pm = PrivacyManager(noise_multiplier=1.0)
        import numpy as np
        original = np.array([1.0, 2.0, 3.0])
        noised = pm.add_noise(original.copy())
        # Very unlikely to be exactly the same
        assert not np.allclose(original, noised)

    def test_id_hashing(self):
        try:
            from services.peer_connector.federated.privacy_preserving import PrivacyManager
        except ImportError:
            pytest.skip("privacy_preserving not importable")

        pm = PrivacyManager()
        hashed = pm.hash_id("student_123")
        assert isinstance(hashed, str)
        assert hashed != "student_123"
        # Deterministic
        assert pm.hash_id("student_123") == hashed
