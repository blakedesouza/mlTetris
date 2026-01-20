# Environment module - exports factory functions and configuration

from .config import EnvConfig
from .tetris_env import create_tetris_env, make_env
from .wrappers import ShapedRewardWrapper

__all__ = [
    "create_tetris_env",
    "make_env",
    "EnvConfig",
    "ShapedRewardWrapper",
]
