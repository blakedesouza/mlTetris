# Phase 2: Training Core - Research

**Researched:** 2026-01-20
**Domain:** DQN Training with Stable-Baselines3, Checkpoint Management, Headless Training
**Confidence:** HIGH

## Summary

Phase 2 delivers a working DQN agent using Stable-Baselines3 (SB3) that can train headlessly, save/load checkpoints, and resume training from saved state. The critical finding is that SB3 provides comprehensive checkpoint support, but **replay buffer and exploration schedule require special handling for true resume capability**.

Key discoveries:
1. SB3's `DQN.save()` preserves model weights, optimizer state, and algorithm parameters but NOT the replay buffer by default
2. For complete resume, must use `save_replay_buffer()` and `load_replay_buffer()` separately
3. The exploration schedule in DQN is tied to `total_timesteps` - when resuming, pass `reset_num_timesteps=False` but be aware the schedule recalculates based on the new `total_timesteps` argument
4. The (40, 13) observation shape from Phase 1 will be automatically flattened by SB3's `FlattenExtractor` to (520,) - this is correct behavior for `MlpPolicy`
5. DQN hyperparameters need Tetris-specific tuning - defaults from Nature paper are suboptimal for Tetris

**Primary recommendation:** Use SB3 DQN with custom hyperparameters tuned for Tetris, implement a `TrainingCheckpoint` wrapper that saves model + replay buffer + metadata (epsilon, timesteps) together, and use `CheckpointCallback` for periodic saves.

## Standard Stack

The established libraries/tools for this phase:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| stable-baselines3 | >=2.4.0 | DQN implementation | Industry standard, well-tested, saves/loads correctly |
| gymnasium | >=1.0.0 | Environment interface | Already used in Phase 1, required by SB3 |
| torch | (via SB3) | Neural network backend | SB3 dependency, PyTorch-based |
| numpy | >=1.24,<2.0 | Array operations | Already in project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tensorboard | (optional) | Training visualization | Monitor training progress, loss curves |
| tqdm | (via SB3) | Progress bars | Training progress display |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SB3 DQN | Custom DQN implementation | Custom gives full control but adds weeks of development, harder to debug |
| SB3 DQN | CleanRL DQN | CleanRL is single-file, less abstraction, but no save/load utilities |
| SB3 DQN | SB3 PPO | PPO is on-policy (no replay buffer), simpler resume but less sample efficient |

**Installation:**
```bash
pip install stable-baselines3>=2.4.0
# Note: torch is installed automatically as SB3 dependency
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  training/
    __init__.py
    agent.py            # DQN agent wrapper with checkpoint support
    config.py           # TrainingConfig dataclass
    callbacks.py        # Custom callbacks (checkpoint, early stopping by goal)
    checkpoint.py       # Checkpoint save/load utilities
  environment/          # From Phase 1
    ...
tests/
  training/
    test_agent.py       # Basic training works
    test_checkpoint.py  # Save/load/resume verification
    test_headless.py    # Headless mode confirmation
```

### Pattern 1: Training Agent Wrapper

**What:** Wrapper class around SB3 DQN that handles checkpoint complexity
**When to use:** Always - hides replay buffer save/load complexity from caller
**Example:**
```python
# Source: SB3 documentation + custom design
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import CheckpointCallback
from pathlib import Path
import json

class TetrisAgent:
    """DQN agent with full checkpoint support."""

    def __init__(self, env, config: TrainingConfig):
        self.env = env
        self.config = config
        self.model = DQN(
            "MlpPolicy",
            env,
            learning_rate=config.learning_rate,
            buffer_size=config.buffer_size,
            batch_size=config.batch_size,
            gamma=config.gamma,
            exploration_fraction=config.exploration_fraction,
            exploration_initial_eps=config.exploration_initial_eps,
            exploration_final_eps=config.exploration_final_eps,
            target_update_interval=config.target_update_interval,
            train_freq=config.train_freq,
            learning_starts=config.learning_starts,
            verbose=1,
        )
        self._total_timesteps_trained = 0

    def train(self, total_timesteps: int, callback=None):
        """Train for specified timesteps."""
        self.model.learn(
            total_timesteps=total_timesteps,
            callback=callback,
            reset_num_timesteps=False,  # Continue from previous
        )
        self._total_timesteps_trained += total_timesteps

    def save_checkpoint(self, path: str):
        """Save complete training state."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        # Save model (includes optimizer state)
        self.model.save(path / "model")

        # Save replay buffer separately
        self.model.save_replay_buffer(path / "replay_buffer")

        # Save metadata for resume
        metadata = {
            "total_timesteps_trained": self._total_timesteps_trained,
            "num_timesteps": self.model.num_timesteps,
            "config": self.config.to_dict(),
        }
        with open(path / "metadata.json", "w") as f:
            json.dump(metadata, f)

    @classmethod
    def load_checkpoint(cls, path: str, env):
        """Load complete training state."""
        path = Path(path)

        # Load metadata first
        with open(path / "metadata.json") as f:
            metadata = json.load(f)

        config = TrainingConfig.from_dict(metadata["config"])

        # Create agent with loaded model
        agent = cls.__new__(cls)
        agent.env = env
        agent.config = config
        agent.model = DQN.load(path / "model", env=env)
        agent._total_timesteps_trained = metadata["total_timesteps_trained"]

        # Load replay buffer
        agent.model.load_replay_buffer(path / "replay_buffer")

        return agent
```

### Pattern 2: Training Configuration

**What:** Dataclass containing all hyperparameters with Tetris-tuned defaults
**When to use:** Always - provides single source of truth for training params
**Example:**
```python
# Source: RL Zoo DQN hyperparameters + Tetris-specific tuning
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class TrainingConfig:
    """DQN training configuration with Tetris-tuned defaults."""

    # Core DQN parameters
    learning_rate: float = 1e-4          # Standard DQN default
    buffer_size: int = 100_000           # Smaller than default (1M) for Tetris
    batch_size: int = 64                 # Slightly larger than default (32)
    gamma: float = 0.99                  # Standard discount factor

    # Exploration schedule
    exploration_fraction: float = 0.2    # 20% of training for exploration decay
    exploration_initial_eps: float = 1.0
    exploration_final_eps: float = 0.05

    # Network updates
    target_update_interval: int = 1000   # Update target network every 1000 steps
    train_freq: int = 4                  # Train every 4 steps
    gradient_steps: int = 1              # One gradient step per train_freq
    learning_starts: int = 10_000        # Start learning after 10k steps

    # Training goal
    target_lines: Optional[int] = None   # Stop when goal reached (None = no goal)
    max_timesteps: int = 500_000         # Default max training steps

    # Network architecture (MlpPolicy)
    net_arch: tuple = (256, 256)         # Two hidden layers of 256 units

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d):
        return cls(**d)
```

### Pattern 3: Goal-Based Early Stopping Callback

**What:** Callback that stops training when target lines cleared is reached
**When to use:** When TRAIN-04 requires configurable goal
**Example:**
```python
# Source: SB3 callbacks documentation
from stable_baselines3.common.callbacks import BaseCallback

class GoalReachedCallback(BaseCallback):
    """Stop training when target lines cleared is achieved."""

    def __init__(self, target_lines: int, check_freq: int = 1000, verbose: int = 1):
        super().__init__(verbose)
        self.target_lines = target_lines
        self.check_freq = check_freq
        self.best_lines = 0

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq != 0:
            return True

        # Get episode info from logger
        if len(self.model.ep_info_buffer) > 0:
            # Assuming 'lines' is tracked in episode info
            recent_lines = [ep.get('lines', 0) for ep in self.model.ep_info_buffer]
            max_recent = max(recent_lines) if recent_lines else 0

            if max_recent > self.best_lines:
                self.best_lines = max_recent
                if self.verbose > 0:
                    print(f"New best lines: {self.best_lines}")

            if self.best_lines >= self.target_lines:
                if self.verbose > 0:
                    print(f"Goal reached: {self.best_lines} >= {self.target_lines}")
                return False  # Stop training

        return True
```

### Pattern 4: Headless Training Loop

**What:** Training without rendering for maximum speed
**When to use:** Always for actual training (TRAIN-07)
**Example:**
```python
# Source: SB3 examples
def train_headless(config: TrainingConfig, checkpoint_dir: str = "./checkpoints"):
    """Run headless training with periodic checkpoints."""
    from src.environment import make_env, EnvConfig

    # Create environment WITHOUT render_mode (headless)
    env_config = EnvConfig(render_mode=None)  # None = headless
    env = make_env(env_config)()

    # Create or load agent
    checkpoint_path = Path(checkpoint_dir) / "latest"
    if checkpoint_path.exists():
        agent = TetrisAgent.load_checkpoint(checkpoint_path, env)
        print(f"Resumed from checkpoint, {agent._total_timesteps_trained} steps trained")
    else:
        agent = TetrisAgent(env, config)

    # Setup callbacks
    callbacks = []

    # Checkpoint callback
    checkpoint_callback = CheckpointCallback(
        save_freq=10_000,
        save_path=checkpoint_dir,
        name_prefix="checkpoint",
        save_replay_buffer=True,  # Important!
    )
    callbacks.append(checkpoint_callback)

    # Goal callback (if target set)
    if config.target_lines:
        goal_callback = GoalReachedCallback(config.target_lines)
        callbacks.append(goal_callback)

    # Train
    agent.train(config.max_timesteps, callback=callbacks)

    # Save final checkpoint
    agent.save_checkpoint(checkpoint_dir / "final")

    return agent
```

### Anti-Patterns to Avoid
- **Creating DQN then calling model.load():** Always use `DQN.load()` class method - it properly restores optimizer state
- **Forgetting replay buffer on resume:** Training will work but agent "forgets" recent experiences
- **Using `reset_num_timesteps=True` on resume:** Resets exploration schedule, causing re-exploration
- **Setting learning_starts > buffer_size:** Agent never starts learning
- **Large buffer_size with limited RAM:** 1M buffer with complex observations can exhaust memory

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DQN algorithm | Custom neural net training loop | `stable_baselines3.DQN` | Handles target networks, experience replay, epsilon-greedy correctly |
| Replay buffer | Custom deque/list | SB3's ReplayBuffer | Handles sampling, storage efficiently, can be saved/loaded |
| Exploration schedule | Custom epsilon decay | SB3's `exploration_fraction` | Automatically handles schedule based on progress |
| Checkpoint saving | Custom pickling | `model.save()` + `save_replay_buffer()` | Handles PyTorch state dict, optimizer state correctly |
| Training progress | Custom logging | SB3's built-in logging + tensorboard | Episode rewards, losses tracked automatically |
| Environment validation | Manual testing | `check_env()` | Catches API issues before training |

**Key insight:** SB3 handles all DQN complexity. The only custom code needed is: (1) checkpoint wrapper that combines model + replay buffer, (2) goal-based callback, (3) training configuration.

## Common Pitfalls

### Pitfall 1: Exploration Schedule Reset on Resume
**What goes wrong:** After loading checkpoint, agent re-explores from epsilon=1.0
**Why it happens:** DQN's exploration schedule uses `total_timesteps` from `.learn()` call, not cumulative
**How to avoid:** When resuming, either: (a) pass remaining timesteps to `.learn()`, or (b) accept that exploration schedule will recalculate. For Tetris, option (b) is fine since we use relatively short exploration fractions.
**Warning signs:** Agent suddenly starts taking random actions after loading checkpoint

### Pitfall 2: Replay Buffer Not Loaded
**What goes wrong:** Agent performance drops significantly after resume
**Why it happens:** Default `model.save()` does NOT save replay buffer
**How to avoid:** Always call `model.save_replay_buffer()` separately and load with `model.load_replay_buffer()`
**Warning signs:** Training loss spikes after resume, agent behavior degrades

### Pitfall 3: Learning Starts Too High for Buffer Size
**What goes wrong:** Training never starts, agent stays random
**Why it happens:** `learning_starts` parameter is higher than number of steps collected
**How to avoid:** Ensure `learning_starts < buffer_size` and reasonably small (10k-50k for Tetris)
**Warning signs:** No training progress after many episodes, loss stays at 0

### Pitfall 4: Observation Shape Warning
**What goes wrong:** SB3 warns about unconventional observation shape (40, 13)
**Why it happens:** SB3 expects 1D vectors for MlpPolicy, but our env returns 2D feature matrix
**How to avoid:** This is fine - SB3's FlattenExtractor will flatten to (520,). Alternatively, wrap env with `gymnasium.wrappers.FlattenObservation` to silence warning.
**Warning signs:** Warning message in console (can be ignored, or silenced with FlattenObservation wrapper)

### Pitfall 5: Target Update Interval Too Large
**What goes wrong:** Agent learns very slowly, Q-values diverge
**Why it happens:** Target network too stale, causing bootstrap error accumulation
**How to avoid:** Use smaller target_update_interval for Tetris (1000-2000 steps, not default 10000)
**Warning signs:** Oscillating or diverging rewards, Q-value explosion

### Pitfall 6: Instantiating Then Loading
**What goes wrong:** Optimizer state not restored, training performance degrades
**Why it happens:** `model = DQN(env); model.load(path)` creates fresh optimizer, then only loads weights
**How to avoid:** Always use `model = DQN.load(path, env=env)` class method
**Warning signs:** Loss behaves differently after resume, learning rate appears wrong

## Code Examples

Verified patterns from official sources:

### Basic DQN Training
```python
# Source: SB3 DQN documentation
from stable_baselines3 import DQN

# Create environment (from Phase 1)
from src.environment import create_tetris_env
env = create_tetris_env(render_mode=None)  # Headless

# Create and train model
model = DQN("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=100_000)

# Save model
model.save("dqn_tetris")
```

### Save and Load with Replay Buffer
```python
# Source: SB3 Examples - saving and loading with replay buffer
from stable_baselines3 import DQN

# Train and save
model = DQN("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=50_000)
model.save("dqn_tetris")
model.save_replay_buffer("dqn_tetris_replay_buffer")

# Load and continue training
loaded_model = DQN.load("dqn_tetris", env=env)
loaded_model.load_replay_buffer("dqn_tetris_replay_buffer")
loaded_model.learn(total_timesteps=50_000, reset_num_timesteps=False)
```

### Custom Policy Network Architecture
```python
# Source: SB3 Custom Policy documentation
from stable_baselines3 import DQN

policy_kwargs = dict(
    net_arch=[256, 256],  # Two hidden layers of 256 units
)

model = DQN(
    "MlpPolicy",
    env,
    policy_kwargs=policy_kwargs,
    verbose=1,
)
```

### Using CheckpointCallback
```python
# Source: SB3 Callbacks documentation
from stable_baselines3 import DQN
from stable_baselines3.common.callbacks import CheckpointCallback

checkpoint_callback = CheckpointCallback(
    save_freq=10_000,           # Save every 10k steps
    save_path="./checkpoints/",
    name_prefix="dqn_tetris",
    save_replay_buffer=True,    # Include replay buffer
    save_vecnormalize=False,    # Not using VecNormalize
)

model = DQN("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=100_000, callback=checkpoint_callback)
```

### Evaluating Model Performance
```python
# Source: SB3 Evaluation documentation
from stable_baselines3.common.evaluation import evaluate_policy

# Evaluate trained model
mean_reward, std_reward = evaluate_policy(
    model,
    env,
    n_eval_episodes=10,
    deterministic=True,
)
print(f"Mean reward: {mean_reward:.2f} +/- {std_reward:.2f}")
```

### Flatten Observation Wrapper (Optional)
```python
# Source: Gymnasium wrappers documentation
from gymnasium.wrappers import FlattenObservation
from src.environment import create_tetris_env

# Create env and flatten observations to silence SB3 warning
env = create_tetris_env(render_mode=None)
env = FlattenObservation(env)
# Now observation is (520,) instead of (40, 13)
```

## DQN Hyperparameters for Tetris

### Recommended Configuration

Based on RL Zoo tuned hyperparameters and Tetris-specific considerations:

| Parameter | Default (SB3) | Tetris-Tuned | Reason |
|-----------|---------------|--------------|--------|
| learning_rate | 1e-4 | 1e-4 | Standard works well |
| buffer_size | 1,000,000 | 100,000 | Tetris has simpler state, smaller buffer sufficient |
| batch_size | 32 | 64 | Slightly larger for stability |
| gamma | 0.99 | 0.99 | Standard discount factor |
| exploration_fraction | 0.1 | 0.2 | Longer exploration for complex game |
| exploration_initial_eps | 1.0 | 1.0 | Start fully random |
| exploration_final_eps | 0.05 | 0.05 | Keep some exploration |
| target_update_interval | 10,000 | 1,000 | More frequent updates for Tetris |
| train_freq | 4 | 4 | Standard |
| learning_starts | 100 | 10,000 | Fill buffer before learning |
| net_arch | [64, 64] | [256, 256] | Larger network for game complexity |

### Hyperparameter Tuning Priority

If agent isn't learning:
1. **First check:** `learning_starts` - should be < buffer_size and reasonable (10k-50k)
2. **Then check:** `target_update_interval` - try reducing to 500-1000
3. **Then check:** `exploration_fraction` - may need longer exploration (0.3-0.5)
4. **Finally:** `net_arch` - try larger networks [256, 256] or [512, 256]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom DQN implementation | SB3 DQN | 2020+ | Saves weeks of debugging, reliable implementations |
| Manual epsilon schedule | SB3's exploration_fraction | 2020+ | Automatic schedule tied to training progress |
| Separate save for each component | CheckpointCallback with replay | 2021+ | One callback handles all saving |
| gym (OpenAI) | Gymnasium (Farama) | 2023+ | New API, SB3 2.x requires gymnasium |
| TensorFlow-based | PyTorch-based (SB3) | 2020+ | Better debugging, cleaner code |

**Deprecated/outdated:**
- `stable_baselines` (v2, TensorFlow) - use `stable_baselines3` (PyTorch)
- Creating model then calling `.load()` - use `Model.load()` class method
- Manual exploration decay - use built-in schedule parameters

## Open Questions

Things that couldn't be fully resolved:

1. **Epsilon state on resume**
   - What we know: SB3 saves algorithm parameters, exploration schedule is restored
   - What's unclear: Exactly where in the schedule agent resumes (may restart from beginning of new `total_timesteps`)
   - Recommendation: Test resume behavior, document actual behavior, consider it acceptable if agent re-explores briefly

2. **Best Tetris DQN hyperparameters**
   - What we know: General ranges from RL Zoo and Tetris papers
   - What's unclear: Optimal values for our specific (40, 13) observation space
   - Recommendation: Start with recommended values, tune based on learning curves

3. **Episode info tracking for goal**
   - What we know: SB3 tracks episode rewards in `ep_info_buffer`
   - What's unclear: Whether tetris-gymnasium includes 'lines' in episode info
   - Recommendation: Check info dict during development, may need custom callback to track lines

## Sources

### Primary (HIGH confidence)
- [SB3 DQN Documentation](https://stable-baselines3.readthedocs.io/en/master/modules/dqn.html) - DQN class parameters, defaults
- [SB3 Save Format Guide](https://stable-baselines3.readthedocs.io/en/master/guide/save_format.html) - What gets saved, replay buffer handling
- [SB3 Callbacks Guide](https://stable-baselines3.readthedocs.io/en/master/guide/callbacks.html) - CheckpointCallback, custom callbacks
- [SB3 GitHub Issue #597](https://github.com/DLR-RM/stable-baselines3/issues/597) - Continued training, reset_num_timesteps
- [SB3 GitHub Issue #29](https://github.com/DLR-RM/stable-baselines3/issues/29) - Proper model loading for resume

### Secondary (MEDIUM confidence)
- [RL Zoo DQN Hyperparameters](https://github.com/DLR-RM/rl-baselines3-zoo/blob/master/hyperparams/dqn.yml) - Tuned hyperparameters for various envs
- [SB3 RL Tips and Tricks](https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html) - Best practices
- [Gymnasium FlattenObservation](https://gymnasium.farama.org/main/api/wrappers/observation_wrappers/) - Observation flattening

### Tertiary (LOW confidence)
- [vietnh1009/Tetris-deep-Q-learning-pytorch](https://github.com/vietnh1009/Tetris-deep-Q-learning-pytorch) - Tetris DQN reference (not SB3)
- [ChesterHuynh/tetrisAI](https://github.com/ChesterHuynh/tetrisAI) - Tetris hyperparameters reference
- Various Tetris RL papers - Reward shaping, state representation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - SB3 is well-documented, API stable
- Architecture: HIGH - Patterns from SB3 docs and examples
- Checkpoint handling: HIGH - Verified through GitHub issues and documentation
- Pitfalls: HIGH - Documented issues and community experience
- Hyperparameters: MEDIUM - General guidance exists, Tetris-specific needs tuning

**Research date:** 2026-01-20
**Valid until:** 2026-02-20 (30 days - SB3 is stable, unlikely to change)
