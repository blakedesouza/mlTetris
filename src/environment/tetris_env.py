"""Factory functions for creating the configured Tetris environment.

This module provides factory functions to create a fully-configured Tetris
environment with feature-based observations, meta-actions, and shaped rewards.
"""

from typing import Callable, Optional

import gymnasium as gym

from tetris_gymnasium.wrappers.grouped import GroupedActionsObservations
from tetris_gymnasium.wrappers.observation import FeatureVectorObservation

from .config import EnvConfig
from .wrappers import ShapedRewardWrapper


def create_tetris_env(
    render_mode: Optional[str] = None,
    reward_config: Optional[dict] = None,
) -> gym.Env:
    """Create fully-configured Tetris environment for RL training.

    Creates a Tetris environment with:
    1. Meta-actions (rotation + column as single action via GroupedActionsObservations)
    2. Feature-based observations (column heights, holes, bumpiness via FeatureVectorObservation)
    3. Shaped rewards (penalties for holes/height, bonus for clears via ShapedRewardWrapper)

    Wrapper integration:
        GroupedActionsObservations wraps FeatureVectorObservation internally via observation_wrappers
        parameter. This produces observations of shape (40, 13) where each of the 40 actions has
        13 feature values. ShapedRewardWrapper is applied on top for reward shaping.

    Args:
        render_mode: Rendering mode for the environment.
            None for headless training, "human" for display, "ansi" for text.
        reward_config: Optional dict with reward shaping parameters:
            - hole_penalty: Penalty per new hole (default: -0.5)
            - height_penalty: Penalty per height increase (default: -0.1)
            - clear_bonus_multiplier: Multiplier for line clears (default: 1.0)
            - game_over_penalty: Penalty on game over (default: -10.0)

    Returns:
        Gymnasium Env with feature observations, meta-actions, and shaped rewards.
    """
    # 1. Base environment with primitive actions
    env = gym.make("tetris_gymnasium/Tetris", render_mode=render_mode)

    # 2. Create feature extraction wrapper (needs its own base env for observation space)
    # FeatureVectorObservation extracts 13 features: column heights, max height, holes, bumpiness
    feature_wrapper = FeatureVectorObservation(
        gym.make("tetris_gymnasium/Tetris", render_mode=render_mode)
    )

    # 3. Wrap with GroupedActionsObservations, passing feature wrapper for internal use
    # This changes action space from Discrete(8) to Discrete(width * 4) = Discrete(40)
    # Observations become shape (40, 13) - features for each possible action
    env = GroupedActionsObservations(env, observation_wrappers=[feature_wrapper])

    # 4. Reward shaping wrapper
    if reward_config:
        env = ShapedRewardWrapper(env, **reward_config)
    else:
        env = ShapedRewardWrapper(env)

    return env


def make_env(config: Optional[EnvConfig] = None) -> Callable[[], gym.Env]:
    """Factory that returns a callable for vectorized env creation.

    This pattern is needed for SB3's make_vec_env which requires a callable
    that creates new environment instances.

    Args:
        config: Optional EnvConfig with environment settings.
            If None, uses default EnvConfig().

    Returns:
        Callable that creates a new configured environment when invoked.

    Example:
        >>> from stable_baselines3.common.vec_env import DummyVecEnv
        >>> env_fn = make_env(EnvConfig(render_mode=None))
        >>> vec_env = DummyVecEnv([env_fn])  # Creates vectorized env
    """
    if config is None:
        config = EnvConfig()

    def _init() -> gym.Env:
        reward_config = {
            "hole_penalty": config.hole_penalty,
            "height_penalty": config.height_penalty,
            "clear_bonus_multiplier": config.clear_bonus_multiplier,
            "game_over_penalty": config.game_over_penalty,
        }
        return create_tetris_env(
            render_mode=config.render_mode,
            reward_config=reward_config,
        )

    return _init
