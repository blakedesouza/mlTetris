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
from src.training.model_slots import ModelSlotManager


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
model_manager = ModelSlotManager()

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


class SaveSlotRequest(BaseModel):
    """Request body for saving model to slot."""

    source: str = "best"  # "best", "latest", or "final"
    slot_name: str


class ExportRequest(BaseModel):
    """Request body for exporting model."""

    slot_name: str
    filename: str  # Just the filename, will be saved to exports/


# Background task for metrics polling
async def poll_metrics() -> None:
    """Background task to poll metrics queue and broadcast to WebSocket clients."""
    from queue import Empty
    import time

    message_count = 0
    last_log_time = time.time()

    while True:
        try:
            # Process all available messages (up to 50 per cycle to avoid blocking)
            processed = 0
            for _ in range(50):
                try:
                    metrics = training_manager.metrics_queue.get_nowait()
                    if connection_manager.active_connections:
                        await connection_manager.broadcast(metrics)
                        processed += 1
                        message_count += 1
                except Empty:
                    break  # No more messages
                except Exception as e:
                    print(f"Broadcast error: {e}", flush=True)

            # Log stats every 10 seconds for debugging
            now = time.time()
            if now - last_log_time > 10:
                print(f"[poll_metrics] {message_count} messages broadcast, {len(connection_manager.active_connections)} clients", flush=True)
                last_log_time = now

        except Exception as e:
            print(f"Metrics polling error: {e}", flush=True)

        await asyncio.sleep(0.05)  # 50ms poll interval


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


# Model management endpoints
@app.get("/api/models")
async def list_models():
    """List all saved model slots with metadata."""
    return model_manager.list_slots()


@app.post("/api/models/save")
async def save_model(request: SaveSlotRequest):
    """Save current model to named slot."""
    # Validate source is one of best/latest/final
    if request.source not in ("best", "latest", "final"):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Invalid source. Use: best, latest, final"},
        )
    success = model_manager.save_to_slot(request.source, request.slot_name)
    if success:
        return {"success": True, "message": f"Model saved to slot '{request.slot_name}'"}
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": f"Source '{request.source}' not found"},
    )


@app.delete("/api/models/{slot_name}")
async def delete_model(slot_name: str):
    """Delete a saved model slot."""
    success = model_manager.delete_slot(slot_name)
    if success:
        return {"success": True, "message": f"Slot '{slot_name}' deleted"}
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": f"Slot '{slot_name}' not found"},
    )


@app.post("/api/models/export")
async def export_model(request: ExportRequest):
    """Export model to standalone file for download."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    # Create exports directory
    exports_dir = Path("./exports")
    exports_dir.mkdir(exist_ok=True)
    export_path = exports_dir / request.filename

    # Run in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=1)
    success = await loop.run_in_executor(
        executor,
        model_manager.export_model,
        request.slot_name,
        str(export_path),
    )

    if success:
        return {"success": True, "path": str(export_path), "message": f"Model exported to {export_path}"}
    return JSONResponse(
        status_code=404,
        content={"success": False, "error": f"Slot '{request.slot_name}' not found"},
    )


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates and commands.

    Accepts connections, receives JSON commands, and broadcasts metrics.
    Commands:
        - {"command": "start", "config": {...}}: Start training
        - {"command": "stop"}: Stop training
        - {"command": "pause"}: Pause training
        - {"command": "resume"}: Resume training
        - {"command": "set_mode", "visual": true/false}: Toggle headless/visual mode
        - {"command": "set_speed", "speed": 0.1-1.0}: Set visualization speed
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
            # Receive with timeout to detect stale connections
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                # Send keepalive ping
                try:
                    await websocket.send_json({"type": "ping"})
                    continue
                except Exception:
                    # Connection dead
                    break
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
            elif command == "pause":
                if training_manager.pause_training():
                    await connection_manager.send_to(
                        websocket,
                        {
                            "type": "status",
                            "status": "paused",
                            "message": "Training paused",
                        },
                    )
                else:
                    await connection_manager.send_to(
                        websocket,
                        {
                            "type": "error",
                            "error": "Cannot pause - training not running",
                        },
                    )
            elif command == "resume":
                if training_manager.resume_training():
                    await connection_manager.send_to(
                        websocket,
                        {
                            "type": "status",
                            "status": "running",
                            "message": "Training resumed",
                        },
                    )
                else:
                    await connection_manager.send_to(
                        websocket,
                        {
                            "type": "error",
                            "error": "Cannot resume - training not paused",
                        },
                    )
            elif command == "set_mode":
                visual = data.get("visual", False)
                training_manager.set_mode(visual)
                await connection_manager.send_to(
                    websocket,
                    {
                        "type": "info",
                        "message": f"Mode change requested: {'visual' if visual else 'headless'}",
                    },
                )
            elif command == "set_speed":
                speed = data.get("speed", 1.0)
                # Clamp speed to valid range
                speed = max(0.1, min(1.0, float(speed)))
                training_manager.set_speed(speed)
                await connection_manager.send_to(
                    websocket,
                    {
                        "type": "info",
                        "message": f"Speed set to {speed:.1f}x",
                    },
                )
            elif command == "status":
                await connection_manager.send_to(
                    websocket,
                    {"type": "status", **training_manager.get_status()},
                )
            elif command == "pong":
                # Keepalive response - connection is alive
                pass
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
