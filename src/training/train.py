"""Headless training function with checkpoint support."""

import os
from pathlib import Path
from typing import Optional

from stable_baselines3.common.callbacks import CallbackList, CheckpointCallback

from src.environment import make_env, EnvConfig
from .agent import TetrisAgent
from .callbacks import LinesTrackingCallback, GoalReachedCallback
from .config import TrainingConfig


def train_headless(
    config: TrainingConfig,
    checkpoint_dir: Optional[str] = None,
) -> TetrisAgent:
    """Run headless training with periodic checkpoints.

    Creates a headless environment (no rendering), trains a DQN agent,
    and saves checkpoints periodically. Supports resuming from existing
    checkpoint if available.

    Args:
        config: Training configuration with DQN hyperparameters.
        checkpoint_dir: Override for checkpoint directory.
            If None, uses config.checkpoint_dir.

    Returns:
        Trained TetrisAgent.

    Example:
        >>> config = TrainingConfig(max_timesteps=100000, target_lines=10)
        >>> agent = train_headless(config)
        >>> print(f"Trained for {agent.timesteps_trained} steps")
    """
    # Set checkpoint directory from param or config
    checkpoint_path = Path(checkpoint_dir or config.checkpoint_dir)
    checkpoint_path.mkdir(parents=True, exist_ok=True)

    # Create headless environment (render_mode=None)
    env_config = EnvConfig(render_mode=None)
    env = make_env(env_config)()

    # Check for existing checkpoint to resume
    latest_checkpoint = checkpoint_path / "latest"
    if latest_checkpoint.exists():
        agent = TetrisAgent.load_checkpoint(latest_checkpoint, env)
        print(
            f"Resumed from checkpoint, {agent.timesteps_trained} steps "
            "already trained"
        )
    else:
        agent = TetrisAgent(env, config)

    # Set up callbacks
    callbacks = []

    # Lines tracking callback (always add for progress monitoring)
    lines_tracker = LinesTrackingCallback(verbose=1)
    callbacks.append(lines_tracker)

    # SB3 CheckpointCallback for periodic saves
    checkpoint_callback = CheckpointCallback(
        save_freq=config.checkpoint_freq,
        save_path=str(checkpoint_path),
        name_prefix="ckpt",
        save_replay_buffer=True,
    )
    callbacks.append(checkpoint_callback)

    # Goal-based early stopping (if target_lines set)
    if config.target_lines is not None:
        goal_callback = GoalReachedCallback(
            target_lines=config.target_lines,
            lines_tracker=lines_tracker,
            verbose=1,
        )
        callbacks.append(goal_callback)

    callback_list = CallbackList(callbacks)

    # Calculate remaining timesteps
    remaining = config.max_timesteps - agent.timesteps_trained
    if remaining <= 0:
        print(f"Already trained {agent.timesteps_trained} steps, nothing to do")
        return agent

    print(f"Training for {remaining} timesteps...")

    # Train
    agent.train(remaining, callback=callback_list)

    # Save final checkpoints
    agent.save_checkpoint(checkpoint_path / "latest")
    agent.save_checkpoint(checkpoint_path / "final")

    print(f"Training complete. Total steps: {agent.timesteps_trained}")
    print(f"Best lines cleared: {lines_tracker.get_best_lines()}")

    return agent


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Train Tetris DQN agent")
    parser.add_argument(
        "--max-timesteps",
        type=int,
        default=500_000,
        help="Maximum training timesteps (default: 500000)",
    )
    parser.add_argument(
        "--target-lines",
        type=int,
        default=None,
        help="Target lines to clear for early stopping (default: no target)",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default="./checkpoints",
        help="Directory for checkpoints (default: ./checkpoints)",
    )
    parser.add_argument(
        "--checkpoint-freq",
        type=int,
        default=10_000,
        help="Save checkpoint every N steps (default: 10000)",
    )
    parser.add_argument(
        "--learning-starts",
        type=int,
        default=10_000,
        help="Start learning after N steps (default: 10000)",
    )

    args = parser.parse_args()

    training_config = TrainingConfig(
        max_timesteps=args.max_timesteps,
        target_lines=args.target_lines,
        checkpoint_dir=args.checkpoint_dir,
        checkpoint_freq=args.checkpoint_freq,
        learning_starts=args.learning_starts,
    )

    trained_agent = train_headless(training_config)
