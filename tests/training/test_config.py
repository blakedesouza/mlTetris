"""Tests for TrainingConfig dataclass."""

import pytest
from src.training import TrainingConfig


class TestTrainingConfigDefaults:
    """Tests for Tetris-tuned default values."""

    def test_config_defaults(self):
        """Verify Tetris-tuned defaults are set."""
        config = TrainingConfig()

        # Core DQN parameters
        assert config.learning_rate == 1e-4
        assert config.buffer_size == 100_000
        assert config.batch_size == 64
        assert config.gamma == 0.99

        # Exploration schedule
        assert config.exploration_fraction == 0.2
        assert config.exploration_initial_eps == 1.0
        assert config.exploration_final_eps == 0.05

        # Network updates
        assert config.target_update_interval == 1000
        assert config.train_freq == 4
        assert config.gradient_steps == 1
        assert config.learning_starts == 10_000

        # Training goal
        assert config.target_lines is None
        assert config.max_timesteps == 500_000

        # Network architecture
        assert config.net_arch == (256, 256)

        # Checkpoint settings
        assert config.checkpoint_dir == "./checkpoints"
        assert config.checkpoint_freq == 10_000


class TestTrainingConfigCustomValues:
    """Tests for custom configuration values."""

    def test_config_custom_values(self):
        """Verify custom values override defaults."""
        config = TrainingConfig(
            learning_rate=0.001,
            buffer_size=50_000,
            batch_size=32,
            gamma=0.95,
            target_lines=100,
            max_timesteps=200_000,
            net_arch=(128, 128, 64),
        )

        assert config.learning_rate == 0.001
        assert config.buffer_size == 50_000
        assert config.batch_size == 32
        assert config.gamma == 0.95
        assert config.target_lines == 100
        assert config.max_timesteps == 200_000
        assert config.net_arch == (128, 128, 64)


class TestTrainingConfigSerialization:
    """Tests for config serialization (to_dict/from_dict)."""

    def test_config_to_dict(self):
        """Serialization preserves all fields."""
        config = TrainingConfig(
            learning_rate=0.001,
            target_lines=50,
        )
        d = config.to_dict()

        assert isinstance(d, dict)
        assert d["learning_rate"] == 0.001
        assert d["target_lines"] == 50
        # net_arch should be converted to list for JSON compatibility
        assert isinstance(d["net_arch"], list)
        assert d["net_arch"] == [256, 256]

    def test_config_from_dict(self):
        """Deserialization restores all fields."""
        d = {
            "learning_rate": 0.002,
            "buffer_size": 25_000,
            "batch_size": 64,
            "gamma": 0.99,
            "exploration_fraction": 0.2,
            "exploration_initial_eps": 1.0,
            "exploration_final_eps": 0.05,
            "target_update_interval": 1000,
            "train_freq": 4,
            "gradient_steps": 1,
            "learning_starts": 5000,
            "target_lines": 200,
            "max_timesteps": 100_000,
            "net_arch": [64, 64],  # List from JSON
            "checkpoint_dir": "./my_checkpoints",
            "checkpoint_freq": 5000,
        }
        config = TrainingConfig.from_dict(d)

        assert config.learning_rate == 0.002
        assert config.buffer_size == 25_000
        assert config.target_lines == 200
        assert config.max_timesteps == 100_000
        # net_arch should be converted back to tuple
        assert isinstance(config.net_arch, tuple)
        assert config.net_arch == (64, 64)
        assert config.checkpoint_dir == "./my_checkpoints"

    def test_config_roundtrip(self):
        """to_dict -> from_dict preserves all values."""
        original = TrainingConfig(
            learning_rate=0.0005,
            buffer_size=75_000,
            target_lines=150,
            net_arch=(512, 256, 128),
            checkpoint_freq=8000,
        )

        d = original.to_dict()
        restored = TrainingConfig.from_dict(d)

        assert restored.learning_rate == original.learning_rate
        assert restored.buffer_size == original.buffer_size
        assert restored.target_lines == original.target_lines
        assert restored.net_arch == original.net_arch
        assert restored.checkpoint_freq == original.checkpoint_freq
        assert restored.max_timesteps == original.max_timesteps
        assert restored.batch_size == original.batch_size
