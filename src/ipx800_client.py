"""IPX800 API client."""

import asyncio
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
                return await asyncio.to_thread(self._parse_global_status, xml_content)

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error("error fetching status", error=str(e))
            return None

    def _parse_global_status(
        self, xml_content: str
    ) -> Tuple[str, list[bool], list[bool]]:
        """Parse globalstatus.xml content."""
        root = ET.fromstring(xml_content)

        # Extract MAC address (IPX800 uses <config_mac> not <mac>)
        mac_elem = root.find("config_mac")
        if mac_elem is not None:
            mac = mac_elem.text.strip()
        else:
            # Fallback to <mac> if present
            mac_elem = root.find("mac")
            mac = mac_elem.text.strip() if mac_elem is not None else "unknown"

        # Parse inputs (btn0 to btn31)
        # Note: IPX800 uses btn0-btn31 with values "dn" (down/active) or "up" (up/inactive)
        inputs = []
        for i in range(0, 32):
            elem = root.find(f"btn{i}")
            if elem is not None:
                # "dn" = button pressed/active = True, "up" or other = inactive = False
                inputs.append(elem.text.strip().lower() == "dn")
            else:
                inputs.append(False)

        # Parse outputs (led0 to led31)
        outputs = []
        for i in range(0, 32):
            elem = root.find(f"led{i}")
            if elem is not None:
                outputs.append(elem.text == "1")
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
        if not (0 <= index <= 31):
            logger.error("invalid output index", index=index)
            return False
        try:
            session = await self._get_session()
            # Use preset.htm for forced ON/OFF
            url = f"{self.base_url}/preset.htm?set{index + 1}={1 if value else 0}"

            async with session.get(url, timeout=10) as response:
                return response.status == 200

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error("error setting output", index=index, value=value, error=str(e))
            return False
