"""Tests for checkpoint save/load functionality.

Covers requirements:
- MODEL-01: Save checkpoint (model + replay buffer + metadata)
- MODEL-02: Load checkpoint (restore full training state)
- MODEL-03: Resume training (continue from exact state)
"""

import pytest
import json
from pathlib import Path

from src.training import TrainingConfig, TetrisAgent
from src.environment import make_env, EnvConfig


class TestCheckpointSave:
    """Tests for checkpoint saving (MODEL-01)."""

    def test_save_checkpoint_creates_files(self, env, config, tmp_checkpoint_dir):
        """save_checkpoint creates model.zip, replay_buffer.pkl, metadata.json."""
        agent = TetrisAgent(env, config)
        agent.train(100)

        checkpoint_path = tmp_checkpoint_dir / "test_checkpoint"
        agent.save_checkpoint(checkpoint_path)

        # Verify all required files exist
        assert (checkpoint_path / "model.zip").exists()
        assert (checkpoint_path / "replay_buffer.pkl").exists()
        assert (checkpoint_path / "metadata.json").exists()

    def test_checkpoint_metadata_contents(self, env, config, tmp_checkpoint_dir):
        """metadata.json contains timesteps, config."""
        agent = TetrisAgent(env, config)
        agent.train(150)

        checkpoint_path = tmp_checkpoint_dir / "test_checkpoint"
        agent.save_checkpoint(checkpoint_path)

        # Read and verify metadata
        with open(checkpoint_path / "metadata.json") as f:
            metadata = json.load(f)

        assert "total_timesteps_trained" in metadata
        assert metadata["total_timesteps_trained"] == 150
        assert "num_timesteps" in metadata
        assert "config" in metadata
        # Config should contain the original values
        assert metadata["config"]["max_timesteps"] == config.max_timesteps
        assert metadata["config"]["learning_starts"] == config.learning_starts


class TestCheckpointLoad:
    """Tests for checkpoint loading (MODEL-02)."""

    def test_load_checkpoint_restores_agent(self, env, config, tmp_checkpoint_dir):
        """load_checkpoint returns working agent."""
        agent = TetrisAgent(env, config)
        agent.train(100)

        checkpoint_path = tmp_checkpoint_dir / "test_checkpoint"
        agent.save_checkpoint(checkpoint_path)

        # Create fresh env for loaded agent
        env2 = make_env(EnvConfig(render_mode=None))()
        try:
            loaded_agent = TetrisAgent.load_checkpoint(checkpoint_path, env2)

            # Loaded agent should be functional
            assert loaded_agent is not None
            obs, _ = env2.reset()
            action, _ = loaded_agent.predict(obs)
            assert action is not None
        finally:
            env2.close()

    def test_load_checkpoint_restores_timesteps(self, env, config, tmp_checkpoint_dir):
        """loaded agent has correct timesteps_trained."""
        agent = TetrisAgent(env, config)
        train_steps = 200

        agent.train(train_steps)
        checkpoint_path = tmp_checkpoint_dir / "test_checkpoint"
        agent.save_checkpoint(checkpoint_path)

        # Load into fresh env
        env2 = make_env(EnvConfig(render_mode=None))()
        try:
            loaded_agent = TetrisAgent.load_checkpoint(checkpoint_path, env2)

            assert loaded_agent.timesteps_trained == train_steps
        finally:
            env2.close()

    def test_load_checkpoint_restores_config(self, env, tmp_checkpoint_dir):
        """loaded agent has original config values."""
        custom_config = TrainingConfig(
            learning_rate=0.0005,
            buffer_size=5000,
            max_timesteps=1000,
            learning_starts=50,
        )

        agent = TetrisAgent(env, custom_config)
        agent.train(100)

        checkpoint_path = tmp_checkpoint_dir / "test_checkpoint"
        agent.save_checkpoint(checkpoint_path)

        # Load into fresh env
        env2 = make_env(EnvConfig(render_mode=None))()
        try:
            loaded_agent = TetrisAgent.load_checkpoint(checkpoint_path, env2)

            assert loaded_agent.config.learning_rate == 0.0005
            assert loaded_agent.config.buffer_size == 5000
            assert loaded_agent.config.max_timesteps == 1000
        finally:
            env2.close()


class TestCheckpointResume:
    """Tests for resuming training from checkpoint (MODEL-03)."""

    def test_resume_training_continues(self, env, config, tmp_checkpoint_dir):
        """train() after load continues from saved state."""
        agent = TetrisAgent(env, config)
        agent.train(100)

        checkpoint_path = tmp_checkpoint_dir / "test_checkpoint"
        agent.save_checkpoint(checkpoint_path)

        # Load and continue training
        env2 = make_env(EnvConfig(render_mode=None))()
        try:
            loaded_agent = TetrisAgent.load_checkpoint(checkpoint_path, env2)
            initial_steps = loaded_agent.timesteps_trained

            loaded_agent.train(50)

            assert loaded_agent.timesteps_trained == initial_steps + 50
        finally:
            env2.close()

    def test_replay_buffer_preserved(self, env, config, tmp_checkpoint_dir):
        """replay buffer has entries after load (not empty)."""
        # Use config with learning_starts=0 so buffer fills during training
        config_fast = TrainingConfig(
            max_timesteps=500,
            learning_starts=0,
            buffer_size=1000,
        )

        agent = TetrisAgent(env, config_fast)
        agent.train(200)  # Train enough to fill buffer

        # Check buffer has entries before save
        buffer_size_before = agent.model.replay_buffer.size()
        assert buffer_size_before > 0, "Buffer should have entries before save"

        checkpoint_path = tmp_checkpoint_dir / "test_checkpoint"
        agent.save_checkpoint(checkpoint_path)

        # Load and verify buffer
        env2 = make_env(EnvConfig(render_mode=None))()
        try:
            loaded_agent = TetrisAgent.load_checkpoint(checkpoint_path, env2)
            buffer_size_after = loaded_agent.model.replay_buffer.size()

            assert buffer_size_after > 0, "Buffer should have entries after load"
            assert buffer_size_after == buffer_size_before, \
                "Buffer size should be preserved through checkpoint"
        finally:
            env2.close()

    def test_exploration_rate_preserved(self, env, tmp_checkpoint_dir):
        """Verify epsilon/exploration_rate is preserved through checkpoint.

        This explicitly verifies that SB3's internal exploration state is saved
        and restored, ensuring resumed training doesn't restart exploration
        from scratch.
        """
        # Train enough to reduce epsilon from initial (1.0)
        config = TrainingConfig(
            max_timesteps=2000,
            learning_starts=100,
            exploration_fraction=0.5,  # Decay over 50% of training
            exploration_initial_eps=1.0,
            exploration_final_eps=0.05,
        )
        agent = TetrisAgent(env, config)
        agent.train(1000)  # Train partway through exploration decay

        # Capture epsilon before save
        epsilon_before = agent.model.exploration_rate
        assert epsilon_before < 1.0, "Epsilon should have decayed during training"

        # Save and reload
        checkpoint_path = tmp_checkpoint_dir / "test_eps"
        agent.save_checkpoint(checkpoint_path)

        # Create fresh env for loaded agent
        env2 = make_env(EnvConfig(render_mode=None))()
        try:
            loaded_agent = TetrisAgent.load_checkpoint(checkpoint_path, env2)
            epsilon_after = loaded_agent.model.exploration_rate

            # Epsilon should be preserved (SB3 stores this in the model)
            assert abs(epsilon_after - epsilon_before) < 0.01, \
                f"Epsilon not preserved: before={epsilon_before}, after={epsilon_after}"
        finally:
            env2.close()
