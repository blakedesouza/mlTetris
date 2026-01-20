# ML Tetris Trainer

## What This Is

A Python application that uses reinforcement learning to teach an AI to play Tetris. Users can watch the AI learn in real-time through a web interface, configure training goals (target lines to clear), and manage multiple model versions to compare how the AI improves over time.

## Core Value

Watch an AI visibly improve at Tetris — from random moves to strategic play — with full control over training and model management.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Tetris game engine (standard rules, playable by AI)
- [ ] Reinforcement learning training loop (DQN or PPO)
- [ ] Configurable goal: target number of lines to clear
- [ ] Web interface with split view (live gameplay + training metrics)
- [ ] Toggle between fast headless training and live visualization
- [ ] Save model checkpoints during training
- [ ] Resume training from saved checkpoint
- [ ] Load and compare different model versions
- [ ] Export best/final model

### Out of Scope

- Mobile app — web-first, accessible from any device
- Multiplayer/competitive modes — single AI training focus
- Custom Tetris piece shapes — standard 7 tetrominoes only
- Cloud deployment — local-first for v1

## Context

- Target platform: local Python environment with web browser for UI
- ML approach: Reinforcement learning (DQN or PPO) — proven effective for Tetris
- Tetris rules: Modern standard rules (SRS rotation, 7-bag randomizer, hold piece optional)
- Training: Must support both headless (fast) and rendered (observable) modes
- The joy is in watching the learning process, not just the end result

## Constraints

- **Language**: Python — user's environment and preference
- **Interface**: Web-based UI primary — handles visualization and stats cleanly
- **Local-first**: Runs on user's machine, no cloud dependencies for v1

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Reinforcement learning over genetic algorithms | Proven track record for Tetris, clearer training signal | — Pending |
| Web interface over desktop GUI | Easier visualization (canvas + charts), cross-platform | — Pending |
| Configurable line goal over fixed objectives | User controls what "success" means for each training run | — Pending |

---
*Last updated: 2025-01-19 after initialization*
