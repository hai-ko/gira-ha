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
    _LOGGER.info("Setting up Gira X1 light platform")
    coordinator: GiraX1DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    
    # Log coordinator data for debugging
    if not coordinator.data:
        _LOGGER.warning("No coordinator data available for light setup")
        return
    
    # Get all functions that are lights from the UI config
    functions = coordinator.data.get("functions", {}) if coordinator.data else {}
    _LOGGER.info("Found %d total functions for light platform", len(functions))
    
    # Log the mappings we're using
    _LOGGER.info("Light mappings - GIRA_FUNCTION_TYPES: %s", {k: v for k, v in GIRA_FUNCTION_TYPES.items() if v == DEVICE_TYPE_LIGHT})
    _LOGGER.info("Light mappings - GIRA_CHANNEL_TYPES: %s", {k: v for k, v in GIRA_CHANNEL_TYPES.items() if v == DEVICE_TYPE_LIGHT})
    
    # Log all function types found in the data for mapping analysis
    all_function_types = set()
    all_channel_types = set()
    for function in functions.values():
        func_type = function.get("functionType", "")
        chan_type = function.get("channelType", "")
        if func_type:
            all_function_types.add(func_type)
        if chan_type:
            all_channel_types.add(chan_type)
    
    _LOGGER.info("ALL function types found in device data: %s", sorted(all_function_types))
    _LOGGER.info("ALL channel types found in device data: %s", sorted(all_channel_types))
    
    # Check which types are not mapped for lights
    unmapped_function_types = all_function_types - set(GIRA_FUNCTION_TYPES.keys())
    unmapped_channel_types = all_channel_types - set(GIRA_CHANNEL_TYPES.keys())
    
    if unmapped_function_types:
        _LOGGER.warning("UNMAPPED function types found (consider adding to const.py): %s", sorted(unmapped_function_types))
    if unmapped_channel_types:
        _LOGGER.warning("UNMAPPED channel types found (consider adding to const.py): %s", sorted(unmapped_channel_types))
    
    light_count = 0
    for function_uid, function in functions.items():
        function_type = function.get("functionType", "")
        channel_type = function.get("channelType", "")
        display_name = function.get("displayName", "Unknown")
        
        # Log every function for debugging
        _LOGGER.debug("Function %s: %s (function_type: %s, channel_type: %s)", 
                     function_uid, display_name, function_type, channel_type)
        
        # Check if this function should be a light entity
        # Allow Switch functions to be lights if they have dimming capability or specific channel types
        is_light_function = GIRA_FUNCTION_TYPES.get(function_type) == DEVICE_TYPE_LIGHT
        is_light_channel = GIRA_CHANNEL_TYPES.get(channel_type) == DEVICE_TYPE_LIGHT
        is_dimmer_switch = (function_type == "de.gira.schema.functions.Switch" and 
                           channel_type == "de.gira.schema.channels.KNX.Dimmer")
        
        if is_light_function or is_light_channel or is_dimmer_switch:
            _LOGGER.info("Adding light entity: %s (%s) - %s/%s", 
                        display_name, function_uid, function_type, channel_type)
            entities.append(GiraX1Light(coordinator, function))
            light_count += 1
        elif function_type or channel_type:
            # Log non-matching functions to help identify missing mappings
            _LOGGER.debug("Function %s not mapped as light - type: %s, channel: %s", 
                         function_uid, function_type, channel_type)
    
    _LOGGER.info("Light platform setup complete: %d light entities created", light_count)
    
    if entities:
        async_add_entities(entities)
    else:
        _LOGGER.warning("No light entities found! Check function types in coordinator data and GIRA_FUNCTION_TYPES mapping")


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
        values = self.coordinator.data.get("values", {}) if self.coordinator.data else {}
        if self._on_off_uid:
            # Use OnOff data point if available
            value = values.get(self._on_off_uid, False)
            return bool(value)
        elif self._brightness_uid:
            # Fall back to brightness data point
            value = values.get(self._brightness_uid, 0)
            return value > 0
        return False

    @property
    def brightness(self) -> Optional[int]:
        """Return the brightness of this light between 0..255."""
        if self._brightness_uid:
            values = self.coordinator.data.get("values", {}) if self.coordinator.data else {}
            value = values.get(self._brightness_uid, 0)
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
