# Domain Pitfalls: ML Tetris Trainer

**Domain:** Reinforcement Learning Game Trainer (Tetris)
**Researched:** 2026-01-19
**Confidence:** HIGH (verified across multiple academic papers, GitHub implementations, and practitioner reports)

---

## Critical Mistakes

Mistakes that cause training failure, require complete rewrites, or waste weeks of development time.

### 1. Using Raw Board State as Input

**What goes wrong:** Training a DQN on the raw 20x10 binary grid (200+ inputs) leads to extremely slow convergence or complete failure. The state space is 2^200 possible configurations - fundamentally intractable for direct learning.

**Why it happens:** Raw pixel/grid input works for Atari games, so developers assume it works for Tetris. But Tetris requires understanding column relationships and hole positions that raw grids obscure.

**Consequences:**
- Training takes days/weeks with no meaningful progress
- Agent learns to "survive" but never clears lines
- Network becomes enormous to capture simple patterns

**Prevention:**
- Use hand-crafted features: column heights, number of holes, bumpiness, lines clearable
- Start with simplified state (column heights only = 10 values)
- Only add raw grid input if feature-based approach is working

**Detection (warning signs):**
- Agent survives many moves but never clears lines after 1000+ episodes
- Loss decreases but reward stays flat
- Network has 10,000+ parameters for a "simple" game

**Phase to address:** Phase 1 (Environment) - Design state representation before training begins

---

### 2. Sparse Reward Only (Lines Cleared)

**What goes wrong:** Rewarding only for cleared lines means the agent gets zero feedback for 99%+ of actions. Random exploration almost never reaches line-clearing states, so the agent never learns what to optimize.

**Why it happens:** Lines cleared is the "real" Tetris score, so it seems like the natural reward. Developers don't realize how sparse this signal is for early-stage agents.

**Consequences:**
- Agent learns to place pieces compactly (accidental stack behavior)
- No understanding of line-clearing strategies
- Stuck at random-level performance indefinitely

**Prevention:**
- Add shaped intermediate rewards:
  - Negative reward for creating holes
  - Negative reward for increasing max height
  - Small positive for reducing bumpiness
  - Game-over penalty (critical for convergence)
- Use reward = (lines_cleared)^2 to incentivize Tetrises over singles
- Keep intermediate rewards small relative to line clears

**Detection:**
- Agent stacks pieces but never clears lines
- Reward signal is 0 for most episodes
- "Random exploration is unsuitable" symptoms

**Phase to address:** Phase 1 (Environment) - Define reward function before training loop

---

### 3. Using Primitive Actions (Left/Right/Rotate/Drop)

**What goes wrong:** Training on individual button presses (move left, move right, rotate, drop) creates an enormous action sequence problem. Agent must learn 10-20 step sequences just to place one piece.

**Why it happens:** This mirrors how humans play, and NES Tetris uses these controls. Seems like the "authentic" approach.

**Consequences:**
- 10-40 actions per piece placement vs 1 action with meta-actions
- Credit assignment nightmare (which of 20 moves was good?)
- Training is 10-40x slower minimum
- Researchers report complete failure on original NES Tetris without action space reduction

**Prevention:**
- Use meta-actions: (rotation, column) pairs = ~40 possible actions
- Action represents final placement, not movement sequence
- Let the environment handle the translation to primitive moves

**Detection:**
- Episode length is hundreds of steps per piece
- Agent learns to "wiggle" pieces without placing them
- Training progress per wall-clock hour is negligible

**Phase to address:** Phase 1 (Environment) - Define action space before agent implementation

---

### 4. Not Saving Full Training State for Resume

**What goes wrong:** Saving only model weights means losing optimizer state (critical for Adam), replay buffer contents, epsilon value, and episode count. Resume from checkpoint behaves like starting fresh with a pre-trained network.

**Why it happens:** PyTorch tutorials show `torch.save(model.state_dict())` and developers assume that's sufficient.

**Consequences:**
- Resumed training diverges or performs worse than before pause
- Adam momentum is reset, causing training instability
- Epsilon resets to 1.0, undoing exploration progress
- Empty replay buffer = learning from scratch

**Prevention:**
Save complete checkpoint including:
```python
checkpoint = {
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'replay_buffer': replay_buffer,  # or recent subset
    'epsilon': epsilon,
    'episode': episode,
    'total_steps': total_steps,
    'random_state': random.getstate(),
    'numpy_random_state': np.random.get_state(),
    'torch_random_state': torch.get_rng_state()
}
```

**Detection:**
- Training metrics spike/crash after resume
- Agent "forgets" learned behavior after pause
- Resume from 50% trained performs worse than 25% trained

**Phase to address:** Phase 2 (Training Core) - Implement checkpointing system

---

### 5. Catastrophic Forgetting During Training

**What goes wrong:** Agent learns to handle early-game states, then forgets them while learning mid-game states. Performance oscillates instead of improving monotonically.

**Why it happens:** Neural networks trained on sequential, correlated data overwrite previous learning. RL training generates exactly this kind of data - sequences of similar states from single episodes.

**Consequences:**
- Agent performs well at episode start, terribly later (or vice versa)
- Training curves show improvement followed by degradation
- "Solved" behaviors suddenly disappear

**Prevention:**
- Use experience replay buffer (minimum 10,000-50,000 transitions)
- Sample randomly from buffer, not sequentially
- Use target network updated every N episodes (reduces Q-value oscillation)
- Consider prioritized experience replay for important transitions

**Detection:**
- Performance on early-game states degrades as training progresses
- Q-values oscillate wildly
- Agent "unlearns" previously successful strategies

**Phase to address:** Phase 2 (Training Core) - Implement experience replay correctly

---

## Common Inefficiencies

Issues that slow development or training without causing complete failure.

### 6. Training Visualization Blocking Training Loop

**What goes wrong:** Rendering Tetris board on every step makes training 100-1000x slower. Visualization and training compete for the same thread.

**Why it happens:** Developers want to see what the agent is doing. Visual feedback is satisfying. The slowdown isn't obvious until you disable it.

**Consequences:**
- 1000 episodes takes hours instead of minutes
- Can't run overnight training sessions effectively
- Iteration cycles are too slow for hyperparameter tuning

**Prevention:**
- Headless training mode as default (no rendering)
- Separate visualization process connected via queue/websocket
- Render only every N episodes for spot checks
- Toggle visualization without restarting training

**Detection:**
- Training loop includes `env.render()` on every step
- CPU/GPU utilization is low during "training"
- Disabling visualization speeds up training by 10x+

**Phase to address:** Phase 3 (Web Interface) - Design training/visualization separation from start

---

### 7. Wrong Hyperparameter Defaults

**What goes wrong:** Using "standard" DQN hyperparameters that work for Atari but not for Tetris's specific dynamics. Training converges to suboptimal behavior.

**Why it happens:** Tutorials provide default values. Tetris has different episode lengths, reward scales, and state dynamics than benchmark environments.

**Consequences:**
- Agent plateaus at mediocre performance
- Hyperparameter sensitivity causes inconsistent results
- "Random" variance is actually hyperparameter mismatch

**Prevention:**
Tetris-specific starting points:
- Learning rate: 0.001 (start), tune down to 0.0001
- Gamma (discount): 0.99 (long episodes need high gamma)
- Epsilon decay: Over 1000-1500 episodes (not steps)
- Replay buffer: 20,000-50,000 transitions
- Batch size: 32-512 (larger often better for Tetris)
- Target network update: Every 10-20 episodes

**Detection:**
- Using default values from unrelated tutorials
- No hyperparameter tuning done
- Results vary wildly across runs

**Phase to address:** Phase 2 (Training Core) - Research Tetris-specific hyperparameters

---

### 8. Blocking UI During Training

**What goes wrong:** Training runs in the main thread, web interface freezes. Can't interact with dashboard, pause training, or view stats during long runs.

**Why it happens:** Simpler to implement synchronously. Async/threading adds complexity.

**Consequences:**
- Must choose between training OR viewing
- Can't adjust parameters mid-run
- User thinks application crashed during long training

**Prevention:**
- Training loop in background thread/process
- WebSocket for real-time metric streaming
- Command queue for pause/resume/adjust
- FastAPI with native WebSocket support (not Flask)

**Detection:**
- UI becomes unresponsive during training
- Metrics only update after training completes
- "Not responding" in title bar

**Phase to address:** Phase 3 (Web Interface) - Architecture for async training

---

### 9. Not Using Vectorized Environments

**What goes wrong:** Training one episode at a time when GPU could handle 100+ parallel environments. Massive underutilization of compute resources.

**Why it happens:** Single-environment code is simpler. Vectorization requires refactoring. Not obvious this is a bottleneck.

**Consequences:**
- GPU utilization at 5-20% instead of 90%+
- Training takes 10-100x longer than necessary
- Can't compete with published Tetris RL results

**Prevention:**
- Use Gymnasium's VectorEnv API
- Batch observations before network forward pass
- Consider EnvPool for higher throughput
- Profile GPU utilization to verify improvement

**Detection:**
- `nvidia-smi` shows low GPU utilization during training
- Training loop processes one env.step() at a time
- Training time doesn't improve much on better GPU

**Phase to address:** Phase 2 (Training Core) - Consider from the start, implement as optimization

---

### 10. Inadequate Logging

**What goes wrong:** Only logging episode reward. When training fails, no data to diagnose why. Debugging requires re-running experiments.

**Why it happens:** Logging seems like overhead. "I'll add more later when I need it."

**Consequences:**
- Can't distinguish reward hacking from genuine learning
- No idea which hyperparameter caused improvement
- Wasted experiments that could have yielded insights

**Prevention:**
Log comprehensively:
- Episode: reward, length, lines cleared, max height, holes created
- Training: loss, Q-values (mean, max, min), gradient norms
- Actions: distribution of actions taken, exploration vs exploitation
- Checkpoints: hyperparameters, git commit, random seeds

Use TensorBoard or Weights & Biases for visualization.

**Detection:**
- Only one metric being tracked
- Can't explain why a run succeeded or failed
- Reproducing good results is difficult

**Phase to address:** Phase 2 (Training Core) - Implement logging infrastructure early

---

## Tetris-Specific Gotchas

Pitfalls unique to Tetris that don't apply to general RL games.

### 11. Ignoring the "Next Piece" Information

**What goes wrong:** Agent only sees current board, not upcoming piece. Makes suboptimal placements because it can't plan ahead.

**Why it happens:** Simplifies state representation. "One piece at a time" seems logical.

**Consequences:**
- Agent can't set up Tetrises (needs to know if I-piece is coming)
- Reactive rather than strategic play
- Performance ceiling well below human level

**Prevention:**
- Include next piece in state (7 additional one-hot values)
- Consider including piece hold state if implementing hold feature
- Some implementations include next 2-3 pieces

**Detection:**
- Agent never sets up Tetris opportunities
- Plays identically regardless of upcoming pieces
- Plateau at "competent but not strategic" level

**Phase to address:** Phase 1 (Environment) - State representation design

---

### 12. Hole Definition Inconsistency

**What goes wrong:** Different implementations define "hole" differently, leading to incomparable results and confused reward signals.

**Why it happens:** Tetris literature isn't consistent. Some count all empty cells below the surface, others only count "trapped" cells.

**Consequences:**
- Reward function behaves unexpectedly
- Literature comparisons are meaningless
- Debugging reward shaping is harder

**Prevention:**
Define clearly and consistently:
- Hole = empty cell with at least one filled cell above it in same column
- Track: total holes, new holes created this move, holes depth
- Document your definition in code comments

**Detection:**
- Hole count doesn't match intuition when viewing board
- Similar-looking boards have very different hole counts

**Phase to address:** Phase 1 (Environment) - Define metrics precisely

---

### 13. Speed Level Complexity

**What goes wrong:** Training on slow piece drop speed, then agent fails when tested on faster speeds (or vice versa).

**Why it happens:** NES Tetris has levels 0-19+ with dramatically different drop speeds. Training on one speed doesn't generalize.

**Consequences:**
- Agent trained on "easy mode" can't handle real gameplay
- Training on hard mode is much more difficult (less time to decide)
- Demonstrated performance doesn't match training performance

**Prevention:**
- Use "instant drop" during training (piece placed immediately)
- Speed is cosmetic - agent chooses placement, speed is just animation
- OR train across multiple speeds with curriculum learning

**Detection:**
- Agent performs very differently at different speed settings
- Training used one speed, demo uses another

**Phase to address:** Phase 1 (Environment) - Decide on speed handling approach

---

### 14. Game Over Handling Edge Cases

**What goes wrong:** Inconsistent game-over conditions cause training instability. Piece spawning overlap, reaching top row, and lock-out rules vary.

**Why it happens:** Tetris has multiple official rulesets (SRS, Classic, etc.) with different game-over conditions.

**Consequences:**
- Agent exploits ambiguous game-over states
- Reward signal is inconsistent at episode boundaries
- Comparison with other implementations is invalid

**Prevention:**
- Use standard Tetris Guideline rules OR document deviations
- Game over when: new piece cannot spawn without overlap
- Apply consistent game-over penalty (-10 to -100)
- Tetris Gymnasium provides configurable, documented ruleset

**Detection:**
- Games end at different "heights" inconsistently
- Agent behavior at top of board is erratic

**Phase to address:** Phase 1 (Environment) - Define clear game rules

---

### 15. Comparing Apples to Oranges (Benchmark Mismatch)

**What goes wrong:** Claiming "my agent achieves X lines" when X depends heavily on implementation details: board size, piece randomization, speed, scoring system.

**Why it happens:** Tetris seems standardized but has many variants. Papers don't always specify details.

**Consequences:**
- Inflated or deflated performance expectations
- Wasted time trying to match irreproducible results
- False confidence in agent capability

**Prevention:**
- Specify exactly: board size (20x10), piece distribution (7-bag vs random), speed
- Use standardized environments (Tetris Gymnasium)
- Compare only within identical configurations
- Report variance (std dev over N runs with different seeds)

**Detection:**
- Impressive numbers from paper can't be reproduced
- Small config changes cause huge score differences

**Phase to address:** Phase 1 (Environment) and Phase 4 (Model Management) - Standardize and document

---

## Prevention Strategies Summary

| Pitfall | Prevention Strategy | Phase |
|---------|---------------------|-------|
| Raw board state | Hand-crafted features (heights, holes, bumpiness) | Environment |
| Sparse rewards | Shaped rewards + game-over penalty | Environment |
| Primitive actions | Meta-actions (rotation, column pairs) | Environment |
| Incomplete checkpoints | Save model + optimizer + buffer + epsilon + seeds | Training Core |
| Catastrophic forgetting | Experience replay + target network | Training Core |
| Visualization blocking | Headless mode + separate render process | Web Interface |
| Wrong hyperparameters | Tetris-specific defaults, systematic tuning | Training Core |
| Blocking UI | Background training thread + WebSocket updates | Web Interface |
| Single environment | Vectorized environments (VectorEnv) | Training Core |
| Poor logging | Comprehensive metrics + TensorBoard/W&B | Training Core |
| Missing next piece | Include in state representation | Environment |
| Hole definition | Document and implement consistently | Environment |
| Speed complexity | Instant drop or curriculum learning | Environment |
| Game over edge cases | Standard rules + consistent penalty | Environment |
| Benchmark mismatch | Standardized env + documented config + seeds | Environment + Model Management |

---

## Phase-Specific Risk Assessment

| Phase | Risk Level | Key Pitfalls | Mitigation |
|-------|------------|--------------|------------|
| Environment | HIGH | #1, #2, #3, #11-15 | Design decisions here cascade through entire project |
| Training Core | HIGH | #4, #5, #7, #9, #10 | Get fundamentals right before optimization |
| Web Interface | MEDIUM | #6, #8 | Architectural separation is key |
| Model Management | LOW | #15 | Mostly documentation/standards |
| Polish/Testing | LOW | None critical | Earlier phases absorb risk |

---

## Sources

**Academic Papers:**
- [Learn to Play Tetris with Deep Reinforcement Learning](https://openreview.net/pdf?id=8TLyqLGQ7Tg) - Liu 2020, OpenReview
- [Playing Tetris with Deep Reinforcement Learning](https://cs231n.stanford.edu/reports/2016/pdfs/121_Report.pdf) - Stevens, Stanford CS231n
- [The Game of Tetris in Machine Learning](https://arxiv.org/abs/1905.01652) - Algorta & Simsek 2019

**Practitioner Reports:**
- [How I trained a Neural Network to Play Tetris](https://timhanewich.medium.com/how-i-trained-a-neural-network-to-play-tetris-using-reinforcement-learning-ecfa529c767a) - Hanewich, Medium
- [Reinforcement Learning on Tetris](https://rex-l.medium.com/reinforcement-learning-on-tetris-707f75716c37) - Rex L, Medium
- [Scaffolding to Superhuman: Curriculum Learning for 2048 and Tetris](https://kywch.github.io/blog/2025/12/curriculum-learning-2048-tetris/) - Choe 2025

**General RL Best Practices:**
- [Stable Baselines3 RL Tips and Tricks](https://stable-baselines3.readthedocs.io/en/master/guide/rl_tips.html)
- [7 Challenges in Reinforcement Learning](https://builtin.com/machine-learning/reinforcement-learning) - Built In
- [Eight Tips for Optimizing DQN Models](https://www.numberanalytics.com/blog/optimizing-dqn-models-in-rl)

**Catastrophic Forgetting:**
- [Catastrophic Forgetting in Deep RL](https://towardsdatascience.com/part-2-building-a-deep-q-network-to-play-gridworld-catastrophic-forgetting-and-experience-6b2b000910d7/)
- [Elastic Weight Consolidation - PNAS](https://www.pnas.org/doi/10.1073/pnas.1611835114)

**GitHub Implementations:**
- [nuno-faria/tetris-ai](https://github.com/nuno-faria/tetris-ai) - Reference DQN implementation
- [Tetris-Gymnasium](https://github.com/Max-We/Tetris-Gymnasium) - Standardized environment
