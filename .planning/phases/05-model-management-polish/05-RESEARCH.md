# Phase 5: Model Management & Polish - Research

**Researched:** 2026-01-20
**Domain:** Model versioning, comparison UI, demo mode, file export
**Confidence:** HIGH

## Summary

Phase 5 completes the ML Tetris Trainer by adding model management features: multiple model slots for storing different versions, a comparison leaderboard, demo mode for watching trained models play, and model export functionality.

The codebase already has solid checkpoint infrastructure (TetrisAgent.save_checkpoint/load_checkpoint with model.zip + metadata.json). This phase builds on top of that foundation by adding a model slot system (named directories under checkpoints/), a REST API for listing/managing models, frontend leaderboard UI, and a demo mode that runs inference without training.

**Primary recommendation:** Implement named model slots as subdirectories under `checkpoints/slots/`, add REST endpoints for CRUD operations, create a sortable leaderboard table in the frontend, and implement demo mode as a separate worker process that sends board state via the existing WebSocket infrastructure.

## Standard Stack

The established libraries/tools for this phase:

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| stable-baselines3 | 2.7.x | DQN.load() for inference | Already used, proven checkpoint support |
| FastAPI | existing | REST API + WebSocket | Already used for training control |
| pathlib | stdlib | File/directory operations | Clean path handling, cross-platform |
| shutil | stdlib | File copy for export | Standard library, reliable |

### Supporting (Already in Project)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | existing | Request/response models | API data validation |
| Chart.js | 4.4.1 (CDN) | Metrics visualization | Already used for training charts |

### No New Dependencies Required

This phase uses existing project dependencies. No new packages needed.

## Architecture Patterns

### Recommended Directory Structure
```
checkpoints/
├── best/              # Auto-saved best model (existing)
├── latest/            # Current training checkpoint (existing)
├── final/             # Final training checkpoint (existing)
└── slots/             # NEW: Named model slots
    ├── model_v1/
    │   ├── model.zip
    │   └── metadata.json
    ├── model_v2/
    │   ├── model.zip
    │   └── metadata.json
    └── my_best_run/
        ├── model.zip
        └── metadata.json
```

### Pattern 1: Model Slot Manager
**What:** Centralized class for model slot CRUD operations
**When to use:** All model management operations
**Example:**
```python
# Source: Project pattern extension of existing TetrisAgent
from pathlib import Path
import json
import shutil
from typing import List, Dict, Optional

class ModelSlotManager:
    """Manages named model slots under checkpoints/slots/."""

    def __init__(self, base_dir: str = "./checkpoints"):
        self.base_dir = Path(base_dir)
        self.slots_dir = self.base_dir / "slots"
        self.slots_dir.mkdir(parents=True, exist_ok=True)

    def list_slots(self) -> List[Dict]:
        """List all model slots with metadata."""
        slots = []
        for slot_dir in self.slots_dir.iterdir():
            if slot_dir.is_dir() and (slot_dir / "model.zip").exists():
                metadata = self._load_metadata(slot_dir)
                slots.append({
                    "name": slot_dir.name,
                    "path": str(slot_dir),
                    **metadata
                })
        return slots

    def save_to_slot(self, source: str, slot_name: str) -> bool:
        """Copy model from source (best/latest) to named slot."""
        source_path = self.base_dir / source
        if not (source_path / "model.zip").exists():
            return False

        slot_path = self.slots_dir / slot_name
        if slot_path.exists():
            shutil.rmtree(slot_path)

        shutil.copytree(source_path, slot_path)
        return True

    def delete_slot(self, slot_name: str) -> bool:
        """Delete a named slot."""
        slot_path = self.slots_dir / slot_name
        if slot_path.exists():
            shutil.rmtree(slot_path)
            return True
        return False

    def export_model(self, slot_name: str, export_path: str) -> bool:
        """Export model.zip to standalone file."""
        slot_path = self.slots_dir / slot_name
        model_file = slot_path / "model.zip"
        if not model_file.exists():
            return False

        shutil.copy2(model_file, export_path)
        return True
```

### Pattern 2: Demo Mode Worker
**What:** Separate process running model inference with visual output
**When to use:** Demo mode playback
**Example:**
```python
# Source: Extension of existing training_manager.py pattern
def _demo_worker(
    model_path: str,
    metrics_queue: Queue,
    command_queue: Queue,
    stop_event: "EventType",
) -> None:
    """Worker for demo mode - inference only, no training."""
    from src.environment import make_env, EnvConfig
    from stable_baselines3 import DQN
    import time

    # Create environment with headless mode
    env_config = EnvConfig(render_mode=None)
    env = make_env(env_config)()

    # Load model directly - no TetrisAgent needed for inference
    model = DQN.load(model_path, env=env)

    metrics_queue.put({"type": "status", "status": "demo_running"})

    obs, _ = env.reset()
    episode = 0
    episode_reward = 0
    episode_lines = 0
    step_delay = 0.1  # Default demo speed

    while not stop_event.is_set():
        # Check for speed commands
        try:
            while not command_queue.empty():
                cmd = command_queue.get_nowait()
                if cmd.get("command") == "set_speed":
                    speed = cmd.get("speed", 1.0)
                    step_delay = (1.0 - speed) * 0.5
        except:
            pass

        # Predict action deterministically (no exploration)
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)

        episode_reward += reward
        lines = info.get("lines", info.get("lines_cleared", 0))
        if lines > episode_lines:
            episode_lines = lines

        # Send board state
        # (reuse existing board extraction pattern)

        if terminated or truncated:
            episode += 1
            metrics_queue.put({
                "type": "episode",
                "episode": episode,
                "reward": episode_reward,
                "lines": episode_lines,
            })
            obs, _ = env.reset()
            episode_reward = 0
            episode_lines = 0

        time.sleep(step_delay)

    metrics_queue.put({"type": "status", "status": "stopped"})
```

### Pattern 3: REST API for Model Management
**What:** FastAPI endpoints for model CRUD operations
**When to use:** Frontend model management
**Example:**
```python
# Source: Extension of existing server.py
from pydantic import BaseModel

class SaveSlotRequest(BaseModel):
    source: str = "best"  # "best", "latest", or "final"
    slot_name: str

class ExportRequest(BaseModel):
    slot_name: str
    filename: str

@app.get("/api/models")
async def list_models():
    """List all saved model slots with metadata."""
    return model_manager.list_slots()

@app.post("/api/models/save")
async def save_model(request: SaveSlotRequest):
    """Save current model to named slot."""
    success = model_manager.save_to_slot(request.source, request.slot_name)
    return {"success": success}

@app.delete("/api/models/{slot_name}")
async def delete_model(slot_name: str):
    """Delete a saved model slot."""
    success = model_manager.delete_slot(slot_name)
    return {"success": success}

@app.post("/api/demo/start/{slot_name}")
async def start_demo(slot_name: str):
    """Start demo mode with specified model."""
    success = training_manager.start_demo(slot_name)
    return {"success": success}
```

### Anti-Patterns to Avoid
- **Loading full TetrisAgent for inference:** Demo mode only needs DQN.load() - the TetrisAgent wrapper adds training infrastructure that's not needed
- **Modifying checkpoints/best directly:** Always copy to slots, never modify auto-saved models
- **Blocking WebSocket for file operations:** Use async file I/O or run in thread pool for large exports

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Model loading | Custom weight loading | DQN.load() class method | Handles optimizer state, version compatibility |
| Directory copy | Manual file-by-file | shutil.copytree() | Handles edge cases, permissions, metadata |
| File export | Raw open/write | shutil.copy2() | Preserves timestamps, handles large files |
| Table sorting | Custom sort algorithm | CSS/JS sortable library | Browser-optimized, accessible |
| Path handling | String concatenation | pathlib.Path | Cross-platform, clean API |

**Key insight:** Model operations in SB3 have edge cases around optimizer state, version compatibility, and device placement. Use the provided class methods.

## Common Pitfalls

### Pitfall 1: Loading Model Without Environment
**What goes wrong:** DQN.load() without env parameter fails or produces wrong predictions
**Why it happens:** Model needs environment to validate observation/action spaces
**How to avoid:** Always pass env parameter when loading for inference
**Warning signs:** Shape mismatch errors, silent wrong predictions

### Pitfall 2: Training During Demo Mode
**What goes wrong:** Demo changes model weights, corrupting saved state
**Why it happens:** Forgetting to set deterministic=True or calling learn()
**How to avoid:** Demo worker never calls model.learn(), always uses deterministic=True
**Warning signs:** Model performance changes during demo playback

### Pitfall 3: Concurrent Checkpoint Access
**What goes wrong:** Corrupted checkpoint files
**Why it happens:** Training saves while export/copy in progress
**How to avoid:** Stop training before model operations, or copy to temp first
**Warning signs:** Truncated files, JSON parse errors

### Pitfall 4: Large File Blocking UI
**What goes wrong:** UI freezes during model export
**Why it happens:** Synchronous file copy in async handler
**How to avoid:** Use run_in_executor for large file operations
**Warning signs:** UI unresponsive during export, timeout errors

### Pitfall 5: Slot Name Collisions
**What goes wrong:** Overwriting existing models without warning
**Why it happens:** No validation before save
**How to avoid:** Check existence, require confirmation or auto-suffix
**Warning signs:** User loses saved model unexpectedly

## Code Examples

Verified patterns from official sources:

### DQN Inference-Only Loading
```python
# Source: https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html
from stable_baselines3 import DQN

# Load model for inference (no training)
model = DQN.load("path/to/model.zip", env=env)

# Set to evaluation mode (affects dropout, batch norm if present)
model.set_training_mode(False)

# Run inference with deterministic actions
obs, _ = env.reset()
while True:
    action, _states = model.predict(obs, deterministic=True)
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, _ = env.reset()
```

### Model Export to Standalone File
```python
# Source: https://stable-baselines3.readthedocs.io/en/master/guide/save_format.html
# For sharing/deployment, the model.zip is self-contained
import shutil
from pathlib import Path

def export_model(source_path: Path, export_path: Path) -> None:
    """Export model.zip to standalone file for sharing."""
    model_file = source_path / "model.zip"
    if not model_file.exists():
        raise FileNotFoundError(f"Model not found: {model_file}")

    # Use copy2 to preserve timestamps
    shutil.copy2(model_file, export_path)
```

### Async File Operations in FastAPI
```python
# Source: FastAPI async patterns
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=2)

@app.post("/api/models/export")
async def export_model(request: ExportRequest):
    """Export model without blocking event loop."""
    loop = asyncio.get_event_loop()

    # Run blocking I/O in thread pool
    success = await loop.run_in_executor(
        executor,
        model_manager.export_model,
        request.slot_name,
        request.filename
    )
    return {"success": success}
```

### Sortable Leaderboard Table
```html
<!-- Source: https://github.com/tofsjonas/sortable -->
<table class="sortable">
    <thead>
        <tr>
            <th>Model Name</th>
            <th>Best Lines</th>
            <th>Episodes</th>
            <th>Timesteps</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody id="model-list">
        <!-- Populated by JavaScript -->
    </tbody>
</table>

<script>
// Simple sorting without external library
function sortTable(table, column, asc = true) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        const aVal = a.cells[column].textContent;
        const bVal = b.cells[column].textContent;
        const numA = parseFloat(aVal) || 0;
        const numB = parseFloat(bVal) || 0;
        return asc ? numA - numB : numB - numA;
    });

    rows.forEach(row => tbody.appendChild(row));
}
</script>
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Save/load weights only | Full checkpoint (model + optimizer + buffer) | SB3 1.0+ | Enables proper training resume |
| String paths | pathlib.Path | Python 3.4+ | Cross-platform compatibility |
| model.save() only | DQN.load() class method | SB3 2.0+ | Proper optimizer restoration |

**Deprecated/outdated:**
- `model = DQN(...); model.load(path)` - Use `model = DQN.load(path, env=env)` instead
- Manual weight extraction for export - Use model.zip directly, it's self-contained

## Open Questions

Things that couldn't be fully resolved:

1. **Replay buffer in slots?**
   - What we know: Full checkpoint includes replay_buffer.pkl (~400MB)
   - What's unclear: Should slots include replay buffer for training resume, or just model.zip for demo?
   - Recommendation: Model-only for slots (model.zip + metadata.json), full checkpoint only for latest/best

2. **Concurrent demo and training?**
   - What we know: Both use multiprocessing.Process
   - What's unclear: Can both run simultaneously on same machine?
   - Recommendation: Probably not worth supporting - one activity at a time simplifies UX

## Sources

### Primary (HIGH confidence)
- [SB3 Save Format Documentation](https://stable-baselines3.readthedocs.io/en/master/guide/save_format.html) - Model structure, versioning
- [SB3 DQN Documentation](https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html) - load(), predict(), set_training_mode()
- [SB3 Export Guide](https://stable-baselines3.readthedocs.io/en/master/guide/export.html) - Standalone export patterns
- [Python shutil Documentation](https://docs.python.org/3/library/shutil.html) - File operations

### Secondary (MEDIUM confidence)
- [FastAPI WebSocket Patterns](https://medium.com/@connect.hashblock/10-fastapi-websocket-patterns-for-live-dashboards-3e36f3080510) - Real-time update architecture
- [sortable.js GitHub](https://github.com/tofsjonas/sortable) - Table sorting library

### Tertiary (LOW confidence)
- WebSearch for leaderboard UI patterns - General guidance, not framework-specific

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Uses existing project dependencies, well-documented
- Architecture: HIGH - Extends proven patterns from earlier phases
- Pitfalls: MEDIUM - Based on SB3 docs and general ML experience

**Research date:** 2026-01-20
**Valid until:** 60 days (stable APIs, no fast-moving dependencies)
