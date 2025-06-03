"""Support for Gira X1 buttons."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import GiraX1DataUpdateCoordinator
from .const import DOMAIN, GIRA_FUNCTION_TYPES, GIRA_CHANNEL_TYPES
from .entity import GiraX1Entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gira X1 button entities."""
    coordinator: GiraX1DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    for function in coordinator.functions.values():
        function_type = function.get("functionType")
        channel_type = function.get("channelType")
        
        # Check if this is a button function
        if (GIRA_FUNCTION_TYPES.get(function_type) == "button" or 
            GIRA_CHANNEL_TYPES.get(channel_type) == "button"):
            
            _LOGGER.debug("Adding button entity for function %s (%s)", 
                         function["uid"], function.get("displayName"))
            entities.append(GiraX1Button(coordinator, function))
    
    if entities:
        async_add_entities(entities)


class GiraX1Button(GiraX1Entity, ButtonEntity):
    """Representation of a Gira X1 button."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict[str, Any],
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator, function)
        
        # Find the trigger data point
        self._trigger_datapoint = None
        for datapoint in function.get("dataPoints", []):
            if datapoint["name"] == "Trigger":
                self._trigger_datapoint = datapoint
                break
        
        if not self._trigger_datapoint:
            _LOGGER.warning("No Trigger datapoint found for button %s", function["uid"])

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available and 
            self._trigger_datapoint is not None and
            self._trigger_datapoint.get("canWrite", False)
        )

    async def async_press(self) -> None:
        """Press the button."""
        if not self._trigger_datapoint:
            _LOGGER.error("No trigger datapoint available for button %s", self._function["uid"])
            return
            
        try:
            # Trigger buttons typically use a value of 1 or True
            await self.coordinator.api.set_value(self._trigger_datapoint["uid"], 1)
            _LOGGER.debug("Triggered button %s (datapoint %s)", 
                         self._function["uid"], self._trigger_datapoint["uid"])
        except Exception as err:
            _LOGGER.error("Failed to trigger button %s: %s", self._function["uid"], err)
            raise
