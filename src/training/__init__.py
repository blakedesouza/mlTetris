# Training module - exports training configuration, agent wrapper, callbacks, and training functions

from .config import TrainingConfig
from .agent import TetrisAgent
from .callbacks import LinesTrackingCallback, GoalReachedCallback, WebMetricsCallback
from .train import train_headless

__all__ = [
    "TrainingConfig",
    "TetrisAgent",
    "LinesTrackingCallback",
    "GoalReachedCallback",
    "WebMetricsCallback",
    "train_headless",
]
