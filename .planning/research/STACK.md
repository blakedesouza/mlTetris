# Stack Research: ML Tetris Trainer

**Project:** ML Tetris Trainer
**Researched:** 2026-01-19
**Overall Confidence:** HIGH

---

## Executive Summary

The 2025 Python ML game trainer stack has matured significantly. For an RL Tetris trainer with web visualization, the winning combination is **Stable Baselines3 + Gymnasium + FastAPI + WebSockets + Plotly/HTMX**. This stack balances ease of use, documentation quality, community support, and performance.

Key insight: A dedicated Tetris Gymnasium environment already exists (tetris-gymnasium), eliminating the need to build game logic from scratch. This dramatically reduces project scope.

---

## Reinforcement Learning

### Recommended: Stable Baselines3

| Attribute | Value |
|-----------|-------|
| **Library** | stable-baselines3 |
| **Version** | 2.7.1 (December 2025) |
| **Confidence** | HIGH (verified via PyPI) |
| **License** | MIT |

**Why SB3:**
- Best-in-class documentation and examples
- Clean, production-ready implementations of DQN, PPO, A2C, SAC
- Native Gymnasium support (no shims needed)
- Built-in TensorBoard and W&B logging
- Active maintenance with regular releases
- Ideal learning curve for this project scope

**Algorithms for Tetris:**
- **DQN**: Best for discrete action spaces like Tetris. Sample efficient due to replay buffer.
- **PPO**: Faster wall-clock training, good baseline. More stable than DQN but less sample efficient.
- **Recommendation**: Start with DQN for sample efficiency, add PPO for comparison.

```bash
pip install stable-baselines3[extra]==2.7.1
```

### Alternative Considered: SBX (Stable Baselines Jax)

| Attribute | Value |
|-----------|-------|
| **Library** | sbx-rl |
| **Version** | 0.25.0 (December 2025) |
| **Confidence** | MEDIUM |

**Why NOT for this project:**
- Up to 20x faster than SB3 PyTorch version
- BUT: Proof-of-concept status, fewer features
- JAX adds complexity (different ecosystem)
- Better for: researchers needing raw speed

**Future consideration:** If training time becomes a bottleneck, SBX is a drop-in replacement with identical API.

### Not Recommended

| Library | Why Not |
|---------|---------|
| **RLlib** | Overkill for single-machine training. Better for distributed/production at scale. |
| **CleanRL** | Not designed for import - single-file implementations for research/learning. |
| **TF-Agents** | TensorFlow ecosystem; SB3 is PyTorch-native and more actively maintained. |
| **TorchRL** | Still maturing; SB3 has better documentation and community. |

---

## Tetris Game Engine

### Recommended: tetris-gymnasium

| Attribute | Value |
|-----------|-------|
| **Library** | tetris-gymnasium |
| **Version** | 0.3.0 (March 2025) |
| **Confidence** | HIGH (verified via PyPI) |
| **License** | MIT |

**Why this library:**
- Pre-built Gymnasium-compatible Tetris environment
- Highly configurable (board size, piece types, rewards)
- Maintained and documented
- Saves weeks of implementation time
- Standard Tetris mechanics already implemented

**Usage:**
```python
import gymnasium as gym
import tetris_gymnasium

env = gym.make("tetris_gymnasium/Tetris")
obs, info = env.reset()
```

**Customization available:**
- Board dimensions
- Piece sets
- Reward functions (line clears, height penalties)
- Rendering modes (rgb_array for ML, human for visualization)

```bash
pip install tetris-gymnasium==0.3.0
```

### Alternative: Custom Implementation

**When to consider:**
- Need non-standard Tetris mechanics
- Educational value of building from scratch
- Specific reward shaping not supported

**If building custom:**
- Subclass `gymnasium.Env`
- Implement `step()`, `reset()`, `render()`
- Define observation and action spaces
- Register with `gymnasium.register()`

**Recommendation:** Use tetris-gymnasium. Building a correct, efficient Tetris implementation is non-trivial (rotation systems, collision detection, line clearing). The existing library handles this.

---

## Core Framework

### Recommended: Gymnasium

| Attribute | Value |
|-----------|-------|
| **Library** | gymnasium |
| **Version** | 1.2.3 (December 2025) |
| **Confidence** | HIGH (verified via PyPI) |
| **Requires** | Python >=3.10 |

**Why Gymnasium:**
- Official successor to OpenAI Gym (same team)
- De-facto standard for RL environments
- Required by SB3 and tetris-gymnasium
- Better API than legacy Gym (5-tuple returns, seed handling)

```bash
pip install gymnasium==1.2.3
```

### Recommended: PyTorch

| Attribute | Value |
|-----------|-------|
| **Library** | torch |
| **Version** | 2.9.1 (November 2025) |
| **Confidence** | HIGH (verified via PyPI) |
| **Requires** | Python >=3.10 |

**Why PyTorch:**
- SB3 is built on PyTorch
- Dominant framework in RL research
- Better debugging than TensorFlow (eager execution by default)
- Excellent CUDA support

```bash
pip install torch==2.9.1
```

---

## Web Visualization

### Backend: FastAPI + WebSockets

| Attribute | Value |
|-----------|-------|
| **Library** | fastapi |
| **Version** | 0.128.0 (December 2025) |
| **Confidence** | HIGH (verified via PyPI) |

**Why FastAPI:**
- Native async/await support (essential for real-time)
- Built-in WebSocket support
- Modern Python type hints
- Excellent performance (on par with Node.js/Go)
- Clean integration with Pydantic for data validation

**WebSocket pattern for real-time game visualization:**
```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/game")
async def game_stream(websocket: WebSocket):
    await websocket.accept()
    while True:
        game_state = get_current_state()
        await websocket.send_json(game_state)
        await asyncio.sleep(1/60)  # 60 FPS
```

```bash
pip install "fastapi[standard]==0.128.0"
```

### Frontend Option A: HTMX (Recommended for Simplicity)

| Attribute | Value |
|-----------|-------|
| **Library** | htmx |
| **Version** | 2.x (CDN) |
| **Confidence** | HIGH |

**Why HTMX:**
- No JavaScript framework needed (Python-only codebase)
- 14KB gzipped (vs 200KB+ for React)
- Server-side rendering with Jinja2 templates
- WebSocket support via `hx-ws`
- Perfect for Python developers who want to avoid frontend complexity

**When to use:**
- Prioritizing development speed
- Avoiding frontend build tooling
- Python-centric team

**Example pattern:**
```html
<div hx-ws="connect:/ws/game">
  <div id="game-board" hx-ws="message:updateBoard"></div>
</div>
```

### Frontend Option B: React (Recommended for Polish)

| Attribute | Value |
|-----------|-------|
| **Why Consider** | Richer interactivity, better canvas rendering |

**When to use:**
- Need smooth canvas-based game rendering
- Want component-based UI architecture
- Planning to extend to a production app

**Trade-off:** Adds ~1-2 weeks development time for frontend setup.

### Charting: Plotly

| Attribute | Value |
|-----------|-------|
| **Library** | plotly |
| **Version** | 6.5.2 (January 2026) |
| **Confidence** | HIGH (verified via GitHub releases) |

**Why Plotly:**
- Native Python integration
- Interactive charts out of the box
- Works with both HTMX (server-side) and React (client-side)
- Good for training metrics (loss curves, reward over time)

**Alternative considered:** Chart.js
- Better real-time performance with throttling
- BUT: Requires more JavaScript; Plotly is Python-native

```bash
pip install plotly==6.5.2
```

### Real-Time Game Rendering

**For canvas-based game display:**

**Option A: Server-side rendering (simpler)**
- Render game state as HTML/SVG on server
- Send via WebSocket as HTML fragments
- HTMX swaps into DOM

**Option B: Client-side canvas (smoother)**
- Send game state as JSON via WebSocket
- JavaScript/React renders to `<canvas>`
- Better for 60fps smooth rendering

**Recommendation:** Start with Option A (HTMX/server-side). Upgrade to Option B if smoothness is critical.

---

## Experiment Tracking and Logging

### Recommended: Weights & Biases

| Attribute | Value |
|-----------|-------|
| **Library** | wandb |
| **Version** | 0.24.0 (January 2026) |
| **Confidence** | HIGH (verified via PyPI) |

**Why W&B:**
- Built-in SB3 integration via `WandbCallback`
- Automatic hyperparameter logging
- Experiment comparison across runs
- Model artifact versioning
- Free tier sufficient for this project

**Usage with SB3:**
```python
from stable_baselines3 import DQN
from wandb.integration.sb3 import WandbCallback
import wandb

run = wandb.init(project="ml-tetris", sync_tensorboard=True)
model = DQN("MlpPolicy", env, verbose=1, tensorboard_log=f"runs/{run.id}")
model.learn(total_timesteps=100000, callback=WandbCallback())
```

```bash
pip install wandb==0.24.0
```

### Alternative: TensorBoard (Local-Only)

| Attribute | Value |
|-----------|-------|
| **Library** | tensorboard |
| **When to Use** | Local development, no cloud dependency |

**Why NOT as primary:**
- Gets cluttered with many experiments
- No built-in experiment comparison
- No team collaboration features

**Recommendation:** Use both. SB3 logs to TensorBoard by default; W&B can sync TensorBoard logs. Use TensorBoard for quick local checks, W&B for experiment tracking.

---

## Model Persistence

### Recommended: Native SB3 + Manual Checkpoints

**SB3 Built-in:**
```python
# Save
model.save("tetris_dqn_v1")

# Load
model = DQN.load("tetris_dqn_v1", env=env)
```

**Full Checkpoint (for resume training):**
```python
import torch

checkpoint = {
    'model_state_dict': model.policy.state_dict(),
    'optimizer_state_dict': model.policy.optimizer.state_dict(),
    'timesteps': model.num_timesteps,
    'replay_buffer': model.replay_buffer,  # For DQN
    'env_stats': env.get_wrapper_attr('obs_rms') if hasattr(env, 'obs_rms') else None,
}
torch.save(checkpoint, 'checkpoint.pth')
```

**Best practices:**
1. Save every N timesteps (e.g., every 10K)
2. Keep last K checkpoints (rolling window)
3. Save "best" model based on eval reward
4. Include metadata (hyperparameters, git commit, timestamp)

**Storage format:**
- `.zip` for SB3 models (contains policy + hyperparams)
- `.pth` for PyTorch checkpoints (more control)
- JSON sidecar for metadata

---

## Summary: Final Recommended Stack

### Core Dependencies

```bash
# Core ML
pip install stable-baselines3[extra]==2.7.1
pip install torch==2.9.1
pip install gymnasium==1.2.3
pip install tetris-gymnasium==0.3.0

# Web
pip install "fastapi[standard]==0.128.0"
pip install uvicorn[standard]
pip install jinja2
pip install python-multipart

# Visualization
pip install plotly==6.5.2
pip install wandb==0.24.0

# Dev
pip install pytest
pip install black
pip install ruff
```

### Python Version

**Recommended:** Python 3.11 or 3.12
- 3.10 minimum (required by gymnasium, tetris-gymnasium)
- 3.11/3.12 preferred for performance improvements
- 3.13 works but newer, less battle-tested

### Architecture Overview

```
mlTetris/
  src/
    environment/        # Tetris env wrapper/customization
    training/           # SB3 training loops
    web/                # FastAPI app
      api/              # REST endpoints
      ws/               # WebSocket handlers
      templates/        # Jinja2/HTMX templates
    models/             # Model management (save/load/compare)
  checkpoints/          # Saved models
  logs/                 # TensorBoard logs
  tests/
```

### Technology Decision Matrix

| Component | Choice | Confidence | Rationale |
|-----------|--------|------------|-----------|
| RL Library | Stable Baselines3 2.7.1 | HIGH | Best docs, production-ready, perfect fit |
| Environment | tetris-gymnasium 0.3.0 | HIGH | Pre-built, eliminates game logic work |
| Framework | Gymnasium 1.2.3 | HIGH | Industry standard, required by SB3 |
| Deep Learning | PyTorch 2.9.1 | HIGH | SB3 backend, excellent debugging |
| Web Framework | FastAPI 0.128.0 | HIGH | Async, WebSocket native, modern |
| Frontend | HTMX + Jinja2 | MEDIUM | Simplest path, Python-only |
| Charting | Plotly 6.5.2 | HIGH | Python-native, interactive |
| Tracking | W&B 0.24.0 | HIGH | SB3 integration, free tier |

### What NOT to Use

| Technology | Why Not |
|------------|---------|
| OpenAI Gym | Deprecated, use Gymnasium |
| TensorFlow | PyTorch ecosystem is SB3 native |
| RLlib | Overkill for single-machine |
| Flask | FastAPI is async-native, better for WebSockets |
| Django | Too heavy for this use case |
| Custom Tetris | tetris-gymnasium exists and works |

---

## Sources

### Primary (HIGH confidence)
- [Stable Baselines3 Documentation](https://stable-baselines3.readthedocs.io/)
- [Gymnasium Documentation](https://gymnasium.farama.org/)
- [Tetris Gymnasium](https://github.com/Max-We/Tetris-Gymnasium)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PyPI Package Pages](https://pypi.org/) (version verification)

### Secondary (MEDIUM confidence)
- [SB3 vs CleanRL vs RLlib Comparison](https://apxml.com/courses/advanced-reinforcement-learning/chapter-8-rl-implementation-optimization/rl-frameworks-libraries)
- [W&B vs TensorBoard Comparison](https://docs.wandb.ai/support/different_tensorboard/)
- [FastAPI + HTMX Tutorial](https://testdriven.io/blog/fastapi-htmx/)
- [Real-Time Dashboards with FastAPI and HTMX](https://medium.com/codex/building-real-time-dashboards-with-fastapi-and-htmx-01ea458673cb)

### Ecosystem Discovery
- [Open RL Benchmark](https://github.com/openrlbenchmark/openrlbenchmark)
- [Neptune.ai Comparisons](https://neptune.ai/blog/the-best-tensorboard-alternatives)
- [SBX (Stable Baselines Jax)](https://github.com/araffin/sbx)
