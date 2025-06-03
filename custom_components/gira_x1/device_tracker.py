"""Device tracker for Gira X1 integration."""
from __future__ import annotations

import logging
from typing import Dict, Any

from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class GiraX1DeviceTracker:
    """Track and manage Gira X1 devices."""

    def __init__(self, hass, coordinator) -> None:
        """Initialize device tracker."""
        self.hass = hass
        self.coordinator = coordinator
        self._devices: Dict[str, DeviceEntry] = {}

    async def async_update_devices(self) -> None:
        """Update device registry with discovered devices."""
        device_registry = dr.async_get(self.hass)
        
        # Get all functions/devices from coordinator
        functions = self.coordinator.data.get("functions", {})
        
        for func_id, function in functions.items():
            device_name = function.get("name", f"Gira X1 Device {func_id}")
            
            # Create or update device entry
            device_registry.async_get_or_create(
                config_entry_id=self.coordinator.config_entry.entry_id,
                identifiers={(DOMAIN, func_id)},
                manufacturer="Gira",
                model="X1",
                name=device_name,
                sw_version="1.0",
            )

    async def get_device_info(self, func_id: str) -> Dict[str, Any]:
        """Get device info for a function ID."""
        function = self.coordinator.data.get("functions", {}).get(func_id, {})
        
        return {
            "identifiers": {(DOMAIN, func_id)},
            "name": function.get("name", f"Gira X1 Device {func_id}"),
            "manufacturer": "Gira",
            "model": "X1",
            "sw_version": "1.0",
            "via_device": (DOMAIN, "gira_x1_hub"),
        }
