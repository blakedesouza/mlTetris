# Roadmap: ML Tetris Trainer

## Overview

This roadmap delivers an ML Tetris trainer in five phases: first building a Gymnasium-compatible Tetris environment with feature-based observations and shaped rewards, then implementing DQN training with checkpointing, followed by a web dashboard for live visualization, then advanced training controls (pause/resume, speed, mode toggle), and finally model management with comparison and demo features. The journey prioritizes getting the RL foundation right before adding user-facing features.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Environment Foundation** - Gymnasium-compatible Tetris with feature-based state and shaped rewards
- [x] **Phase 2: Training Core** - DQN agent with experience replay, headless training, and checkpointing
- [x] **Phase 3: Web Visualization** - Live dashboard with game board, metrics, and start/stop controls
- [x] **Phase 4: Training Controls** - Pause/resume, headless/visual toggle, and speed control
- [ ] **Phase 5: Model Management & Polish** - Multiple model slots, comparison view, and demo mode

## Phase Details

### Phase 1: Environment Foundation
**Goal**: Deliver a working Gymnasium-compatible Tetris environment with feature-based observations, meta-actions, and shaped rewards
**Depends on**: Nothing (first phase)
**Requirements**: ENV-01, ENV-02, ENV-03, ENV-04, ENV-05
**Success Criteria** (what must be TRUE):
  1. Environment can be instantiated and reset via Gymnasium API
  2. Observations are feature vectors (column heights, holes, bumpiness) not raw board grids
  3. Agent can select final piece placements (rotation + column) as single actions
  4. Rewards penalize holes/height and reward line clears (not just sparse line-clear scoring)
  5. Environment passes Gymnasium check_env validation
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md — Project setup and ShapedRewardWrapper implementation
- [x] 01-02-PLAN.md — Environment factory, tests, and Gymnasium validation

### Phase 2: Training Core
**Goal**: Deliver a working DQN agent that learns to play Tetris with headless training and full checkpoint support
**Depends on**: Phase 1
**Requirements**: TRAIN-01, TRAIN-04, TRAIN-07, MODEL-01, MODEL-02, MODEL-03
**Success Criteria** (what must be TRUE):
  1. Training runs headless without any visualization overhead
  2. Agent shows measurable improvement over random play after training
  3. User can configure target lines-to-clear goal before training starts
  4. Checkpoints can be saved during training and loaded to resume later
  5. Resumed training continues from exact state (optimizer, replay buffer, epsilon preserved)
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — Training configuration and TetrisAgent wrapper with checkpoint support
- [x] 02-02-PLAN.md — Callbacks (goal-based stopping, lines tracking) and headless training function
- [x] 02-03-PLAN.md — Test suite and end-to-end training verification

### Phase 3: Web Visualization
**Goal**: Deliver a web dashboard where users can watch AI play, view metrics, and control training
**Depends on**: Phase 2
**Requirements**: VIS-01, VIS-02, VIS-03, VIS-04, TRAIN-02, TRAIN-03, TRAIN-05, TRAIN-06, TRAIN-08
**Success Criteria** (what must be TRUE):
  1. User can open browser and see the Tetris game board with current AI play
  2. User can start new training session from web UI
  3. User can stop training session from web UI
  4. Dashboard shows live metrics (episode count, current score, lines cleared)
  5. Real-time chart updates showing reward/score progression during training
  6. Split view displays game board and metrics side by side
  7. Training status indicator shows running/paused/stopped state
**Plans**: 5 plans

Plans:
- [x] 03-01-PLAN.md — FastAPI server with WebSocket support and TrainingManager with process isolation
- [x] 03-02-PLAN.md — Frontend static assets: HTML template, CSS styles, JavaScript modules
- [x] 03-03-PLAN.md — Training-web integration: WebMetricsCallback and board state extraction
- [x] 03-04-PLAN.md — Frontend functionality: WebSocket client, Canvas rendering, Chart.js wiring
- [x] 03-05-PLAN.md — Server command handling and end-to-end integration verification

### Phase 4: Training Controls
**Goal**: Deliver fine-grained training control including pause/resume, mode toggle, and speed adjustment
**Depends on**: Phase 3
**Requirements**: TRAIN-09, TRAIN-10, TRAIN-11, TRAIN-12, MODEL-07
**Success Criteria** (what must be TRUE):
  1. User can toggle between headless (fast) and visual (watchable) modes without interrupting training
  2. User can pause training mid-session and resume from exact state
  3. User can adjust game speed during visual mode to watch faster or slower
  4. Best model auto-saves when new high score is achieved during training
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — Backend Event-based pause/resume and enhanced WebMetricsCallback with controls
- [x] 04-02-PLAN.md — WebSocket command handlers and frontend UI control elements
- [x] 04-03-PLAN.md — Frontend control wiring and end-to-end verification

### Phase 5: Model Management & Polish
**Goal**: Deliver model comparison features and demo mode for showcasing trained models
**Depends on**: Phase 4
**Requirements**: VIS-05, MODEL-04, MODEL-05, MODEL-06
**Success Criteria** (what must be TRUE):
  1. User can store multiple model versions in separate slots
  2. User can view leaderboard comparing performance metrics across saved models
  3. User can watch any saved model play in demo mode (no training, just showcase)
  4. User can export best model to standalone file for sharing/backup
**Plans**: 3 plans

Plans:
- [ ] 05-01-PLAN.md — Backend: ModelSlotManager class and REST API for model operations
- [ ] 05-02-PLAN.md — Demo mode worker implementation in TrainingManager
- [ ] 05-03-PLAN.md — Frontend: Leaderboard table, save/delete/export UI, and demo controls

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Environment Foundation | 2/2 | Complete | 2025-01-20 |
| 2. Training Core | 3/3 | Complete | 2026-01-20 |
| 3. Web Visualization | 5/5 | Complete | 2026-01-20 |
| 4. Training Controls | 3/3 | Complete | 2026-01-20 |
| 5. Model Management & Polish | 0/3 | Planned | - |

---
*Roadmap created: 2025-01-19*
*Phase 1 planned: 2025-01-20*
*Phase 2 planned: 2025-01-20*
*Phase 3 planned: 2026-01-20*
*Phase 4 planned: 2026-01-20*
*Phase 5 planned: 2026-01-20*
*Coverage: 29/29 v1 requirements mapped*
