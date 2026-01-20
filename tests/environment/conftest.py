"""Pytest fixtures for environment tests."""

import pytest

from src.environment import create_tetris_env, EnvConfig


@pytest.fixture
def env():
    """Create a default Tetris environment for testing."""
    e = create_tetris_env()
    yield e
    e.close()


@pytest.fixture
def env_with_config():
    """Create a Tetris environment with custom config."""
    config = EnvConfig(
        hole_penalty=-1.0,
        height_penalty=-0.2,
        clear_bonus_multiplier=2.0,
        game_over_penalty=-20.0,
    )
    e = create_tetris_env(
        reward_config={
            "hole_penalty": config.hole_penalty,
            "height_penalty": config.height_penalty,
            "clear_bonus_multiplier": config.clear_bonus_multiplier,
            "game_over_penalty": config.game_over_penalty,
        }
    )
    yield e
    e.close()
