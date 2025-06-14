"""Support for Gira X1 covers (blinds/shutters)."""
from __future__ import annotations

import logging
from typing import Any, Optional

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import GiraX1DataUpdateCoordinator
from .const import DOMAIN, DEVICE_TYPE_COVER, GIRA_FUNCTION_TYPES, GIRA_CHANNEL_TYPES
from .entity import GiraX1Entity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Gira X1 covers from a config entry."""
    coordinator: GiraX1DataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    
    # Get all functions that are covers from the UI config
    functions = coordinator.data.get("functions", {}) if coordinator.data else {}
    for function in functions.values():
        function_type = function.get("functionType", "")
        channel_type = function.get("channelType", "")
        
        # Check if this function should be a cover entity
        if (GIRA_FUNCTION_TYPES.get(function_type) == DEVICE_TYPE_COVER or
            GIRA_CHANNEL_TYPES.get(channel_type) == DEVICE_TYPE_COVER):
            entities.append(GiraX1Cover(coordinator, function))

    async_add_entities(entities)


class GiraX1Cover(GiraX1Entity, CoverEntity):
    """Representation of a Gira X1 cover."""

    def __init__(
        self,
        coordinator: GiraX1DataUpdateCoordinator,
        function: dict,
    ) -> None:
        """Initialize the cover."""
        super().__init__(coordinator, function)
        self._attr_device_class = CoverDeviceClass.BLIND
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )

        # Find data points for this function based on real device data
        self._data_points = {dp["name"]: dp["uid"] for dp in function.get("dataPoints", [])}
        self._position_uid = self._data_points.get("Position")
        self._up_down_uid = self._data_points.get("Up-Down")  # Updated to match real data
        self._step_up_down_uid = self._data_points.get("Step-Up-Down")  # Additional control
        self._slat_position_uid = self._data_points.get("Slat-Position")
        self._movement_uid = self._data_points.get("Movement")  # Movement status

        # Debug logging for data points
        _LOGGER.debug("Cover %s data points: %s", self._function["uid"], self._data_points)
        _LOGGER.debug("Cover %s slat position UID: %s", self._function["uid"], self._slat_position_uid)

        # Add slat support if available
        if self._slat_position_uid:
            self._attr_supported_features |= CoverEntityFeature.SET_TILT_POSITION
            _LOGGER.debug("Cover %s: Added tilt support with UID %s", self._function["uid"], self._slat_position_uid)

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._function["uid"])},
            "name": self._attr_name,
            "manufacturer": "Gira",
            "model": "X1",
            "sw_version": "1.0",
        }

    @property
    def current_cover_position(self) -> Optional[int]:
        """Return current position of cover.
        
        None is unknown, 0 is closed, 100 is fully open.
        """
        if self._position_uid:
            values = self.coordinator.data.get("values", {}) if self.coordinator.data else {}
            value = values.get(self._position_uid, 0)
            try:
                # Convert and invert: device 0=open,100=closed -> HA 0=closed,100=open
                raw = float(value) if isinstance(value, str) else value
                return int(100 - raw)
            except (ValueError, TypeError):
                return 0
        return None

    @property
    def current_cover_tilt_position(self) -> Optional[int]:
        """Return current tilt position of cover."""
        if self._slat_position_uid:
            values = self.coordinator.data.get("values", {}) if self.coordinator.data else {}
            value = values.get(self._slat_position_uid, 0)
            try:
                # Convert and invert tilt similarly
                raw = float(value) if isinstance(value, str) else value
                return int(100 - raw)
            except (ValueError, TypeError):
                return 0
        return None

    @property
    def is_closed(self) -> Optional[bool]:
        """Return if the cover is closed or not."""
        position = self.current_cover_position
        if position is None:
            return None
        return position == 0

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        if self._position_uid:
            # Device expects 0 for open
            await self.coordinator.api.set_value(self._position_uid, 0)
        elif self._up_down_uid:
            await self.coordinator.api.set_value(self._up_down_uid, 1)  # Up/Open
        else:
            _LOGGER.warning("No suitable data point found for opening cover %s", self._function["uid"])
            return
        
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        if self._position_uid:
            # Device expects 100 for close
            await self.coordinator.api.set_value(self._position_uid, 100)
        elif self._up_down_uid:
            await self.coordinator.api.set_value(self._up_down_uid, 0)  # Down/Close
        else:
            _LOGGER.warning("No suitable data point found for closing cover %s", self._function["uid"])
            return
        
        await self.coordinator.async_request_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        position = kwargs.get(ATTR_POSITION)
        if position is not None and self._position_uid:
            # Invert position before sending: HA->device
            await self.coordinator.api.set_value(self._position_uid, 100 - position)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.warning("Position setting not supported for cover %s", self._function["uid"])

    async def async_set_cover_tilt_position(self, **kwargs: Any) -> None:
        """Move the cover tilt to a specific position."""
        position = kwargs.get(ATTR_TILT_POSITION)
        _LOGGER.debug("Cover %s: Tilt position request - position=%s, slat_uid=%s", 
                     self._function["uid"], position, self._slat_position_uid)
        
        if position is not None and self._slat_position_uid:
            # Invert tilt before sending: HA->device
            device_position = 100 - position
            _LOGGER.debug("Cover %s: Setting tilt position %s -> device %s", 
                         self._function["uid"], position, device_position)
            await self.coordinator.api.set_value(self._slat_position_uid, device_position)
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.warning("Tilt position setting not supported for cover %s (position=%s, slat_uid=%s)", 
                           self._function["uid"], position, self._slat_position_uid)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        # For blinds without explicit stop, we can use step controls
        if self._step_up_down_uid:
            # Send a stop command by sending opposite step commands or using specific stop value
            await self.coordinator.api.set_value(self._step_up_down_uid, 0)  # Stop
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.warning("Stop not supported for cover %s", self._function["uid"])
            # Send a stop command - this might need adjustment based on actual API
            # For now, we'll just refresh to get current position
            await self.coordinator.async_request_refresh()
