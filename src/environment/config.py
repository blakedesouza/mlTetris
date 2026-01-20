"""Configuration dataclass for Tetris environment creation."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class EnvConfig:
    """Configuration for Tetris environment creation.

    Attributes:
        render_mode: Rendering mode for the environment.
            None for headless, "human" for display, "ansi" for text, "rgb_array" for images.
        hole_penalty: Penalty per new hole created (should be negative).
        height_penalty: Penalty per row of height increase (should be negative).
        clear_bonus_multiplier: Multiplier for base line clear reward.
        game_over_penalty: Additional penalty when game ends (should be negative).
    """

    render_mode: Optional[str] = None
    hole_penalty: float = -0.5
    height_penalty: float = -0.1
    clear_bonus_multiplier: float = 1.0
    game_over_penalty: float = -10.0
