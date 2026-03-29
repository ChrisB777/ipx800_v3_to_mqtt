"""HTTP server for receiving IPX800 push notifications."""

from typing import Callable, Optional
from aiohttp import web
import structlog

logger = structlog.get_logger()


class PushServer:
    """HTTP server to receive IPX800 push notifications."""

    def __init__(self, port: int, state_manager):
        self.port = port
        self.state_manager = state_manager
        self.app = web.Application()
        self.app.router.add_get("/", self.handle_root)
        self.app.router.add_get("/api/ipx/push", self.handle_push)
        self.app.router.add_post("/api/ipx/push", self.handle_push)
        self.runner: web.AppRunner = None
        self._change_handler: Optional[Callable[[int, bool, bool], None]] = None

    def set_change_handler(self, handler: Callable[[int, bool, bool], None]):
        """Set handler for state changes (index, is_input, state)."""
        self._change_handler = handler

    async def handle_root(self, request: web.Request) -> web.Response:
        """Simple health check endpoint."""
        return web.Response(status=200, text="IPX800 Bridge OK")

    async def handle_push(self, request: web.Request) -> web.Response:
        """Handle push notification from IPX800 (GET or POST).

        Expected params:
        - mac: MAC address (format: 00:04:A3:87:00:1F)
        - inputs: 32 chars of 0/1 representing input states
        - outputs: 32 chars of 0/1 representing output states
        """
        try:
            # Support both GET (query params) and POST (body or query params)
            if request.method == "POST":
                data = await request.post()
                mac = data.get("mac") or request.query.get("mac")
                inputs_str = data.get("inputs") or request.query.get("inputs")
                outputs_str = data.get("outputs") or request.query.get("outputs")
            else:
                mac = request.query.get("mac")
                inputs_str = request.query.get("inputs")
                outputs_str = request.query.get("outputs")

            if not all([mac, inputs_str, outputs_str]):
                logger.warning(
                    "push_missing_params",
                    mac=bool(mac),
                    inputs=bool(inputs_str),
                    outputs=bool(outputs_str),
                )
                return web.Response(status=400, text="Missing parameters")

            # Validate input length
            if len(inputs_str) != 32 or len(outputs_str) != 32:
                logger.warning(
                    "push_invalid_length",
                    inputs_len=len(inputs_str),
                    outputs_len=len(outputs_str),
                )
                return web.Response(status=400, text="Invalid parameter length")

            # Parse states
            inputs = [c == "1" for c in inputs_str]
            outputs = [c == "1" for c in outputs_str]

            # Update state manager
            await self.state_manager.update_mac(mac)
            changed_inputs = await self.state_manager.update_inputs(inputs)
            changed_outputs = await self.state_manager.update_outputs(outputs)

            # Notify MQTT of changes
            if self._change_handler:
                for idx in changed_inputs:
                    self._change_handler(idx, True, inputs[idx])
                for idx in changed_outputs:
                    self._change_handler(idx, False, outputs[idx])

            logger.info(
                "push_processed",
                mac=mac,
                changed_inputs=len(changed_inputs),
                changed_outputs=len(changed_outputs),
            )

            return web.Response(status=200, text="OK")

        except Exception as e:
            logger.error("push_processing_error", error=str(e))
            return web.Response(status=500, text="Internal error")

    async def start(self):
        """Start the HTTP server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await site.start()
        logger.info("http_server_started", port=self.port)

    async def stop(self):
        """Stop the HTTP server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("http_server_stopped")
