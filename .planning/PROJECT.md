# ML Tetris Trainer

## What This Is

A Python application that uses reinforcement learning (DQN) to teach an AI to play Tetris. Users can watch the AI learn in real-time through a web dashboard, control training with pause/resume/speed adjustments, and manage multiple model versions with a comparison leaderboard and demo playback.

## Core Value

Watch an AI visibly improve at Tetris — from random moves to strategic play — with full control over training and model management.

## Requirements

### Validated

- Tetris game engine with standard rules (SRS rotation, 7-bag) — v1.0
- Feature-based observations (column heights, holes, bumpiness) — v1.0
- Meta-action space (40 final placements) — v1.0
- Shaped reward function (penalties + bonuses) — v1.0
- Gymnasium-compatible interface — v1.0
- DQN agent with experience replay — v1.0
- Web dashboard with live board + metrics — v1.0
- Start/stop/pause/resume training from UI — v1.0
- Headless/visual mode toggle — v1.0
- Speed control during visual mode — v1.0
- Checkpoint save/load/resume — v1.0
- Multiple model slots with leaderboard — v1.0
- Demo mode for saved models — v1.0
- Export best model — v1.0
- Auto-save on new high score — v1.0

### Active

(None — define in next milestone)

### Out of Scope

- Mobile app — web-first, accessible from any device
- Multiplayer/competitive modes — single AI training focus
- Custom Tetris piece shapes — standard 7 tetrominoes only
- Cloud deployment — local-first for simplicity
- Real-time hyperparameter tuning — complex, defer to v2+
- Multiple algorithms (PPO, A2C) — DQN sufficient for v1
- Distributed training — single-machine sufficient for Tetris scale

## Context

**Current State (v1.0 shipped):**
- ~5,300 lines of code (3,668 Python + 1,643 frontend)
- Tech stack: Python, Stable-Baselines3, FastAPI, WebSockets, Chart.js, Canvas API
- 5 phases completed, 16 plans executed
- 80+ tests validating all 29 requirements
- Checkpoint format: directory with model.zip + replay_buffer.pkl + metadata.json

**Architecture:**
- `src/environment/` — Gymnasium-compatible Tetris with wrappers
- `src/training/` — DQN agent, callbacks, training loop
- `src/web/` — FastAPI server, WebSocket handlers, static frontend
- Process isolation: training runs in subprocess, communicates via queues

**Known Technical Notes:**
- SB3 warns about unconventional observation shape (40, 13) — may need flatten or custom policy for advanced training
- tetris-gymnasium v0.2.1 recommended (v0.3.0 has jax/chex dependency issues)

## Constraints

- **Language**: Python — user's environment and preference
- **Interface**: Web-based UI primary — handles visualization and stats cleanly
- **Local-first**: Runs on user's machine, no cloud dependencies

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Reinforcement learning (DQN) | Proven track record for Tetris, clearer training signal | Good |
| Web interface over desktop GUI | Easier visualization (canvas + charts), cross-platform | Good |
| Feature-based observations (not raw board) | More efficient learning, proven approach | Good |
| Meta-actions (final placements) | Simpler action space than primitive moves | Good |
| Process isolation for training | Prevents blocking async event loop | Good |
| Queue-based IPC | Clean separation, reliable message passing | Good |
| Event-based pause/resume | Simple, no complex state machine | Good |
| Chart.js via CDN | No build tooling needed for single-page dashboard | Good |
| Model slots with metadata | Clean organization, supports leaderboard | Good |

---
*Last updated: 2026-01-20 after v1.0 milestone*
