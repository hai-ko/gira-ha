"""The Gira X1 integration."""
from __future__ import annotations

import asyncio
import logging
import socket
import subprocess
import platform
from datetime import timedelta, datetime

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
    FAST_UPDATE_INTERVAL_SECONDS,
    CALLBACK_UPDATE_INTERVAL_SECONDS,
    WEBHOOK_VALUE_CALLBACK_PATH,
    WEBHOOK_SERVICE_CALLBACK_PATH,
    CONF_AUTH_METHOD, 
    CONF_TOKEN, 
    CONF_CALLBACK_URL_OVERRIDE,
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
    callback_success = await coordinator.setup_callbacks()
    
    if callback_success:
        _LOGGER.info("Callback system enabled - real-time updates active")
    else:
        _LOGGER.info("Callback system failed - using default 5-second polling")
    
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

        # Use 5-second polling as default (no batch requests - individual datapoint polling)
        update_interval = timedelta(seconds=UPDATE_INTERVAL_SECONDS)
        _LOGGER.info("Initializing coordinator with %d-second default polling interval", UPDATE_INTERVAL_SECONDS)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def setup_callbacks(self) -> bool:
        """Set up callback system for real-time updates."""
        try:
            # Use the new intelligent callback URL determination
            external_url = determine_callback_base_url(self.hass, self.config_entry)
            
            if not external_url:
                _LOGGER.warning("No suitable callback URL available, using polling")
                return False
            
            _LOGGER.info("Using callback base URL: %s", external_url)

            # Register webhook handlers
            self._webhook_handlers = register_webhook_handlers(self.hass, self)
            
            # Build callback URLs
            value_callback_url = f"{external_url}{WEBHOOK_VALUE_CALLBACK_PATH}"
            service_callback_url = f"{external_url}{WEBHOOK_SERVICE_CALLBACK_PATH}"
            
            _LOGGER.info("Registering callbacks with URLs: value=%s, service=%s", 
                        value_callback_url, service_callback_url)
            
            # Register callbacks with Gira X1
            # Try with callback testing first, then without if it fails
            _LOGGER.info("Attempting callback registration with testing enabled...")
            success = await self.client.register_callbacks(
                value_callback_url=value_callback_url,
                service_callback_url=service_callback_url,
                test_callbacks=True
            )
            
            if not success:
                _LOGGER.warning("Callback test failed, retrying without test")
                _LOGGER.info("Attempting callback registration without testing...")
                success = await self.client.register_callbacks(
                    value_callback_url=value_callback_url,
                    service_callback_url=service_callback_url,
                    test_callbacks=False
                )
            
            if success:
                self.callbacks_enabled = True
                # Even with callbacks, use 5-second polling to ensure external changes are detected
                # Callbacks may fail silently or miss updates, so we rely on polling as primary method
                self.update_interval = timedelta(seconds=UPDATE_INTERVAL_SECONDS)
                _LOGGER.info("Callbacks registered successfully, but still using %d second polling for reliability", 
                           UPDATE_INTERVAL_SECONDS)
                return True
            else:
                _LOGGER.warning("Failed to register callbacks, using default 5-second polling")
                # Use default 5-second polling when callbacks fail
                self.callbacks_enabled = False
                self.update_interval = timedelta(seconds=UPDATE_INTERVAL_SECONDS)
                return False
                
        except Exception as err:
            _LOGGER.error("Error setting up callbacks: %s", err, exc_info=True)
            # Use default 5-second polling when callback setup fails
            _LOGGER.warning("Callback setup failed, using default 5-second polling")
            self.callbacks_enabled = False
            self.update_interval = timedelta(seconds=UPDATE_INTERVAL_SECONDS)
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
            current_time = datetime.now().strftime("%H:%M:%S")
            if self.callbacks_enabled:
                _LOGGER.debug("[%s] Starting data update cycle (callbacks registered, but polling for reliability)", current_time)
            else:
                _LOGGER.debug("[%s] Starting data update cycle (polling mode)", current_time)
            
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
            
            # Get current values for all data points using individual polling (no batch endpoint)
            # ALWAYS poll for values to ensure external changes are detected
            # Callbacks are unreliable and may fail silently, so we use polling as the primary method
            _LOGGER.debug("Fetching current values from device using individual datapoint polling...")
            try:
                values = await self.client.get_values()
                _LOGGER.debug("Successfully received %d values from device via polling", len(values) if values else 0)
                
                # Cache values for potential future use
                self._last_values = values
                
            except Exception as poll_error:
                _LOGGER.warning("Failed to poll for values: %s", poll_error)
                # Fall back to cached values if polling fails
                values = getattr(self, '_last_values', {})
                _LOGGER.debug("Using cached values due to polling failure (%d values)", len(values))

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

def get_local_ip_for_gira_x1() -> str | None:
    """
    Detect the local IP address that should be used for Gira X1 callbacks.
    
    Returns:
        The best IP address to use for callbacks, or None if not found.
        
    Priority:
    1. 10.1.1.85 (Home Assistant host) if we're running on that IP
    2. 10.1.1.175 (local testing machine) if we're running on that IP
    3. Any IP in 10.1.1.x subnet
    4. Any private IP that can reach Gira X1
    """
    try:
        # First, check if we're running on the known target IPs
        hostname = socket.gethostname()
        _LOGGER.debug("Current hostname: %s", hostname)
        
        # Get all local IP addresses
        local_ips = []
        
        # Method 1: Get IPs from hostname resolution
        try:
            for addr_info in socket.getaddrinfo(hostname, None):
                ip = addr_info[4][0]
                if ip not in local_ips and not ip.startswith('127.'):
                    local_ips.append(ip)
        except Exception as e:
            _LOGGER.debug("Error getting IPs from hostname: %s", e)
        
        # Method 2: Get IPs from network interfaces (cross-platform)
        try:
            # Connect to a remote address to find the local IP used for routing
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                # Connect to Gira X1 device to find the best local IP
                s.connect(("10.1.1.85", 80))  # Gira X1 IP
                local_ip = s.getsockname()[0]
                if local_ip not in local_ips and not local_ip.startswith('127.'):
                    local_ips.append(local_ip)
        except Exception as e:
            _LOGGER.debug("Error getting routing IP: %s", e)
            
        # Method 3: Try connecting to Google DNS to find default route IP
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                if local_ip not in local_ips and not local_ip.startswith('127.'):
                    local_ips.append(local_ip)
        except Exception as e:
            _LOGGER.debug("Error getting default route IP: %s", e)
        
        _LOGGER.info("Detected local IP addresses: %s", local_ips)
        
        # Priority selection logic
        for ip in local_ips:
            # Priority 1: Home Assistant host IP
            if ip == "10.1.1.85":
                _LOGGER.info("Detected Home Assistant host IP: %s", ip)
                return ip
                
        for ip in local_ips:
            # Priority 2: Local testing machine IP
            if ip == "10.1.1.175":
                _LOGGER.info("Detected local testing machine IP: %s", ip)
                return ip
                
        for ip in local_ips:
            # Priority 3: Any IP in the Gira X1 subnet
            if ip.startswith("10.1.1."):
                _LOGGER.info("Detected IP in Gira X1 subnet: %s", ip)
                return ip
                
        for ip in local_ips:
            # Priority 4: Any private IP
            if (ip.startswith("192.168.") or 
                ip.startswith("10.") or 
                ip.startswith("172.")):
                _LOGGER.info("Detected private IP: %s", ip)
                return ip
                
        # If no suitable IP found, return the first available
        if local_ips:
            _LOGGER.info("Using first available IP: %s", local_ips[0])
            return local_ips[0]
            
        _LOGGER.warning("No suitable local IP address found")
        return None
        
    except Exception as e:
        _LOGGER.error("Error detecting local IP: %s", e, exc_info=True)
        return None


def determine_callback_base_url(hass: HomeAssistant, config_entry) -> str | None:
    """
    Determine the best callback base URL for Gira X1 callbacks.
    
    Args:
        hass: Home Assistant instance
        config_entry: Configuration entry with optional override
        
    Returns:
        The base URL to use for callbacks (without path), or None if not available
    """
    # Check for explicit callback URL override first
    callback_url_override = config_entry.data.get(CONF_CALLBACK_URL_OVERRIDE)
    
    if callback_url_override:
        base_url = callback_url_override.rstrip('/')
        _LOGGER.info("Using explicit callback URL override: %s", base_url)
        return base_url
    
    # Try to detect local IP for Gira X1 network
    local_ip = get_local_ip_for_gira_x1()
    
    if local_ip:
        # Get Home Assistant port
        ha_port = 8123  # Default HA port
        try:
            # Try to get actual HA port from configuration
            if hasattr(hass.config, 'api') and hasattr(hass.config.api, 'port'):
                ha_port = hass.config.api.port
            elif hasattr(hass, 'http') and hasattr(hass.http, 'server_port'):
                ha_port = hass.http.server_port
        except Exception as e:
            _LOGGER.debug("Could not determine HA port, using default 8123: %s", e)
        
        # Build local network URL - Gira X1 requires HTTPS for callbacks
        base_url = f"https://{local_ip}:{ha_port}"
        _LOGGER.info("Using local network callback URL: %s", base_url)
        return base_url
    
    # Fallback to Home Assistant's default URL detection
    try:
        external_url = get_url(hass, prefer_external=True)
        if external_url:
            _LOGGER.info("Using Home Assistant external URL: %s", external_url)
            return external_url.rstrip('/')
    except Exception as e:
        _LOGGER.debug("Error getting external URL: %s", e)
    
    # Last resort: try internal URL
    try:
        internal_url = get_url(hass, prefer_external=False)
        if internal_url:
            _LOGGER.info("Using Home Assistant internal URL: %s", internal_url)
            return internal_url.rstrip('/')
    except Exception as e:
        _LOGGER.debug("Error getting internal URL: %s", e)
    
    _LOGGER.warning("Could not determine any suitable callback base URL")
    return None
