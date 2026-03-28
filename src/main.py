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
                structlog.processors.JSONRenderer(),
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
            self.config.ipx800_password,
        )

        # Create MQTT client
        self.mqtt_client = MQTTClient(
            self.config.mqtt_broker_host,
            self.config.mqtt_broker_port,
            self.config.mqtt_client_id,
            self.config.mqtt_username,
            self.config.mqtt_password,
            self.state_manager,
            topic_prefix=self.config.mqtt_topic_prefix,
        )
        self.mqtt_client.set_command_handler(self.handle_mqtt_command)

        # Create HTTP server
        self.http_server = PushServer(self.config.http_port, self.state_manager)

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
                    self._shutdown_event.wait(), timeout=self.config.polling_interval
                )
            except asyncio.TimeoutError:
                continue

    async def publish_auto_discovery(self):
        """Publish HomeAssistant auto-discovery configurations."""
        mac = await self.state_manager.get_mac()
        if not mac or not self.mqtt_client:
            return

        discovery = AutoDiscovery(mac, topic_prefix=self.config.mqtt_topic_prefix)
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
