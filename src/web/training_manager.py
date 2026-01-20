"""Process-based training management with Queue communication."""

from multiprocessing import Process, Queue
from typing import Optional, Dict, Any


class TrainingManager:
    """Manages training in a separate process for isolation.

    Runs SB3 training in a separate Process to avoid blocking the async
    event loop. Uses Queues for communication: metrics flow from training
    to server, commands flow from server to training.

    Attributes:
        metrics_queue: Queue for training to send metrics to server.
        command_queue: Queue for server to send commands to training.
        process: Handle to the training subprocess.
        status: Current status ("stopped", "running", "stopping").
    """

    def __init__(self):
        """Initialize training manager with queues and stopped status."""
        self.metrics_queue: Queue = Queue()
        self.command_queue: Queue = Queue()
        self.process: Optional[Process] = None
        self.status: str = "stopped"

    def start_training(self, config_dict: Dict[str, Any]) -> bool:
        """Start training in a subprocess.

        Args:
            config_dict: Training configuration dictionary.

        Returns:
            True if training started, False if already running.
        """
        if self.process is not None and self.process.is_alive():
            return False

        # Clear queues before starting new training
        self._clear_queue(self.metrics_queue)
        self._clear_queue(self.command_queue)

        self.process = Process(
            target=self._training_worker,
            args=(config_dict, self.metrics_queue, self.command_queue),
        )
        self.process.start()
        self.status = "running"
        return True

    def stop_training(self) -> None:
        """Stop the training process.

        Sends stop command, waits with timeout, and terminates if needed.
        """
        if self.process is None or not self.process.is_alive():
            self.status = "stopped"
            return

        self.status = "stopping"
        self.command_queue.put({"command": "stop"})
        self.process.join(timeout=5)

        if self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=2)

        self.status = "stopped"

    def is_running(self) -> bool:
        """Check if training process is alive.

        Returns:
            True if process is running, False otherwise.
        """
        return self.process is not None and self.process.is_alive()

    def get_status(self) -> Dict[str, Any]:
        """Get current training status.

        Returns:
            Dictionary with status and process info.
        """
        return {
            "status": self.status,
            "is_running": self.is_running(),
        }

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
    ) -> None:
        """Worker function that runs in separate process.

        This is a stub - the actual training loop is implemented in Plan 03.
        The function signature is what matters for now.

        Args:
            config_dict: Training configuration dictionary.
            metrics_queue: Queue to send metrics to server.
            command_queue: Queue to receive commands from server.
        """
        # Import training modules inside function to avoid pickle issues
        # Actual implementation will be added in Plan 03
        pass
