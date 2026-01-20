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
        """Stop the training process.

        Sets stop event, unblocks pause if paused, waits with timeout,
        and terminates if needed.
        """
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
        """Get current training status.

        Returns:
            Dictionary with status, process info, and control state.
        """
        return {
            "status": self.status,
            "is_running": self.is_running(),
            "visual_mode": self.visual_mode,
            "speed": self.speed,
        }

    def start_demo(self, model_path: str) -> bool:
        """Start demo mode with specified model.

        Args:
            model_path: Path to model.zip file to use for demo.

        Returns:
            True if demo started, False if training/demo already running.
        """
        if self.is_running():
            return False

        # TODO: Full demo implementation in Plan 05-02
        # For now, just check if we can start
        self.status = "demo_running"
        return True

    def stop_demo(self) -> None:
        """Stop demo mode.

        Stops the demo process if running.
        """
        # TODO: Full demo implementation in Plan 05-02
        if self.status == "demo_running":
            self.status = "stopped"

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
