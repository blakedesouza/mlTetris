"""Custom SB3 callbacks for Tetris training."""

import json
import time
from multiprocessing import Queue
from multiprocessing.synchronize import Event as EventType
from pathlib import Path
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
    progress to the web visualization server. Supports Event-based pause/resume,
    visual/headless mode toggle, speed control, and auto-save best model.

    Message types sent:
    - metrics: Periodic training statistics
    - board: Current board state for visualization
    - episode: Episode completion data
    - status: Training status updates (running/stopped)
    - info: Informational messages (mode changes, best model saved)
    """

    def __init__(
        self,
        metrics_queue: Queue,
        command_queue: Queue,
        pause_event: Optional[EventType] = None,
        stop_event: Optional[EventType] = None,
        checkpoint_dir: str = "./checkpoints",
        update_freq: int = 100,
        board_update_freq: int = 10,
        verbose: int = 0,
    ):
        """Initialize web metrics callback.

        Args:
            metrics_queue: multiprocessing.Queue for sending metrics to server.
            command_queue: multiprocessing.Queue for receiving commands from server.
            pause_event: Event for pause/resume (set=running, clear=paused). Optional.
            stop_event: Event for stop signal (set=stop requested). Optional.
            checkpoint_dir: Directory for saving best model checkpoints.
            update_freq: Send metrics every N steps.
            board_update_freq: Send board state every N steps (more frequent for smooth viz).
            verbose: Verbosity level.
        """
        super().__init__(verbose)
        self.metrics_queue = metrics_queue
        self.command_queue = command_queue
        self.pause_event = pause_event
        self.stop_event = stop_event
        self.checkpoint_dir = Path(checkpoint_dir)
        self.update_freq = update_freq
        self.board_update_freq = board_update_freq

        # Control state
        self.visual_mode = False  # Start in headless mode
        self.step_delay = 0.0  # Seconds between steps in visual mode

        # Track episode stats
        self.episode_rewards: list = []
        self.episode_lines: list = []
        self.current_episode_reward: float = 0
        self.current_episode_lines: int = 0
        self.episode_count: int = 0
        self.best_lines: int = 0

    def _on_step(self) -> bool:
        """Called after each environment step.

        Execution order (from 04-RESEARCH.md):
        1. Check for stop FIRST (fast path via Event)
        2. Process commands BEFORE pause check (so resume works)
        3. Block if paused (wait returns immediately if event is set)
        4. After unpausing, check stop again (might have been set while paused)
        5-9. Normal callback logic (rewards, lines, board, metrics, episode end)

        Returns:
            True to continue training, False to stop.
        """
        # 1. Check for stop FIRST (fast path via Event)
        if self.stop_event is not None and self.stop_event.is_set():
            return False

        # 2. Process commands BEFORE pause check (so resume works)
        self._process_commands()

        # 3. Block if paused (wait returns immediately if event is set)
        if self.pause_event is not None:
            self.pause_event.wait()

        # 4. After unpausing, check stop again (might have been set while paused)
        if self.stop_event is not None and self.stop_event.is_set():
            return False

        # 5. Track reward
        rewards = self.locals.get("rewards", [0])
        self.current_episode_reward += rewards[0] if rewards else 0

        # 6. Track lines from info
        infos = self.locals.get("infos", [{}])
        for info in infos:
            lines = info.get("lines", info.get("lines_cleared", 0))
            if lines > self.current_episode_lines:
                self.current_episode_lines = lines

        # 7. Send board state if in visual mode
        if self.visual_mode and self.n_calls % self.board_update_freq == 0:
            self._send_board_state()
            if self.step_delay > 0:
                time.sleep(self.step_delay)

        # 8. Send metrics periodically (regardless of mode)
        if self.n_calls % self.update_freq == 0:
            self._send_metrics()

        # 9. Check for episode end
        dones = self.locals.get("dones", [False])
        if dones[0]:
            self._on_episode_end()

        return True

    def _process_commands(self) -> None:
        """Process pending commands from web server."""
        try:
            while not self.command_queue.empty():
                cmd = self.command_queue.get_nowait()
                command = cmd.get("command")

                if command == "stop":
                    # Backward compatibility: also handle stop via command queue
                    if self.stop_event is not None:
                        self.stop_event.set()
                    if self.verbose > 0:
                        print("Received stop command from web server")
                elif command == "set_mode":
                    self.visual_mode = cmd.get("visual", False)
                    self.metrics_queue.put({
                        "type": "info",
                        "message": f"Mode: {'visual' if self.visual_mode else 'headless'}"
                    })
                elif command == "set_speed":
                    # Speed 1.0 = no delay, 0.1 = max delay (500ms between board updates)
                    speed = max(0.1, min(1.0, cmd.get("speed", 1.0)))
                    self.step_delay = (1.0 - speed) * 0.5
        except Exception:
            pass

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
            # Use project_tetromino() to include active piece if available
            if hasattr(unwrapped, "project_tetromino"):
                full_board = unwrapped.project_tetromino()
                board = [[int(cell) for cell in row] for row in full_board[0:20, 4:-4]]
                self.metrics_queue.put({
                    "type": "board",
                    "board": board,
                })
            elif hasattr(unwrapped, "board"):
                # Fallback to static board without piece
                board = [[int(cell) for cell in row] for row in unwrapped.board[0:20, 4:-4]]
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

        # Convert numpy types to native Python types for JSON serialization
        self.metrics_queue.put({
            "type": "metrics",
            "timesteps": int(self.num_timesteps),
            "episode_count": int(self.episode_count),
            "current_score": float(self.current_episode_reward),
            "lines_cleared": int(self.current_episode_lines),
            "avg_reward": float(avg_reward),
            "best_lines": int(self.best_lines),
        })

    def _on_episode_end(self) -> None:
        """Handle episode completion and auto-save best model (MODEL-07)."""
        self.episode_count += 1
        self.episode_rewards.append(self.current_episode_reward)
        self.episode_lines.append(self.current_episode_lines)

        # Check for new best and auto-save
        if self.current_episode_lines > self.best_lines:
            self.best_lines = self.current_episode_lines
            self._save_best_model()

        # Send episode completion data (convert numpy types for JSON)
        self.metrics_queue.put({
            "type": "episode",
            "episode": int(self.episode_count),
            "reward": float(self.current_episode_reward),
            "lines": int(self.current_episode_lines),
        })

        # Reset for next episode
        self.current_episode_reward = 0
        self.current_episode_lines = 0

    def _save_best_model(self) -> None:
        """Save best model checkpoint when new high score achieved."""
        try:
            best_path = self.checkpoint_dir / "best"
            best_path.mkdir(parents=True, exist_ok=True)

            # Save model
            self.model.save(best_path / "model.zip")

            # Save metadata
            metadata = {
                "best_lines": int(self.best_lines),
                "episode": int(self.episode_count),
                "timesteps": int(self.num_timesteps),
            }
            with open(best_path / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            self.metrics_queue.put({
                "type": "info",
                "message": f"New best: {self.best_lines} lines - saved to {best_path}"
            })
        except Exception as e:
            if self.verbose > 0:
                print(f"Error saving best model: {e}")

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
