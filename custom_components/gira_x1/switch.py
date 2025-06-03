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
    _LOGGER.info("Setting up Gira X1 switch platform")
    coordinator: GiraX1DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    
    # Log coordinator data for debugging
    if not coordinator.data:
        _LOGGER.warning("No coordinator data available for switch setup")
        return
    
    _LOGGER.info("Coordinator data keys: %s", list(coordinator.data.keys()))
    
    # Get all functions that are switches from the UI config
    functions = coordinator.data.get("functions", {}) if coordinator.data else {}
    _LOGGER.info("Found %d total functions in coordinator data", len(functions))
    
    # Log the mappings we're using
    _LOGGER.info("Switch mappings - GIRA_FUNCTION_TYPES: %s", {k: v for k, v in GIRA_FUNCTION_TYPES.items() if v == DEVICE_TYPE_SWITCH})
    _LOGGER.info("Switch mappings - GIRA_CHANNEL_TYPES: %s", {k: v for k, v in GIRA_CHANNEL_TYPES.items() if v == DEVICE_TYPE_SWITCH})
    
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
    
    # Check which types are not mapped
    unmapped_function_types = all_function_types - set(GIRA_FUNCTION_TYPES.keys())
    unmapped_channel_types = all_channel_types - set(GIRA_CHANNEL_TYPES.keys())
    
    if unmapped_function_types:
        _LOGGER.warning("UNMAPPED function types found (consider adding to const.py): %s", sorted(unmapped_function_types))
    if unmapped_channel_types:
        _LOGGER.warning("UNMAPPED channel types found (consider adding to const.py): %s", sorted(unmapped_channel_types))
    
    switch_count = 0
    for function_uid, function in functions.items():
        function_type = function.get("functionType", "")
        channel_type = function.get("channelType", "")
        display_name = function.get("displayName", "Unknown")
        
        # Log every function for debugging
        _LOGGER.debug("Function %s: %s (type: %s, channel: %s)", 
                     function_uid, display_name, function_type, channel_type)
        
        # Check if this function should be a switch entity
        is_switch_function = GIRA_FUNCTION_TYPES.get(function_type) == DEVICE_TYPE_SWITCH
        is_switch_channel = GIRA_CHANNEL_TYPES.get(channel_type) == DEVICE_TYPE_SWITCH
        
        if is_switch_function or is_switch_channel:
            _LOGGER.info("Adding switch entity: %s (%s) - %s", 
                        display_name, function_uid, function_type)
            entities.append(GiraX1Switch(coordinator, function))
            switch_count += 1
        elif function_type or channel_type:
            # Log non-matching functions to help identify missing mappings
            _LOGGER.debug("Function %s not mapped as switch - type: %s, channel: %s", 
                         function_uid, function_type, channel_type)
    
    _LOGGER.info("Switch platform setup complete: %d switch entities created", switch_count)
    
    if entities:
        async_add_entities(entities)
    else:
        _LOGGER.warning("No switch entities found! Check function types in coordinator data and GIRA_FUNCTION_TYPES mapping")


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
