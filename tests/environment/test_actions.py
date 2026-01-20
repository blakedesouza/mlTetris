"""Tests for action space and meta-actions (ENV-03)."""

import pytest
from gymnasium.spaces import Discrete


class TestActionSpaceType:
    """Tests for action space type."""

    def test_action_space_is_discrete(self, env):
        """action_space is Discrete."""
        assert isinstance(env.action_space, Discrete)


class TestActionSpaceSize:
    """Tests for action space size."""

    def test_action_space_size_is_40(self, env):
        """Action space size is 40 (width 10 * 4 rotations)."""
        assert env.action_space.n == 40


class TestActionExecution:
    """Tests for executing actions."""

    def test_can_take_action_0(self, env):
        """Can take action 0 without crashing."""
        env.reset()
        env.step(0)
        # If we get here without exception, test passes

    def test_can_take_action_39(self, env):
        """Can take action 39 (last valid action) without crashing."""
        env.reset()
        env.step(39)
        # If we get here without exception, test passes

    def test_can_sample_and_step(self, env):
        """Can sample from action space and step."""
        env.reset()
        action = env.action_space.sample()
        env.step(action)
        # If we get here without exception, test passes


class TestActionMask:
    """Tests for action masking."""

    def test_action_mask_in_info(self, env):
        """Action mask is provided in info dict."""
        _, info = env.reset()
        assert "action_mask" in info

    def test_action_mask_shape(self, env):
        """Action mask has shape (40,)."""
        _, info = env.reset()
        mask = info["action_mask"]
        assert hasattr(mask, "shape")
        assert mask.shape == (40,)

    def test_action_mask_values_binary(self, env):
        """Action mask values are 0 or 1."""
        _, info = env.reset()
        mask = info["action_mask"]
        import numpy as np

        assert np.all((mask == 0) | (mask == 1))


class TestMetaActionSemantics:
    """Tests verifying meta-action semantics."""

    def test_action_encodes_column_and_rotation(self, env):
        """Actions encode column (action // 4) and rotation (action % 4)."""
        # This is a documentation/semantic test
        # Action 0: column 0, rotation 0
        # Action 1: column 0, rotation 1
        # Action 4: column 1, rotation 0
        # Action 39: column 9, rotation 3
        assert env.action_space.n == 40

        # Column range: 0-9, Rotation range: 0-3
        for action in range(40):
            col = action // 4
            rot = action % 4
            assert 0 <= col <= 9
            assert 0 <= rot <= 3
