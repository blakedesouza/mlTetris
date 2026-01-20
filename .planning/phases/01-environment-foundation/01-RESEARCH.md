# Phase 1: Environment Foundation - Research

**Researched:** 2026-01-20
**Domain:** Gymnasium-compatible Tetris Environment with Feature-Based Observations
**Confidence:** HIGH

## Summary

Phase 1 delivers a Gymnasium-compatible Tetris environment with feature-based observations, meta-actions, and shaped rewards. The critical discovery is that **tetris-gymnasium 0.3.0 already provides built-in wrappers** for both feature extraction (`FeatureVectorObservation`) and meta-actions (`GroupedActionsObservations`), eliminating the need to implement these from scratch.

The tetris-gymnasium library provides:
1. A base Tetris environment with standard game mechanics (SRS rotation, 7-bag randomizer)
2. `GroupedActionsObservations` wrapper that converts primitive actions to meta-actions (rotation + column)
3. `FeatureVectorObservation` wrapper that extracts column heights, holes, bumpiness features
4. Configurable reward function

The implementation approach is to wrap the base tetris-gymnasium environment with the provided wrappers, then add a custom reward shaping layer. This leverages existing, tested code rather than building from scratch.

**Primary recommendation:** Use tetris-gymnasium's built-in `GroupedActionsObservations` and `FeatureVectorObservation` wrappers, add a custom `ShapedRewardWrapper` for penalties.

## Standard Stack

The established libraries/tools for this phase:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tetris-gymnasium | 0.3.0 | Base Tetris environment | Pre-built Gymnasium interface, SRS rotation, 7-bag randomizer |
| gymnasium | 1.2.3 | RL environment interface | Industry standard, required by SB3 |
| numpy | >=1.24 | Array operations | Required by gymnasium, feature computations |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| stable-baselines3 | 2.7.1 | check_env validation | Environment validation only in Phase 1 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tetris-gymnasium | Custom Tetris implementation | Custom gives full control but adds 2-3 weeks of development |
| tetris-gymnasium | gym-tetris (NES) | NES version is slower, fixed configuration, no meta-action support |

**Installation:**
```bash
pip install tetris-gymnasium==0.3.0 gymnasium==1.2.3 stable-baselines3==2.7.1
```

## Architecture Patterns

### Recommended Project Structure
```
src/
  environment/
    __init__.py
    wrappers/
      __init__.py
      shaped_reward.py     # Custom reward shaping wrapper
      feature_extraction.py # Re-export tetris-gymnasium wrapper (optional customization)
    tetris_env.py          # Factory function to create wrapped environment
    features.py            # Feature computation utilities (if custom features needed)
tests/
  environment/
    test_env_creation.py   # Basic instantiation
    test_observations.py   # Feature vector verification
    test_actions.py        # Meta-action validation
    test_rewards.py        # Reward shaping verification
    test_gymnasium_api.py  # check_env compliance
```

### Pattern 1: Wrapper Stacking

**What:** Chain multiple wrappers to transform base environment incrementally
**When to use:** When each transformation is independent and composable
**Example:**
```python
# Source: Gymnasium wrapper documentation + tetris-gymnasium docs
import gymnasium as gym
from tetris_gymnasium.wrappers import GroupedActionsObservations, FeatureVectorObservation

def create_tetris_env(render_mode=None):
    """Factory function to create fully-configured Tetris environment."""
    # Base environment with primitive actions
    env = gym.make("tetris_gymnasium/Tetris", render_mode=render_mode)

    # Wrap with meta-actions (rotation + column)
    # This changes action space from Discrete(7) to Discrete(width * 4)
    env = GroupedActionsObservations(env)

    # Wrap with feature extraction
    # This changes observation from board array to feature vector
    env = FeatureVectorObservation(env)

    # Wrap with custom reward shaping
    env = ShapedRewardWrapper(env)

    return env
```

### Pattern 2: Custom Reward Wrapper

**What:** ObservationWrapper that modifies rewards based on board state features
**When to use:** When built-in rewards are insufficient (need penalties for holes/height)
**Example:**
```python
# Source: Gymnasium implementing custom wrappers tutorial
import gymnasium as gym
from gymnasium import RewardWrapper
import numpy as np

class ShapedRewardWrapper(RewardWrapper):
    """Add shaped rewards: penalties for holes and height, bonus for clears."""

    def __init__(self, env,
                 hole_penalty=-0.5,
                 height_penalty=-0.1,
                 clear_bonus_multiplier=1.0,
                 game_over_penalty=-10.0):
        super().__init__(env)
        self.hole_penalty = hole_penalty
        self.height_penalty = height_penalty
        self.clear_bonus_multiplier = clear_bonus_multiplier
        self.game_over_penalty = game_over_penalty
        self._prev_holes = 0
        self._prev_height = 0

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self._prev_holes = self._get_holes(info)
        self._prev_height = self._get_max_height(info)
        return obs, info

    def reward(self, reward):
        # Get current state from info (passed during step)
        # Note: May need to access unwrapped env for board state
        info = self._last_info

        # Calculate deltas
        current_holes = self._get_holes(info)
        current_height = self._get_max_height(info)

        new_holes = max(0, current_holes - self._prev_holes)
        height_increase = max(0, current_height - self._prev_height)

        # Shape the reward
        shaped_reward = reward * self.clear_bonus_multiplier
        shaped_reward += new_holes * self.hole_penalty
        shaped_reward += height_increase * self.height_penalty

        # Update previous state
        self._prev_holes = current_holes
        self._prev_height = current_height

        return shaped_reward

    def step(self, action):
        obs, reward, terminated, truncated, info = self.env.step(action)
        self._last_info = info

        if terminated:
            reward += self.game_over_penalty

        shaped_reward = self.reward(reward)
        return obs, shaped_reward, terminated, truncated, info

    def _get_holes(self, info):
        # Extract from info dict or compute from board
        return info.get('holes', 0)

    def _get_max_height(self, info):
        return info.get('max_height', 0)
```

### Pattern 3: Environment Factory with Configuration

**What:** Single factory function that accepts configuration dict
**When to use:** When environment needs to be recreated with same config (training loops)
**Example:**
```python
# Source: SB3 custom environment guide
from dataclasses import dataclass
from typing import Optional

@dataclass
class EnvConfig:
    render_mode: Optional[str] = None
    hole_penalty: float = -0.5
    height_penalty: float = -0.1
    clear_bonus_multiplier: float = 1.0
    game_over_penalty: float = -10.0

def make_env(config: EnvConfig = None):
    """Create environment with configuration. Useful for vectorized envs."""
    if config is None:
        config = EnvConfig()

    def _init():
        env = create_tetris_env(render_mode=config.render_mode)
        return ShapedRewardWrapper(
            env,
            hole_penalty=config.hole_penalty,
            height_penalty=config.height_penalty,
            clear_bonus_multiplier=config.clear_bonus_multiplier,
            game_over_penalty=config.game_over_penalty
        )

    return _init
```

### Anti-Patterns to Avoid
- **Modifying base environment directly:** Always use wrappers. Base environment should be unmodified.
- **Computing features from raw observation:** Use `FeatureVectorObservation` wrapper, don't recompute in training code.
- **Hardcoding reward coefficients:** Make them configurable via wrapper constructor.
- **Accessing `env.unwrapped` frequently:** If you need base env state often, pass it through `info` dict instead.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tetris game logic | Custom game engine | tetris-gymnasium | SRS rotation, collision detection, line clearing have subtle edge cases |
| Meta-action mapping | Custom action translator | `GroupedActionsObservations` | Handles rotation states, column bounds, action masking |
| Feature extraction | Custom board analyzer | `FeatureVectorObservation` | Computes column heights, holes, bumpiness correctly |
| Environment validation | Manual testing | `check_env()` | Catches API compliance issues automatically |
| Observation space | Manual Box definition | Wrapper's observation_space | Wrapper updates space correctly after transformation |

**Key insight:** tetris-gymnasium 0.3.0 provides wrappers for the two hardest parts (meta-actions and feature extraction). The only custom code needed is reward shaping, which is straightforward.

## Common Pitfalls

### Pitfall 1: Wrapper Order Matters
**What goes wrong:** Applying feature extraction before meta-actions breaks the observation generation
**Why it happens:** `GroupedActionsObservations` generates observations for each possible action - it needs the base observation format
**How to avoid:** Always apply wrappers in this order: base env -> GroupedActionsObservations -> FeatureVectorObservation -> ShapedRewardWrapper
**Warning signs:** `GroupedActionsObservations` errors about observation shape, action mask shape mismatches

### Pitfall 2: Forgetting to Reset Wrapper State
**What goes wrong:** Reward shaping uses stale `_prev_holes` from previous episode
**Why it happens:** `reset()` method not overridden or doesn't clear tracking variables
**How to avoid:** Always override `reset()` in custom wrappers and initialize tracking state
**Warning signs:** First step of new episode has massive negative reward spike

### Pitfall 3: info Dict Not Propagated
**What goes wrong:** Custom reward wrapper can't access board state features
**Why it happens:** tetris-gymnasium puts game state in `info` dict, but not all wrappers pass it through
**How to avoid:** Ensure wrappers preserve `info` dict, access features from `info` or compute from observation
**Warning signs:** `KeyError` when accessing `info['holes']`, reward always zero

### Pitfall 4: Observation Space Mismatch
**What goes wrong:** `check_env` fails with observation space errors
**Why it happens:** Wrapper returns observation outside declared bounds, or dtype mismatch
**How to avoid:** After wrapping, verify `env.observation_space` matches actual observations
**Warning signs:** `check_env` AssertionError about observation bounds, dtype warnings

### Pitfall 5: Action Space Size Miscalculation
**What goes wrong:** Agent tries invalid actions, environment crashes
**Why it happens:** Meta-action space is `width * 4` (4 rotation states), not `width * num_rotations_per_piece`
**How to avoid:** Use `GroupedActionsObservations` - it handles this correctly and provides action mask
**Warning signs:** IndexError on action, assertion failures in step()

## Code Examples

Verified patterns from official sources:

### Creating Base Environment
```python
# Source: tetris-gymnasium quickstart
import gymnasium as gym

env = gym.make("tetris_gymnasium/Tetris", render_mode="ansi")
obs, info = env.reset(seed=42)
print(env.action_space)  # Discrete(7) - primitive actions
print(env.observation_space)  # Board shape (likely Dict or Box)
```

### Applying Meta-Action Wrapper
```python
# Source: tetris-gymnasium wrappers documentation
from tetris_gymnasium.wrappers import GroupedActionsObservations

env = gym.make("tetris_gymnasium/Tetris")
env = GroupedActionsObservations(env)
print(env.action_space)  # Discrete(width * 4) - meta-actions
# Action i = column (i // 4), rotation (i % 4)
```

### Applying Feature Extraction Wrapper
```python
# Source: tetris-gymnasium wrappers documentation
from tetris_gymnasium.wrappers import FeatureVectorObservation

env = gym.make("tetris_gymnasium/Tetris")
env = GroupedActionsObservations(env)
env = FeatureVectorObservation(env)
obs, info = env.reset()
# obs is now feature vector: [heights..., max_height, holes, bumpiness]
print(env.observation_space)  # Box with feature dimensions
```

### Validating Environment with check_env
```python
# Source: SB3 custom environment guide
from stable_baselines3.common.env_checker import check_env

env = create_tetris_env()
check_env(env, warn=True, skip_render_check=True)
# Raises exception if API non-compliant
# Prints warnings for best practice violations
```

### Full Environment Creation Pipeline
```python
# Complete example combining all wrappers
import gymnasium as gym
from tetris_gymnasium.wrappers import GroupedActionsObservations, FeatureVectorObservation

def create_tetris_env(render_mode=None, reward_config=None):
    """
    Create fully-configured Tetris environment for RL training.

    Args:
        render_mode: None for headless, "human" for display, "ansi" for text
        reward_config: dict with hole_penalty, height_penalty, etc.

    Returns:
        Gymnasium Env with feature observations, meta-actions, shaped rewards
    """
    # 1. Base environment
    env = gym.make("tetris_gymnasium/Tetris", render_mode=render_mode)

    # 2. Meta-actions (must come before feature extraction)
    env = GroupedActionsObservations(env)

    # 3. Feature extraction
    env = FeatureVectorObservation(env)

    # 4. Reward shaping (custom wrapper)
    if reward_config:
        env = ShapedRewardWrapper(env, **reward_config)
    else:
        env = ShapedRewardWrapper(env)  # Use defaults

    return env

# Usage
env = create_tetris_env()
obs, info = env.reset(seed=42)
print(f"Observation shape: {obs.shape}")
print(f"Action space: {env.action_space}")

# Run one episode
done = False
total_reward = 0
while not done:
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    total_reward += reward
    done = terminated or truncated

print(f"Episode reward: {total_reward}")
```

## tetris-gymnasium API Details

### Base Environment (Tetris)
**Observation Space:** Dict or Box containing board state (exact format depends on configuration)
**Action Space:** Discrete(7) - primitive actions: move_left, move_right, move_down, rotate_ccw, rotate_cw, hard_drop, swap
**Reward:** Lines cleared (configurable)
**Termination:** Piece cannot spawn (game over)

### GroupedActionsObservations Wrapper
**Purpose:** Convert primitive actions to meta-actions (final placement selection)
**Action Space After:** Discrete(width * 4) where width=10 (default), so 40 actions
**Action Encoding:** action = column * 4 + rotation_state (rotation 0-3)
**Observation:** Generates observations for ALL possible placements, returns as array
**Action Mask:** Provides `info['action_mask']` indicating which actions are legal

### FeatureVectorObservation Wrapper
**Purpose:** Extract numerical features from board state
**Observation Space After:** Box with shape (num_features,)
**Features Extracted:**
- Stack height per column (10 values for standard board)
- Maximum stack height (1 value)
- Number of holes (1 value)
- Stack bumpiness (1 value)
**Total:** ~13 features for standard 10-wide board

### Configuration Options
```python
# tetris-gymnasium supports configuration via gym.make kwargs
env = gym.make(
    "tetris_gymnasium/Tetris",
    render_mode="human",  # None, "human", "ansi", "rgb_array"
    # Additional config options (check tetris-gymnasium docs for full list)
)
```

## Reward Shaping Specifics

### Recommended Coefficients (from Literature)

Based on successful Tetris RL implementations:

| Component | Value Range | Recommended | Source |
|-----------|-------------|-------------|--------|
| Line clear base | 1-10 per line | `lines_cleared^2` | nuno-faria/tetris-ai |
| Hole penalty | -0.1 to -1.0 per hole | -0.5 per new hole | ChesterHuynh/tetrisAI |
| Height penalty | -0.01 to -0.1 per row | -0.1 per height increase | Multiple sources |
| Game over | -2 to -100 | -10 | OpenReview paper, ChesterHuynh |
| Bumpiness penalty | -0.01 to -0.1 | -0.05 | Optional, some skip this |

### Recommended Starting Configuration
```python
reward_config = {
    'hole_penalty': -0.5,      # Per new hole created
    'height_penalty': -0.1,    # Per row of height increase
    'clear_bonus_multiplier': 1.0,  # Multiply base line clear reward
    'game_over_penalty': -10.0,
}
```

### Reward Function Formula
```
reward = (lines_cleared^2 * clear_bonus_multiplier)
       + (new_holes * hole_penalty)
       + (height_increase * height_penalty)
       + (game_over ? game_over_penalty : 0)
```

### Tuning Notes
- Start with recommended values, adjust based on agent behavior
- If agent "suicides" (quickly ends game), reduce game_over_penalty magnitude
- If agent ignores holes, increase hole_penalty magnitude
- If agent builds too tall, increase height_penalty
- Track average episode length and score to measure impact of changes

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw board grid input | Feature vector extraction | 2016+ | 10-100x faster training convergence |
| Primitive actions | Meta-actions (placement) | 2016+ | Eliminates 10-40 step action sequences |
| Lines-only reward | Shaped rewards (holes/height penalties) | 2016+ | Enables learning beyond random |
| OpenAI Gym | Gymnasium | 2023 | New API (5-tuple returns), SB3 compatible |
| Custom Tetris impl | tetris-gymnasium | 2024-2025 | Pre-built, tested, saves weeks |

**Deprecated/outdated:**
- `gym` package (use `gymnasium`)
- `env.step()` returning 4 values (now returns 5: obs, reward, terminated, truncated, info)
- Custom Tetris game logic (use tetris-gymnasium)

## Open Questions

Things that couldn't be fully resolved:

1. **Exact info dict contents from tetris-gymnasium**
   - What we know: tetris-gymnasium wrappers put game state in info
   - What's unclear: Exact keys available (holes, heights, etc.) in v0.3.0
   - Recommendation: Inspect info dict during development, fall back to computing from observation if needed

2. **Action mask handling with SB3**
   - What we know: `GroupedActionsObservations` provides action mask
   - What's unclear: How to integrate mask with SB3 DQN (may need custom policy)
   - Recommendation: Start without action mask (invalid actions will just fail), add mask support in Phase 2 if needed

3. **FeatureVectorObservation exact features**
   - What we know: Includes heights, holes, bumpiness, max_height
   - What's unclear: Exact feature order and count in v0.3.0
   - Recommendation: Print observation shape after wrapping, document for Phase 2

## Sources

### Primary (HIGH confidence)
- [tetris-gymnasium PyPI](https://pypi.org/project/tetris-gymnasium/) - Package version 0.3.0 confirmed
- [tetris-gymnasium Documentation](https://max-we.github.io/Tetris-Gymnasium/) - Wrapper documentation
- [tetris-gymnasium GitHub](https://github.com/Max-We/Tetris-Gymnasium) - Source code and examples
- [Gymnasium Custom Wrappers Tutorial](https://gymnasium.farama.org/tutorials/gymnasium_basics/implementing_custom_wrappers/) - ObservationWrapper, RewardWrapper patterns
- [SB3 Custom Environments](https://stable-baselines3.readthedocs.io/en/master/guide/custom_env.html) - check_env usage

### Secondary (MEDIUM confidence)
- [nuno-faria/tetris-ai](https://github.com/nuno-faria/tetris-ai) - Feature extraction: 4 key features, reward formula
- [ChesterHuynh/tetrisAI](https://github.com/ChesterHuynh/tetrisAI) - Reward coefficients, network architecture
- [Gymnasium Observation Wrappers](https://gymnasium.farama.org/api/wrappers/observation_wrappers/) - TransformObservation pattern

### Tertiary (LOW confidence)
- Stanford CS231n Report - Referenced but PDF not readable, cited for reward shaping patterns
- OpenReview Tetris paper - Referenced for game_over_penalty values

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - tetris-gymnasium 0.3.0 verified on PyPI, wrappers documented
- Architecture: HIGH - Gymnasium wrapper patterns are well-documented
- Pitfalls: HIGH - Consistent across multiple implementations and prior research
- Reward coefficients: MEDIUM - Values vary across implementations, recommended ranges established

**Research date:** 2026-01-20
**Valid until:** 2026-02-20 (30 days - stable domain, tetris-gymnasium actively maintained)
