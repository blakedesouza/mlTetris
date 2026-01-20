# Architecture Research

**Project:** ML Tetris Trainer
**Researched:** 2026-01-19
**Confidence:** HIGH (based on established patterns from successful implementations)

## Executive Summary

An ML Tetris trainer requires five distinct components that communicate through well-defined interfaces. The architecture follows an event-driven pattern where the training loop orchestrates all other components, with optional real-time visualization through WebSocket connections.

The key architectural insight: **decouple the Tetris game engine from the RL training loop**. This enables headless training at maximum speed while allowing visualization to attach/detach without affecting training.

---

## Components

### 1. Tetris Game Engine (Environment)

**Responsibility:** Pure game logic, state management, move validation

**Boundary:** Implements Gymnasium `Env` interface - knows nothing about ML, neural networks, or visualization

**Key Methods:**
```python
class TetrisEnv(gymnasium.Env):
    def __init__(self, config):
        self.observation_space = ...  # Board state representation
        self.action_space = ...       # Available moves

    def reset(self, seed=None) -> tuple[observation, info]:
        """Start new game, return initial state"""

    def step(self, action) -> tuple[observation, reward, terminated, truncated, info]:
        """Execute action, return results"""

    def render(self) -> Optional[np.ndarray]:
        """Return visual representation (optional)"""
```

**State Representation Options:**

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| Raw board (20x10 grid) | Complete information | Slow to train, large state space | Avoid |
| Feature vector | Fast training, proven effective | Requires feature engineering | **Use this** |
| Hybrid (board + features) | Best of both | More complex | Consider for advanced |

**Recommended Feature Vector (based on Dellacherie's algorithm):**
- Lines cleared (this move)
- Total holes count
- Bumpiness (height variation between columns)
- Total height (sum of column heights)
- Max/min column heights
- Current piece type
- Next piece type (if known)

**Sources:**
- [nuno-faria/tetris-ai](https://github.com/nuno-faria/tetris-ai) - Proven implementation
- [Gymnasium Custom Environment Guide](https://gymnasium.farama.org/introduction/create_custom_env/)

---

### 2. RL Agent (Model + Training Logic)

**Responsibility:** Neural network, Q-learning, experience replay, action selection

**Boundary:** Receives observations from environment, outputs actions. Knows nothing about Tetris rules.

**Architecture:**

```python
class DQNAgent:
    def __init__(self, state_size, action_size, config):
        self.model = self._build_network()
        self.target_model = self._build_network()  # For stable training
        self.memory = ReplayBuffer(config.memory_size)
        self.epsilon = config.epsilon_start

    def select_action(self, state) -> action:
        """Epsilon-greedy action selection"""

    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""

    def train(self, batch_size) -> float:
        """Sample from memory, update network, return loss"""

    def save(self, path) / load(self, path):
        """Checkpoint management"""
```

**Network Architecture (proven effective for Tetris):**
```
Input (feature_size) -> Dense(32, ReLU) -> Dense(32, ReLU) -> Output(1, Linear)
```

Note: Output is 1 because we evaluate board states, not actions directly. The agent evaluates all possible final positions and picks the best one.

**Key Hyperparameters:**
| Parameter | Recommended Value | Notes |
|-----------|-------------------|-------|
| Hidden layers | 2 x 32 neurons | Larger not necessary for feature-based state |
| Discount (gamma) | 0.95-0.99 | Higher = considers future rewards |
| Replay memory | 20,000-30,000 | Balance between memory and diversity |
| Batch size | 512 | Larger batches stabilize training |
| Epsilon decay | Linear over 75% of training | Start 1.0, end 0.0 |
| Learning rate | 0.001 (Adam) | Standard starting point |

**Sources:**
- [ChesterHuynh/tetrisAI](https://github.com/ChesterHuynh/tetrisAI)
- [Stable-Baselines3 DQN](https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html)

---

### 3. Training Loop (Orchestrator)

**Responsibility:** Coordinates training episodes, manages mode switching, emits events

**Boundary:** Connects agent to environment, controls training flow, but doesn't implement game logic or neural network details

**Architecture:**

```python
class TrainingLoop:
    def __init__(self, env, agent, config):
        self.env = env
        self.agent = agent
        self.mode = "headless"  # or "visual"
        self.callbacks = []

    def train(self, target_episodes: int):
        """Main training loop"""
        for episode in range(target_episodes):
            state = self.env.reset()
            while not done:
                action = self.agent.select_action(state)
                next_state, reward, done, truncated, info = self.env.step(action)
                self.agent.remember(state, action, reward, next_state, done)
                state = next_state
                self._emit("step", step_data)  # For visualization

            loss = self.agent.train(batch_size)
            self._emit("episode_complete", episode_data)

            if episode % checkpoint_interval == 0:
                self.agent.save(checkpoint_path)

    def set_mode(self, mode: str):
        """Switch between headless and visual modes"""

    def pause(self) / resume(self):
        """Training control"""
```

**Mode Switching Pattern:**
```
Headless Mode:
- render_mode = None
- No delays between steps
- Maximum training speed

Visual Mode:
- render_mode = "rgb_array" or "human"
- Configurable step delay (e.g., 50ms)
- State emitted via WebSocket
```

**Sources:**
- [Gymnasium render modes](https://gymnasium.farama.org/introduction/basic_usage/)

---

### 4. Web Interface (Visualization Layer)

**Responsibility:** Display live gameplay, show training metrics, provide controls

**Boundary:** Receives data via WebSocket, sends control commands. Never accesses training internals directly.

**Architecture:**

```
Backend (Flask + Flask-SocketIO):
├── REST endpoints for control (start, stop, save, load)
├── WebSocket events for real-time data
│   ├── board_state (current game board)
│   ├── metrics (loss, reward, epsilon)
│   └── episode_complete (summary stats)
└── Static file serving for frontend

Frontend (HTML/JS or React):
├── Game canvas (renders board state)
├── Metrics charts (Chart.js, Plotly)
├── Controls panel (buttons, sliders)
└── Model selector (load/compare)
```

**WebSocket Events:**

| Event | Direction | Payload |
|-------|-----------|---------|
| `board_update` | Server -> Client | `{board: 2D array, piece: {...}, score: int}` |
| `metrics` | Server -> Client | `{episode: int, reward: float, loss: float, lines: int}` |
| `training_status` | Server -> Client | `{state: "running"/"paused", mode: "headless"/"visual"}` |
| `set_mode` | Client -> Server | `{mode: "headless"/"visual"}` |
| `save_model` | Client -> Server | `{name: string}` |
| `load_model` | Client -> Server | `{name: string}` |

**Sources:**
- [Flask-SocketIO for real-time dashboards](https://codezup.com/how-to-build-real-time-dashboards-with-flask-and-socketio/)
- [Building Real-time Dashboard with Flask](https://testdriven.io/blog/flask-svelte/)

---

### 5. Model Manager (Persistence Layer)

**Responsibility:** Save/load checkpoints, manage model versions, enable comparison

**Boundary:** File I/O and metadata management. Knows nothing about training or game state.

**Architecture:**

```python
class ModelManager:
    def __init__(self, models_dir: Path):
        self.models_dir = models_dir

    def save_checkpoint(self, agent, metadata: dict) -> str:
        """Save model state + metadata, return checkpoint ID"""
        checkpoint = {
            'model_state_dict': agent.model.state_dict(),
            'optimizer_state_dict': agent.optimizer.state_dict(),
            'episode': metadata['episode'],
            'epsilon': agent.epsilon,
            'config': metadata['config'],
            'timestamp': datetime.now().isoformat(),
            'metrics': metadata['metrics']  # Best score, avg reward, etc.
        }
        torch.save(checkpoint, path)

    def load_checkpoint(self, checkpoint_id: str) -> dict:
        """Load checkpoint data"""

    def list_checkpoints(self) -> list[CheckpointInfo]:
        """Return available checkpoints with metadata"""

    def compare_models(self, ids: list[str]) -> ComparisonResult:
        """Load and compare multiple model metrics"""
```

**Checkpoint Structure:**
```
models/
├── checkpoint_20260119_143022.tar
├── checkpoint_20260119_150000.tar
├── best_model.tar  (symlink to best performer)
└── metadata.json   (index of all checkpoints)
```

**What to Save:**
- Model weights (state_dict)
- Optimizer state (for resume training)
- Training progress (episode, total steps)
- Hyperparameters used
- Performance metrics at save time
- Timestamp

**Sources:**
- [PyTorch Saving and Loading](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)
- [PyTorch Lightning Checkpointing](https://lightning.ai/docs/pytorch/stable/common/checkpointing_basic.html)

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Training Loop                                   │
│  ┌──────────┐     action     ┌──────────┐     state/reward    ┌──────────┐  │
│  │          │ ──────────────>│          │ ──────────────────> │          │  │
│  │  Agent   │                │ Tetris   │                     │  Agent   │  │
│  │ (select) │ <───────────── │   Env    │                     │ (learn)  │  │
│  └──────────┘   all states   └──────────┘                     └──────────┘  │
│       │              │                                              │        │
│       │              │ board state (if visual mode)                 │        │
│       │              v                                              │        │
│       │        ┌──────────┐                                         │        │
│       │        │ Renderer │                                         │        │
│       │        └────┬─────┘                                         │        │
└───────│─────────────│───────────────────────────────────────────────│────────┘
        │             │                                               │
        │ metrics     │ frame                              save/load  │
        v             v                                               v
   ┌─────────────────────────────────────────────────────────────────────────┐
   │                          WebSocket Bridge                                │
   │                     (Flask-SocketIO server)                              │
   └───────────────────────────────┬─────────────────────────────────────────┘
                                   │
                          events   │   commands
                                   v
   ┌─────────────────────────────────────────────────────────────────────────┐
   │                          Web Frontend                                    │
   │  ┌────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
   │  │  Tetris    │  │   Metrics    │  │   Controls   │  │    Model      │  │
   │  │  Display   │  │   Charts     │  │    Panel     │  │   Selector    │  │
   │  └────────────┘  └──────────────┘  └──────────────┘  └───────────────┘  │
   └─────────────────────────────────────────────────────────────────────────┘
```

### Detailed Flow: Training Episode

1. **Training Loop** calls `env.reset()` -> Environment returns initial state
2. **Training Loop** sends state to **Agent** -> Agent evaluates all possible moves
3. **Agent** returns best action -> **Training Loop** calls `env.step(action)`
4. **Environment** executes move, calculates reward -> Returns (state, reward, done)
5. **Agent** stores experience in replay buffer
6. If visual mode: **Training Loop** emits board state via WebSocket
7. Repeat steps 2-6 until episode ends
8. **Agent** trains on batch from replay buffer
9. **Training Loop** emits episode metrics
10. Every N episodes: **Model Manager** saves checkpoint

### Detailed Flow: Mode Switch

1. User clicks "Visual Mode" in web UI
2. Frontend sends `set_mode` event via WebSocket
3. Backend receives, calls `training_loop.set_mode("visual")`
4. Training loop sets `self.mode = "visual"` and `env.render_mode = "rgb_array"`
5. Each step now emits board state
6. No training interruption - just adds visualization overhead

---

## Build Order

Based on component dependencies, here's the recommended implementation sequence:

### Phase 1: Core Engine (Foundation)

**Build first:** Tetris Environment

Why: Everything depends on this. Can be tested independently with random actions.

Deliverables:
- `TetrisEnv` class implementing Gymnasium interface
- Board logic (piece movement, rotation, collision, line clearing)
- Feature-based state representation
- Reward function
- Unit tests for game mechanics

**Validation:** Run 1000 random episodes, verify no crashes, correct line clearing

---

### Phase 2: Learning System

**Build second:** RL Agent + Training Loop

Why: Needs environment. Can train headless without visualization.

Deliverables:
- `DQNAgent` class with neural network
- Replay buffer
- Training loop with episode management
- Console output for progress
- Basic checkpointing

**Validation:** Train for 500 episodes, observe reward increasing

---

### Phase 3: Persistence

**Build third:** Model Manager

Why: Needs agent to exist. Enables save/resume.

Deliverables:
- Checkpoint save/load
- Metadata tracking
- Resume from checkpoint

**Validation:** Train 100 episodes, save, load, train 100 more, verify continuity

---

### Phase 4: Visualization

**Build fourth:** Web Interface + WebSocket Bridge

Why: Needs all other components. Pure addition, doesn't change training.

Deliverables:
- Flask-SocketIO backend
- WebSocket event handlers
- Tetris board renderer (canvas)
- Metrics charts
- Control panel

**Validation:** Watch agent play in browser while training

---

### Phase 5: Polish

**Build last:** Advanced features

- Model comparison UI
- Hyperparameter tuning interface
- Export to standalone player
- Performance optimization

---

## Integration Points

### Environment <-> Agent

**Interface:** Gymnasium standard

```python
# Agent sees:
observation: np.ndarray  # Feature vector or board state
action_space: gymnasium.spaces.Discrete  # Available actions

# Agent provides:
action: int  # Index into action space
```

**Key Decision: Action Representation**

| Approach | Actions | Complexity | Speed |
|----------|---------|------------|-------|
| Primitive (left, right, rotate, drop) | 4-6 | Agent must plan sequence | Slow |
| Meta (final position + rotation) | 40 | Agent picks destination | **Fast, recommended** |

Recommendation: **Use meta-actions.** Agent evaluates all 40 possible placements, picks best. Simpler learning, faster training.

---

### Training Loop <-> Web Backend

**Interface:** Event emitter pattern

```python
# Training loop emits:
training_loop.on("step", callback)        # Every game step
training_loop.on("episode", callback)     # Episode complete
training_loop.on("checkpoint", callback)  # Model saved

# Web backend calls:
training_loop.set_mode(mode)
training_loop.pause()
training_loop.resume()
training_loop.get_status()
```

---

### Web Backend <-> Frontend

**Interface:** WebSocket (Socket.IO)

```javascript
// Frontend receives:
socket.on('board_update', (data) => { /* render board */ });
socket.on('metrics', (data) => { /* update charts */ });
socket.on('status', (data) => { /* update UI state */ });

// Frontend sends:
socket.emit('set_mode', { mode: 'visual' });
socket.emit('save_model', { name: 'my_model' });
socket.emit('load_model', { name: 'checkpoint_123' });
socket.emit('set_speed', { delay_ms: 100 });
```

---

## Threading Considerations

**Challenge:** Training is CPU-intensive, web server needs to remain responsive

**Recommended Pattern:**

```
Main Thread:
├── Flask-SocketIO server
└── Event loop for WebSocket

Background Thread:
└── Training loop
    ├── Runs continuously
    ├── Emits events to queue
    └── Checks command queue for mode changes

Queue Pattern:
├── Event queue (training -> web): Board updates, metrics
└── Command queue (web -> training): Mode changes, save/load
```

**Implementation:**
```python
import threading
import queue

class TrainingRunner:
    def __init__(self, training_loop, socketio):
        self.training_loop = training_loop
        self.socketio = socketio
        self.event_queue = queue.Queue()
        self.command_queue = queue.Queue()
        self.running = False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        while self.running:
            # Check for commands
            try:
                cmd = self.command_queue.get_nowait()
                self._handle_command(cmd)
            except queue.Empty:
                pass

            # Run one training step
            event = self.training_loop.step()
            self.event_queue.put(event)
```

---

## Key Architectural Decisions

### 1. Feature-based State vs Raw Board

**Decision:** Use feature-based state representation

**Rationale:**
- Proven effective (800,000+ point games achieved)
- Faster training (smaller neural network)
- Interpretable (can debug what agent "sees")
- Raw board requires CNN, much slower to converge

### 2. Custom DQN vs Stable-Baselines3

**Decision:** Start with custom DQN, consider SB3 later

**Rationale:**
- Custom gives full control and understanding
- Tetris state evaluation is non-standard (evaluate positions, not actions)
- SB3 useful for comparison or trying PPO later
- Educational value in building from scratch

### 3. Flask-SocketIO vs FastAPI WebSockets

**Decision:** Flask-SocketIO

**Rationale:**
- Simpler setup
- Socket.IO client well-supported in browsers
- Good enough for single-user dashboard
- FastAPI better for production API, overkill here

### 4. TensorBoard vs Custom Charts

**Decision:** Custom charts in web UI + optional TensorBoard

**Rationale:**
- Custom charts integrated into the product experience
- TensorBoard useful for detailed debugging
- Use both: custom for "watching AI learn", TensorBoard for deep analysis

---

## Scalability Considerations

| Concern | At 1 User | At 10 Users | Recommendation |
|---------|-----------|-------------|----------------|
| Training load | Single thread | N/A (training is single-user) | Not a concern |
| WebSocket connections | Single | Need scaling | Use Redis pub/sub if needed |
| Model storage | Local files | Need versioning | Stay with local for MVP |

**For MVP:** Single user, local training. Scalability not a concern.

---

## Sources

**Gymnasium/Environment:**
- [Gymnasium Custom Environment Documentation](https://gymnasium.farama.org/introduction/create_custom_env/)
- [Gymnasium Basic Usage](https://gymnasium.farama.org/introduction/basic_usage/)

**Tetris AI Implementations:**
- [nuno-faria/tetris-ai](https://github.com/nuno-faria/tetris-ai) - HIGH confidence reference
- [ChesterHuynh/tetrisAI](https://github.com/ChesterHuynh/tetrisAI)
- [jaybutera/tetrisRL](https://github.com/jaybutera/tetrisRL)
- [Stanford CS231n Tetris Report](https://cs231n.stanford.edu/reports/2016/pdfs/121_Report.pdf)

**RL Frameworks:**
- [Stable-Baselines3 Documentation](https://stable-baselines3.readthedocs.io/en/master/)
- [Stable-Baselines3 Callbacks](https://stable-baselines3.readthedocs.io/en/master/guide/callbacks.html)

**Checkpointing:**
- [PyTorch Saving and Loading Models](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html)
- [PyTorch Lightning Checkpointing](https://lightning.ai/docs/pytorch/stable/common/checkpointing_basic.html)

**Real-time Visualization:**
- [Flask-SocketIO Real-time Dashboards](https://codezup.com/how-to-build-real-time-dashboards-with-flask-and-socketio/)
- [Building Real-time Dashboard with Flask and Svelte](https://testdriven.io/blog/flask-svelte/)

**Experiment Tracking:**
- [W&B vs TensorBoard Comparison](https://docs.wandb.ai/support/different_tensorboard/)
- [Neptune TensorBoard Alternatives](https://neptune.ai/blog/the-best-tensorboard-alternatives)
