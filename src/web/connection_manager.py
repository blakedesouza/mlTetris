"""WebSocket connection tracking and broadcasting."""

from typing import List

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for real-time updates.

    Tracks active WebSocket connections and provides methods to broadcast
    messages to all connected clients or send to specific clients.

    Attributes:
        active_connections: List of currently connected WebSocket clients.
    """

    def __init__(self):
        """Initialize connection manager with empty connection list."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and track a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection from tracking.

        Args:
            websocket: The WebSocket connection to remove.
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to all connected clients.

        Handles disconnected clients gracefully by catching exceptions
        during send and continuing to other clients.

        Args:
            message: Dictionary to send as JSON to all clients.
        """
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections[:]:  # Copy list to avoid mutation issues
            try:
                await connection.send_json(message)
            except Exception as e:
                # Client disconnected, mark for removal
                print(f"[broadcast] Client disconnected: {e}", flush=True)
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
            print(f"[broadcast] Removed client, {len(self.active_connections)} remaining", flush=True)

    async def send_to(self, websocket: WebSocket, message: dict) -> None:
        """Send a JSON message to a specific client.

        Args:
            websocket: The target WebSocket connection.
            message: Dictionary to send as JSON.
        """
        try:
            await websocket.send_json(message)
        except Exception:
            # Client disconnected, remove from tracking
            self.disconnect(websocket)
