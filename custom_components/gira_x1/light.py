"""Support for Gira X1 lights."""
from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import GiraX1DataUpdateCoordinator
from .const import DOMAIN, DEVICE_TYPE_LIGHT, GIRA_FUNCTION_TYPES, GIRA_CHANNEL_TYPES
from .entity import GiraX1Entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gira X1 lights from a config entry."""
    coordinator: GiraX1DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    
    # Get all functions that are lights from the UI config
    for function in coordinator.functions.values():
        function_type = function.get("functionType", "")
        channel_type = function.get("channelType", "")
        
        # Check if this function should be a light entity
        # Allow Switch functions to be lights if they have dimming capability or specific channel types
        if (GIRA_FUNCTION_TYPES.get(function_type) == DEVICE_TYPE_LIGHT or
            GIRA_CHANNEL_TYPES.get(channel_type) == DEVICE_TYPE_LIGHT or
            (function_type == "de.gira.schema.functions.Switch" and 
             channel_type == "de.gira.schema.channels.KNX.Dimmer")):
            entities.append(GiraX1Light(coordinator, function))

    async_add_entities(entities)


class GiraX1Light(GiraX1Entity, LightEntity):
    """Representation of a Gira X1 light."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator, function)
        
        # Find data points for this function
        self._data_points = {dp["name"]: dp["uid"] for dp in function.get("dataPoints", [])}
        self._on_off_uid = self._data_points.get("OnOff")
        self._brightness_uid = self._data_points.get("Brightness")
        self._shift_uid = self._data_points.get("Shift")  # For dimmer shift functionality
        
        # Determine capabilities based on available data points
        if self._brightness_uid:
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
            self._attr_supported_features = LightEntityFeature.TRANSITION
        else:
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._func_id)},
            "name": self._attr_name,
            "manufacturer": "Gira",
            "model": "X1",
            "sw_version": "1.0",
        }

    @property
    def is_on(self) -> bool:
        """Return true if light is on."""
        if self._on_off_uid:
            # Use OnOff data point if available
            value = self.coordinator.data.get(self._on_off_uid, False)
            return bool(value)
        elif self._brightness_uid:
            # Fall back to brightness data point
            value = self.coordinator.data.get(self._brightness_uid, 0)
            return value > 0
        return False

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness of this light between 0..255."""
        if self._brightness_uid:
            value = self.coordinator.data.get(self._brightness_uid, 0)
            # Convert from percentage (0-100) to HA brightness (0-255)
            return int(value * 255 / 100) if value > 0 else 0
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Instruct the light to turn on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        
        if self._brightness_uid and brightness is not None:
            # Set brightness (0-100%)
            value = int(brightness * 100 / 255)
            await self.coordinator.api.set_value(self._brightness_uid, value)
        elif self._on_off_uid:
            # Use OnOff data point
            await self.coordinator.api.set_value(self._on_off_uid, True)
        elif self._brightness_uid:
            # No OnOff, set brightness to 100%
            await self.coordinator.api.set_value(self._brightness_uid, 100)
        else:
            _LOGGER.warning("No suitable data point found for turning on light %s", self._func_id)
            return

        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the light to turn off."""
        if self._on_off_uid:
            # Use OnOff data point
            await self.coordinator.api.set_value(self._on_off_uid, False)
        elif self._brightness_uid:
            # Use brightness data point
            await self.coordinator.api.set_value(self._brightness_uid, 0)
        else:
            _LOGGER.warning("No suitable data point found for turning off light %s", self._func_id)
            return
            
        await self.coordinator.async_request_refresh()
