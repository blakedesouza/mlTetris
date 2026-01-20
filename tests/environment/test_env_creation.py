"""Tests for environment creation and basic functionality."""

import pytest

from src.environment import create_tetris_env, make_env, EnvConfig


class TestCreateEnv:
    """Tests for create_tetris_env factory function."""

    def test_create_env_default(self):
        """Can create environment with no arguments."""
        env = create_tetris_env()
        assert env is not None
        env.close()

    def test_create_env_with_render_mode(self):
        """Can create environment with render_mode='ansi'."""
        env = create_tetris_env(render_mode="ansi")
        assert env is not None
        env.close()

    def test_create_env_with_reward_config(self):
        """Can create environment with custom reward config."""
        reward_config = {
            "hole_penalty": -1.0,
            "height_penalty": -0.2,
        }
        env = create_tetris_env(reward_config=reward_config)
        assert env is not None
        env.close()


class TestMakeEnv:
    """Tests for make_env factory function."""

    def test_make_env_returns_callable(self):
        """make_env returns a callable."""
        env_fn = make_env()
        assert callable(env_fn)

    def test_make_env_callable_creates_env(self):
        """Calling the returned function creates an environment."""
        env_fn = make_env()
        env = env_fn()
        assert env is not None
        env.close()

    def test_make_env_with_config(self):
        """make_env works with EnvConfig."""
        config = EnvConfig(
            hole_penalty=-2.0,
            height_penalty=-0.5,
        )
        env_fn = make_env(config)
        env = env_fn()
        assert env is not None
        env.close()


class TestEnvReset:
    """Tests for environment reset functionality."""

    def test_env_reset_returns_tuple(self, env):
        """reset() returns (obs, info) tuple."""
        result = env.reset()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_env_reset_returns_observation(self, env):
        """reset() returns an observation as first element."""
        obs, info = env.reset()
        assert obs is not None
        assert hasattr(obs, "shape")

    def test_env_reset_returns_info_dict(self, env):
        """reset() returns an info dict as second element."""
        obs, info = env.reset()
        assert isinstance(info, dict)

    def test_env_reset_with_seed(self, env):
        """reset() accepts seed parameter without error."""
        # Note: The environment uses randomizers (7-bag) that may not be
        # deterministically seeded through wrapper layers, so we just verify
        # that the seed parameter is accepted and returns valid observations
        obs, _ = env.reset(seed=42)
        assert obs is not None
        assert hasattr(obs, "shape")


class TestEnvStep:
    """Tests for environment step functionality."""

    def test_env_step_returns_five_tuple(self, env):
        """step() returns 5-tuple (obs, reward, terminated, truncated, info)."""
        env.reset()
        result = env.step(env.action_space.sample())
        assert isinstance(result, tuple)
        assert len(result) == 5

    def test_env_step_returns_observation(self, env):
        """step() returns observation as first element."""
        env.reset()
        obs, _, _, _, _ = env.step(env.action_space.sample())
        assert obs is not None
        assert hasattr(obs, "shape")

    def test_env_step_returns_float_reward(self, env):
        """step() returns float reward."""
        env.reset()
        _, reward, _, _, _ = env.step(env.action_space.sample())
        assert isinstance(reward, (int, float))

    def test_env_step_returns_terminated_bool(self, env):
        """step() returns boolean terminated flag."""
        env.reset()
        _, _, terminated, _, _ = env.step(env.action_space.sample())
        assert isinstance(terminated, bool)

    def test_env_step_returns_truncated_bool(self, env):
        """step() returns boolean truncated flag."""
        env.reset()
        _, _, _, truncated, _ = env.step(env.action_space.sample())
        assert isinstance(truncated, bool)

    def test_env_step_returns_info_dict(self, env):
        """step() returns info dict."""
        env.reset()
        _, _, _, _, info = env.step(env.action_space.sample())
        assert isinstance(info, dict)
