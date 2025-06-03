"""Base entity class for Gira X1 integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import GiraX1DataUpdateCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class GiraX1Entity(CoordinatorEntity[GiraX1DataUpdateCoordinator]):
    """Base entity class for Gira X1 devices."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict[str, Any],
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._function = function
        self._attr_unique_id = function["uid"]
        self._attr_name = function.get("displayName", f"Gira X1 {function['uid']}")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.host)},
            name=f"Gira X1 ({self.coordinator.host})",
            manufacturer="Gira",
            model="X1",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success
