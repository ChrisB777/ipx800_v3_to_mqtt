"""Tests for auto-discovery."""

import pytest
import json
from src.auto_discovery import AutoDiscovery


class TestAutoDiscovery:
    """Test auto-discovery configuration generation."""

    @pytest.fixture
    def discovery(self):
        return AutoDiscovery("00:04:A3:87:00:1F")

    def test_generate_relay_config(self, discovery):
        """Test relay switch configuration."""
        config = discovery.generate_relay_config(0)

        assert config["name"] == "Relay 1"
        assert "unique_id" in config
        assert "state_topic" in config
        assert "command_topic" in config
        assert config["device"]["manufacturer"] == "GCE Electronics"

    def test_generate_input_config(self, discovery):
        """Test input binary sensor configuration."""
        config = discovery.generate_input_config(5)

        assert config["name"] == "Input 6"
        assert config["device_class"] == "connectivity"
        assert "state_topic" in config

    def test_get_discovery_topics(self, discovery):
        """Test discovery topics generation."""
        topics = discovery.get_discovery_topics()

        # 32 relays + 32 inputs = 64 topics
        assert len(topics) == 64

        # Check first relay topic
        topic, payload = topics[0]
        assert "homeassistant/switch/" in topic
        assert json.loads(payload)["name"] == "Relay 1"

    def test_custom_prefix(self):
        """Test custom topic prefix in discovery."""
        discovery = AutoDiscovery("00:04:A3:87:00:1F", topic_prefix="myhome")
        config = discovery.generate_relay_config(0)

        assert "myhome" in config["state_topic"]
        assert "myhome" in config["unique_id"]
