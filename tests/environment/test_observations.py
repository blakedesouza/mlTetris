"""Tests for observation space and feature-based observations (ENV-02)."""

import numpy as np
import pytest


class TestObservationShape:
    """Tests for observation shape and structure."""

    def test_observation_is_numpy_array(self, env):
        """Observation is a numpy array."""
        obs, _ = env.reset()
        assert isinstance(obs, np.ndarray)

    def test_observation_is_2d(self, env):
        """Observation is 2D: (num_actions, num_features)."""
        obs, _ = env.reset()
        assert len(obs.shape) == 2

    def test_observation_has_40_actions(self, env):
        """Observation first dimension is 40 (width * 4 rotations)."""
        obs, _ = env.reset()
        assert obs.shape[0] == 40

    def test_observation_has_13_features(self, env):
        """Observation second dimension is 13 (features per action)."""
        obs, _ = env.reset()
        assert obs.shape[1] == 13

    def test_observation_full_shape(self, env):
        """Full observation shape is (40, 13)."""
        obs, _ = env.reset()
        assert obs.shape == (40, 13)


class TestObservationType:
    """Tests for observation data type."""

    def test_observation_dtype_is_numeric(self, env):
        """Observation dtype is a numeric type (uint8, float32, or float64)."""
        obs, _ = env.reset()
        # FeatureVectorObservation uses uint8 for feature values
        assert obs.dtype in [np.uint8, np.float32, np.float64]


class TestObservationSpace:
    """Tests for observation space specification."""

    def test_observation_in_space(self, env):
        """Observation is within observation_space bounds."""
        obs, _ = env.reset()
        assert env.observation_space.contains(obs)

    def test_observation_space_is_box(self, env):
        """observation_space is a gymnasium Box."""
        from gymnasium.spaces import Box

        assert isinstance(env.observation_space, Box)

    def test_observation_space_shape_matches(self, env):
        """observation_space shape matches actual observation shape."""
        obs, _ = env.reset()
        assert env.observation_space.shape == obs.shape


class TestObservationContent:
    """Tests for observation content (feature values)."""

    def test_observation_values_non_negative(self, env):
        """All observation values are non-negative."""
        obs, _ = env.reset()
        # Features are heights, holes, bumpiness - all non-negative
        assert np.all(obs >= 0)

    def test_observation_changes_after_step(self, env):
        """Observation changes after taking a step."""
        obs1, _ = env.reset()
        obs2, _, _, _, _ = env.step(env.action_space.sample())
        # At least some values should change
        assert not np.array_equal(obs1, obs2)
