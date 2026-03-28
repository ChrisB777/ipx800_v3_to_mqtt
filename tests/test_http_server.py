"""Tests for HTTP push server."""

import pytest
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from src.http_server import PushServer
from src.state_manager import StateManager


class TestPushServer(AioHTTPTestCase):
    """Test push server endpoints."""

    async def get_application(self):
        """Create test application."""
        self.state_manager = StateManager()
        self.server = PushServer(8080, self.state_manager)
        return self.server.app

    @unittest_run_loop
    async def test_push_missing_params(self):
        """Test push with missing parameters."""
        resp = await self.client.request("GET", "/api/ipx/push")
        assert resp.status == 400

    @unittest_run_loop
    async def test_push_invalid_length(self):
        """Test push with invalid parameter length."""
        resp = await self.client.request(
            "GET", "/api/ipx/push?mac=00:04:A3:87:00:1F&inputs=123&outputs=123"
        )
        assert resp.status == 400

    @unittest_run_loop
    async def test_push_success(self):
        """Test successful push notification."""
        inputs = "0" * 32
        outputs = "1" * 32

        resp = await self.client.request(
            "GET",
            f"/api/ipx/push?mac=00:04:A3:87:00:1F&inputs={inputs}&outputs={outputs}",
        )

        assert resp.status == 200

        # Verify state was updated
        state = await self.state_manager.get_state()
        assert state.mac_address == "00:04:A3:87:00:1F"
        assert all(state.outputs)
