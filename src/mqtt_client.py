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
        state_manager=None,
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
