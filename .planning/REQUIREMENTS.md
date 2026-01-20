# Requirements: ML Tetris Trainer

**Defined:** 2025-01-19
**Core Value:** Watch an AI visibly improve at Tetris with full control over training and model management

## v1 Requirements

### Environment

- [ ] **ENV-01**: Tetris game engine with standard rules (SRS rotation, 7-bag randomizer)
- [ ] **ENV-02**: Feature-based state representation (column heights, holes, bumpiness)
- [ ] **ENV-03**: Meta-action space (agent selects final piece placement, not primitive moves)
- [ ] **ENV-04**: Shaped reward function (penalties for holes/height, bonus for lines cleared)
- [ ] **ENV-05**: Gymnasium-compatible interface for RL integration

### Training

- [ ] **TRAIN-01**: DQN agent with experience replay buffer
- [ ] **TRAIN-02**: Start training from web UI
- [ ] **TRAIN-03**: Stop training from web UI
- [ ] **TRAIN-04**: Configurable goal (target number of lines to clear)
- [ ] **TRAIN-05**: Progress display (episode count, current score, lines cleared)
- [ ] **TRAIN-06**: Real-time reward/score chart updating during training
- [ ] **TRAIN-07**: Headless mode for fast training (no visualization overhead)
- [ ] **TRAIN-08**: Visual mode for watching AI play in real-time
- [ ] **TRAIN-09**: Toggle between headless and visual modes without interrupting training
- [ ] **TRAIN-10**: Pause training mid-session
- [ ] **TRAIN-11**: Resume training from paused state
- [ ] **TRAIN-12**: Training speed control (adjust game speed during visual mode)

### Visualization

- [ ] **VIS-01**: Web-based interface accessible via browser
- [ ] **VIS-02**: Live game board showing current Tetris state
- [ ] **VIS-03**: Training status indicator (running/paused/stopped)
- [ ] **VIS-04**: Split view layout (game board + metrics side by side)
- [ ] **VIS-05**: Demo mode to watch trained models play without training

### Model Management

- [ ] **MODEL-01**: Save model checkpoint to file
- [ ] **MODEL-02**: Load model checkpoint from file
- [ ] **MODEL-03**: Resume training from saved checkpoint (preserves full state)
- [ ] **MODEL-04**: Multiple model slots (store different model versions)
- [ ] **MODEL-05**: Model comparison view (leaderboard showing performance metrics)
- [ ] **MODEL-06**: Export best model to standalone file
- [ ] **MODEL-07**: Auto-save best model when new high score achieved

## v2 Requirements

### Advanced Training

- **TRAIN-ADV-01**: Multiple algorithm support (PPO, A2C in addition to DQN)
- **TRAIN-ADV-02**: Hyperparameter tuning interface
- **TRAIN-ADV-03**: Training session history with replay

### Advanced Visualization

- **VIS-ADV-01**: Multiple simultaneous game views (watch several AIs at once)
- **VIS-ADV-02**: Side-by-side model comparison (two models playing simultaneously)
- **VIS-ADV-03**: Desktop GUI option (pygame or tkinter alternative to web)

### Advanced Model Management

- **MODEL-ADV-01**: Model versioning with git-like history
- **MODEL-ADV-02**: Model annotations and notes
- **MODEL-ADV-03**: Import/export model bundles with metadata

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multiplayer/competitive modes | Single AI training focus for v1 |
| Custom Tetris piece shapes | Standard 7 tetrominoes sufficient |
| Cloud deployment | Local-first for v1, reduces complexity |
| Mobile app | Web interface accessible on any device |
| Real-time hyperparameter modification | Complex to implement, defer to v2 |
| Distributed training | Single-machine sufficient for Tetris scale |
| Custom reward function editor | Predefined shaped rewards work well |
| OAuth/user accounts | Single-user local application |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ENV-01 | Phase 1 | Complete |
| ENV-02 | Phase 1 | Complete |
| ENV-03 | Phase 1 | Complete |
| ENV-04 | Phase 1 | Complete |
| ENV-05 | Phase 1 | Complete |
| TRAIN-01 | Phase 2 | Complete |
| TRAIN-02 | Phase 3 | Complete |
| TRAIN-03 | Phase 3 | Complete |
| TRAIN-04 | Phase 2 | Complete |
| TRAIN-05 | Phase 3 | Complete |
| TRAIN-06 | Phase 3 | Complete |
| TRAIN-07 | Phase 2 | Complete |
| TRAIN-08 | Phase 3 | Complete |
| TRAIN-09 | Phase 4 | Complete |
| TRAIN-10 | Phase 4 | Complete |
| TRAIN-11 | Phase 4 | Complete |
| TRAIN-12 | Phase 4 | Complete |
| VIS-01 | Phase 3 | Complete |
| VIS-02 | Phase 3 | Complete |
| VIS-03 | Phase 3 | Complete |
| VIS-04 | Phase 3 | Complete |
| VIS-05 | Phase 5 | Pending |
| MODEL-01 | Phase 2 | Complete |
| MODEL-02 | Phase 2 | Complete |
| MODEL-03 | Phase 2 | Complete |
| MODEL-04 | Phase 5 | Pending |
| MODEL-05 | Phase 5 | Pending |
| MODEL-06 | Phase 5 | Pending |
| MODEL-07 | Phase 4 | Complete |

**Coverage:**
- v1 requirements: 29 total
- Mapped to phases: 29
- Unmapped: 0 [OK]

---
*Requirements defined: 2025-01-19*
*Last updated: 2026-01-20 after Phase 4 completion*
