"""Tests for MQTT client."""

import pytest
from unittest.mock import Mock, patch
from src.mqtt_client import MQTTClient


class TestMQTTClient:
    """Test MQTT client functionality."""

    @pytest.fixture
    def client(self):
        return MQTTClient("mosquitto", 1883, "test-client")

    def test_init(self, client):
        """Test client initialization."""
        assert client.broker_host == "mosquitto"
        assert client.broker_port == 1883
        assert client.client_id == "test-client"

    def test_set_mac_address(self, client):
        """Test MAC address formatting."""
        client.set_mac_address("00:04:A3:87:00:1F")
        assert client._mac_address == "0004A387001F"

    def test_topic_prefix(self):
        """Test custom topic prefix."""
        client = MQTTClient("mosquitto", 1883, "test-client", topic_prefix="myhome")
        assert client.topic_prefix == "myhome"
