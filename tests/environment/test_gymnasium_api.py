"""Tests for Gymnasium API compliance (ENV-05)."""

import pytest
from gymnasium.spaces import Box, Discrete

from src.environment import create_tetris_env


class TestCheckEnv:
    """Tests using Gymnasium check_env validation."""

    def test_check_env_passes(self, env):
        """Environment passes Gymnasium check_env validation."""
        from stable_baselines3.common.env_checker import check_env

        # check_env raises exception if validation fails
        # skip_render_check=True because we don't require rendering
        check_env(env, warn=True, skip_render_check=True)


class TestResetAPI:
    """Tests for reset() API compliance."""

    def test_reset_returns_tuple(self, env):
        """reset() returns (obs, info) tuple."""
        result = env.reset()
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestStepAPI:
    """Tests for step() API compliance."""

    def test_step_returns_five_tuple(self, env):
        """step() returns 5-tuple."""
        env.reset()
        result = env.step(env.action_space.sample())
        assert isinstance(result, tuple)
        assert len(result) == 5

    def test_step_tuple_types(self, env):
        """step() returns correct types in tuple."""
        env.reset()
        obs, reward, terminated, truncated, info = env.step(env.action_space.sample())

        import numpy as np

        assert isinstance(obs, np.ndarray)
        assert isinstance(reward, (int, float))
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)


class TestObservationSpaceAPI:
    """Tests for observation_space API compliance."""

    def test_observation_space_is_box(self, env):
        """observation_space is a gymnasium Box."""
        assert isinstance(env.observation_space, Box)

    def test_observation_space_contains_observation(self, env):
        """observation_space.contains(obs) is True for actual observations."""
        obs, _ = env.reset()
        assert env.observation_space.contains(obs)


class TestActionSpaceAPI:
    """Tests for action_space API compliance."""

    def test_action_space_is_discrete(self, env):
        """action_space is a gymnasium Discrete."""
        assert isinstance(env.action_space, Discrete)

    def test_action_space_contains_sample(self, env):
        """action_space.contains(action) is True for sampled actions."""
        action = env.action_space.sample()
        assert env.action_space.contains(action)


class TestEpisodeCompletion:
    """Tests for complete episode run."""

    def test_can_run_full_episode(self, env):
        """Can run a complete episode until termination."""
        obs, info = env.reset(seed=42)
        done = False
        steps = 0
        max_steps = 10000

        while not done and steps < max_steps:
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            steps += 1
            done = terminated or truncated

        # Episode should terminate before max_steps with random policy
        assert done, "Episode should terminate with random policy"
        assert steps < max_steps, "Episode should complete within reasonable steps"

    def test_can_reset_after_done(self, env):
        """Can reset and run again after episode ends."""
        # Run until done
        env.reset()
        done = False
        while not done:
            _, _, terminated, truncated, _ = env.step(env.action_space.sample())
            done = terminated or truncated

        # Reset and run again
        obs, info = env.reset()
        assert obs is not None
        _, reward, _, _, _ = env.step(env.action_space.sample())
        assert isinstance(reward, (int, float))
