# Phase 4: Training Controls - Research

**Researched:** 2026-01-20
**Domain:** RL training control, process synchronization, real-time UI interaction
**Confidence:** HIGH

## Summary

This phase adds fine-grained training controls to the existing web dashboard: pause/resume, headless/visual mode toggle, speed control, and auto-save best model. The implementation builds on Phase 3's process-isolated architecture with Queue-based communication.

The key insight is that Gymnasium environments cannot change `render_mode` after creation, so headless/visual toggle requires a different approach. Instead of switching environment render modes, we control **whether board updates are sent to the frontend**. Training always runs headless for performance; "visual mode" means the callback sends board state updates at a configurable rate. This avoids environment recreation and state loss.

For pause/resume, we use `multiprocessing.Event` objects passed to the training worker. The callback checks these events on each step, calling `pause_event.wait()` to block when paused. This preserves exact training state (optimizer, replay buffer, epsilon) without checkpointing overhead.

**Primary recommendation:** Use Event-based pause/resume in the callback, control visualization by toggling board update frequency (not environment render_mode), track best score in callback and trigger checkpoint save on improvement.

## Standard Stack

The established libraries/tools for this domain:

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| multiprocessing.Event | Python stdlib | Pause/resume synchronization | Process-safe flag with blocking wait |
| multiprocessing.Queue | Python stdlib | Command communication | Already in use for metrics/commands |
| stable-baselines3 | 2.7.1 | DQN training | Already in use, has callback infrastructure |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| time | Python stdlib | Step delay for speed control | time.sleep() between steps in visual mode |

### No New Dependencies Required
All functionality can be implemented with Python stdlib and existing project dependencies.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Event-based pause | Checkpoint/reload pause | Event is instant, checkpoint has I/O overhead and potential state drift |
| Speed via sleep | Speed via train_freq | train_freq changes learning dynamics, sleep only affects visualization |
| Board update toggle | Environment swap with set_env | Update toggle preserves state, swap requires matching env and forces reset |

## Architecture Patterns

### Recommended Additions to Existing Structure
```
src/
├── web/
│   ├── training_manager.py  # Add Event objects for pause/resume/visual
│   └── server.py            # Add WebSocket commands: pause, resume, set_mode, set_speed
├── training/
│   └── callbacks.py         # Enhance WebMetricsCallback with pause/speed/best-save logic
```

### Pattern 1: Event-Based Pause/Resume
**What:** Use multiprocessing.Event to block training loop when paused
**When to use:** For instant pause/resume without losing training state
**Example:**
```python
# Source: Python multiprocessing docs
from multiprocessing import Event

class TrainingManager:
    def __init__(self):
        self.metrics_queue = Queue()
        self.command_queue = Queue()
        self.pause_event = Event()
        self.stop_event = Event()
        self.pause_event.set()  # Start unpaused (event set = not paused)

    def start_training(self, config: dict):
        self.pause_event.set()  # Ensure unpaused
        self.stop_event.clear()  # Ensure not stopped
        self.process = Process(
            target=self._training_worker,
            args=(config, self.metrics_queue, self.command_queue,
                  self.pause_event, self.stop_event)
        )
        self.process.start()

    def pause_training(self):
        self.pause_event.clear()  # Clear = paused, wait() will block
        self.status = "paused"

    def resume_training(self):
        self.pause_event.set()  # Set = unpaused, wait() returns immediately
        self.status = "running"
```

### Pattern 2: Pause Check in Callback
**What:** Callback checks pause_event on each step, blocks if paused
**When to use:** For pause/resume that preserves exact training state
**Example:**
```python
# Source: SB3 callback pattern + multiprocessing Event
from multiprocessing import Event

class WebMetricsCallback(BaseCallback):
    def __init__(self, pause_event: Event, stop_event: Event, ...):
        super().__init__()
        self.pause_event = pause_event
        self.stop_event = stop_event

    def _on_step(self) -> bool:
        # Check for stop
        if self.stop_event.is_set():
            return False  # Stop training

        # Block if paused (wait returns immediately if event is set)
        self.pause_event.wait()

        # Continue with normal callback logic...
        return True
```

### Pattern 3: Visual Mode via Board Update Frequency
**What:** Toggle board updates without changing environment render_mode
**When to use:** For headless/visual toggle without environment recreation
**Example:**
```python
# Visual mode = send board updates frequently
# Headless mode = skip board updates entirely

class WebMetricsCallback(BaseCallback):
    def __init__(self, ...):
        self.visual_mode = False  # Start in headless mode
        self.board_update_freq = 50  # Send every N steps when visual
        self.step_delay = 0.0  # Delay between steps (for speed control)

    def _on_step(self) -> bool:
        # Check command queue for mode/speed changes
        self._process_commands()

        # Only send board updates in visual mode
        if self.visual_mode and self.n_calls % self.board_update_freq == 0:
            self._send_board_state()
            if self.step_delay > 0:
                time.sleep(self.step_delay)

        return True

    def _process_commands(self):
        try:
            while not self.command_queue.empty():
                cmd = self.command_queue.get_nowait()
                if cmd.get("command") == "set_mode":
                    self.visual_mode = cmd.get("visual", False)
                elif cmd.get("command") == "set_speed":
                    # Speed 1.0 = normal, 0.5 = half speed (more delay)
                    speed = cmd.get("speed", 1.0)
                    self.step_delay = max(0, (1.0 - speed) * 0.1)
        except:
            pass
```

### Pattern 4: Auto-Save Best Model
**What:** Track best score in callback, save checkpoint when improved
**When to use:** For MODEL-07 - auto-save best model
**Example:**
```python
class WebMetricsCallback(BaseCallback):
    def __init__(self, checkpoint_dir: str, ...):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.best_score = float('-inf')
        self.best_lines = 0

    def _on_episode_end(self):
        episode_score = self.current_episode_lines  # Or reward, configurable

        if episode_score > self.best_score:
            self.best_score = episode_score
            # Save best model checkpoint
            self._save_best_model()
            self.metrics_queue.put({
                "type": "info",
                "message": f"New best score: {episode_score} - model saved"
            })

    def _save_best_model(self):
        # Access model through callback's model reference
        best_path = self.checkpoint_dir / "best"
        best_path.mkdir(parents=True, exist_ok=True)
        self.model.save(best_path / "model.zip")
        # Note: For full checkpoint, also save replay buffer and metadata
```

### Anti-Patterns to Avoid
- **Environment swap for visual toggle:** Don't use `model.set_env()` to switch between headless/visual environments - causes reset and potential state loss
- **Checkpoint for pause:** Don't save/reload checkpoint for pause/resume - unnecessary I/O, Event is instant
- **Changing train_freq for speed:** Don't modify DQN's train_freq to control speed - affects learning dynamics
- **Recreating environment:** Don't create new environment for mode toggle - Gymnasium render_mode is immutable after creation

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Process-safe pause flag | Lock + boolean | multiprocessing.Event | Atomic, has blocking wait() |
| Inter-process commands | Custom socket/pipe | multiprocessing.Queue | Already in use, thread-safe |
| Best model tracking | File comparison | Callback state variable | No I/O, instant comparison |
| Training state preservation | Manual pickle | Event blocking | Pause preserves everything automatically |

**Key insight:** The existing callback infrastructure handles pause/resume elegantly. The callback's `_on_step()` is the perfect injection point for pause checks, mode toggling, and speed control. No need to modify SB3 internals.

## Common Pitfalls

### Pitfall 1: Environment Render Mode is Immutable
**What goes wrong:** Attempting to change `env.render_mode` after creation fails silently or crashes
**Why it happens:** Gymnasium fixed render_mode at creation for reproducibility (post-v0.26 change)
**How to avoid:** Toggle visualization by controlling board update frequency, not render_mode
**Warning signs:** No visual change after toggle, AttributeError on render_mode assignment

### Pitfall 2: Blocking Main Process with Event.wait()
**What goes wrong:** Calling `pause_event.wait()` in the wrong place blocks web server
**Why it happens:** Event.wait() blocks the calling thread/process
**How to avoid:** Only call wait() inside the training worker process (in callback)
**Warning signs:** Web UI freezes when pause is clicked, WebSocket disconnects

### Pitfall 3: Lost Commands During Pause
**What goes wrong:** Commands sent while paused are never processed
**Why it happens:** Callback only processes commands in `_on_step()`, which doesn't run while paused
**How to avoid:** Process commands BEFORE calling `pause_event.wait()`
**Warning signs:** Resume command doesn't work, have to restart training

### Pitfall 4: Race Condition on Best Score
**What goes wrong:** Multiple "best model" saves for same score, or missed saves
**Why it happens:** Async metrics and save operations interleave
**How to avoid:** All best-score logic in single callback method, atomic comparison and save
**Warning signs:** Multiple "best" checkpoints with same score, or score regression after restart

### Pitfall 5: Speed Control Affects Training Speed
**What goes wrong:** Changing speed slider slows down actual training (not just visualization)
**Why it happens:** sleep() in callback delays ALL training, not just visual updates
**How to avoid:** Only apply delay when in visual mode AND sending board update
**Warning signs:** Training timesteps/sec drops dramatically in visual mode

### Pitfall 6: Event State on Training Restart
**What goes wrong:** New training session starts paused or immediately stops
**Why it happens:** Events retain state from previous session
**How to avoid:** Reset Event states (pause_event.set(), stop_event.clear()) before starting
**Warning signs:** Training starts but immediately pauses, or doesn't respond to controls

## Code Examples

Verified patterns from official sources:

### Enhanced WebMetricsCallback with All Controls
```python
# Source: SB3 callback docs + multiprocessing.Event docs
from multiprocessing import Event, Queue
from pathlib import Path
import time
from stable_baselines3.common.callbacks import BaseCallback

class WebMetricsCallback(BaseCallback):
    """Callback with pause/resume, visual mode, speed control, and auto-save."""

    def __init__(
        self,
        metrics_queue: Queue,
        command_queue: Queue,
        pause_event: Event,
        stop_event: Event,
        checkpoint_dir: str = "./checkpoints",
        update_freq: int = 100,
        board_update_freq: int = 50,
        verbose: int = 0,
    ):
        super().__init__(verbose)
        self.metrics_queue = metrics_queue
        self.command_queue = command_queue
        self.pause_event = pause_event
        self.stop_event = stop_event
        self.checkpoint_dir = Path(checkpoint_dir)
        self.update_freq = update_freq
        self.board_update_freq = board_update_freq

        # Control state
        self.visual_mode = False
        self.step_delay = 0.0  # Seconds between steps in visual mode

        # Tracking state
        self.best_lines = 0
        self.current_episode_lines = 0
        self.episode_count = 0

    def _on_step(self) -> bool:
        # 1. Check for stop FIRST
        if self.stop_event.is_set():
            return False

        # 2. Process commands BEFORE pause check (so resume works)
        self._process_commands()

        # 3. Block if paused
        self.pause_event.wait()

        # 4. Normal callback logic
        self._track_episode_progress()

        # 5. Send metrics periodically
        if self.n_calls % self.update_freq == 0:
            self._send_metrics()

        # 6. Send board state if in visual mode
        if self.visual_mode and self.n_calls % self.board_update_freq == 0:
            self._send_board_state()
            if self.step_delay > 0:
                time.sleep(self.step_delay)

        return True

    def _process_commands(self):
        """Process pending commands from web server."""
        try:
            while not self.command_queue.empty():
                cmd = self.command_queue.get_nowait()
                command = cmd.get("command")

                if command == "stop":
                    self.stop_event.set()
                elif command == "set_mode":
                    self.visual_mode = cmd.get("visual", False)
                    self.metrics_queue.put({
                        "type": "info",
                        "message": f"Mode: {'visual' if self.visual_mode else 'headless'}"
                    })
                elif command == "set_speed":
                    # Speed 1.0 = no delay, 0.1 = max delay
                    speed = max(0.1, min(1.0, cmd.get("speed", 1.0)))
                    self.step_delay = (1.0 - speed) * 0.1  # 0-100ms delay
        except Exception:
            pass

    def _on_episode_end(self):
        """Handle episode completion, check for new best."""
        self.episode_count += 1

        # Check for new best
        if self.current_episode_lines > self.best_lines:
            self.best_lines = self.current_episode_lines
            self._save_best_model()

        self.current_episode_lines = 0

    def _save_best_model(self):
        """Save best model checkpoint."""
        best_path = self.checkpoint_dir / "best"
        best_path.mkdir(parents=True, exist_ok=True)

        # Save model
        self.model.save(best_path / "model.zip")

        # Save metadata
        import json
        metadata = {
            "best_lines": self.best_lines,
            "episode": self.episode_count,
            "timesteps": self.num_timesteps,
        }
        with open(best_path / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        self.metrics_queue.put({
            "type": "info",
            "message": f"New best: {self.best_lines} lines - saved to {best_path}"
        })
```

### TrainingManager with Event Objects
```python
# Source: Python multiprocessing docs
from multiprocessing import Process, Queue, Event

class TrainingManager:
    def __init__(self):
        self.metrics_queue = Queue()
        self.command_queue = Queue()
        self.pause_event = Event()
        self.stop_event = Event()
        self.process = None
        self.status = "stopped"

        # Initialize events to correct state
        self.pause_event.set()  # Not paused
        self.stop_event.clear()  # Not stopped

    def start_training(self, config: dict) -> bool:
        if self.is_running():
            return False

        # Reset events for new session
        self.pause_event.set()
        self.stop_event.clear()
        self._clear_queues()

        self.process = Process(
            target=self._training_worker,
            args=(config, self.metrics_queue, self.command_queue,
                  self.pause_event, self.stop_event),
            daemon=True,
        )
        self.process.start()
        self.status = "running"
        return True

    def pause_training(self) -> bool:
        if not self.is_running() or self.status == "paused":
            return False
        self.pause_event.clear()  # Block wait()
        self.status = "paused"
        return True

    def resume_training(self) -> bool:
        if self.status != "paused":
            return False
        self.pause_event.set()  # Unblock wait()
        self.status = "running"
        return True

    def stop_training(self):
        if not self.is_running():
            self.status = "stopped"
            return

        self.stop_event.set()  # Signal stop
        self.pause_event.set()  # Unblock if paused
        self.process.join(timeout=5)

        if self.process.is_alive():
            self.process.terminate()

        self.status = "stopped"

    def set_mode(self, visual: bool):
        """Toggle headless/visual mode."""
        self.command_queue.put({"command": "set_mode", "visual": visual})

    def set_speed(self, speed: float):
        """Set visualization speed (0.1 to 1.0)."""
        self.command_queue.put({"command": "set_speed", "speed": speed})
```

### WebSocket Command Handlers
```python
# Source: FastAPI WebSocket docs
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            command = data.get("command")

            if command == "start":
                # ... existing start logic
                pass
            elif command == "stop":
                training_manager.stop_training()
                await manager.send_to(websocket, {
                    "type": "status", "status": "stopped"
                })
            elif command == "pause":
                if training_manager.pause_training():
                    await manager.send_to(websocket, {
                        "type": "status", "status": "paused"
                    })
            elif command == "resume":
                if training_manager.resume_training():
                    await manager.send_to(websocket, {
                        "type": "status", "status": "running"
                    })
            elif command == "set_mode":
                visual = data.get("visual", False)
                training_manager.set_mode(visual)
            elif command == "set_speed":
                speed = data.get("speed", 1.0)
                training_manager.set_speed(speed)
```

### Frontend Controls
```javascript
// Source: Standard DOM patterns
function setupTrainingControls() {
    // Pause/Resume button
    const btnPause = document.getElementById('btn-pause');
    btnPause.addEventListener('click', () => {
        if (currentStatus === 'running') {
            wsClient.send({ command: 'pause' });
        } else if (currentStatus === 'paused') {
            wsClient.send({ command: 'resume' });
        }
    });

    // Mode toggle
    const modeToggle = document.getElementById('mode-toggle');
    modeToggle.addEventListener('change', (e) => {
        wsClient.send({
            command: 'set_mode',
            visual: e.target.checked
        });
    });

    // Speed slider
    const speedSlider = document.getElementById('speed-slider');
    speedSlider.addEventListener('input', (e) => {
        const speed = parseFloat(e.target.value);
        wsClient.send({ command: 'set_speed', speed: speed });
    });
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Checkpoint pause/resume | Event-based pause | N/A | Instant pause, no state drift |
| Environment swap for visual | Board update toggle | Gymnasium v0.26+ | Simpler, preserves state |
| Manual best model tracking | Callback-integrated auto-save | SB3 best practice | Automatic, no user intervention |

**Deprecated/outdated:**
- **env.render(mode="..."):** Old Gym API allowed changing render mode per call - removed in Gymnasium
- **Threading for pause:** Threads share GIL, Events are cleaner for process isolation

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal board update frequency for visual mode**
   - What we know: Current code uses 50 steps, could be too fast or slow
   - What's unclear: Best balance of smoothness vs performance
   - Recommendation: Make configurable via speed slider, start with 25-100 range

2. **Best metric for "best model"**
   - What we know: Could use lines cleared, episode reward, or average reward
   - What's unclear: Which metric best predicts model quality
   - Recommendation: Use lines cleared (user-visible, matches goal), but track all metrics

3. **Pause event timing precision**
   - What we know: Event.wait() unblocks after set(), but exact timing varies
   - What's unclear: Sub-millisecond precision requirements
   - Recommendation: For this use case, millisecond-level is fine - not a concern

## Sources

### Primary (HIGH confidence)
- [Python multiprocessing.Event docs](https://docs.python.org/3/library/multiprocessing.html) - Event, wait(), set(), clear()
- [SB3 Callbacks docs](https://stable-baselines3.readthedocs.io/en/master/guide/callbacks.html) - BaseCallback pattern, _on_step()
- [Gymnasium Basic Usage](https://gymnasium.farama.org/introduction/basic_usage/) - render_mode immutability explanation

### Secondary (MEDIUM confidence)
- [SB3 base_class source](https://stable-baselines3.readthedocs.io/en/master/_modules/stable_baselines3/common/base_class.html) - set_env() constraints
- [Gymnasium Rendering docs](https://gymnasium.farama.org/api/env/) - render mode semantics

### Tertiary (LOW confidence)
- Various WebSearch results for pause/resume patterns - verified against primary sources

## Metadata

**Confidence breakdown:**
- Pause/resume via Event: HIGH - Official Python docs, well-established pattern
- Visual mode via update toggle: HIGH - Based on Gymnasium render_mode constraints
- Speed control via delay: HIGH - Standard time.sleep pattern
- Auto-save best model: HIGH - SB3 callback has model access, standard checkpoint pattern

**Research date:** 2026-01-20
**Valid until:** 2026-02-20 (30 days - stable domain)
