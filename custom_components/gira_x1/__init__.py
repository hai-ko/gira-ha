"""The Gira X1 integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta, datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import voluptuous as vol

from .api import GiraX1ApiError, GiraX1Client
from .const import (
    DOMAIN, 
    UPDATE_INTERVAL_SECONDS,
    CONF_AUTH_METHOD, 
    CONF_TOKEN, 
    AUTH_METHOD_TOKEN
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SWITCH,
    Platform.COVER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gira X1 from a config entry."""
    auth_method = entry.data.get(CONF_AUTH_METHOD, "password")
    
    if auth_method == AUTH_METHOD_TOKEN:
        client = GiraX1Client(
            hass,
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            token=entry.data[CONF_TOKEN],
        )
    else:
        client = GiraX1Client(
            hass,
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            username=entry.data[CONF_USERNAME],
            password=entry.data[CONF_PASSWORD],
        )

    # Test connection
    try:
        _LOGGER.info("Testing connection to Gira X1 at %s:%s", entry.data[CONF_HOST], entry.data[CONF_PORT])
        if not await client.test_connection():
            _LOGGER.error("Connection test failed to Gira X1")
            raise ConfigEntryNotReady("Unable to connect to Gira X1")
        _LOGGER.info("Successfully connected to Gira X1")
    except Exception as err:
        _LOGGER.error("Error connecting to Gira X1: %s", err, exc_info=True)
        raise ConfigEntryNotReady(f"Error connecting to Gira X1: {err}") from err

    coordinator = GiraX1DataUpdateCoordinator(hass, client)

    # Fetch initial data so we have data when entities subscribe
    _LOGGER.info("Fetching initial data from Gira X1...")
    await coordinator.async_config_entry_first_refresh()
    
    # Pure polling mode only - no callbacks
    _LOGGER.info("Integration configured for pure polling mode with %d second intervals", UPDATE_INTERVAL_SECONDS)
    
    # Log initial data summary
    if coordinator.data:
        _LOGGER.info("Initial data fetch successful. Data keys: %s", list(coordinator.data.keys()))
        functions = coordinator.data.get("functions", {})
        values = coordinator.data.get("values", {})
        ui_config = coordinator.data.get("ui_config", {})
        _LOGGER.info("Found %d functions and %d values", len(functions), len(values))
        
        # Log function type summary
        function_types = {}
        channel_types = {}
        for func in functions.values():
            func_type = func.get("functionType", "unknown")
            chan_type = func.get("channelType", "unknown")
            function_types[func_type] = function_types.get(func_type, 0) + 1
            channel_types[chan_type] = channel_types.get(chan_type, 0) + 1
        
        _LOGGER.info("Function types found: %s", function_types)
        _LOGGER.info("Channel types found: %s", channel_types)
        _LOGGER.info("Pure polling mode active")
        
        # Log a sample of the raw UI config for debugging
        if ui_config and "functions" in ui_config:
            sample_functions = ui_config["functions"][:3] if len(ui_config["functions"]) > 0 else []
            for i, func in enumerate(sample_functions):
                _LOGGER.info("Sample function %d: %s", i+1, {
                    "uid": func.get("uid"),
                    "displayName": func.get("displayName"),
                    "functionType": func.get("functionType"),
                    "channelType": func.get("channelType"),
                    "dataPoints": [dp.get("name") for dp in func.get("dataPoints", [])]
                })
    else:
        _LOGGER.warning("No initial data received from Gira X1")

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    _LOGGER.info("Setting up platforms: %s", PLATFORMS)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info("Platform setup completed")

    # Register services
    async def refresh_device(call: ServiceCall):
        """Service to refresh a specific device."""
        device_id = call.data.get("device_id")
        if device_id:
            await coordinator.async_request_refresh()

    async def set_raw_value(call: ServiceCall):
        """Service to set a raw value for a datapoint."""
        datapoint_id = call.data.get("datapoint_id")
        value = call.data.get("value")
        if datapoint_id is not None and value is not None:
            await client.set_value(datapoint_id, value)
            await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        "refresh_device",
        refresh_device,
        schema=vol.Schema({vol.Required("device_id"): str}),
    )

    hass.services.async_register(
        DOMAIN,
        "set_raw_value",
        set_raw_value,
        schema=vol.Schema({
            vol.Required("datapoint_id"): str,
            vol.Required("value"): vol.Any(int, float, bool, str),
        }),
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator = hass.data[DOMAIN][entry.entry_id]
        
        # Clean up client connection
        await coordinator.client.logout()
        
        # Remove services
        hass.services.async_remove(DOMAIN, "refresh_device")
        hass.services.async_remove(DOMAIN, "set_raw_value")
        
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class GiraX1DataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Gira X1."""

    def __init__(self, hass: HomeAssistant, client: GiraX1Client) -> None:
        """Initialize."""
        self.api = client  # Expose client as 'api' for entity compatibility
        self.client = client
        self.ui_config = {}
        self.functions = {}
        self.ui_config_uid = None
        self.host = client.host  # Expose host for device info

        # Use 5-second polling interval
        update_interval = timedelta(seconds=UPDATE_INTERVAL_SECONDS)
        _LOGGER.info("Initializing coordinator with %d-second polling interval", UPDATE_INTERVAL_SECONDS)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            _LOGGER.debug("[%s] Starting data update cycle (pure polling mode)", current_time)
            
            # Check if UI config has changed
            current_uid = await self.client.get_ui_config_uid()
            _LOGGER.debug("Current UI config UID: %s, cached UID: %s", current_uid, self.ui_config_uid)
            
            if current_uid != self.ui_config_uid:
                _LOGGER.info("UI configuration changed (UID: %s), refreshing full config...", current_uid)
                # Get full UI configuration with expanded data point flags
                self.ui_config = await self.client.get_ui_config(
                    expand=["dataPointFlags", "parameters"]
                )
                self.ui_config_uid = current_uid
                
                # Log UI config structure
                _LOGGER.info("Received UI config with %d functions", len(self.ui_config.get("functions", [])))
                
                # Log the complete structure of the first few functions for debugging
                raw_functions = self.ui_config.get("functions", [])
                if raw_functions:
                    _LOGGER.info("=== RAW UI CONFIG DEBUG ===")
                    for i, func in enumerate(raw_functions[:5]):  # Log first 5 functions in detail
                        _LOGGER.info("Function %d complete structure: %s", i+1, func)
                    _LOGGER.info("=== END RAW UI CONFIG DEBUG ===")
                else:
                    _LOGGER.warning("No functions found in raw UI config!")
                
                # Update functions cache
                self.functions = {
                    func["uid"]: func for func in self.ui_config.get("functions", [])
                }
                
                # Log function summary for debugging
                if self.functions:
                    _LOGGER.info("Cached %d functions in coordinator", len(self.functions))
                    # Log first few function details for debugging
                    sample_functions = list(self.functions.items())[:3]
                    for uid, func in sample_functions:
                        _LOGGER.info("Sample function: %s - %s (function_type: %s, channel_type: %s)", 
                                    uid, func.get("displayName", "Unknown"), 
                                    func.get("functionType", "Unknown"),
                                    func.get("channelType", "Unknown"))
                else:
                    _LOGGER.warning("No functions found in UI config!")
            
            # Get current values for all data points using individual polling
            # Pure polling mode ensures all external changes are detected
            _LOGGER.debug("Fetching current values from device using individual datapoint polling...")
            try:
                values = await self.client.get_values()
                _LOGGER.debug("Successfully received %d values from device via polling", len(values) if values else 0)
                
                # Log polled state changes
                if hasattr(self, '_last_values') and self._last_values:
                    changes_detected = 0
                    for uid, new_value in values.items():
                        old_value = self._last_values.get(uid)
                        if old_value != new_value:
                            _LOGGER.info("🔄 POLLED STATE CHANGE: %s: '%s' → '%s'", uid, old_value, new_value)
                            changes_detected += 1
                    
                    if changes_detected == 0:
                        _LOGGER.debug("No state changes detected in polling cycle")
                    else:
                        _LOGGER.info("📊 Total polled state changes: %d", changes_detected)
                else:
                    _LOGGER.info("📊 Initial polling cycle - received %d datapoint values", len(values))
                    # Log first few values for debugging
                    sample_values = list(values.items())[:5]
                    for uid, value in sample_values:
                        _LOGGER.debug("Initial value: %s = '%s'", uid, value)
                
                # Cache values for potential future use
                self._last_values = values
                
            except Exception as poll_error:
                _LOGGER.warning("Failed to poll for values: %s", poll_error)
                # Fall back to cached values if polling fails
                values = getattr(self, '_last_values', {})
                _LOGGER.debug("Using cached values due to polling failure (%d values)", len(values))
                if not values:
                    _LOGGER.warning("No cached values available after polling failure")

            data = {
                "values": values,
                "ui_config": self.ui_config,
                "functions": self.functions,
                "ui_config_uid": self.ui_config_uid,
            }
            
            _LOGGER.debug("Data update completed successfully")
            return data
            
        except GiraX1ApiError as err:
            _LOGGER.error("API error during data update: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error during data update: %s", err, exc_info=True)
            raise UpdateFailed(f"Unexpected error: {err}") from err
