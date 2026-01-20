"""Process-based training management with Queue communication."""

import traceback
from multiprocessing import Process, Queue, Event
from multiprocessing.synchronize import Event as EventType
from pathlib import Path
from typing import Optional, Dict, Any


class TrainingManager:
    """Manages training in a separate process for isolation.

    Runs SB3 training in a separate Process to avoid blocking the async
    event loop. Uses Queues for communication: metrics flow from training
    to server, commands flow from server to training. Uses Events for
    pause/resume and stop synchronization.

    Attributes:
        metrics_queue: Queue for training to send metrics to server.
        command_queue: Queue for server to send commands to training.
        pause_event: Event for pause/resume (set=running, clear=paused).
        stop_event: Event for stop signal (set=stop requested).
        process: Handle to the training subprocess.
        status: Current status ("stopped", "running", "paused", "stopping").
    """

    def __init__(self):
        """Initialize training manager with queues, events, and stopped status."""
        self.metrics_queue: Queue = Queue()
        self.command_queue: Queue = Queue()
        self.pause_event: EventType = Event()
        self.stop_event: EventType = Event()
        self.process: Optional[Process] = None
        self.demo_process: Optional[Process] = None
        self.status: str = "stopped"

        # Control state (tracked for UI sync on reconnect)
        self.visual_mode: bool = False
        self.speed: float = 1.0

        # Initialize events to correct state
        self.pause_event.set()  # Not paused (set = unblocked)
        self.stop_event.clear()  # Not stopped

    def start_training(self, config_dict: Dict[str, Any]) -> bool:
        """Start training in a subprocess.

        Args:
            config_dict: Training configuration dictionary.
                Keys: target_lines, max_timesteps, checkpoint_dir, checkpoint_freq

        Returns:
            True if training started, False if already running.
        """
        if self.is_running():
            return False

        # Clear queues before starting new training
        self._clear_queue(self.metrics_queue)
        self._clear_queue(self.command_queue)

        # Reset events and control state for new session
        self.pause_event.set()  # Not paused
        self.stop_event.clear()  # Not stopped
        self.visual_mode = False
        self.speed = 1.0

        self.process = Process(
            target=self._training_worker,
            args=(
                config_dict,
                self.metrics_queue,
                self.command_queue,
                self.pause_event,
                self.stop_event,
            ),
            daemon=True,  # Terminate with parent
        )
        self.process.start()
        self.status = "running"
        return True

    def stop_training(self) -> None:
        """Stop the training process (or demo if running).

        Sets stop event, unblocks pause if paused, waits with timeout,
        and terminates if needed.
        """
        # Also stop demo if running
        if self.is_demo_running():
            self.stop_demo()
            return

        if not self.is_running():
            self.status = "stopped"
            return

        self.status = "stopping"
        self.stop_event.set()  # Signal stop via Event (fast path)
        self.pause_event.set()  # Unblock if paused so worker can exit
        self.command_queue.put({"command": "stop"})  # Backward compatibility
        self.process.join(timeout=5)

        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=2)

        self.status = "stopped"

    def pause_training(self) -> bool:
        """Pause the training process.

        Clears pause_event to block the callback's wait() call.

        Returns:
            True if successfully paused, False if not running or already paused.
        """
        if not self.is_running() or self.status == "paused":
            return False
        self.pause_event.clear()  # Block wait()
        self.status = "paused"
        return True

    def resume_training(self) -> bool:
        """Resume a paused training process.

        Sets pause_event to unblock the callback's wait() call.

        Returns:
            True if successfully resumed, False if not paused.
        """
        if self.status != "paused":
            return False
        self.pause_event.set()  # Unblock wait()
        self.status = "running"
        return True

    def set_mode(self, visual: bool) -> None:
        """Toggle visual/headless mode.

        Sends command to callback to control board update frequency.

        Args:
            visual: True for visual mode (send board updates), False for headless.
        """
        self.visual_mode = visual
        self.command_queue.put({"command": "set_mode", "visual": visual})

    def set_speed(self, speed: float) -> None:
        """Set visualization speed.

        Sends command to callback to control step delay in visual mode.

        Args:
            speed: Speed factor from 0.1 (slowest) to 1.0 (fastest).
        """
        self.speed = speed
        self.command_queue.put({"command": "set_speed", "speed": speed})

    def is_running(self) -> bool:
        """Check if training process is alive.

        Returns:
            True if process is running, False otherwise.
        """
        return self.process is not None and self.process.is_alive()

    def get_status(self) -> Dict[str, Any]:
        """Get current training/demo status.

        Returns:
            Dictionary with status, process info, and control state.
        """
        return {
            "status": self.status,
            "is_running": self.is_running(),
            "is_demo": self.is_demo_running(),
            "visual_mode": self.visual_mode,
            "speed": self.speed,
        }

    def start_demo(self, model_path: str) -> bool:
        """Start demo mode with specified model.

        Args:
            model_path: Path to model.zip file to load.

        Returns:
            True if demo started, False if demo already running.
        """
        # Stop training first if running (auto-transition to demo)
        if self.is_running():
            self.stop_training()
        # Prevent if demo already running
        if self.is_demo_running():
            return False

        # Clear queues before starting
        self._clear_queue(self.metrics_queue)
        self._clear_queue(self.command_queue)

        # Reset stop event
        self.stop_event.clear()

        # Start demo process
        self.demo_process = Process(
            target=self._demo_worker,
            args=(
                model_path,
                self.metrics_queue,
                self.command_queue,
                self.stop_event,
            ),
            daemon=True,
        )
        self.demo_process.start()
        self.status = "demo_running"
        self.visual_mode = True  # Demo is always visual
        return True

    def stop_demo(self) -> None:
        """Stop the demo process."""
        if not self.is_demo_running():
            return

        self.status = "stopping"
        self.stop_event.set()
        self.demo_process.join(timeout=3)

        if self.demo_process.is_alive():
            self.demo_process.terminate()
            self.demo_process.join(timeout=1)

        self.demo_process = None
        self.status = "stopped"

    def is_demo_running(self) -> bool:
        """Check if demo process is alive.

        Returns:
            True if demo process is running, False otherwise.
        """
        return self.demo_process is not None and self.demo_process.is_alive()

    @staticmethod
    def _clear_queue(queue: Queue) -> None:
        """Clear all items from a queue.

        Args:
            queue: Queue to clear.
        """
        try:
            while not queue.empty():
                queue.get_nowait()
        except Exception:
            pass

    @staticmethod
    def _training_worker(
        config_dict: Dict[str, Any],
        metrics_queue: Queue,
        command_queue: Queue,
        pause_event: "EventType",
        stop_event: "EventType",
    ) -> None:
        """Worker function that runs in separate process.

        Creates environment, agent, and callbacks, then runs training loop.
        Communicates with server via queues, uses Events for pause/stop sync.

        Args:
            config_dict: Training configuration dictionary.
            metrics_queue: Queue to send metrics to server.
            command_queue: Queue to receive commands from server.
            pause_event: Event for pause/resume (set=running, clear=paused).
            stop_event: Event for stop signal (set=stop requested).
        """
        # Import inside worker to avoid pickle issues with multiprocessing
        try:
            from src.environment import make_env, EnvConfig
            from src.training.agent import TetrisAgent
            from src.training.config import TrainingConfig
            from src.training.callbacks import WebMetricsCallback, LinesTrackingCallback
            from stable_baselines3.common.callbacks import CallbackList

            # Create config from dict
            training_config = TrainingConfig(
                target_lines=config_dict.get("target_lines"),
                max_timesteps=config_dict.get("max_timesteps", 100000),
                checkpoint_dir=config_dict.get("checkpoint_dir", "./checkpoints"),
                checkpoint_freq=config_dict.get("checkpoint_freq", 10000),
            )

            # Create environment (headless for training, but we extract board state)
            env_config = EnvConfig(render_mode=None)
            env = make_env(env_config)()

            # Create or load agent
            checkpoint_path = Path(training_config.checkpoint_dir)
            checkpoint_path.mkdir(parents=True, exist_ok=True)
            latest_checkpoint = checkpoint_path / "latest"

            if latest_checkpoint.exists():
                agent = TetrisAgent.load_checkpoint(latest_checkpoint, env)
                metrics_queue.put({
                    "type": "info",
                    "message": f"Resumed from checkpoint ({agent.timesteps_trained} steps)",
                })
            else:
                agent = TetrisAgent(env, training_config)

            # Set up callbacks
            web_callback = WebMetricsCallback(
                metrics_queue=metrics_queue,
                command_queue=command_queue,
                pause_event=pause_event,
                stop_event=stop_event,
                checkpoint_dir=str(checkpoint_path),
                update_freq=100,
                board_update_freq=50,  # Reduced from 10 to prevent overwhelming WebSocket
                verbose=1,
            )

            lines_tracker = LinesTrackingCallback(verbose=0)

            callback_list = CallbackList([web_callback, lines_tracker])

            # Calculate remaining timesteps
            remaining = training_config.max_timesteps - agent.timesteps_trained
            if remaining <= 0:
                metrics_queue.put({
                    "type": "status",
                    "status": "stopped",
                    "message": "Training already complete",
                })
                return

            # Send training started status
            metrics_queue.put({
                "type": "status",
                "status": "running",
            })

            # Train
            agent.train(remaining, callback=callback_list)

            # Save checkpoint
            agent.save_checkpoint(checkpoint_path / "latest")
            agent.save_checkpoint(checkpoint_path / "final")

            metrics_queue.put({
                "type": "status",
                "status": "stopped",
                "message": f"Training complete ({agent.timesteps_trained} total steps)",
            })

        except Exception as e:
            # Send error to server
            metrics_queue.put({
                "type": "error",
                "error": str(e),
                "traceback": traceback.format_exc(),
            })
            metrics_queue.put({
                "type": "status",
                "status": "stopped",
            })

    @staticmethod
    def _demo_worker(
        model_path: str,
        metrics_queue: Queue,
        command_queue: Queue,
        stop_event: "EventType",
    ) -> None:
        """Worker function for demo mode - inference only, no training.

        Runs the model in evaluation mode, sending board state for visualization.
        Handles speed commands but not pause (demo is always visual).

        Args:
            model_path: Path to model.zip file to load.
            metrics_queue: Queue to send metrics/board to server.
            command_queue: Queue to receive commands from server.
            stop_event: Event for stop signal.
        """
        import time

        try:
            from src.environment import make_env, EnvConfig
            from stable_baselines3 import DQN

            # Create environment (headless - we extract board state manually)
            env_config = EnvConfig(render_mode=None)
            env = make_env(env_config)()

            # Load model for inference (no TetrisAgent needed)
            # deterministic=True is passed to predict() below, no need for training mode toggle
            model = DQN.load(model_path, env=env)

            metrics_queue.put({"type": "status", "status": "demo_running"})

            obs, _ = env.reset()
            episode = 0
            episode_reward = 0.0
            episode_lines = 0
            step_delay = 0.1  # Default demo speed (fairly slow for watching)
            steps_in_episode = 0

            while not stop_event.is_set():
                # Check for speed commands
                try:
                    while not command_queue.empty():
                        cmd = command_queue.get_nowait()
                        if cmd.get("command") == "set_speed":
                            speed = cmd.get("speed", 1.0)
                            # Convert speed (0.1-1.0) to delay (0.5s - 0s)
                            step_delay = (1.0 - speed) * 0.5
                except Exception:
                    pass

                # Predict action deterministically (no exploration)
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(action)

                episode_reward += float(reward)
                steps_in_episode += 1

                # Track lines cleared (convert to int for JSON)
                lines = int(info.get("lines", info.get("lines_cleared", 0)))
                if lines > episode_lines:
                    episode_lines = lines

                # Extract and send board state
                # Navigate through wrappers to get board with active piece
                try:
                    unwrapped = env.unwrapped
                    if hasattr(unwrapped, 'project_tetromino'):
                        # project_tetromino() returns board with active piece rendered
                        full_board = unwrapped.project_tetromino()
                        # Extract playable area (20 rows, 10 cols)
                        # Convert to Python ints for JSON serialization
                        board = [[int(cell) for cell in row] for row in full_board[0:20, 4:-4]]
                        metrics_queue.put({
                            "type": "board",
                            "board": board,
                        })
                    elif hasattr(unwrapped, 'board'):
                        # Fallback to static board without piece
                        board = [[int(cell) for cell in row] for row in unwrapped.board[0:20, 4:-4]]
                        metrics_queue.put({
                            "type": "board",
                            "board": board,
                        })
                except Exception:
                    pass  # Skip board update on error

                # Send periodic demo metrics (separate from training)
                if steps_in_episode % 10 == 0:
                    metrics_queue.put({
                        "type": "demo_metrics",
                        "episode": int(episode),
                        "score": float(episode_reward),
                        "lines": int(episode_lines),
                        "steps": int(steps_in_episode),
                    })

                if terminated or truncated:
                    episode += 1
                    metrics_queue.put({
                        "type": "demo_episode",
                        "episode": int(episode),
                        "reward": float(episode_reward),
                        "lines": int(episode_lines),
                    })
                    # Reset for next episode
                    obs, _ = env.reset()
                    episode_reward = 0.0
                    episode_lines = 0
                    steps_in_episode = 0

                # Delay for visualization
                if step_delay > 0:
                    time.sleep(step_delay)

            metrics_queue.put({"type": "status", "status": "stopped"})

        except Exception as e:
            import traceback as tb
            metrics_queue.put({
                "type": "error",
                "error": str(e),
                "traceback": tb.format_exc(),
            })
            metrics_queue.put({"type": "status", "status": "stopped"})
