# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2025-01-19)

**Core value:** Watch an AI visibly improve at Tetris with full control over training and model management
**Current focus:** Phase 2 - Training Core (in progress)

## Current Position

Phase: 2 of 5 (Training Core)
Plan: 2 of 3 in current phase
Status: In progress
Last activity: 2026-01-20 - Completed 02-02-PLAN.md

Progress: [████░░░░░░] 40%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 5.75 min
- Total execution time: 23 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-environment-foundation | 2 | 17 min | 8.5 min |
| 02-training-core | 2 | 6 min | 3 min |

**Recent Trend:**
- Last 5 plans: 01-01 (9 min), 01-02 (8 min), 02-01 (2 min), 02-02 (4 min)
- Trend: Improving

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

### Pending Todos

None yet.

### Blockers/Concerns

Research flags from SUMMARY.md:
- Phase 2 (Training Core): MEDIUM RISK - DQN hyperparameters need Tetris-specific tuning.
- SB3 warns about unconventional observation shape (40, 13) - may need flatten or custom policy

**Resolved:**
- tetris-gymnasium API verified: wrappers work in v0.2.1, direct Tetris class import required
- Environment factory complete with check_env validation passing
- TrainingConfig and TetrisAgent created with checkpoint support
- Training callbacks and headless training function complete

## Session Continuity

Last session: 2026-01-20T08:04:00Z
Stopped at: Completed 02-02-PLAN.md
Resume file: None
