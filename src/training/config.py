"""Training configuration dataclass for DQN hyperparameters."""

from dataclasses import dataclass, asdict, field
from typing import Optional, Tuple, Dict, Any


@dataclass
class TrainingConfig:
    """DQN training configuration with Tetris-tuned defaults.

    These defaults are tuned specifically for Tetris based on RL Zoo
    hyperparameters and Tetris-specific considerations.

    Attributes:
        learning_rate: Learning rate for the optimizer.
        buffer_size: Size of the replay buffer.
        batch_size: Mini-batch size for each gradient update.
        gamma: Discount factor for future rewards.
        exploration_fraction: Fraction of total training for epsilon decay.
        exploration_initial_eps: Initial exploration rate.
        exploration_final_eps: Final exploration rate.
        target_update_interval: Number of steps between target network updates.
        train_freq: Number of steps between gradient updates.
        gradient_steps: Number of gradient steps per update.
        learning_starts: Number of steps before learning starts.
        target_lines: Optional goal for early stopping (lines to clear).
        max_timesteps: Maximum training timesteps.
        net_arch: Network architecture (hidden layer sizes).
        checkpoint_dir: Directory for saving checkpoints.
        checkpoint_freq: Save checkpoint every N steps.
    """

    # Core DQN parameters
    learning_rate: float = 1e-4
    buffer_size: int = 100_000
    batch_size: int = 64
    gamma: float = 0.99

    # Exploration schedule
    exploration_fraction: float = 0.2
    exploration_initial_eps: float = 1.0
    exploration_final_eps: float = 0.05

    # Network updates
    target_update_interval: int = 1000
    train_freq: int = 4
    gradient_steps: int = 1
    learning_starts: int = 10_000

    # Training goal
    target_lines: Optional[int] = None
    max_timesteps: int = 500_000

    # Network architecture
    net_arch: Tuple[int, ...] = (256, 256)

    # Checkpoint settings
    checkpoint_dir: str = "./checkpoints"
    checkpoint_freq: int = 10_000

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization.

        Returns:
            Dictionary with all configuration values.
        """
        d = asdict(self)
        # Convert tuple to list for JSON compatibility
        d["net_arch"] = list(d["net_arch"])
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TrainingConfig":
        """Create config from dictionary.

        Args:
            d: Dictionary with configuration values.

        Returns:
            TrainingConfig instance.
        """
        # Convert net_arch back to tuple if it's a list
        if "net_arch" in d and isinstance(d["net_arch"], list):
            d = d.copy()
            d["net_arch"] = tuple(d["net_arch"])
        return cls(**d)
