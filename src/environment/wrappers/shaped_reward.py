"""Custom reward shaping wrapper for Tetris environment.

This wrapper modifies the base reward to include penalties for creating holes
and building too high, encouraging cleaner play.
"""

from typing import Any

import numpy as np
from gymnasium import RewardWrapper


class ShapedRewardWrapper(RewardWrapper):
    """Add shaped rewards: penalties for holes and height, bonus for clears.

    Reward formula:
        reward = (base_reward * clear_bonus_multiplier)
               + (new_holes * hole_penalty)
               + (height_increase * height_penalty)
               + (game_over ? game_over_penalty : 0)

    Where:
        - base_reward: The original reward from the environment (lines cleared)
        - new_holes: Number of new holes created this step (0 if holes decreased)
        - height_increase: Increase in max stack height (0 if height decreased)

    The wrapper tracks holes and height between steps to compute deltas,
    only penalizing increases (not improvements).

    Attributes:
        hole_penalty: Penalty per new hole created (default: -0.5)
        height_penalty: Penalty per row of height increase (default: -0.1)
        clear_bonus_multiplier: Multiplier for line clear reward (default: 1.0)
        game_over_penalty: Penalty applied when game ends (default: -10.0)
    """

    # Board layout constants for tetris-gymnasium
    # Board is 24 rows x 18 cols with 4-cell padding on sides and bottom
    BOARD_ROWS = 20  # Playable rows (0-19 in slice)
    BOARD_COLS = 10  # Playable cols
    PADDING_LEFT = 4  # Frame padding on left
    PADDING_RIGHT = 4  # Frame padding on right
    PADDING_BOTTOM = 4  # Floor padding

    def __init__(
        self,
        env,
        hole_penalty: float = -0.5,
        height_penalty: float = -0.1,
        clear_bonus_multiplier: float = 1.0,
        game_over_penalty: float = -10.0,
    ):
        """Initialize the shaped reward wrapper.

        Args:
            env: The environment to wrap.
            hole_penalty: Penalty per new hole created (should be negative).
            height_penalty: Penalty per row of height increase (should be negative).
            clear_bonus_multiplier: Multiplier for base line clear reward.
            game_over_penalty: Additional penalty when game ends (should be negative).
        """
        super().__init__(env)
        self.hole_penalty = hole_penalty
        self.height_penalty = height_penalty
        self.clear_bonus_multiplier = clear_bonus_multiplier
        self.game_over_penalty = game_over_penalty

        # State tracking for delta calculations
        self._prev_holes = 0
        self._prev_height = 0

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[Any, dict[str, Any]]:
        """Reset the environment and initialize tracking state.

        Args:
            seed: Optional seed for the environment's random number generator.
            options: Optional additional options for reset.

        Returns:
            Initial observation and info dict.
        """
        obs, info = self.env.reset(seed=seed, options=options)

        # Initialize tracking from initial board state
        board = self._get_playable_board()
        self._prev_holes = self._count_holes(board)
        self._prev_height = self._get_max_height(board)

        # Ensure observation dtype matches observation_space (fix upstream float64 issue)
        if hasattr(obs, "dtype") and obs.dtype != self.observation_space.dtype:
            obs = obs.astype(self.observation_space.dtype)

        return obs, info

    def step(self, action: Any) -> tuple[Any, float, bool, bool, dict[str, Any]]:
        """Take a step and compute shaped reward.

        Args:
            action: The action to take.

        Returns:
            Tuple of (observation, shaped_reward, terminated, truncated, info).
        """
        obs, reward, terminated, truncated, info = self.env.step(action)

        # Compute current board metrics
        board = self._get_playable_board()
        current_holes = self._count_holes(board)
        current_height = self._get_max_height(board)

        # Only penalize increases (new problems), not improvements
        new_holes = max(0, current_holes - self._prev_holes)
        height_increase = max(0, current_height - self._prev_height)

        # Shape the reward
        shaped_reward = reward * self.clear_bonus_multiplier
        shaped_reward += new_holes * self.hole_penalty
        shaped_reward += height_increase * self.height_penalty

        # Add game over penalty
        if terminated:
            shaped_reward += self.game_over_penalty

        # Update tracking state
        self._prev_holes = current_holes
        self._prev_height = current_height

        # Ensure observation dtype matches observation_space (fix upstream float64 issue)
        if hasattr(obs, "dtype") and obs.dtype != self.observation_space.dtype:
            obs = obs.astype(self.observation_space.dtype)

        return obs, shaped_reward, terminated, truncated, info

    def reward(self, reward: float) -> float:
        """Required by RewardWrapper but not used - we override step() instead.

        This method exists for API compatibility but step() handles all
        reward shaping since we need access to the board state and info.

        Args:
            reward: The original reward.

        Returns:
            The reward unchanged.
        """
        return reward

    def _get_playable_board(self) -> np.ndarray:
        """Extract the playable area from the environment's board.

        Returns:
            2D numpy array of shape (BOARD_ROWS, BOARD_COLS) representing
            the playable area. Values > 0 indicate placed blocks.
        """
        # Access the unwrapped environment's board (placed blocks only)
        full_board = self.env.unwrapped.board

        # Extract playable area: skip padding
        # Rows: 0 to BOARD_ROWS (top 20 rows are playable)
        # Cols: PADDING_LEFT to -PADDING_RIGHT
        playable = full_board[
            : self.BOARD_ROWS, self.PADDING_LEFT : -self.PADDING_RIGHT
        ]

        return playable

    def _count_holes(self, board: np.ndarray) -> int:
        """Count the number of holes in the board.

        A hole is an empty cell with at least one filled cell above it
        in the same column.

        Args:
            board: 2D array of the playable board area.

        Returns:
            Total number of holes.
        """
        holes = 0
        rows, cols = board.shape

        for col in range(cols):
            column = board[:, col]
            # Find first filled cell from top
            filled_indices = np.where(column > 0)[0]
            if len(filled_indices) == 0:
                continue  # Empty column, no holes

            first_filled_row = filled_indices[0]
            # Count empty cells below the first filled cell
            for row in range(first_filled_row + 1, rows):
                if column[row] == 0:
                    holes += 1

        return holes

    def _get_max_height(self, board: np.ndarray) -> int:
        """Get the maximum stack height on the board.

        Height is measured from the bottom, with 0 being an empty board.

        Args:
            board: 2D array of the playable board area.

        Returns:
            Maximum stack height (0 to BOARD_ROWS).
        """
        rows, cols = board.shape

        max_height = 0
        for col in range(cols):
            column = board[:, col]
            filled_indices = np.where(column > 0)[0]
            if len(filled_indices) > 0:
                # Height is rows - first_filled_row
                # (first filled row from top converted to height from bottom)
                col_height = rows - filled_indices[0]
                max_height = max(max_height, col_height)

        return max_height
