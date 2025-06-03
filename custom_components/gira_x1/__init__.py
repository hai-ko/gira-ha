"""The Gira X1 integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.network import get_url
import voluptuous as vol

from .api import GiraX1ApiError, GiraX1Client
from .const import (
    DOMAIN, 
    UPDATE_INTERVAL_SECONDS,
    CALLBACK_UPDATE_INTERVAL_SECONDS,
    WEBHOOK_VALUE_CALLBACK_PATH,
    WEBHOOK_SERVICE_CALLBACK_PATH,
    CONF_AUTH_METHOD, 
    CONF_TOKEN, 
    AUTH_METHOD_TOKEN
)
from .webhook import register_webhook_handlers, unregister_webhook_handlers

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
    
    # Set up callback system
    _LOGGER.info("Setting up callback system...")
    try:
        await coordinator.setup_callbacks()
    except Exception as err:
        _LOGGER.warning("Failed to setup callbacks, falling back to polling: %s", err)
    
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
        _LOGGER.info("Callback system: %s", "Active" if coordinator.callbacks_enabled else "Disabled (using polling)")
        
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
        
        # Clean up callbacks
        await coordinator.cleanup_callbacks()
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
        self.callbacks_enabled = False
        self._webhook_handlers = None

        # Use longer polling interval when callbacks are enabled
        update_interval = timedelta(seconds=UPDATE_INTERVAL_SECONDS)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def setup_callbacks(self) -> bool:
        """Set up callback system for real-time updates."""
        try:
            # Get the external URL for Home Assistant
            try:
                external_url = get_url(self.hass, prefer_external=True)
            except Exception:
                # Fallback to internal URL if external not available
                external_url = get_url(self.hass, prefer_external=False)
            
            if not external_url:
                _LOGGER.warning("No URL available for callbacks, using polling")
                return False

            # Register webhook handlers
            self._webhook_handlers = register_webhook_handlers(self.hass, self)
            
            # Build callback URLs
            value_callback_url = f"{external_url}{WEBHOOK_VALUE_CALLBACK_PATH}"
            service_callback_url = f"{external_url}{WEBHOOK_SERVICE_CALLBACK_PATH}"
            
            _LOGGER.info("Registering callbacks with URLs: value=%s, service=%s", 
                        value_callback_url, service_callback_url)
            
            # Register callbacks with Gira X1
            success = await self.client.register_callbacks(
                value_callback_url=value_callback_url,
                service_callback_url=service_callback_url,
                test_callbacks=True
            )
            
            if success:
                self.callbacks_enabled = True
                # Use longer polling interval as fallback when callbacks are active
                self.update_interval = timedelta(seconds=CALLBACK_UPDATE_INTERVAL_SECONDS)
                _LOGGER.info("Callbacks enabled, using %d second fallback polling", 
                           CALLBACK_UPDATE_INTERVAL_SECONDS)
                return True
            else:
                _LOGGER.warning("Failed to register callbacks, using standard polling")
                return False
                
        except Exception as err:
            _LOGGER.error("Error setting up callbacks: %s", err, exc_info=True)
            return False

    async def cleanup_callbacks(self) -> None:
        """Clean up callback system."""
        if self.callbacks_enabled:
            try:
                await self.client.unregister_callbacks()
                _LOGGER.info("Unregistered callbacks from Gira X1")
            except Exception as err:
                _LOGGER.warning("Error unregistering callbacks: %s", err)
        
        if self._webhook_handlers:
            unregister_webhook_handlers(self.hass)
            self._webhook_handlers = None
        
        self.callbacks_enabled = False

    async def _async_update_data(self):
        """Update data via library."""
        try:
            if self.callbacks_enabled:
                _LOGGER.debug("Starting fallback data update cycle (callbacks enabled)")
            else:
                _LOGGER.debug("Starting data update cycle (polling mode)")
            
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
                    
                # Re-register callbacks if config changed (callbacks might have been lost)
                if self.callbacks_enabled:
                    _LOGGER.info("Re-registering callbacks after config change")
                    try:
                        await self.setup_callbacks()
                    except Exception as err:
                        _LOGGER.warning("Failed to re-register callbacks: %s", err)
            
            # Get current values for all data points
            if not self.callbacks_enabled:
                # Only fetch values via API in polling mode
                # In callback mode, values are updated via webhooks
                _LOGGER.debug("Fetching current values from device...")
                values = await self.client.get_values()
                _LOGGER.debug("Received %d values from device", len(values) if values else 0)
            else:
                # In callback mode, preserve existing values (updated via webhooks)
                values = getattr(self, '_last_values', {})
                _LOGGER.debug("Using cached values in callback mode (%d values)", len(values))

            data = {
                "values": values,
                "ui_config": self.ui_config,
                "functions": self.functions,
                "ui_config_uid": self.ui_config_uid,
            }
            
            # Cache values for callback mode
            self._last_values = values
            
            _LOGGER.debug("Data update completed successfully")
            return data
            
        except GiraX1ApiError as err:
            _LOGGER.error("API error during data update: %s", err, exc_info=True)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.error("Unexpected error during data update: %s", err, exc_info=True)
            raise UpdateFailed(f"Unexpected error: {err}") from err
