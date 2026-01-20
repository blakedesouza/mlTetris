# Features Research: ML Tetris Trainer

**Domain:** ML game training application with web visualization
**Researched:** 2026-01-19
**Overall Confidence:** HIGH (well-documented domain with many reference implementations)

## Table Stakes

Features users expect from any ML game training application. Missing these makes the product feel incomplete or broken.

### Core Training Features

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Start/Stop Training** | Basic control over training process | Low | Essential - training without control is unusable |
| **Training Progress Display** | Users need to know training is happening | Low | Episode count, elapsed time at minimum |
| **Reward/Score Chart** | Primary indicator AI is learning | Medium | Episode rewards over time, moving average for noise smoothing |
| **Live Game Visualization** | Core value prop - "watch AI learn" | Medium | Render current game state during training |
| **Model Save/Load** | Training can take hours/days; must persist | Medium | Save checkpoints, resume from checkpoint |
| **Basic Metrics Panel** | Understand training state at a glance | Low | Current episode, total episodes, best score, current score |

### Visualization Requirements

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Episode Reward Chart** | Standard RL visualization | Medium | X: episode, Y: reward. Moving average overlay |
| **Lines Cleared Metric** | Domain-specific success metric | Low | Tetris-specific KPI users understand |
| **Current Game Board** | Visual feedback that training is active | Medium | Real-time or periodic board state rendering |
| **Training Status Indicator** | Is it training? Paused? Done? | Low | Clear state machine display |

### Model Management

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Save Model to File** | Standard ML workflow | Low | Keras/PyTorch native format |
| **Load Existing Model** | Resume training or demo | Low | File picker or path input |
| **Best Model Auto-Save** | Don't lose peak performance | Medium | Track best score, auto-save when surpassed |

## Differentiators

Features that stand out and provide competitive advantage. Not strictly expected, but valuable.

### Training Controls

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Headless/Visual Toggle** | Fast training when not watching, slow when demonstrating | Medium | Critical for UX - 100x speed difference |
| **Training Speed Control** | Watch AI at different speeds during visual mode | Medium | Slider: 1x, 2x, 5x, 10x, Max |
| **Pause/Resume Training** | Inspect state, adjust, continue | Medium | Save training state, not just model |
| **Target Goal Setting** | "Train until 100 lines cleared" | Low | Configurable success criteria |

### Advanced Visualization

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Split View (Game + Metrics)** | See AI play AND training progress simultaneously | Medium | Core to project vision |
| **Loss Curve Display** | Diagnose training issues | Low | Q-learning loss over time |
| **Steps per Episode Chart** | Efficiency indicator | Low | Should decrease as AI improves |
| **Exploration Rate (Epsilon) Display** | Understand exploration vs exploitation | Low | Shows training phase |

### Model Comparison

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Multiple Model Slots** | Compare different training runs | Medium | Name/save multiple models |
| **Side-by-Side Playback** | Visual comparison of model performance | High | Two game boards, different models |
| **Performance Leaderboard** | Track which model/config performs best | Medium | Table: model name, best score, avg score, lines cleared |
| **Training Run Comparison** | Overlay reward curves from different runs | Medium | Compare hyperparameter experiments |

### User Experience

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Demo Mode** | Showcase trained model without training UI | Low | Clean view for showing off results |
| **Export Model for Deployment** | Use trained model elsewhere | Medium | ONNX or TensorFlow Lite export |
| **Training Notifications** | Know when milestone reached or training done | Medium | Browser notification, optional email |
| **Persistent Training History** | Resume where you left off across sessions | Medium | Store training state in DB/file |

### Hyperparameter Controls

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Adjustable Learning Rate** | Tune training speed/stability | Low | Slider with reasonable defaults |
| **Epsilon Decay Configuration** | Control exploration schedule | Medium | Start, end, decay rate |
| **Replay Memory Size** | Trade memory for learning stability | Low | Numeric input with guidance |
| **Neural Network Architecture Selection** | Experiment with different models | High | Preset architectures or custom layers |

## Anti-Features

Things to deliberately NOT build for v1. Common mistakes or scope traps.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Real-time Hyperparameter Modification** | Breaks training stability, complex to implement | Allow config before training starts, restart to change |
| **Distributed Training** | Massive complexity for marginal benefit at this scale | Single-process training is sufficient for Tetris |
| **Multiple Algorithm Support** | DQN/PPO/A3C etc. adds huge complexity | Pick one algorithm (DQN), do it well |
| **Custom Reward Function Editor** | Edge case feature, complex UI | Hardcode sensible reward (lines^2, game over penalty) |
| **Cloud Training Integration** | Infrastructure complexity, cost | Local training only for v1 |
| **Replay Recording/Playback** | Storage complexity, marginal value | Live visualization is sufficient |
| **A/B Testing Framework** | Over-engineering for personal tool | Manual model comparison is sufficient |
| **Mobile/Responsive Design** | Desktop ML training workflow | Desktop-first, tablet acceptable |
| **Multi-Game Support** | Scope explosion | Tetris only, architecture can be extensible |
| **Collaborative/Multi-User** | Authentication, permissions, sync complexity | Single-user local application |
| **Auto-Hyperparameter Tuning** | Complex to implement well (Optuna/Ray Tune level) | Manual configuration with sensible defaults |
| **Model Interpretability/Explainability** | Research-level feature, complex | Simple metrics are sufficient for learning tool |

## Feature Dependencies

```
Core Training Loop
    |
    +-- Training Progress Display (requires training loop metrics)
    |
    +-- Reward Chart (requires episode reward logging)
    |
    +-- Live Game Visualization (requires game state access)
    |
    +-- Model Save/Load (requires serializable model)
            |
            +-- Best Model Auto-Save (requires score tracking + save)
            |
            +-- Model Comparison (requires multiple saved models)
                    |
                    +-- Side-by-Side Playback (requires model loading + dual rendering)
                    |
                    +-- Performance Leaderboard (requires model metadata storage)

Headless/Visual Toggle
    |
    +-- Training Speed Control (only relevant in visual mode)
    |
    +-- Split View (requires visual mode)

Pause/Resume Training
    |
    +-- Training State Persistence (enables resume across sessions)
```

### Implementation Order Recommendation

**Phase 1: Core Training (Table Stakes)**
1. Training loop with basic metrics
2. Simple game visualization (can be console or basic canvas)
3. Episode reward logging
4. Model save/load

**Phase 2: Web Visualization (Table Stakes + Core Differentiator)**
1. Web UI with game board display
2. Reward chart (line chart with moving average)
3. Metrics panel (episode, score, lines cleared)
4. Start/Stop controls

**Phase 3: Training Controls (Differentiators)**
1. Headless/Visual toggle
2. Pause/Resume
3. Training speed control
4. Target goal setting

**Phase 4: Model Management (Differentiators)**
1. Multiple model slots
2. Best model auto-save
3. Performance leaderboard
4. Demo mode

## MVP Feature Set

For a functional MVP that delivers core value:

**Must Have:**
- Start training from web UI
- Watch game board update during training
- See reward chart updating in real-time
- Stop training
- Save trained model
- Load and demo a trained model

**Should Have:**
- Headless/visual toggle (massive UX improvement)
- Best score tracking
- Lines cleared metric
- Episode count display

**Nice to Have:**
- Pause/resume
- Training speed slider
- Multiple model slots

## Sources

**ML Training Visualization:**
- [Visualizing Training Statistics in Reinforcement Learning](https://codesignal.com/learn/courses/game-on-integrating-rl-agents-with-environments/lessons/visualizing-training-statistics-in-reinforcement-learning)
- [Neptune: RL Agents Training and Debug](https://neptune.ai/blog/reinforcement-learning-agents-training-debug)
- [RLInspect: Interactive Visual Approach](https://arxiv.org/html/2411.08392v1)

**Experiment Tracking Tools:**
- [Best Tools for ML Experiment Tracking](https://neptune.ai/blog/best-ml-experiment-tracking-tools)
- [TensorBoard Alternatives](https://neptune.ai/blog/the-best-tensorboard-alternatives)

**Tetris AI Implementations:**
- [Tetris AI (nuno-faria)](https://github.com/nuno-faria/tetris-ai) - TensorBoard integration, replay memory, model saving
- [Tetris Deep Q-Learning PyTorch](https://github.com/uvipen/Tetris-deep-Q-learning-pytorch) - Basic train/test workflow
- [Tim Hanewich Tetris RL](https://timhanewich.medium.com/how-i-trained-a-neural-network-to-play-tetris-using-reinforcement-learning-ecfa529c767a) - State features, scoring approach

**Dashboard/UI Patterns:**
- [Streamlit Real-Time Dashboard](https://medium.com/@hadiyolworld007/i-built-a-streamlit-dashboard-that-updates-in-real-time-heres-how-2b0c54b0a266)
- [Evidently + Streamlit ML Dashboard Tutorial](https://www.evidentlyai.com/blog/ml-model-monitoring-dashboard-tutorial)

**Model Checkpoint Best Practices:**
- [ML Design Pattern: Checkpoints](https://towardsdatascience.com/ml-design-pattern-2-checkpoints-e6ca25a4c5fe)
- [PyTorch Lightning Checkpointing](https://lightning.ai/docs/pytorch/stable/common/checkpointing_basic.html)

**RL Training Controls:**
- [Isaac Gym: Headless Training](https://github.com/isaac-sim/IsaacGymEnvs) - 'v' key toggle for viewer
- [MATLAB RL Toolbox Pause/Resume](https://www.mathworks.com/matlabcentral/answers/1673039-setting-up-a-pause-resume-reinforcement-learning-training-using-rl-toolbox)

**Training Notifications:**
- [MLNotify](https://github.com/aporia-ai/mlnotify) - Training completion notifications
- [Azure ML + Logic Apps Notifications](https://medium.com/geekculture/notifications-on-azure-machine-learning-pipelines-with-logic-apps-5d5df11d3126)
