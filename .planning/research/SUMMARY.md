# Project Research Summary

**Project:** ML Tetris Trainer
**Domain:** Reinforcement Learning Game Trainer with Web Visualization
**Researched:** 2026-01-19
**Confidence:** HIGH

## Executive Summary

Building an ML Tetris trainer is a well-documented problem with established solutions. The recommended approach uses **Stable Baselines3 + tetris-gymnasium + FastAPI/WebSockets** for training, with feature-based state representation and meta-actions for the RL agent. The discovery of `tetris-gymnasium` is significant: it eliminates weeks of game engine development and provides a proven, configurable Gymnasium-compatible environment.

The core architectural insight is **separation of training from visualization**. Training runs headless at maximum speed (1000x faster than visual mode), while a WebSocket bridge enables optional real-time visualization without affecting training. This decoupling is essential for usability: users can watch the AI learn when interesting, but train efficiently when they just want results.

The highest-risk phase is environment setup and state representation. Three critical decisions here cascade through the entire project: (1) use feature-based state not raw board, (2) use meta-actions not primitive controls, and (3) implement shaped rewards not just line-clear scoring. Getting these wrong wastes weeks; getting them right enables rapid iteration on training. The web visualization phase is lower risk with well-established patterns (FastAPI + HTMX or React).

## Key Findings

### Recommended Stack

The 2025 Python ML ecosystem has matured significantly. Stable Baselines3 provides production-ready DQN/PPO implementations with excellent documentation. The `tetris-gymnasium` library (v0.3.0) provides a pre-built, Gymnasium-compatible Tetris environment, eliminating custom game logic entirely.

**Core technologies:**
- **Stable Baselines3 2.7.1**: RL library — best documentation, native Gymnasium support, built-in logging
- **tetris-gymnasium 0.3.0**: Game environment — pre-built Tetris, highly configurable, saves weeks of work
- **FastAPI 0.128.0**: Web framework — async-native, built-in WebSocket support, modern
- **PyTorch 2.9.1**: Deep learning — SB3 backend, excellent debugging experience
- **Plotly 6.5.2**: Charting — Python-native interactive charts for training metrics
- **W&B 0.24.0**: Experiment tracking — SB3 integration, free tier sufficient

**Frontend approach:** HTMX + Jinja2 for simplicity (Python-only codebase, no JS build tooling). Upgrade to React if smooth canvas rendering becomes critical.

### Expected Features

**Must have (table stakes):**
- Start/stop training from web UI
- Live game board visualization during training
- Real-time reward/score chart
- Model save/load functionality
- Basic metrics panel (episode count, best score, lines cleared)
- Training status indicator

**Should have (competitive):**
- Headless/visual mode toggle (100x speed difference)
- Pause/resume training
- Training speed control slider
- Best model auto-save
- Demo mode for showcasing trained models
- Split view (game + metrics simultaneously)

**Defer (v2+):**
- Multiple algorithm support (start with DQN only)
- Distributed training
- Custom reward function editor
- Model interpretability/explainability
- Real-time hyperparameter modification
- A/B testing framework

### Architecture Approach

Five distinct components with clean separation: Tetris Environment (Gymnasium interface), RL Agent (DQN with replay buffer), Training Loop (orchestrator with event emission), Web Interface (FastAPI + WebSocket), and Model Manager (checkpointing). The training loop runs in a background thread, communicating with the web server via queues to maintain UI responsiveness.

**Major components:**
1. **Tetris Environment** — Game logic via Gymnasium interface, feature-based state representation
2. **RL Agent** — Neural network, Q-learning, experience replay buffer, action selection
3. **Training Loop** — Episode coordination, mode switching, event emission to visualization
4. **Web Interface** — FastAPI backend, WebSocket streaming, HTMX/Jinja2 frontend
5. **Model Manager** — Checkpoint save/load, metadata tracking, model comparison

**Key architectural decisions:**
- Feature-based state (column heights, holes, bumpiness) NOT raw board grid
- Meta-actions (rotation + column = ~40 actions) NOT primitive controls (left/right/rotate/drop)
- Shaped rewards (hole penalty, height penalty, game-over penalty) NOT just line clears
- Headless training by default with optional visualization attachment

### Critical Pitfalls

1. **Using raw board state as input** — Use feature vector (heights, holes, bumpiness) instead. Raw 20x10 grid is intractable (2^200 states). Proven implementations all use features.

2. **Sparse reward (lines only)** — Add shaped intermediate rewards: negative for holes, negative for height increases, game-over penalty (-10 to -100). Lines-only rewards provide zero feedback for 99%+ of actions.

3. **Primitive actions (left/right/rotate/drop)** — Use meta-actions where agent picks final placement (rotation, column). Reduces 10-40 actions per piece to 1, making credit assignment tractable.

4. **Incomplete checkpoint saves** — Save full state: model weights, optimizer state, replay buffer, epsilon, random seeds. Model weights alone breaks resume (Adam momentum lost, exploration resets).

5. **Visualization blocking training** — Run training in background thread, headless by default. Rendering every step makes training 100-1000x slower. Toggle visualization without interrupting training.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Environment Foundation
**Rationale:** Everything depends on correct environment design. State representation, action space, and reward function decisions cascade through entire project. tetris-gymnasium eliminates game logic work but still needs wrapper for feature extraction.
**Delivers:** Working Gymnasium environment with feature-based observations, meta-actions, shaped rewards
**Addresses:** Core training foundation (table stakes), state representation
**Avoids:** Pitfalls #1 (raw board), #2 (sparse rewards), #3 (primitive actions), #11-15 (Tetris-specific gotchas)

### Phase 2: Training Core
**Rationale:** Requires environment. Agent + training loop can run headless without visualization. This is where the ML actually happens.
**Delivers:** Working DQN agent that learns to play Tetris, console-based progress output, basic checkpointing
**Uses:** Stable Baselines3, PyTorch, tetris-gymnasium
**Implements:** RL Agent component, Training Loop component, Model Manager (basic)
**Avoids:** Pitfalls #4 (incomplete checkpoints), #5 (catastrophic forgetting), #7 (wrong hyperparameters)

### Phase 3: Web Visualization
**Rationale:** Requires working training. This is the user interface layer. Architecture must support headless/visual mode switching without affecting training.
**Delivers:** Web dashboard with live game display, metrics charts, start/stop/save/load controls
**Uses:** FastAPI, WebSockets, HTMX/Jinja2, Plotly
**Implements:** Web Interface component
**Avoids:** Pitfalls #6 (visualization blocking), #8 (blocking UI)

### Phase 4: Training Controls
**Rationale:** Enhances base visualization with training control features. Builds on working web interface.
**Delivers:** Headless/visual toggle, pause/resume, speed control, target goal setting
**Addresses:** Key differentiating features from FEATURES.md
**Implements:** Advanced Training Loop features

### Phase 5: Model Management
**Rationale:** Requires multiple training runs worth of models. Polish phase for comparing and showcasing results.
**Delivers:** Multiple model slots, performance leaderboard, demo mode, comparison UI
**Addresses:** Model comparison differentiators from FEATURES.md
**Implements:** Full Model Manager component

### Phase Ordering Rationale

- **Environment first** because state/action/reward choices are irreversible. Wrong decisions here waste weeks of training.
- **Training core second** because it validates environment design. Must work headless before adding visualization complexity.
- **Web visualization third** because it's additive — training doesn't depend on it. Easier to debug training issues without UI layer.
- **Controls and model management last** because they're polish on working foundation. Nice-to-haves that don't block core value.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (Environment):** HIGH RISK — State representation and reward shaping are critical. Research tetris-gymnasium API in detail; may need custom wrapper.
- **Phase 2 (Training Core):** MEDIUM RISK — DQN hyperparameters for Tetris differ from defaults. SB3 documentation is excellent but Tetris-specific tuning needed.

Phases with standard patterns (skip research-phase):
- **Phase 3 (Web Visualization):** Well-documented FastAPI + WebSocket + HTMX patterns. Many tutorials available.
- **Phase 4-5 (Controls/Model Management):** Extension of Phase 3 patterns, no new research needed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All libraries verified on PyPI with recent releases, versions confirmed |
| Features | HIGH | Multiple reference implementations and practitioner reports agree on core features |
| Architecture | HIGH | Consistent patterns across nuno-faria/tetris-ai, ChesterHuynh/tetrisAI, and academic papers |
| Pitfalls | HIGH | Documented across academic papers, GitHub issues, and practitioner blog posts with specific solutions |

**Overall confidence:** HIGH

All four research dimensions converged on consistent recommendations. The domain is well-studied with multiple successful open-source implementations. tetris-gymnasium provides battle-tested game logic.

### Gaps to Address

- **tetris-gymnasium feature extraction:** Library provides environment but may need custom observation wrapper for feature-based state. Verify during Phase 1 implementation.
- **SB3 vs custom DQN:** Architecture research suggests custom DQN for Tetris-specific state evaluation. May conflict with stack recommendation of SB3. Resolve in Phase 2 planning.
- **HTMX real-time performance:** HTMX server-side rendering may struggle at 60fps game display. May need to fall back to client-side canvas. Test early in Phase 3.
- **Vectorized environments:** Identified as optimization opportunity but adds complexity. Defer decision until baseline training works.

## Cross-Cutting Themes

Several themes emerged across multiple research dimensions:

1. **Simplicity over sophistication:** Feature-based state beats raw pixels, meta-actions beat primitives, HTMX beats React (unless needed), DQN beats complex algorithms. Start simple.

2. **Decouple for flexibility:** Training from visualization, agent from environment, web from training loop. Clean interfaces enable iteration.

3. **Existing work exists:** tetris-gymnasium, Stable Baselines3, established reward functions. Don't reinvent wheels.

4. **Tetris is special:** Many RL "best practices" don't apply. State representation, action space, and hyperparameters need Tetris-specific choices.

## Sources

### Primary (HIGH confidence)
- [Stable Baselines3 Documentation](https://stable-baselines3.readthedocs.io/) — RL library API, callbacks, tips
- [Gymnasium Documentation](https://gymnasium.farama.org/) — Environment interface, custom env creation
- [Tetris-Gymnasium GitHub](https://github.com/Max-We/Tetris-Gymnasium) — Pre-built Tetris environment
- [FastAPI Documentation](https://fastapi.tiangolo.com/) — Web framework, WebSocket support
- PyPI package pages — Version verification for all dependencies

### Secondary (MEDIUM confidence)
- [nuno-faria/tetris-ai](https://github.com/nuno-faria/tetris-ai) — Reference DQN implementation, feature engineering
- [Stanford CS231n Tetris Report](https://cs231n.stanford.edu/reports/2016/pdfs/121_Report.pdf) — Academic validation of approach
- [Tim Hanewich Medium Article](https://timhanewich.medium.com/how-i-trained-a-neural-network-to-play-tetris-using-reinforcement-learning-ecfa529c767a) — Practitioner experience
- [Neptune.ai RL Training Debug](https://neptune.ai/blog/reinforcement-learning-agents-training-debug) — Logging best practices

### Tertiary (LOW confidence)
- Various Medium articles on FastAPI + HTMX — Implementation patterns, needs validation
- SBX (Stable Baselines Jax) — Performance claims need verification if pursuing optimization

---
*Research completed: 2026-01-19*
*Ready for roadmap: yes*
