"""Tests for configuration module."""

import os
import pytest
from src.config import Config, get_config


class TestConfig:
    """Test configuration loading."""

    def test_default_values(self):
        """Test default configuration values."""
        config = Config()
        assert config.ipx800_host == "192.168.1.100"
        assert config.ipx800_port == 80
        assert config.ipx800_username == "admin"
        assert config.mqtt_broker_port == 1883
        assert config.http_port == 8080
        assert config.polling_interval == 30

    def test_environment_override(self, monkeypatch):
        """Test environment variable override."""
        monkeypatch.setenv("IPX800_HOST", "10.0.0.50")
        monkeypatch.setenv("HTTP_PORT", "9090")

        config = Config()
        assert config.ipx800_host == "10.0.0.50"
        assert config.http_port == 9090

    def test_get_config_singleton(self, monkeypatch):
        """Test get_config returns Config instance."""
        monkeypatch.setenv("IPX800_HOST", "192.168.0.10")
        config = get_config()
        assert isinstance(config, Config)
        assert config.ipx800_host == "192.168.0.10"

    def test_topic_prefix_default(self):
        """Test default MQTT topic prefix."""
        config = Config()
        assert config.mqtt_topic_prefix == "ipx800"

    def test_topic_prefix_override(self, monkeypatch):
        """Test MQTT topic prefix override."""
        monkeypatch.setenv("MQTT_TOPIC_PREFIX", "myhome")
        config = Config()
        assert config.mqtt_topic_prefix == "myhome"
