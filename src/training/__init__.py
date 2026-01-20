# Training module - exports training configuration and agent wrapper

from .config import TrainingConfig
from .agent import TetrisAgent

__all__ = [
    "TrainingConfig",
    "TetrisAgent",
]
