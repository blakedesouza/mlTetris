"""Shared fixtures for training module tests."""

import pytest
import tempfile
from pathlib import Path
from src.training import TrainingConfig, TetrisAgent
from src.environment import make_env, EnvConfig


@pytest.fixture
def env():
    """Create headless environment for testing."""
    _env = make_env(EnvConfig(render_mode=None))()
    yield _env
    _env.close()


@pytest.fixture
def config():
    """Training config with small values for fast tests."""
    return TrainingConfig(
        max_timesteps=500,
        learning_starts=50,
        buffer_size=1000,
        checkpoint_freq=100,
    )


@pytest.fixture
def tmp_checkpoint_dir():
    """Temporary directory for checkpoint tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
