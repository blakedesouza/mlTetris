---
phase: 03-web-visualization
plan: 03
subsystem: training-web-integration
tags: [multiprocessing, queue, callback, metrics, board-state]
dependency-graph:
  requires: ["03-01"]
  provides: ["WebMetricsCallback", "complete-training-worker"]
  affects: ["03-04", "03-05"]
tech-stack:
  added: []
  patterns: ["Queue-based IPC", "subprocess isolation", "callback metrics extraction"]
key-files:
  created: []
  modified:
    - src/training/callbacks.py
    - src/training/__init__.py
    - src/web/training_manager.py
decisions:
  - key: board-state-extraction
    choice: "Navigate through wrappers to unwrapped env, extract board[0:20, 4:-4]"
    reason: "tetris-gymnasium board includes padding, playable area is 20x10"
  - key: callback-message-types
    choice: "Four message types: metrics, board, episode, status"
    reason: "Distinct types allow frontend to handle each appropriately"
metrics:
  duration: 6 min
  completed: 2026-01-20
---

# Phase 03 Plan 03: Training-to-Web Integration Summary

Queue-based metrics communication between training subprocess and web server with real-time board state extraction.

## Completed Work

### Task 1: WebMetricsCallback for Queue-based Metrics Reporting
**Commit:** af9ff61

Added `WebMetricsCallback` class to `src/training/callbacks.py`:
- Sends metrics every 100 steps (timesteps, episode count, scores, avg reward)
- Sends board state every 10 steps for smooth visualization
- Sends episode completion data with reward and lines
- Sends status updates (running/stopped)
- Checks command_queue for stop commands (non-blocking)
- Extracts board state via `env.unwrapped.board[0:20, 4:-4]`

**Key code:**
```python
class WebMetricsCallback(BaseCallback):
    def _send_board_state(self) -> None:
        unwrapped = env
        while hasattr(unwrapped, "env"):
            unwrapped = unwrapped.env
        if hasattr(unwrapped, "board"):
            board = unwrapped.board[0:20, 4:-4].tolist()
            self.metrics_queue.put({"type": "board", "board": board})
```

### Task 2: Complete Training Worker Implementation
**Commit:** 821bb7c

Implemented full `_training_worker` in `TrainingManager`:
- Creates environment with headless config
- Loads from checkpoint if exists, otherwise creates new agent
- Sets up WebMetricsCallback and LinesTrackingCallback
- Calculates remaining timesteps and runs training
- Saves checkpoint on completion (latest and final)
- Handles errors with full traceback reporting via queue

**Key code:**
```python
@staticmethod
def _training_worker(config_dict, metrics_queue, command_queue):
    from src.environment import make_env, EnvConfig
    from src.training.agent import TetrisAgent
    # ... setup ...
    web_callback = WebMetricsCallback(metrics_queue, command_queue)
    agent.train(remaining, callback=callback_list)
    agent.save_checkpoint(checkpoint_path / "latest")
```

### Task 3: Integration Test Verification
- Imports verified working
- Training starts in subprocess without blocking
- Metrics flow through queue (25 messages in 3 seconds)
- Board state received successfully
- Status updates received
- Stop command terminates training gracefully
- All 73 existing tests pass

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

| Check | Status |
|-------|--------|
| WebMetricsCallback sends metrics via Queue | PASS |
| TrainingManager._training_worker runs complete loop | PASS |
| Board state extraction (20x10) | PASS |
| Stop command terminates gracefully | PASS |
| Existing tests pass | PASS (73 tests) |

## Message Types

The callback sends four types of messages:

| Type | Frequency | Content |
|------|-----------|---------|
| `metrics` | Every 100 steps | timesteps, episode_count, current_score, lines_cleared, avg_reward, best_lines |
| `board` | Every 10 steps | 20x10 board state array |
| `episode` | On episode end | episode number, reward, lines |
| `status` | On start/stop | "running" or "stopped" |

## Next Phase Readiness

Ready for Plan 04 (Frontend WebSocket Integration):
- WebSocket endpoint already exists from Plan 01
- Server can poll metrics_queue and broadcast to clients
- Board state format matches frontend canvas expectations
- Metrics format matches chart.js update requirements

**Integration point:** Server needs to poll `training_manager.metrics_queue` and send to WebSocket clients.
