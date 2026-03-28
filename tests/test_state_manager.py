"""Tests for state manager."""

import pytest
import asyncio
from src.state_manager import StateManager, IPX800State


class TestStateManager:
    """Test state manager functionality."""

    @pytest.fixture
    def state_manager(self):
        return StateManager()

    @pytest.mark.asyncio
    async def test_update_mac(self, state_manager):
        """Test MAC address update."""
        changed = await state_manager.update_mac("00:04:A3:87:00:1F")
        assert changed is True

        # Second update with same value
        changed = await state_manager.update_mac("00:04:A3:87:00:1F")
        assert changed is False

        mac = await state_manager.get_mac()
        assert mac == "00:04:A3:87:00:1F"

    @pytest.mark.asyncio
    async def test_update_inputs(self, state_manager):
        """Test input state updates."""
        inputs = [False] * 32
        inputs[0] = True
        inputs[5] = True

        changed = await state_manager.update_inputs(inputs)
        assert 0 in changed
        assert 5 in changed

        # Same values, no change
        changed = await state_manager.update_inputs(inputs)
        assert len(changed) == 0

    @pytest.mark.asyncio
    async def test_update_outputs(self, state_manager):
        """Test output state updates."""
        outputs = [False] * 32
        outputs[10] = True

        changed = await state_manager.update_outputs(outputs)
        assert 10 in changed

        state = await state_manager.get_state()
        assert state.outputs[10] is True

    @pytest.mark.asyncio
    async def test_set_output(self, state_manager):
        """Test setting single output."""
        changed = await state_manager.set_output(0, True)
        assert changed is True

        changed = await state_manager.set_output(0, True)
        assert changed is False

        # Invalid index
        changed = await state_manager.set_output(32, True)
        assert changed is False
