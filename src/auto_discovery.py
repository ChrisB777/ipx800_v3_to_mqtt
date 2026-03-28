"""HomeAssistant MQTT auto-discovery."""

import json
from typing import Dict, List
import structlog

logger = structlog.get_logger()


class AutoDiscovery:
    """Generate HomeAssistant discovery configurations."""

    def __init__(
        self,
        mac_address: str,
        device_name: str = "IPX800 v3",
        topic_prefix: str = "ipx800",
    ):
        self.mac_address = mac_address.replace(":", "")
        self.device_name = device_name
        self.topic_prefix = topic_prefix
        self._device_info = {
            "identifiers": [self.mac_address],
            "name": device_name,
            "manufacturer": "GCE Electronics",
            "model": "IPX800 v3",
            "connections": [["mac", mac_address]],
        }

    def generate_relay_config(self, index: int) -> Dict:
        """Generate switch configuration for a relay."""
        return {
            "name": f"Relay {index + 1}",
            "unique_id": f"{self.topic_prefix}_{self.mac_address}_relay_{index}",
            "state_topic": f"{self.topic_prefix}/{self.mac_address}/relay/{index}/state",
            "command_topic": f"{self.topic_prefix}/{self.mac_address}/relay/{index}/set",
            "payload_on": "ON",
            "payload_off": "OFF",
            "state_on": "ON",
            "state_off": "OFF",
            "device": self._device_info,
            "availability_topic": f"{self.topic_prefix}/{self.mac_address}/availability",
        }

    def generate_input_config(self, index: int) -> Dict:
        """Generate binary sensor configuration for an input."""
        return {
            "name": f"Input {index + 1}",
            "unique_id": f"{self.topic_prefix}_{self.mac_address}_input_{index}",
            "state_topic": f"{self.topic_prefix}/{self.mac_address}/input/{index}/state",
            "payload_on": "ON",
            "payload_off": "OFF",
            "device_class": "connectivity",
            "device": self._device_info,
            "availability_topic": f"{self.topic_prefix}/{self.mac_address}/availability",
        }

    def get_discovery_topics(self) -> List[tuple]:
        """Get all discovery topic/payload pairs."""
        topics = []

        # Relays (switches)
        for i in range(32):
            config = self.generate_relay_config(i)
            topic = f"homeassistant/switch/{self.topic_prefix}_{self.mac_address}_relay_{i}/config"
            topics.append((topic, json.dumps(config)))

        # Digital inputs (binary sensors)
        for i in range(32):
            config = self.generate_input_config(i)
            topic = f"homeassistant/binary_sensor/{self.topic_prefix}_{self.mac_address}_input_{i}/config"
            topics.append((topic, json.dumps(config)))

        return topics
