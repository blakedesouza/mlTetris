"""Custom SB3 callbacks for Tetris training."""

from multiprocessing import Queue
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


class WebMetricsCallback(BaseCallback):
    """Callback that sends metrics and board state to web server via Queue.

    Designed for use with multiprocessing.Queue to communicate training
    progress to the web visualization server.

    Message types sent:
    - metrics: Periodic training statistics
    - board: Current board state for visualization
    - episode: Episode completion data
    - status: Training status updates (running/stopped)
    """

    def __init__(
        self,
        metrics_queue: Queue,
        command_queue: Queue,
        update_freq: int = 100,
        board_update_freq: int = 10,
        verbose: int = 0,
    ):
        """Initialize web metrics callback.

        Args:
            metrics_queue: multiprocessing.Queue for sending metrics to server.
            command_queue: multiprocessing.Queue for receiving commands from server.
            update_freq: Send metrics every N steps.
            board_update_freq: Send board state every N steps (more frequent for smooth viz).
            verbose: Verbosity level.
        """
        super().__init__(verbose)
        self.metrics_queue = metrics_queue
        self.command_queue = command_queue
        self.update_freq = update_freq
        self.board_update_freq = board_update_freq

        # Track episode stats
        self.episode_rewards: list = []
        self.episode_lines: list = []
        self.current_episode_reward: float = 0
        self.current_episode_lines: int = 0
        self.episode_count: int = 0
        self.best_lines: int = 0

    def _on_step(self) -> bool:
        """Called after each environment step.

        Returns:
            True to continue training, False to stop.
        """
        # Check for stop command (non-blocking)
        try:
            while not self.command_queue.empty():
                cmd = self.command_queue.get_nowait()
                if cmd.get("command") == "stop":
                    if self.verbose > 0:
                        print("Received stop command from web server")
                    return False
        except Exception:
            pass

        # Track reward
        rewards = self.locals.get("rewards", [0])
        self.current_episode_reward += rewards[0] if rewards else 0

        # Track lines from info
        infos = self.locals.get("infos", [{}])
        for info in infos:
            lines = info.get("lines", info.get("lines_cleared", 0))
            if lines > self.current_episode_lines:
                self.current_episode_lines = lines

        # Send board state frequently for smooth visualization
        if self.n_calls % self.board_update_freq == 0:
            self._send_board_state()

        # Send metrics periodically
        if self.n_calls % self.update_freq == 0:
            self._send_metrics()

        # Check for episode end
        dones = self.locals.get("dones", [False])
        if dones[0]:
            self._on_episode_end()

        return True

    def _send_board_state(self) -> None:
        """Extract and send current board state."""
        try:
            # Access the unwrapped environment to get board state
            env = self.training_env.envs[0]
            # Navigate through wrappers to get base Tetris env
            unwrapped = env
            while hasattr(unwrapped, "env"):
                unwrapped = unwrapped.env

            # Extract playable board area (20 rows x 10 cols)
            # tetris-gymnasium board includes padding: [0:20, 4:-4]
            if hasattr(unwrapped, "board"):
                board = unwrapped.board[0:20, 4:-4].tolist()
                self.metrics_queue.put({
                    "type": "board",
                    "board": board,
                })
        except Exception as e:
            if self.verbose > 0:
                print(f"Error sending board state: {e}")

    def _send_metrics(self) -> None:
        """Send current training metrics."""
        avg_reward = 0.0
        if self.episode_rewards:
            recent = self.episode_rewards[-100:]  # Last 100 episodes
            avg_reward = sum(recent) / len(recent)

        self.metrics_queue.put({
            "type": "metrics",
            "timesteps": self.num_timesteps,
            "episode_count": self.episode_count,
            "current_score": self.current_episode_reward,
            "lines_cleared": self.current_episode_lines,
            "avg_reward": avg_reward,
            "best_lines": self.best_lines,
        })

    def _on_episode_end(self) -> None:
        """Handle episode completion."""
        self.episode_count += 1
        self.episode_rewards.append(self.current_episode_reward)
        self.episode_lines.append(self.current_episode_lines)

        if self.current_episode_lines > self.best_lines:
            self.best_lines = self.current_episode_lines

        # Send episode completion data
        self.metrics_queue.put({
            "type": "episode",
            "episode": self.episode_count,
            "reward": self.current_episode_reward,
            "lines": self.current_episode_lines,
        })

        # Reset for next episode
        self.current_episode_reward = 0
        self.current_episode_lines = 0

    def _on_training_start(self) -> None:
        """Reset tracking at training start."""
        self.episode_rewards = []
        self.episode_lines = []
        self.current_episode_reward = 0
        self.current_episode_lines = 0
        self.episode_count = 0
        self.best_lines = 0

        # Send initial status
        self.metrics_queue.put({
            "type": "status",
            "status": "running",
        })

    def _on_training_end(self) -> None:
        """Notify when training ends."""
        self.metrics_queue.put({
            "type": "status",
            "status": "stopped",
        })
