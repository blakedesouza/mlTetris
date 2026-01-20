"""Custom SB3 callbacks for Tetris training."""

from typing import Optional

from stable_baselines3.common.callbacks import BaseCallback


class LinesTrackingCallback(BaseCallback):
    """Track lines cleared during training.

    Since tetris-gymnasium may not include 'lines' in ep_info_buffer
    automatically, this callback extracts lines from info dict after
    each episode ends.

    Attributes:
        best_lines: Maximum lines cleared in a single episode.
        total_lines: Total lines cleared across all episodes.
    """

    def __init__(self, verbose: int = 0):
        """Initialize lines tracking callback.

        Args:
            verbose: Verbosity level (0=silent, 1=info).
        """
        super().__init__(verbose)
        self.best_lines = 0
        self.total_lines = 0
        self._episode_lines = 0

    def _on_step(self) -> bool:
        """Called after each environment step.

        Extracts lines from info dict and tracks best/total.

        Returns:
            True to continue training.
        """
        # Access info from locals - this is available after step()
        infos = self.locals.get("infos", [])

        for info in infos:
            # Check for lines in info dict
            # tetris-gymnasium may use 'lines' or 'lines_cleared'
            lines = info.get("lines", info.get("lines_cleared", 0))

            # Track episode lines (accumulate within episode)
            # Some envs report total lines, some report delta
            if lines > self._episode_lines:
                self._episode_lines = lines

            # Check if episode ended
            if info.get("episode") or self.locals.get("dones", [False])[0]:
                # Episode finished, record final lines
                if self._episode_lines > self.best_lines:
                    self.best_lines = self._episode_lines
                    if self.verbose > 0:
                        print(f"New best lines: {self.best_lines}")

                self.total_lines += self._episode_lines
                self._episode_lines = 0

        return True

    def get_best_lines(self) -> int:
        """Get the maximum lines cleared in a single episode.

        Returns:
            Best lines cleared.
        """
        return self.best_lines

    def _on_training_start(self) -> None:
        """Reset tracking at training start."""
        self.best_lines = 0
        self.total_lines = 0
        self._episode_lines = 0


class GoalReachedCallback(BaseCallback):
    """Stop training when target lines cleared is achieved.

    Works with LinesTrackingCallback to monitor progress and
    stop training early when the goal is reached (TRAIN-04).
    """

    def __init__(
        self,
        target_lines: int,
        lines_tracker: LinesTrackingCallback,
        check_freq: int = 1000,
        verbose: int = 1,
    ):
        """Initialize goal reached callback.

        Args:
            target_lines: Target lines to clear (training stops when reached).
            lines_tracker: LinesTrackingCallback instance for coordination.
            check_freq: How often to check progress (in steps).
            verbose: Verbosity level (0=silent, 1=info).
        """
        super().__init__(verbose)
        self.target_lines = target_lines
        self.lines_tracker = lines_tracker
        self.check_freq = check_freq

    def _on_step(self) -> bool:
        """Check if goal has been reached.

        Returns:
            True to continue training, False to stop.
        """
        if self.n_calls % self.check_freq != 0:
            return True

        best_lines = self.lines_tracker.get_best_lines()

        if best_lines >= self.target_lines:
            if self.verbose > 0:
                print(
                    f"Goal reached! Best lines: {best_lines} >= "
                    f"target: {self.target_lines}"
                )
            return False  # Stop training

        return True
