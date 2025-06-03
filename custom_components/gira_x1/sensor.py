"""Support for Gira X1 sensors."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import GiraX1DataUpdateCoordinator
from .const import DOMAIN, DEVICE_TYPE_SENSOR, GIRA_FUNCTION_TYPES, GIRA_CHANNEL_TYPES
from .entity import GiraX1Entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gira X1 sensors from a config entry."""
    coordinator: GiraX1DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    
    # Get all functions that are sensors from the UI config
    functions = coordinator.data.get("functions", {}) if coordinator.data else {}
    for function in functions.values():
        function_type = function.get("functionType", "")
        channel_type = function.get("channelType", "")
        
        # Check if this function should be a sensor entity
        if (GIRA_FUNCTION_TYPES.get(function_type) == DEVICE_TYPE_SENSOR or
            GIRA_CHANNEL_TYPES.get(channel_type) == DEVICE_TYPE_SENSOR):
            
            # Determine sensor type based on channel or function type
            if "Temperature" in channel_type or "temperature" in function.get("displayName", "").lower():
                entities.append(GiraX1TemperatureSensor(coordinator, function))
            elif "Humidity" in channel_type or "humidity" in function.get("displayName", "").lower():
                entities.append(GiraX1HumiditySensor(coordinator, function))
            elif "Audio" in channel_type:
                # Add volume and other audio-related sensors
                entities.append(GiraX1AudioSensor(coordinator, function))
            else:
                # Generic sensor
                entities.append(GiraX1GenericSensor(coordinator, function))

    async_add_entities(entities)


class GiraX1Sensor(GiraX1Entity, SensorEntity):
    """Base class for Gira X1 sensors."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
        data_point_name: str = None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, function)
        
        # Find data points for this function
        self._data_points = {dp["name"]: dp["uid"] for dp in function.get("dataPoints", [])}
        
        # Find the specific data point for this sensor
        if data_point_name:
            self._data_point_name = data_point_name
            self._data_point_uid = self._data_points.get(data_point_name)
        else:
            # Use the first available data point
            if self._data_points:
                self._data_point_name = next(iter(self._data_points.keys()))
                self._data_point_uid = next(iter(self._data_points.values()))
            else:
                self._data_point_name = None
                self._data_point_uid = None

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._data_point_uid:
            values = self.coordinator.data.get("values", {}) if self.coordinator.data else {}
            return values.get(self._data_point_uid)
        return None


class GiraX1TemperatureSensor(GiraX1Sensor):
    """Representation of a Gira X1 temperature sensor."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the temperature sensor."""
        super().__init__(coordinator, function, "Temperature")
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_unique_id = f"gira_x1_temperature_{self._function['uid']}"


class GiraX1HumiditySensor(GiraX1Sensor):
    """Representation of a Gira X1 humidity sensor."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the humidity sensor."""
        super().__init__(coordinator, function, "Humidity")
        self._attr_device_class = SensorDeviceClass.HUMIDITY
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_unique_id = f"gira_x1_humidity_{self._function['uid']}"


class GiraX1AudioSensor(GiraX1Sensor):
    """Representation of a Gira X1 audio sensor (volume, etc.)."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the audio sensor."""
        # Try to find Volume data point first
        super().__init__(coordinator, function, "Volume")
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_unique_id = f"gira_x1_audio_{self._function['uid']}"
        
        # Update name to be more specific
        self._attr_name = f"{function.get('displayName', 'Audio')} Volume"


class GiraX1GenericSensor(GiraX1Sensor):
    """Representation of a generic Gira X1 sensor."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the generic sensor."""
        super().__init__(coordinator, function)
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_unique_id = f"gira_x1_generic_{self._function['uid']}"
