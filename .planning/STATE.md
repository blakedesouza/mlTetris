# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2025-01-19)

**Core value:** Watch an AI visibly improve at Tetris with full control over training and model management
**Current focus:** Phase 3 - Web Visualization (in progress)

## Current Position

Phase: 3 of 5 (Web Visualization)
Plan: 4 of 5 in current phase
Status: In progress
Last activity: 2026-01-20 - Completed 03-04-PLAN.md (Frontend WebSocket Integration)

Progress: [██████░░░░] 57%

## Performance Metrics

**Velocity:**
- Total plans completed: 8
- Average duration: 6.4 min
- Total execution time: 52 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-environment-foundation | 2 | 17 min | 8.5 min |
| 02-training-core | 3 | 19 min | 6.3 min |
| 03-web-visualization | 3 | 16 min | 5.3 min |

**Recent Trend:**
- Last 5 plans: 02-02 (4 min), 02-03 (13 min), 03-02 (4 min), 03-01 (8 min), 03-04 (4 min)
- Trend: Stable

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- **tetris-gymnasium version**: Use >=0.2.1 (v0.3.0 has jax/chex dependency conflict)
- **Reward shaping approach**: Override step() not reward() for board state access
- **Board extraction**: Use env.unwrapped.board[0:20, 4:-4] for playable area
- **Wrapper integration**: GroupedActionsObservations uses observation_wrappers parameter for FeatureVectorObservation
- **Observation shape**: (40, 13) - 40 actions x 13 features (column heights, max height, holes, bumpiness)
- **DQN.load() for checkpoints**: Use class method, not create-then-load, for proper optimizer restoration
- **Checkpoint format**: Directory with model.zip + replay_buffer.pkl + metadata.json
- **Callback coordination**: LinesTrackingCallback provides data, GoalReachedCallback queries it
- **Checkpoint resume pattern**: Check for 'latest' directory existence before starting training
- **Baseline comparison threshold**: 25k timesteps with soft 0.9x threshold for statistical robustness
- **Chart.js via CDN**: Simpler than npm bundling for single-page dashboard
- **Manual Chart.js updates**: chartjs-plugin-streaming unmaintained, manual update() more reliable
- **Process isolation for training**: multiprocessing.Process to avoid blocking async event loop
- **Queue-based IPC**: metrics_queue and command_queue for bidirectional communication
- **WebSocket auto-reconnect**: 10 max attempts with exponential backoff (1s to 30s max)
- **Message types**: board, metrics, episode, status, info, error for frontend routing

### Pending Todos

None yet.

### Blockers/Concerns

Research flags from SUMMARY.md:
- SB3 warns about unconventional observation shape (40, 13) - may need flatten or custom policy

**Resolved:**
- tetris-gymnasium API verified: wrappers work in v0.2.1, direct Tetris class import required
- Environment factory complete with check_env validation passing
- TrainingConfig and TetrisAgent created with checkpoint support
- Training callbacks and headless training function complete
- **Phase 2 complete:** Test suite verifies all requirements, trained agent outperforms random baseline
- Frontend assets created: HTML template, CSS styling, JS modules for Canvas and Chart.js
- FastAPI server with WebSocket endpoint, TrainingManager with process isolation
- **Frontend wiring complete:** WebSocketClient connects, routes messages to GameBoard.render() and MetricsChart.addDataPoint()

## Session Continuity

Last session: 2026-01-20
Stopped at: Completed 03-04-PLAN.md (Frontend WebSocket Integration)
Resume file: None
