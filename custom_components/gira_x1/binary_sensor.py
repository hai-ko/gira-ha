"""Support for Gira X1 binary sensors."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from . import GiraX1DataUpdateCoordinator
from .const import DOMAIN, DEVICE_TYPE_BINARY_SENSOR, GIRA_FUNCTION_TYPES, GIRA_CHANNEL_TYPES
from .entity import GiraX1Entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gira X1 binary sensors from a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    entities = []
    
    # Get all functions that are binary sensors from the UI config
    for function in coordinator.data.get("functions", []):
        function_type = function.get("functionType", "")
        channel_type = function.get("channelType", "")
        display_name = function.get("displayName", "").lower()
        
        # Check if this function should be a binary sensor entity
        if (GIRA_FUNCTION_TYPES.get(function_type) == DEVICE_TYPE_BINARY_SENSOR or
            GIRA_CHANNEL_TYPES.get(channel_type) == DEVICE_TYPE_BINARY_SENSOR):
            
            # Determine binary sensor type based on name or type
            if "motion" in display_name or "bewegung" in display_name:
                entities.append(GiraX1MotionSensor(coordinator, function))
            elif "presence" in display_name or "präsenz" in display_name or "anwesenheit" in display_name:
                entities.append(GiraX1PresenceSensor(coordinator, function))
            elif "door" in display_name or "tür" in display_name:
                entities.append(GiraX1DoorSensor(coordinator, function))
            elif "window" in display_name or "fenster" in display_name:
                entities.append(GiraX1WindowSensor(coordinator, function))
            else:
                # Generic binary sensor
                entities.append(GiraX1GenericBinarySensor(coordinator, function))

    async_add_entities(entities)


class GiraX1BinarySensor(GiraX1Entity, BinarySensorEntity):
    """Base class for Gira X1 binary sensors."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
        data_point_name: str = None,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, function)
        
        # Find the specific data point for this binary sensor
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
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if self._data_point_uid:
            value = self.coordinator.data.get(self._data_point_uid, False)
            return bool(value)
        return False


class GiraX1MotionSensor(GiraX1BinarySensor):
    """Representation of a Gira X1 motion sensor."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the motion sensor."""
        super().__init__(coordinator, function, "Motion")
        self._attr_device_class = BinarySensorDeviceClass.MOTION
        self._attr_unique_id = f"gira_x1_motion_{self._func_id}"


class GiraX1PresenceSensor(GiraX1BinarySensor):
    """Representation of a Gira X1 presence sensor."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the presence sensor."""
        super().__init__(coordinator, function, "Presence")
        self._attr_device_class = BinarySensorDeviceClass.OCCUPANCY
        self._attr_unique_id = f"gira_x1_presence_{self._func_id}"


class GiraX1DoorSensor(GiraX1BinarySensor):
    """Representation of a Gira X1 door sensor."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the door sensor."""
        super().__init__(coordinator, function, "Status")
        self._attr_device_class = BinarySensorDeviceClass.DOOR
        self._attr_unique_id = f"gira_x1_door_{self._func_id}"


class GiraX1WindowSensor(GiraX1BinarySensor):
    """Representation of a Gira X1 window sensor."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the window sensor."""
        super().__init__(coordinator, function, "Status")
        self._attr_device_class = BinarySensorDeviceClass.WINDOW
        self._attr_unique_id = f"gira_x1_window_{self._func_id}"


class GiraX1GenericBinarySensor(GiraX1BinarySensor):
    """Representation of a generic Gira X1 binary sensor."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the generic binary sensor."""
        super().__init__(coordinator, function)
        self._attr_unique_id = f"gira_x1_generic_binary_{self._func_id}"
