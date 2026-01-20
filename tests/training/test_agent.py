"""Tests for TetrisAgent wrapper."""

import pytest
import numpy as np
from stable_baselines3 import DQN

from src.training import TrainingConfig, TetrisAgent
from src.environment import make_env, EnvConfig


class TestTetrisAgentCreation:
    """Tests for agent creation and initialization."""

    def test_agent_creation(self, env, config):
        """Agent creates with env and config."""
        agent = TetrisAgent(env, config)

        assert agent is not None
        assert agent.env is env
        assert agent.config is config

    def test_agent_has_model(self, env, config):
        """agent.model is DQN instance."""
        agent = TetrisAgent(env, config)

        assert hasattr(agent, "model")
        assert isinstance(agent.model, DQN)

    def test_agent_initial_timesteps(self, env, config):
        """timesteps_trained starts at 0."""
        agent = TetrisAgent(env, config)

        assert agent.timesteps_trained == 0


class TestTetrisAgentPredict:
    """Tests for agent prediction."""

    def test_agent_predict(self, env, config):
        """predict() returns valid action for observation."""
        agent = TetrisAgent(env, config)

        obs, _ = env.reset()
        action, state = agent.predict(obs)

        # Action should be within action space bounds
        assert action >= 0
        assert action < env.action_space.n
        # State is None for DQN
        assert state is None

    def test_agent_predict_deterministic(self, env, config):
        """predict() with deterministic=True returns consistent action."""
        agent = TetrisAgent(env, config)

        obs, _ = env.reset()

        # With deterministic=True, same observation should give same action
        action1, _ = agent.predict(obs, deterministic=True)
        action2, _ = agent.predict(obs, deterministic=True)

        assert action1 == action2


class TestTetrisAgentTraining:
    """Tests for agent training."""

    def test_agent_train_increments_timesteps(self, env, config):
        """train() increases timesteps_trained."""
        agent = TetrisAgent(env, config)

        initial_steps = agent.timesteps_trained
        train_steps = 100

        agent.train(train_steps)

        # timesteps_trained should increase by the trained amount
        assert agent.timesteps_trained == initial_steps + train_steps

    def test_agent_train_multiple_calls(self, env, config):
        """Multiple train() calls accumulate timesteps."""
        agent = TetrisAgent(env, config)

        agent.train(50)
        assert agent.timesteps_trained == 50

        agent.train(50)
        assert agent.timesteps_trained == 100

        agent.train(100)
        assert agent.timesteps_trained == 200
