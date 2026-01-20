# ML Tetris Trainer

A reinforcement learning application that trains an AI to play Tetris. Watch the AI learn in real-time through a web dashboard, control training with pause/resume/speed adjustments, and manage multiple model versions.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Version](https://img.shields.io/badge/version-1.0-brightgreen.svg)

## Features

- **Live Training Visualization** - Watch the AI play Tetris in real-time via web dashboard
- **Training Controls** - Start, stop, pause, resume training from the browser
- **Headless/Visual Toggle** - Switch between fast headless training and watchable visual mode
- **Speed Control** - Adjust game speed during visual mode
- **Real-time Metrics** - Live charts showing reward progression and training stats
- **Model Management** - Save models to named slots, compare on leaderboard
- **Demo Mode** - Watch any saved model play without training
- **Checkpoint System** - Full save/load/resume with optimizer and replay buffer preserved
- **Export Models** - Download trained models for sharing or backup

## Tech Stack

- **RL Framework**: Stable-Baselines3 (DQN)
- **Environment**: tetris-gymnasium with custom wrappers
- **Backend**: FastAPI + WebSockets
- **Frontend**: Vanilla JS, Canvas API, Chart.js

## Installation

```bash
# Clone the repository
git clone https://github.com/blakedesouza/mlTetris.git
cd mlTetris

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,web]"
```

## Usage

### Start the Web Dashboard

```bash
uvicorn src.web.server:app --reload
```

Then open http://localhost:8000 in your browser.

### Training from the Web UI

1. Set your target lines goal (default: 10)
2. Set timesteps (training iterations)
3. Click **Start Training**
4. Toggle **Visual Mode** to watch the AI play
5. Use **Pause/Resume** to control training
6. Adjust **Speed** slider to watch faster or slower

### Model Management

- **Save Current Model** - Save to a named slot during or after training
- **Leaderboard** - Compare saved models by best lines cleared
- **Demo** - Watch any saved model play
- **Export** - Download model file

## Project Structure

```
mlTetris/
├── src/
│   ├── environment/       # Gymnasium-compatible Tetris environment
│   │   ├── tetris_env.py  # Environment factory
│   │   ├── config.py      # Environment configuration
│   │   └── wrappers/      # Reward shaping wrapper
│   ├── training/          # RL training components
│   │   ├── agent.py       # TetrisAgent with checkpoint support
│   │   ├── callbacks.py   # Training callbacks (metrics, goals)
│   │   ├── train.py       # Headless training function
│   │   └── model_slots.py # Model slot management
│   └── web/               # Web dashboard
│       ├── server.py      # FastAPI application
│       ├── training_manager.py  # Training process management
│       ├── static/        # JS, CSS
│       └── templates/     # HTML templates
├── tests/                 # Test suite (80+ tests)
├── checkpoints/           # Saved checkpoints and model slots
└── exports/               # Exported model files
```

## How It Works

### Environment

The Tetris environment uses:
- **Feature-based observations**: Column heights, holes, bumpiness (not raw pixels)
- **Meta-actions**: Agent selects final piece placement (rotation + column), not primitive moves
- **Shaped rewards**: Penalties for holes/height, bonuses for line clears

### Training

- DQN (Deep Q-Network) with experience replay
- Training runs in a subprocess to keep the web UI responsive
- Checkpoints preserve full state (model weights, optimizer, replay buffer, exploration rate)

## Configuration

Training parameters can be set in the web UI:
- **Target Lines**: Goal for the AI to reach
- **Timesteps**: Number of training iterations
- **Learning Rate**: DQN learning rate (default: 1e-4)

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# Type checking (if configured)
mypy src
```

## License

MIT

## Acknowledgments

- [tetris-gymnasium](https://github.com/Hewitt-Learning/tetris-gymnasium) - Tetris environment
- [Stable-Baselines3](https://github.com/DLR-RM/stable-baselines3) - RL algorithms
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
