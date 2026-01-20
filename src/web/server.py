"""FastAPI web server with WebSocket support for ML Tetris trainer."""

import asyncio
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .connection_manager import ConnectionManager
from .training_manager import TrainingManager


# FastAPI application
app = FastAPI(title="ML Tetris Trainer")

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Module-level instances
connection_manager = ConnectionManager()
training_manager = TrainingManager()

# Paths for static files and templates
WEB_DIR = Path(__file__).parent
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"

# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates: Optional[Jinja2Templates] = None
if TEMPLATES_DIR.exists():
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class TrainingConfigRequest(BaseModel):
    """Request body for starting training."""

    max_timesteps: int = 100_000
    target_lines: Optional[int] = None
    learning_rate: float = 1e-4
    checkpoint_dir: str = "./checkpoints"


# Background task for metrics polling
async def poll_metrics() -> None:
    """Background task to poll metrics queue and broadcast to WebSocket clients."""
    while True:
        try:
            # Non-blocking check for new metrics
            while not training_manager.metrics_queue.empty():
                try:
                    metrics = training_manager.metrics_queue.get_nowait()
                    await connection_manager.broadcast(metrics)
                except Exception:
                    break
        except Exception as e:
            # Log error but don't crash the polling loop
            print(f"Metrics polling error: {e}")
        await asyncio.sleep(0.1)  # 100ms poll interval


@app.on_event("startup")
async def startup_event() -> None:
    """Start background tasks on app startup."""
    asyncio.create_task(poll_metrics())


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up on app shutdown."""
    training_manager.stop_training()


# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard page."""
    if templates is None:
        return HTMLResponse(
            content="<html><body><h1>ML Tetris Trainer</h1>"
            "<p>Templates not found</p></body></html>"
        )
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/status")
async def get_status():
    """Get current training status."""
    return training_manager.get_status()


@app.post("/api/training/start")
async def start_training(config: Optional[TrainingConfigRequest] = None):
    """Start a new training session.

    Args:
        config: Optional training configuration. Uses defaults if not provided.

    Returns:
        JSON response with success status and message.
    """
    if config is None:
        config = TrainingConfigRequest()

    config_dict = config.model_dump()
    success = training_manager.start_training(config_dict)

    if success:
        return {"success": True, "message": "Training started"}
    else:
        return JSONResponse(
            status_code=409,
            content={"success": False, "message": "Training already running"},
        )


@app.post("/api/training/stop")
async def stop_training():
    """Stop the current training session.

    Returns:
        JSON response with success status and message.
    """
    training_manager.stop_training()
    return {"success": True, "message": "Training stopped"}


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates and commands.

    Accepts connections, receives JSON commands, and broadcasts metrics.
    Commands:
        - {"command": "start"}: Start training
        - {"command": "stop"}: Stop training
        - {"command": "status"}: Get current status
    """
    await connection_manager.connect(websocket)
    try:
        # Send initial status
        await connection_manager.send_to(
            websocket,
            {"type": "status", **training_manager.get_status()},
        )

        while True:
            # Receive and handle commands
            data = await websocket.receive_json()
            command = data.get("command")

            if command == "start":
                config_dict = data.get("config", {})
                success = training_manager.start_training(config_dict)
                if success:
                    await connection_manager.send_to(
                        websocket,
                        {
                            "type": "status",
                            "status": "running",
                            "message": "Training started",
                        },
                    )
                else:
                    await connection_manager.send_to(
                        websocket,
                        {
                            "type": "error",
                            "error": "Training already running",
                        },
                    )
            elif command == "stop":
                training_manager.stop_training()
                await connection_manager.send_to(
                    websocket,
                    {
                        "type": "status",
                        "status": "stopped",
                        "message": "Training stopped",
                    },
                )
            elif command == "status":
                await connection_manager.send_to(
                    websocket,
                    {"type": "status", **training_manager.get_status()},
                )
            else:
                await connection_manager.send_to(
                    websocket,
                    {
                        "type": "error",
                        "message": f"Unknown command: {command}",
                    },
                )

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
