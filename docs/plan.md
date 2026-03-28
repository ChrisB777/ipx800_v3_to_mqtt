# IPX800 v3 to MQTT - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Dockerized Python bridge that connects IPX800 v3 to MQTT with HomeAssistant auto-discovery

**Architecture:** Asyncio-based monolithic service with HTTP server for push notifications, MQTT client, periodic polling fallback, and state management

**Tech Stack:** Python 3.11, asyncio, aiohttp, paho-mqtt, pydantic

---

## Project Structure

```
ipx800-v3-mqtt/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration management
│   ├── state_manager.py     # State management
│   ├── ipx800_client.py     # IPX800 API client
│   ├── mqtt_client.py       # MQTT client wrapper
│   ├── http_server.py       # HTTP server for push
│   └── auto_discovery.py    # HomeAssistant discovery
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_state_manager.py
│   ├── test_ipx800_client.py
│   ├── test_mqtt_client.py
│   └── conftest.py
├── Dockerfile
├── requirements.txt
├── docker-compose.yml
└── README.md
```

---

## Task 1: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.gitignore`

### Step 1.1: Create requirements.txt

```txt
aiohttp==3.9.1
paho-mqtt==1.6.1
pydantic==2.5.0
pydantic-settings==2.1.0
structlog==23.2.0
```

### Step 1.2: Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "-m", "src.main"]
```

### Step 1.3: Create docker-compose.yml

```yaml
version: '3.8'

services:
  ipx800-mqtt:
    build: .
    container_name: ipx800-mqtt
    ports:
      - "8080:8080"
    environment:
      - IPX800_HOST=${IPX800_HOST:-192.168.1.100}
      - IPX800_PORT=${IPX800_PORT:-80}
      - IPX800_USERNAME=${IPX800_USERNAME:-admin}
      - IPX800_PASSWORD=${IPX800_PASSWORD}
      - MQTT_BROKER_HOST=${MQTT_BROKER_HOST:-mosquitto}
      - MQTT_BROKER_PORT=${MQTT_BROKER_PORT:-1883}
      - MQTT_USERNAME=${MQTT_USERNAME}
      - MQTT_PASSWORD=${MQTT_PASSWORD}
      - HTTP_PORT=${HTTP_PORT:-8080}
      - POLLING_INTERVAL=${POLLING_INTERVAL:-30}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    restart: unless-stopped
```

### Step 1.4: Create .gitignore

```gitignore
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/
.coverage
.env
.venv
venv/
ENV/
```

### Step 1.5: Commit

```bash
git add requirements.txt Dockerfile docker-compose.yml .gitignore
git commit -m "chore: initial project setup"
```

---

## Task 2: Configuration Module

**Files:**
- Create: `src/__init__.py`
- Create: `src/config.py`
- Test: `tests/test_config.py`

### Step 2.1: Create src/config.py

```python
"""Configuration module using pydantic-settings."""
from pydantic import Field
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration from environment variables."""
    
    # IPX800 Configuration
    ipx800_host: str = Field(default="192.168.1.100", alias="IPX800_HOST")
    ipx800_port: int = Field(default=80, alias="IPX800_PORT")
    ipx800_username: str = Field(default="admin", alias="IPX800_USERNAME")
    ipx800_password: str = Field(default="", alias="IPX800_PASSWORD")
    
    # MQTT Configuration
    mqtt_broker_host: str = Field(default="mosquitto", alias="MQTT_BROKER_HOST")
    mqtt_broker_port: int = Field(default=1883, alias="MQTT_BROKER_PORT")
    mqtt_username: str = Field(default="", alias="MQTT_USERNAME")
    mqtt_password: str = Field(default="", alias="MQTT_PASSWORD")
    mqtt_client_id: str = Field(default="ipx800-bridge", alias="MQTT_CLIENT_ID")
    
    # Bridge Configuration
    http_port: int = Field(default=8080, alias="HTTP_PORT")
    polling_interval: int = Field(default=30, alias="POLLING_INTERVAL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    class Config:
        env_prefix = ""
        case_sensitive = False


def get_config() -> Config:
    """Get application configuration."""
    return Config()
```

### Step 2.2: Create tests/test_config.py

```python
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
```

### Step 2.3: Run tests to verify

```bash
python -m pytest tests/test_config.py -v
```

Expected: All tests pass

### Step 2.4: Commit

```bash
git add src/__init__.py src/config.py tests/__init__.py tests/test_config.py
git commit -m "feat: add configuration module with pydantic-settings"
```

---

## Task 3: State Manager

**Files:**
- Create: `src/state_manager.py`
- Test: `tests/test_state_manager.py`

### Step 3.1: Create src/state_manager.py

```python
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
                outputs=self._state.outputs.copy()
            )
    
    async def get_mac(self) -> Optional[str]:
        """Get MAC address."""
        async with self._lock:
            return self._state.mac_address
    
    def register_callback(self, callback: Callable):
        """Register callback for state changes."""
        self._callbacks.append(callback)
```

### Step 3.2: Create tests/test_state_manager.py

```python
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
```

### Step 3.3: Run tests

```bash
python -m pytest tests/test_state_manager.py -v
```

Expected: All tests pass

### Step 3.4: Commit

```bash
git add src/state_manager.py tests/test_state_manager.py
git commit -m "feat: add thread-safe state manager"
```

---

## Task 4: IPX800 API Client

**Files:**
- Create: `src/ipx800_client.py`
- Test: `tests/test_ipx800_client.py`

### Step 4.1: Create src/ipx800_client.py

```python
"""IPX800 API client."""
import aiohttp
import xml.etree.ElementTree as ET
from typing import Optional, Tuple
import structlog

logger = structlog.get_logger()


class IPX800Client:
    """Client for IPX800 v3 API."""
    
    def __init__(self, host: str, port: int, username: str, password: str):
        self.base_url = f"http://{host}:{port}"
        self.username = username
        self.password = password
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            auth = aiohttp.BasicAuth(self.username, self.password)
            self._session = aiohttp.ClientSession(auth=auth)
        return self._session
    
    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def get_global_status(self) -> Optional[Tuple[str, list[bool], list[bool]]]:
        """Fetch global status from IPX800.
        
        Returns: (mac_address, inputs, outputs) or None on error
        """
        try:
            session = await self._get_session()
            url = f"{self.base_url}/globalstatus.xml"
            
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    logger.error("failed to fetch status", status=response.status)
                    return None
                
                xml_content = await response.text()
                return self._parse_global_status(xml_content)
        
        except Exception as e:
            logger.error("error fetching status", error=str(e))
            return None
    
    def _parse_global_status(self, xml_content: str) -> Tuple[str, list[bool], list[bool]]:
        """Parse globalstatus.xml content."""
        root = ET.fromstring(xml_content)
        
        # Extract MAC address
        mac_elem = root.find('mac')
        mac = mac_elem.text if mac_elem is not None else "unknown"
        
        # Parse inputs (16 standard entrées)
        inputs = []
        for i in range(1, 33):
            elem = root.find(f'btn{i}')
            if elem is not None:
                inputs.append(elem.text == '1')
            else:
                inputs.append(False)
        
        # Parse outputs (relays)
        outputs = []
        for i in range(0, 32):
            elem = root.find(f'led{i}')
            if elem is not None:
                outputs.append(elem.text == '1')
            else:
                outputs.append(False)
        
        return mac, inputs, outputs
    
    async def set_output(self, index: int, value: bool) -> bool:
        """Set relay state.
        
        Args:
            index: Relay index (0-31)
            value: True for ON, False for OFF
        
        Returns:
            True if successful
        """
        try:
            session = await self._get_session()
            # Use preset.htm for forced ON/OFF
            url = f"{self.base_url}/preset.htm?set{index+1}={1 if value else 0}"
            
            async with session.get(url, timeout=10) as response:
                return response.status == 200
        
        except Exception as e:
            logger.error("error setting output", index=index, value=value, error=str(e))
            return False
```

### Step 4.2: Create tests/test_ipx800_client.py

```python
"""Tests for IPX800 client."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
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
```

### Step 4.3: Run tests

```bash
python -m pytest tests/test_ipx800_client.py -v
```

### Step 4.4: Commit

```bash
git add src/ipx800_client.py tests/test_ipx800_client.py
git commit -m "feat: add IPX800 API client with XML parsing"
```

---

## Task 5: MQTT Client

**Files:**
- Create: `src/mqtt_client.py`
- Test: `tests/test_mqtt_client.py`

### Step 5.1: Create src/mqtt_client.py

```python
"""MQTT client for HomeAssistant integration."""
import asyncio
import json
from typing import Optional, Callable, Awaitable
import paho.mqtt.client as mqtt
import structlog

logger = structlog.get_logger()


class MQTTClient:
    """MQTT client with auto-reconnection."""
    
    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        client_id: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        state_manager=None
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.state_manager = state_manager
        
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._command_handler: Optional[Callable[[int, str], Awaitable[bool]]] = None
        self._mac_address: Optional[str] = None
    
    def set_mac_address(self, mac: str):
        """Set MAC address for topic construction."""
        self._mac_address = mac.replace(":", "")
    
    def set_command_handler(self, handler: Callable[[int, str], Awaitable[bool]]):
        """Set handler for incoming commands."""
        self._command_handler = handler
    
    def connect(self):
        """Connect to MQTT broker."""
        self._client = mqtt.Client(client_id=self.client_id)
        
        if self.username and self.password:
            self._client.username_pw_set(self.username, self.password)
        
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        
        try:
            self._client.connect(self.broker_host, self.broker_port, 60)
            self._client.loop_start()
            logger.info("mqtt_connecting", host=self.broker_host, port=self.broker_port)
        except Exception as e:
            logger.error("mqtt_connection_failed", error=str(e))
    
    def _on_connect(self, client, userdata, flags, rc):
        """Handle connection callback."""
        if rc == 0:
            self._connected = True
            logger.info("mqtt_connected")
            self._subscribe_commands()
        else:
            logger.error("mqtt_connection_refused", code=rc)
    
    def _on_disconnect(self, client, userdata, rc):
        """Handle disconnection."""
        self._connected = False
        if rc != 0:
            logger.warning("mqtt_unexpected_disconnect", code=rc)
        else:
            logger.info("mqtt_disconnected")
    
    def _subscribe_commands(self):
        """Subscribe to command topics."""
        if not self._mac_address:
            return
        
        topic = f"ipx800/{self._mac_address}/relay/+/set"
        self._client.subscribe(topic)
        logger.info("mqtt_subscribed", topic=topic)
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming message."""
        asyncio.create_task(self._handle_message(msg))
    
    async def _handle_message(self, msg):
        """Process incoming command."""
        try:
            # Parse topic: ipx800/{mac}/relay/{n}/set
            parts = msg.topic.split("/")
            if len(parts) >= 5 and parts[3].isdigit():
                relay_index = int(parts[3])
                command = msg.payload.decode().upper()
                
                logger.info("mqtt_command_received", relay=relay_index, command=command)
                
                if self._command_handler:
                    success = await self._command_handler(relay_index, command)
                    if success:
                        # Publish state confirmation
                        await self.publish_relay_state(relay_index, command == "ON")
        
        except Exception as e:
            logger.error("mqtt_message_error", error=str(e))
    
    async def publish_relay_state(self, index: int, state: bool):
        """Publish relay state."""
        if not self._connected or not self._mac_address:
            return
        
        topic = f"ipx800/{self._mac_address}/relay/{index}/state"
        payload = "ON" if state else "OFF"
        
        self._client.publish(topic, payload, retain=True)
        logger.debug("mqtt_published", topic=topic, payload=payload)
    
    async def publish_input_state(self, index: int, state: bool):
        """Publish input state."""
        if not self._connected or not self._mac_address:
            return
        
        topic = f"ipx800/{self._mac_address}/input/{index}/state"
        payload = "ON" if state else "OFF"
        
        self._client.publish(topic, payload, retain=True)
        logger.debug("mqtt_published", topic=topic, payload=payload)
    
    async def publish_availability(self, available: bool):
        """Publish availability status."""
        if not self._connected or not self._mac_address:
            return
        
        topic = f"ipx800/{self._mac_address}/availability"
        payload = "online" if available else "offline"
        
        self._client.publish(topic, payload, retain=True)
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
```

### Step 5.2: Create tests/test_mqtt_client.py

```python
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
```

### Step 5.3: Run tests

```bash
python -m pytest tests/test_mqtt_client.py -v
```

### Step 5.4: Commit

```bash
git add src/mqtt_client.py tests/test_mqtt_client.py
git commit -m "feat: add MQTT client with command handling"
```

---

## Task 6: Auto-Discovery

**Files:**
- Create: `src/auto_discovery.py`
- Test: `tests/test_auto_discovery.py`

### Step 6.1: Create src/auto_discovery.py

```python
"""HomeAssistant MQTT auto-discovery."""
import json
from typing import Dict, List
import structlog

logger = structlog.get_logger()


class AutoDiscovery:
    """Generate HomeAssistant discovery configurations."""
    
    def __init__(self, mac_address: str, device_name: str = "IPX800 v3"):
        self.mac_address = mac_address.replace(":", "")
        self.device_name = device_name
        self._device_info = {
            "identifiers": [self.mac_address],
            "name": device_name,
            "manufacturer": "GCE Electronics",
            "model": "IPX800 v3",
            "connections": [["mac", mac_address]]
        }
    
    def generate_relay_config(self, index: int) -> Dict:
        """Generate switch configuration for a relay."""
        return {
            "name": f"Relay {index + 1}",
            "unique_id": f"ipx800_{self.mac_address}_relay_{index}",
            "state_topic": f"ipx800/{self.mac_address}/relay/{index}/state",
            "command_topic": f"ipx800/{self.mac_address}/relay/{index}/set",
            "payload_on": "ON",
            "payload_off": "OFF",
            "state_on": "ON",
            "state_off": "OFF",
            "device": self._device_info,
            "availability_topic": f"ipx800/{self.mac_address}/availability"
        }
    
    def generate_input_config(self, index: int) -> Dict:
        """Generate binary sensor configuration for an input."""
        return {
            "name": f"Input {index + 1}",
            "unique_id": f"ipx800_{self.mac_address}_input_{index}",
            "state_topic": f"ipx800/{self.mac_address}/input/{index}/state",
            "payload_on": "ON",
            "payload_off": "OFF",
            "device_class": "connectivity",
            "device": self._device_info,
            "availability_topic": f"ipx800/{self.mac_address}/availability"
        }
    
    def get_discovery_topics(self) -> List[tuple]:
        """Get all discovery topic/payload pairs."""
        topics = []
        
        # Relays (switches)
        for i in range(32):
            config = self.generate_relay_config(i)
            topic = f"homeassistant/switch/ipx800_{self.mac_address}_relay_{i}/config"
            topics.append((topic, json.dumps(config)))
        
        # Digital inputs (binary sensors)
        for i in range(32):
            config = self.generate_input_config(i)
            topic = f"homeassistant/binary_sensor/ipx800_{self.mac_address}_input_{i}/config"
            topics.append((topic, json.dumps(config)))
        
        return topics
```

### Step 6.2: Create tests/test_auto_discovery.py

```python
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
```

### Step 6.3: Run tests

```bash
python -m pytest tests/test_auto_discovery.py -v
```

### Step 6.4: Commit

```bash
git add src/auto_discovery.py tests/test_auto_discovery.py
git commit -m "feat: add HomeAssistant auto-discovery"
```

---

## Task 7: HTTP Server for Push Notifications

**Files:**
- Create: `src/http_server.py`
- Test: `tests/test_http_server.py`

### Step 7.1: Create src/http_server.py

```python
"""HTTP server for receiving IPX800 push notifications."""
from aiohttp import web
import structlog

logger = structlog.get_logger()


class PushServer:
    """HTTP server to receive IPX800 push notifications."""
    
    def __init__(self, port: int, state_manager):
        self.port = port
        self.state_manager = state_manager
        self.app = web.Application()
        self.app.router.add_get('/api/ipx/push', self.handle_push)
        self.runner: web.AppRunner = None
    
    async def handle_push(self, request: web.Request) -> web.Response:
        """Handle push notification from IPX800.
        
        Expected query params:
        - mac: MAC address (format: 00:04:A3:87:00:1F)
        - inputs: 32 chars of 0/1 representing input states
        - outputs: 32 chars of 0/1 representing output states
        """
        try:
            mac = request.query.get('mac')
            inputs_str = request.query.get('inputs')
            outputs_str = request.query.get('outputs')
            
            if not all([mac, inputs_str, outputs_str]):
                logger.warning("push_missing_params", 
                              mac=bool(mac), 
                              inputs=bool(inputs_str), 
                              outputs=bool(outputs_str))
                return web.Response(status=400, text="Missing parameters")
            
            # Validate input length
            if len(inputs_str) != 32 or len(outputs_str) != 32:
                logger.warning("push_invalid_length",
                              inputs_len=len(inputs_str),
                              outputs_len=len(outputs_str))
                return web.Response(status=400, text="Invalid parameter length")
            
            # Parse states
            inputs = [c == '1' for c in inputs_str]
            outputs = [c == '1' for c in outputs_str]
            
            # Update state manager
            await self.state_manager.update_mac(mac)
            changed_inputs = await self.state_manager.update_inputs(inputs)
            changed_outputs = await self.state_manager.update_outputs(outputs)
            
            logger.info("push_processed",
                       mac=mac,
                       changed_inputs=len(changed_inputs),
                       changed_outputs=len(changed_outputs))
            
            return web.Response(status=200, text="OK")
        
        except Exception as e:
            logger.error("push_processing_error", error=str(e))
            return web.Response(status=500, text="Internal error")
    
    async def start(self):
        """Start the HTTP server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, '0.0.0.0', self.port)
        await site.start()
        logger.info("http_server_started", port=self.port)
    
    async def stop(self):
        """Stop the HTTP server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("http_server_stopped")
```

### Step 7.2: Create tests/test_http_server.py

```python
"""Tests for HTTP push server."""
import pytest
from unittest.mock import AsyncMock
from aiohttp import web
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
            "GET", 
            "/api/ipx/push?mac=00:04:A3:87:00:1F&inputs=123&outputs=123"
        )
        assert resp.status == 400
    
    @unittest_run_loop
    async def test_push_success(self):
        """Test successful push notification."""
        inputs = "0" * 32
        outputs = "1" * 32
        
        resp = await self.client.request(
            "GET",
            f"/api/ipx/push?mac=00:04:A3:87:00:1F&inputs={inputs}&outputs={outputs}"
        )
        
        assert resp.status == 200
        
        # Verify state was updated
        state = await self.state_manager.get_state()
        assert state.mac_address == "00:04:A3:87:00:1F"
        assert all(state.outputs)
```

### Step 7.3: Run tests

```bash
python -m pytest tests/test_http_server.py -v
```

### Step 7.4: Commit

```bash
git add src/http_server.py tests/test_http_server.py
git commit -m "feat: add HTTP server for IPX800 push notifications"
```

---

## Task 8: Main Application

**Files:**
- Create: `src/main.py`

### Step 8.1: Create src/main.py

```python
"""Main application entry point."""
import asyncio
import signal
import sys
from typing import Optional

import structlog

from src.config import get_config
from src.state_manager import StateManager
from src.ipx800_client import IPX800Client
from src.mqtt_client import MQTTClient
from src.http_server import PushServer
from src.auto_discovery import AutoDiscovery

logger = structlog.get_logger()


class IPX800Bridge:
    """Main bridge application."""
    
    def __init__(self):
        self.config = get_config()
        self.state_manager = StateManager()
        self.ipx_client: Optional[IPX800Client] = None
        self.mqtt_client: Optional[MQTTClient] = None
        self.http_server: Optional[PushServer] = None
        self._shutdown_event = asyncio.Event()
        self._polling_task: Optional[asyncio.Task] = None
        
        # Configure logging
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ]
        )
    
    async def setup(self):
        """Initialize all components."""
        logger.info("bridge_starting")
        
        # Create IPX800 client
        self.ipx_client = IPX800Client(
            self.config.ipx800_host,
            self.config.ipx800_port,
            self.config.ipx800_username,
            self.config.ipx800_password
        )
        
        # Create MQTT client
        self.mqtt_client = MQTTClient(
            self.config.mqtt_broker_host,
            self.config.mqtt_broker_port,
            self.config.mqtt_client_id,
            self.config.mqtt_username,
            self.config.mqtt_password,
            self.state_manager
        )
        self.mqtt_client.set_command_handler(self.handle_mqtt_command)
        
        # Create HTTP server
        self.http_server = PushServer(
            self.config.http_port,
            self.state_manager
        )
        
        # Start HTTP server
        await self.http_server.start()
        
        # Connect to MQTT
        self.mqtt_client.connect()
        
        # Initial polling to get MAC address
        await self.poll_ipx800()
        
        # Start polling task
        self._polling_task = asyncio.create_task(self.polling_loop())
        
        logger.info("bridge_started")
    
    async def handle_mqtt_command(self, relay_index: int, command: str) -> bool:
        """Handle relay command from MQTT."""
        if not self.ipx_client:
            return False
        
        value = command == "ON"
        success = await self.ipx_client.set_output(relay_index, value)
        
        if success:
            await self.state_manager.set_output(relay_index, value)
        
        return success
    
    async def poll_ipx800(self):
        """Poll IPX800 for current state."""
        if not self.ipx_client:
            return
        
        result = await self.ipx_client.get_global_status()
        if result:
            mac, inputs, outputs = result
            
            # Update MAC and set in MQTT client
            await self.state_manager.update_mac(mac)
            if self.mqtt_client and not self.mqtt_client._mac_address:
                self.mqtt_client.set_mac_address(mac)
                # Publish auto-discovery
                await self.publish_auto_discovery()
                # Publish availability
                await self.mqtt_client.publish_availability(True)
            
            # Update states
            changed_inputs = await self.state_manager.update_inputs(inputs)
            changed_outputs = await self.state_manager.update_outputs(outputs)
            
            # Publish changes to MQTT
            if self.mqtt_client:
                for idx in changed_outputs:
                    await self.mqtt_client.publish_relay_state(idx, outputs[idx])
                for idx in changed_inputs:
                    await self.mqtt_client.publish_input_state(idx, inputs[idx])
    
    async def polling_loop(self):
        """Background polling task."""
        while not self._shutdown_event.is_set():
            try:
                await self.poll_ipx800()
            except Exception as e:
                logger.error("polling_error", error=str(e))
            
            try:
                await asyncio.wait_for(
                    self._shutdown_event.wait(),
                    timeout=self.config.polling_interval
                )
            except asyncio.TimeoutError:
                continue
    
    async def publish_auto_discovery(self):
        """Publish HomeAssistant auto-discovery configurations."""
        mac = await self.state_manager.get_mac()
        if not mac or not self.mqtt_client:
            return
        
        discovery = AutoDiscovery(mac)
        topics = discovery.get_discovery_topics()
        
        for topic, payload in topics:
            self.mqtt_client._client.publish(topic, payload, retain=True)
        
        logger.info("auto_discovery_published", count=len(topics))
    
    async def shutdown(self):
        """Graceful shutdown."""
        logger.info("bridge_shutting_down")
        
        self._shutdown_event.set()
        
        if self._polling_task:
            self._polling_task.cancel()
            try:
                await self._polling_task
            except asyncio.CancelledError:
                pass
        
        if self.mqtt_client:
            await self.mqtt_client.publish_availability(False)
            self.mqtt_client.disconnect()
        
        if self.http_server:
            await self.http_server.stop()
        
        if self.ipx_client:
            await self.ipx_client.close()
        
        logger.info("bridge_stopped")
    
    def run(self):
        """Run the bridge."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.shutdown()))
        
        try:
            loop.run_until_complete(self.setup())
            loop.run_until_complete(self._shutdown_event.wait())
        except Exception as e:
            logger.error("bridge_error", error=str(e))
        finally:
            loop.run_until_complete(self.shutdown())
            loop.close()


if __name__ == "__main__":
    bridge = IPX800Bridge()
    bridge.run()
```

### Step 8.2: Commit

```bash
git add src/main.py
git commit -m "feat: add main application with asyncio event loop"
```

---

## Task 9: Documentation

**Files:**
- Create: `README.md`

### Step 9.1: Create README.md

```markdown
# IPX800 v3 to MQTT Bridge

Bridge Dockerisé pour connecter une carte IPX800 v3 à HomeAssistant via MQTT.

## Fonctionnalités

- **Push notifications** : Réception instantanée des changements d'état via HTTP
- **Polling** : Récupération périodique (30s par défaut) pour garantir la cohérence
- **Auto-discovery** : Détection automatique par HomeAssistant
- **32 relais** : Commande ON/OFF avec état en temps réel
- **32 entrées digitales** : État des entrées

## Configuration

### Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|---------|
| `IPX800_HOST` | IP de l'IPX800 | 192.168.1.100 |
| `IPX800_PORT` | Port HTTP de l'IPX800 | 80 |
| `IPX800_USERNAME` | Utilisateur IPX800 | admin |
| `IPX800_PASSWORD` | Mot de passe IPX800 | - |
| `MQTT_BROKER_HOST` | Host du broker MQTT | mosquitto |
| `MQTT_BROKER_PORT` | Port MQTT | 1883 |
| `MQTT_USERNAME` | Utilisateur MQTT (optionnel) | - |
| `MQTT_PASSWORD` | Mot de passe MQTT (optionnel) | - |
| `HTTP_PORT` | Port du serveur HTTP | 8080 |
| `POLLING_INTERVAL` | Intervalle de polling (s) | 30 |

### Configuration IPX800

Dans l'interface web de l'IPX800, configurer une notification push :

**URL**: `http://<container-ip>:8080/api/ipx/push?mac=$M&inputs=$I&outputs=$O`

## Utilisation

### Docker Compose

```bash
docker-compose up -d
```

### HomeAssistant

Les entités sont automatiquement découvertes sous le préfixe `ipx800_`.

- **Relais** : `switch.ipx800_XXXXXXXXXXXX_relay_X`
- **Entrées** : `binary_sensor.ipx800_XXXXXXXXXXXX_input_X`

## Topics MQTT

### Publication

- `ipx800/{mac}/relay/{n}/state` - État des relais
- `ipx800/{mac}/input/{n}/state` - État des entrées
- `ipx800/{mac}/availability` - Online/offline

### Commande

- `ipx800/{mac}/relay/{n}/set` - Commander un relais (ON/OFF)

## Développement

### Tests

```bash
python -m pytest tests/ -v
```

### Build

```bash
docker build -t ipx800-mqtt .
```
```

### Step 9.2: Commit

```bash
git add README.md
git commit -m "docs: add comprehensive README"
```

---

## Verification

### Run all tests

```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

Expected: All tests pass with >80% coverage

### Build and test Docker

```bash
docker-compose build
docker-compose up -d
```

Check logs:
```bash
docker-compose logs -f
```

---

## Summary

This implementation plan creates a complete IPX800 v3 to MQTT bridge with:

1. **8 modules** with comprehensive test coverage
2. **Docker containerization** ready for deployment
3. **HomeAssistant integration** via MQTT auto-discovery
4. **Hybrid push/polling** architecture for reliability
5. **Configuration management** via environment variables

The bridge handles:
- 32 relays (switches) with ON/OFF commands
- 32 digital inputs (binary sensors)
- Real-time state updates via HTTP push
- Fallback polling every 30 seconds
- Auto-discovery for seamless HA integration
