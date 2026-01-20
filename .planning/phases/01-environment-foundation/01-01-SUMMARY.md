---
phase: 01-environment-foundation
plan: 01
subsystem: environment
tags: [tetris-gymnasium, gymnasium, numpy, reward-shaping, wrappers]

# Dependency graph
requires: []
provides:
  - Installable Python package with pyproject.toml
  - ShapedRewardWrapper for custom reward shaping
  - Package structure for environment module
affects: [01-02, training-core]

# Tech tracking
tech-stack:
  added: [tetris-gymnasium>=0.2.1, gymnasium>=1.0.0, numpy>=1.24, stable-baselines3>=2.4.0]
  patterns: [gymnasium-wrappers, reward-shaping]

key-files:
  created:
    - pyproject.toml
    - src/__init__.py
    - src/environment/__init__.py
    - src/environment/wrappers/__init__.py
    - src/environment/wrappers/shaped_reward.py
  modified: []

key-decisions:
  - "Use tetris-gymnasium>=0.2.1 instead of 0.3.0 (jax/chex dependency conflict)"
  - "Override step() rather than reward() for access to board state"
  - "Compute holes/height from env.unwrapped.board (placed blocks only)"

patterns-established:
  - "RewardWrapper pattern: override step() for full state access"
  - "Board extraction: unwrapped.board[0:20, 4:-4] for playable area"
  - "Delta-based penalties: only penalize increases, not improvements"

# Metrics
duration: 9min
completed: 2026-01-20
---

# Phase 01 Plan 01: Project Setup & ShapedRewardWrapper Summary

**Installable Python package with ShapedRewardWrapper providing configurable reward shaping (holes, height, clears, game over penalties)**

## Performance

- **Duration:** 9 min
- **Started:** 2026-01-20T07:13:05Z
- **Completed:** 2026-01-20T07:21:33Z
- **Tasks:** 2
- **Files created:** 5

## Accomplishments
- Established project structure with pyproject.toml and src/ layout
- Implemented ShapedRewardWrapper with configurable coefficients
- Verified tetris-gymnasium integration and wrapper functionality

## Task Commits

Each task was committed atomically:

1. **Task 1: Initialize project structure and dependencies** - `ce20726` (chore)
2. **Task 2: Implement ShapedRewardWrapper** - `8c5ef6c` (feat)

## Files Created/Modified
- `pyproject.toml` - Project configuration with dependencies
- `src/__init__.py` - Package marker
- `src/environment/__init__.py` - Environment module exports
- `src/environment/wrappers/__init__.py` - Wrappers module exports
- `src/environment/wrappers/shaped_reward.py` - ShapedRewardWrapper implementation (214 lines)

## Decisions Made

1. **tetris-gymnasium version**: Used >=0.2.1 instead of 0.3.0
   - Rationale: v0.3.0 has jax/chex dependency conflict (chex>=0.1.87 requires jax>=0.7.0, but tetris-gymnasium requires jax<0.5.0)
   - v0.2.1 works without jax dependency

2. **Override step() not reward()**: ShapedRewardWrapper overrides step() rather than just reward()
   - Rationale: Need access to board state and terminated flag for game over penalty
   - reward() only receives the reward value, not environment state

3. **Board access via unwrapped**: Extract board from env.unwrapped.board
   - Rationale: Gets placed blocks only (not active falling piece)
   - Playable area is board[0:20, 4:-4] after removing frame padding

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Dependency version conflict**
- **Found during:** Task 1 (pip install)
- **Issue:** tetris-gymnasium 0.3.0 has internal dependency conflict with chex/jax versions
- **Fix:** Changed to tetris-gymnasium>=0.2.1 which doesn't require jax
- **Files modified:** pyproject.toml
- **Verification:** pip install -e ".[dev]" succeeds
- **Committed in:** ce20726 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to make package installable. v0.2.1 has same wrappers needed (GroupedActionsObservations, FeatureVectorObservation).

## Issues Encountered

- tetris-gymnasium environment not auto-registered with gym.make() - must import Tetris class directly
- GroupedActionsObservations accepts observation_wrappers parameter (not stacked after FeatureVectorObservation)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

**Ready for Plan 01-02:**
- ShapedRewardWrapper can be applied to any gymnasium environment
- tetris-gymnasium wrappers (GroupedActionsObservations, FeatureVectorObservation) confirmed working
- Package structure ready for environment factory function

**Notes for next plan:**
- Use direct import: `from tetris_gymnasium.envs.tetris import Tetris`
- Wrapper order: Tetris -> GroupedActionsObservations(env, observation_wrappers=[FeatureVectorObservation(env)]) -> ShapedRewardWrapper
- Or: Tetris -> FeatureVectorObservation -> ShapedRewardWrapper (if not using grouped actions)

---
*Phase: 01-environment-foundation*
*Completed: 2026-01-20*
