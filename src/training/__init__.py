# Training module - exports training configuration, agent wrapper, and callbacks

from .config import TrainingConfig
from .agent import TetrisAgent
from .callbacks import LinesTrackingCallback, GoalReachedCallback

__all__ = [
    "TrainingConfig",
    "TetrisAgent",
    "LinesTrackingCallback",
    "GoalReachedCallback",
]
