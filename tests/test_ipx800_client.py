"""Tests for IPX800 client."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import aiohttp
from src.ipx800_client import IPX800Client


class TestIPX800Client:
    """Test IPX800 API client."""

    @pytest.fixture
    def client(self):
        return IPX800Client("192.168.1.100", 80, "admin", "password")

    def test_init(self, client):
        """Test client initialization."""
        assert client.base_url == "http://192.168.1.100:80"
        assert client.username == "admin"
        assert client.password == "password"

    def test_parse_global_status(self, client):
        """Test XML parsing."""
        xml_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
        <response>
            <mac>00:04:A3:87:00:1F</mac>
            <btn1>1</btn1>
            <btn2>0</btn2>
            <led0>1</led0>
            <led1>0</led1>
        </response>"""

        mac, inputs, outputs = client._parse_global_status(xml_content)

        assert mac == "00:04:A3:87:00:1F"
        assert inputs[0] is True  # btn1
        assert inputs[1] is False  # btn2
        assert outputs[0] is True  # led0
        assert outputs[1] is False  # led1

    @pytest.mark.asyncio
    async def test_set_output_invalid_index(self, client):
        """Test set_output with invalid index."""
        result = await client.set_output(32, True)
        assert result is False

        result = await client.set_output(-1, True)
        assert result is False

    @pytest.mark.asyncio
    async def test_get_global_status_returns_coroutine(self, client):
        """Test that get_global_status is async and returns a coroutine."""
        import inspect

        result = client.get_global_status()
        assert inspect.iscoroutine(result)
        result.close()  # Clean up unawaited coroutine

    @pytest.mark.asyncio
    async def test_set_output_returns_coroutine(self, client):
        """Test that set_output is async and returns a coroutine."""
        import inspect

        result = client.set_output(0, True)
        assert inspect.iscoroutine(result)
        result.close()  # Clean up unawaited coroutine
