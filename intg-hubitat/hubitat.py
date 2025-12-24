"""Hubitat API client for accessing devices and sending commands."""

import logging
from typing import Any
import aiohttp

_LOG = logging.getLogger(__name__)


class HubitatClient:
    """Client for interacting with Hubitat Maker API."""

    def __init__(self, hub_address: str, app_id: str, access_token: str):
        """
        Initialize Hubitat client.

        Args:
            hub_address: IP address or hostname of Hubitat hub
            app_id: Maker API application ID
            access_token: Maker API access token
        """
        self.hub_address = hub_address.rstrip("/")
        self.app_id = app_id
        self.access_token = access_token
        self.base_url = f"http://{self.hub_address}/apps/api/{self.app_id}"
        self._session: aiohttp.ClientSession | None = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_all_devices(self) -> list[dict[str, Any]]:
        """
        Get all devices from Hubitat hub with full details.

        Note: The /devices endpoint only returns basic info (id, name, type).
        We need to fetch each device individually to get capabilities and attributes.

        Returns:
            List of device dictionaries with full details
        """
        url = f"{self.base_url}/devices?access_token={self.access_token}"

        try:
            session = await self.get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    basic_devices = await response.json()
                    _LOG.debug(f"Retrieved {len(basic_devices)} devices from Hubitat")

                    # Fetch full details for each device
                    full_devices = []
                    for basic_device in basic_devices:
                        device_id = str(basic_device.get("id"))
                        full_device = await self.get_device(device_id)
                        if full_device:
                            full_devices.append(full_device)
                        else:
                            # Fallback to basic info if fetch fails
                            full_devices.append(basic_device)

                    _LOG.info(f"Retrieved full details for {len(full_devices)} devices")
                    return full_devices
                else:
                    _LOG.error(f"Failed to get devices: HTTP {response.status}")
                    return []
        except Exception as e:
            _LOG.error(f"Error getting devices: {e}")
            return []

    async def get_device(self, device_id: str) -> dict[str, Any] | None:
        """
        Get specific device information.

        Args:
            device_id: Device ID

        Returns:
            Device information or None if not found
        """
        url = f"{self.base_url}/devices/{device_id}?access_token={self.access_token}"

        try:
            session = await self.get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    _LOG.error(f"Failed to get device {device_id}: HTTP {response.status}")
                    return None
        except Exception as e:
            _LOG.error(f"Error getting device {device_id}: {e}")
            return None

    async def send_command(
        self, device_id: str, command: str, parameters: list[Any] | None = None
    ) -> bool:
        """
        Send command to a device.

        Args:
            device_id: Device ID
            command: Command to send
            parameters: Optional command parameters

        Returns:
            True if successful, False otherwise
        """
        if parameters:
            param_str = "/".join(str(p) for p in parameters)
            url = f"{self.base_url}/devices/{device_id}/{command}/{param_str}?access_token={self.access_token}"
        else:
            url = f"{self.base_url}/devices/{device_id}/{command}?access_token={self.access_token}"

        try:
            session = await self.get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    _LOG.debug(f"Command {command} sent to device {device_id}")
                    return True
                else:
                    _LOG.error(f"Failed to send command: HTTP {response.status}")
                    return False
        except Exception as e:
            _LOG.error(f"Error sending command: {e}")
            return False

    async def test_connection(self) -> bool:
        """
        Test connection to Hubitat hub.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            devices = await self.get_all_devices()
            return devices is not None
        except Exception as e:
            _LOG.error(f"Connection test failed: {e}")
            return False
