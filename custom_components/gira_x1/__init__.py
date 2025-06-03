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
import voluptuous as vol

from .api import GiraX1ApiError, GiraX1Client
from .const import DOMAIN, UPDATE_INTERVAL_SECONDS, CONF_AUTH_METHOD, CONF_TOKEN, AUTH_METHOD_TOKEN

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
        if not await client.test_connection():
            raise ConfigEntryNotReady("Unable to connect to Gira X1")
    except Exception as err:
        raise ConfigEntryNotReady(f"Error connecting to Gira X1: {err}") from err

    coordinator = GiraX1DataUpdateCoordinator(hass, client)

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            # Check if UI config has changed
            current_uid = await self.client.get_ui_config_uid()
            if current_uid != self.ui_config_uid:
                _LOGGER.info("UI configuration changed, refreshing...")
                # Get full UI configuration with expanded data point flags
                self.ui_config = await self.client.get_ui_config(
                    expand=["dataPointFlags", "parameters"]
                )
                self.ui_config_uid = current_uid
                
                # Update functions cache
                self.functions = {
                    func["uid"]: func for func in self.ui_config.get("functions", [])
                }
            
            # Get current values for all data points
            values = await self.client.get_values()

            data = {
                "values": values,
                "ui_config": self.ui_config,
                "functions": self.functions,
                "ui_config_uid": self.ui_config_uid,
            }
            
            return data
            
        except GiraX1ApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
