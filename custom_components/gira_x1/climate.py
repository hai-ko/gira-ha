"""Support for Gira X1 climate devices."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
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
    """Set up Gira X1 climate entities."""
    coordinator: GiraX1DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    functions = coordinator.data.get("functions", {}) if coordinator.data else {}
    for function in functions.values():
        function_type = function.get("functionType")
        channel_type = function.get("channelType")
        
        # Check if this is a climate function
        if (GIRA_FUNCTION_TYPES.get(function_type) == "climate" or 
            GIRA_CHANNEL_TYPES.get(channel_type) == "climate"):
            
            _LOGGER.debug("Adding climate entity for function %s (%s)", 
                         function["uid"], function.get("displayName"))
            entities.append(GiraX1Climate(coordinator, function))
    
    if entities:
        async_add_entities(entities)


class GiraX1Climate(GiraX1Entity, ClimateEntity):
    """Representation of a Gira X1 climate device."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict[str, Any],
    ) -> None:
        """Initialize the climate device."""
        super().__init__(coordinator, function)
        
        # Find temperature data points
        self._current_temp_datapoint = None
        self._setpoint_datapoint = None
        
        for datapoint in function.get("dataPoints", []):
            if datapoint["name"] == "Current":
                self._current_temp_datapoint = datapoint
            elif datapoint["name"] == "Set-Point":
                self._setpoint_datapoint = datapoint
        
        if not self._current_temp_datapoint:
            _LOGGER.warning("No Current temperature datapoint found for climate %s", function["uid"])
        if not self._setpoint_datapoint:
            _LOGGER.warning("No Set-Point datapoint found for climate %s", function["uid"])

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available and 
            self._current_temp_datapoint is not None and
            self._setpoint_datapoint is not None
        )

    @property
    def supported_features(self) -> ClimateEntityFeature:
        """Return the list of supported features."""
        features = ClimateEntityFeature(0)
        
        if (self._setpoint_datapoint and 
            self._setpoint_datapoint.get("canWrite", False)):
            features |= ClimateEntityFeature.TARGET_TEMPERATURE
            
        return features

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement used by the platform."""
        return UnitOfTemperature.CELSIUS

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation mode."""
        # For now, assume heating mode - could be extended with more logic
        return HVACMode.HEAT

    @property
    def hvac_modes(self) -> list[HVACMode]:
        """Return the list of available operation modes."""
        return [HVACMode.HEAT, HVACMode.OFF]

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        if not self._current_temp_datapoint:
            return None
            
        values = self.coordinator.data.get("values", {}) if self.coordinator.data else {}
        value = values.get(self._current_temp_datapoint["uid"])
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid temperature value: %s", value)
        return None

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if not self._setpoint_datapoint:
            return None
            
        values = self.coordinator.data.get("values", {}) if self.coordinator.data else {}
        value = values.get(self._setpoint_datapoint["uid"])
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                _LOGGER.warning("Invalid setpoint value: %s", value)
        return None

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return 5.0

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return 35.0

    @property
    def target_temperature_step(self) -> float:
        """Return the supported step of target temperature."""
        return 0.5

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if not self._setpoint_datapoint:
            _LOGGER.error("No setpoint datapoint available for climate %s", self._function["uid"])
            return
            
        if not self._setpoint_datapoint.get("canWrite", False):
            _LOGGER.error("Setpoint datapoint is not writable for climate %s", self._function["uid"])
            return

        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        try:
            await self.coordinator.api.set_value(self._setpoint_datapoint["uid"], temperature)
            _LOGGER.debug("Set temperature %s°C for climate %s (datapoint %s)", 
                         temperature, self._function["uid"], self._setpoint_datapoint["uid"])
            
            # Request immediate update
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.error("Failed to set temperature for climate %s: %s", self._function["uid"], err)
            raise

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        # This would need additional datapoints to control heating/cooling mode
        # For now, just log the attempt
        _LOGGER.info("HVAC mode change requested to %s for climate %s (not implemented)", 
                    hvac_mode, self._function["uid"])
