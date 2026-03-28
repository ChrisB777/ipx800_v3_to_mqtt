"""State manager for IPX800 states."""

import asyncio
from dataclasses import dataclass, field
from typing import Optional, Callable
import structlog

logger = structlog.get_logger()


@dataclass
class IPX800State:
    """Current state of IPX800."""

    mac_address: Optional[str] = None
    inputs: list[bool] = field(default_factory=lambda: [False] * 32)
    outputs: list[bool] = field(default_factory=lambda: [False] * 32)


class StateManager:
    """Thread-safe state manager with change detection."""

    def __init__(self):
        self._state = IPX800State()
        self._lock = asyncio.Lock()
        self._callbacks: list[Callable] = []

    async def update_mac(self, mac: str) -> bool:
        """Update MAC address. Returns True if changed."""
        async with self._lock:
            if self._state.mac_address != mac:
                self._state.mac_address = mac
                logger.info("mac_address_updated", mac=mac)
                return True
            return False

    async def update_inputs(self, inputs: list[bool]) -> list[int]:
        """Update input states. Returns list of changed indices."""
        async with self._lock:
            changed = []
            for i, (old, new) in enumerate(zip(self._state.inputs, inputs)):
                if old != new:
                    self._state.inputs[i] = new
                    changed.append(i)
            if changed:
                logger.debug("inputs_updated", changed=changed)
            return changed

    async def update_outputs(self, outputs: list[bool]) -> list[int]:
        """Update output states. Returns list of changed indices."""
        async with self._lock:
            changed = []
            for i, (old, new) in enumerate(zip(self._state.outputs, outputs)):
                if old != new:
                    self._state.outputs[i] = new
                    changed.append(i)
            if changed:
                logger.debug("outputs_updated", changed=changed)
            return changed

    async def set_output(self, index: int, value: bool) -> bool:
        """Set single output state. Returns True if changed."""
        async with self._lock:
            if 0 <= index < 32:
                if self._state.outputs[index] != value:
                    self._state.outputs[index] = value
                    return True
            return False

    async def get_state(self) -> IPX800State:
        """Get current state copy."""
        async with self._lock:
            return IPX800State(
                mac_address=self._state.mac_address,
                inputs=self._state.inputs.copy(),
                outputs=self._state.outputs.copy(),
            )

    async def get_mac(self) -> Optional[str]:
        """Get MAC address."""
        async with self._lock:
            return self._state.mac_address

    def register_callback(self, callback: Callable):
        """Register callback for state changes."""
        self._callbacks.append(callback)
