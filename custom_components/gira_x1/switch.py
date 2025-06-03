"""Support for Gira X1 switches."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import GiraX1DataUpdateCoordinator
from .const import DOMAIN, DEVICE_TYPE_SWITCH, GIRA_FUNCTION_TYPES, GIRA_CHANNEL_TYPES
from .entity import GiraX1Entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gira X1 switches from a config entry."""
    coordinator: GiraX1DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    
    # Get all functions that are switches from the UI config
    functions = coordinator.data.get("functions", {}) if coordinator.data else {}
    for function in functions.values():
        function_type = function.get("functionType", "")
        channel_type = function.get("channelType", "")
        
        # Check if this function should be a switch entity
        if (GIRA_FUNCTION_TYPES.get(function_type) == DEVICE_TYPE_SWITCH or
            GIRA_CHANNEL_TYPES.get(channel_type) == DEVICE_TYPE_SWITCH):
            entities.append(GiraX1Switch(coordinator, function))

    async_add_entities(entities)


class GiraX1Switch(GiraX1Entity, SwitchEntity):
    """Representation of a Gira X1 switch."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, function)

        # Find data points for this function
        self._data_points = {dp["name"]: dp["uid"] for dp in function.get("dataPoints", [])}
        self._on_off_uid = self._data_points.get("OnOff") or self._data_points.get("Switch")

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        if self._on_off_uid:
            values = self.coordinator.data.get("values", {}) if self.coordinator.data else {}
            value = values.get(self._on_off_uid, False)
            return bool(value)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if self._on_off_uid:
            await self.coordinator.api.set_value(self._on_off_uid, True)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.warning("No suitable data point found for turning on switch %s", self._function["uid"])

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        if self._on_off_uid:
            await self.coordinator.api.set_value(self._on_off_uid, False)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.warning("No suitable data point found for turning off switch %s", self._function["uid"])
