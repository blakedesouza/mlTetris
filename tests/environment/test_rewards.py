"""Tests for reward shaping (ENV-04)."""

import pytest


class TestRewardType:
    """Tests for reward value type."""

    def test_reward_is_numeric(self, env):
        """Reward from step is numeric (int or float)."""
        env.reset()
        _, reward, _, _, _ = env.step(env.action_space.sample())
        assert isinstance(reward, (int, float))


class TestShapedRewardConfig:
    """Tests for shaped reward configuration."""

    def test_default_config_works(self, env):
        """Default reward configuration works."""
        env.reset()
        _, reward, _, _, _ = env.step(env.action_space.sample())
        # Should get some numeric reward
        assert isinstance(reward, (int, float))

    def test_custom_config_accepted(self, env_with_config):
        """Custom reward configuration is accepted."""
        env_with_config.reset()
        _, reward, _, _, _ = env_with_config.step(env_with_config.action_space.sample())
        assert isinstance(reward, (int, float))


class TestGameOverPenalty:
    """Tests for game over penalty."""

    def test_terminated_episode_has_negative_reward(self, env):
        """Terminated episode includes game over penalty (negative reward)."""
        env.reset()
        total_reward = 0
        done = False
        steps = 0
        max_steps = 10000

        while not done and steps < max_steps:
            _, reward, terminated, truncated, _ = env.step(env.action_space.sample())
            if terminated:
                # Game over penalty should be applied (default -10.0)
                assert reward < 0, "Game over should have negative reward"
            total_reward += reward
            done = terminated or truncated
            steps += 1


class TestRewardNotSparse:
    """Tests that rewards are not sparse (shaping provides intermediate rewards)."""

    def test_rewards_occur_before_game_over(self, env):
        """Rewards occur during gameplay, not just at game over."""
        env.reset()
        rewards = []
        done = False
        steps = 0
        max_steps = 100  # Limit steps for this test

        while not done and steps < max_steps:
            _, reward, terminated, truncated, _ = env.step(env.action_space.sample())
            rewards.append(reward)
            done = terminated or truncated
            steps += 1

        # Should have at least some non-zero rewards from shaping
        non_zero = [r for r in rewards if r != 0]
        assert len(non_zero) > 0, "Should have non-zero rewards from shaping"

    def test_reward_variety(self, env):
        """Rewards vary (not all the same value)."""
        env.reset()
        rewards = []
        done = False
        steps = 0
        max_steps = 50

        while not done and steps < max_steps:
            _, reward, terminated, truncated, _ = env.step(env.action_space.sample())
            rewards.append(reward)
            done = terminated or truncated
            steps += 1

        unique_rewards = set(rewards)
        # Should have more than 1 unique reward value due to shaping
        assert len(unique_rewards) > 1, "Rewards should vary due to shaping"


class TestHeightPenalty:
    """Tests for height penalty behavior."""

    def test_negative_rewards_occur(self, env):
        """Negative rewards should occur during gameplay due to height/hole penalties."""
        # Run multiple episodes if needed to find negative rewards
        found_negative = False

        for _ in range(5):  # Try up to 5 episodes
            env.reset()
            for _ in range(50):  # Check up to 50 steps per episode
                _, reward, terminated, _, _ = env.step(env.action_space.sample())
                if reward < 0:
                    found_negative = True
                    break
                if terminated:
                    break
            if found_negative:
                break

        assert found_negative, "Should see negative rewards from height/hole penalties"
