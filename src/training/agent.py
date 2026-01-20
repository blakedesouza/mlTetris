"""TetrisAgent wrapper around SB3 DQN with unified checkpoint support."""

import json
from pathlib import Path
from typing import Optional, Tuple, Any, List, Union

import numpy as np
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import BaseCallback

from .config import TrainingConfig


class TetrisAgent:
    """DQN agent with full checkpoint support for Tetris training.

    Wraps Stable-Baselines3 DQN with unified checkpoint save/load that
    preserves model weights, optimizer state, replay buffer, and metadata.

    Example:
        >>> from src.environment import make_env, EnvConfig
        >>> env = make_env(EnvConfig())()
        >>> config = TrainingConfig(max_timesteps=10000)
        >>> agent = TetrisAgent(env, config)
        >>> agent.train(1000)
        >>> agent.save_checkpoint("./checkpoints/run1")
    """

    def __init__(self, env, config: TrainingConfig):
        """Initialize TetrisAgent with environment and configuration.

        Args:
            env: Gymnasium environment (from make_env factory).
            config: TrainingConfig with DQN hyperparameters.
        """
        self.env = env
        self.config = config
        self._total_timesteps_trained = 0

        # Create DQN with Tetris-tuned parameters
        self.model = DQN(
            "MlpPolicy",
            env,
            learning_rate=config.learning_rate,
            buffer_size=config.buffer_size,
            batch_size=config.batch_size,
            gamma=config.gamma,
            exploration_fraction=config.exploration_fraction,
            exploration_initial_eps=config.exploration_initial_eps,
            exploration_final_eps=config.exploration_final_eps,
            target_update_interval=config.target_update_interval,
            train_freq=config.train_freq,
            gradient_steps=config.gradient_steps,
            learning_starts=config.learning_starts,
            policy_kwargs=dict(net_arch=list(config.net_arch)),
            verbose=1,
        )

    def train(
        self,
        total_timesteps: int,
        callback: Optional[Union[BaseCallback, List[BaseCallback]]] = None,
    ) -> None:
        """Train the agent for specified timesteps.

        Continues from previous training - does not reset timestep counter.

        Args:
            total_timesteps: Number of timesteps to train.
            callback: Optional callback(s) for monitoring/checkpointing.
        """
        timesteps_before = self.model.num_timesteps
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=callback,
            reset_num_timesteps=False,  # Continue counting from previous
        )
        # Track actual timesteps trained (not requested), handles early stopping
        actual_trained = self.model.num_timesteps - timesteps_before
        self._total_timesteps_trained += actual_trained

    def save_checkpoint(self, path: Union[str, Path]) -> None:
        """Save complete training state to checkpoint directory.

        Saves:
        - model.zip: Model weights and optimizer state
        - replay_buffer.pkl: Experience replay buffer
        - metadata.json: Training metadata and config

        Args:
            path: Directory path to save checkpoint.
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save model (includes optimizer state)
        self.model.save(path / "model.zip")

        # Save replay buffer separately
        self.model.save_replay_buffer(path / "replay_buffer.pkl")

        # Save metadata for resume
        metadata = {
            "total_timesteps_trained": self._total_timesteps_trained,
            "num_timesteps": self.model.num_timesteps,
            "config": self.config.to_dict(),
        }
        with open(path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    @classmethod
    def load_checkpoint(cls, path: Union[str, Path], env) -> "TetrisAgent":
        """Load complete training state from checkpoint.

        Uses DQN.load() class method to properly restore optimizer state.

        Args:
            path: Directory path containing checkpoint.
            env: Gymnasium environment to use (must match original env spec).

        Returns:
            TetrisAgent instance with restored state.
        """
        path = Path(path)

        # Load metadata first
        with open(path / "metadata.json") as f:
            metadata = json.load(f)

        config = TrainingConfig.from_dict(metadata["config"])

        # Create agent with loaded model using __new__ to bypass __init__
        agent = cls.__new__(cls)
        agent.env = env
        agent.config = config
        agent._total_timesteps_trained = metadata["total_timesteps_trained"]

        # Use DQN.load() class method - NOT create then load
        # This properly restores optimizer state
        agent.model = DQN.load(path / "model.zip", env=env)

        # Load replay buffer
        agent.model.load_replay_buffer(path / "replay_buffer.pkl")

        return agent

    def predict(
        self,
        observation: np.ndarray,
        deterministic: bool = True,
    ) -> Tuple[int, Any]:
        """Predict action for given observation.

        Args:
            observation: Environment observation.
            deterministic: If True, use greedy action. If False, may explore.

        Returns:
            Tuple of (action, state). State is None for DQN.
        """
        return self.model.predict(observation, deterministic=deterministic)

    @property
    def timesteps_trained(self) -> int:
        """Total number of timesteps trained across all train() calls."""
        return self._total_timesteps_trained
