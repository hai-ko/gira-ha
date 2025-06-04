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
    CONF_CALLBACK_URL_OVERRIDE,
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
    
    # Set up callback system for real-time updates
    callback_success = await coordinator.setup_callbacks()
    if callback_success:
        _LOGGER.info("✅ CALLBACK SYSTEM ENABLED: Real-time updates active with %d second fallback polling", CALLBACK_UPDATE_INTERVAL_SECONDS)
    else:
        _LOGGER.info("⚠️ CALLBACK SYSTEM FAILED: Using fast polling mode with %d second intervals", FAST_UPDATE_INTERVAL_SECONDS)
    
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
        
        # Clean up callbacks
        await coordinator.cleanup_callbacks()
        
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
        self.hass = hass

        # Callback system attributes
        self.callbacks_enabled = False
        self._webhook_handlers = None

        # Use default polling interval initially (will be adjusted based on callback success)
        update_interval = timedelta(seconds=UPDATE_INTERVAL_SECONDS)
        _LOGGER.info("Initializing coordinator with %d-second polling interval", UPDATE_INTERVAL_SECONDS)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    async def setup_callbacks(self) -> bool:
        """Set up callback system for real-time updates."""
        try:
            _LOGGER.info("🔧 CALLBACK SETUP: Starting callback system setup")
            
            # Determine callback URLs
            base_url = self._determine_callback_base_url()
            if not base_url:
                _LOGGER.error("❌ CALLBACK SETUP FAILED: Could not determine callback base URL")
                return False
                
            value_callback_url = f"{base_url}{WEBHOOK_VALUE_CALLBACK_PATH}"
            service_callback_url = f"{base_url}{WEBHOOK_SERVICE_CALLBACK_PATH}"
            
            _LOGGER.info("🔧 CALLBACK SETUP: URLs determined")
            _LOGGER.info("🔧   Base URL: %s", base_url)
            _LOGGER.info("🔧   Value callback: %s", value_callback_url)
            _LOGGER.info("🔧   Service callback: %s", service_callback_url)
            
            # Try to register callbacks with Gira X1 FIRST
            _LOGGER.info("🔧 CALLBACK SETUP: Registering callbacks with Gira X1...")
            success = await self.client.register_callbacks(
                value_callback_url=value_callback_url,
                service_callback_url=service_callback_url,
                test_callbacks=True
            )
            
            if success:
                # Only register webhook handlers if Gira X1 registration succeeded
                _LOGGER.info("🔧 CALLBACK SETUP: Gira X1 registration successful, setting up webhook handlers...")
                self._webhook_handlers = register_webhook_handlers(self.hass, self)
                self.callbacks_enabled = True
                
                # Switch to slow fallback polling since we have real-time callbacks
                self.update_interval = timedelta(seconds=CALLBACK_UPDATE_INTERVAL_SECONDS)
                _LOGGER.info("✅ CALLBACK SETUP SUCCESS: Real-time callbacks active, fallback polling every %d seconds", CALLBACK_UPDATE_INTERVAL_SECONDS)
                
                return True
            else:
                # Gira X1 registration failed, use fast polling instead
                _LOGGER.warning("❌ CALLBACK SETUP FAILED: Gira X1 registration failed, switching to fast polling")
                self._webhook_handlers = None
                self.callbacks_enabled = False
                
                # Switch to fast polling to compensate for lack of real-time updates
                self.update_interval = timedelta(seconds=FAST_UPDATE_INTERVAL_SECONDS)
                _LOGGER.info("⚠️ FALLBACK MODE: Using fast polling every %d seconds", FAST_UPDATE_INTERVAL_SECONDS)
                
                return False
                
        except Exception as err:
            _LOGGER.error("❌ CALLBACK SETUP ERROR: Unexpected error - %s", err, exc_info=True)
            
            # Ensure no webhook handlers are left registered on error
            if hasattr(self, '_webhook_handlers') and self._webhook_handlers:
                try:
                    unregister_webhook_handlers(self.hass)
                except Exception as cleanup_err:
                    _LOGGER.warning("Failed to clean up webhook handlers: %s", cleanup_err)
            
            self._webhook_handlers = None
            self.callbacks_enabled = False
            
            # Use fast polling as fallback
            self.update_interval = timedelta(seconds=FAST_UPDATE_INTERVAL_SECONDS)
            _LOGGER.info("⚠️ ERROR FALLBACK: Using fast polling every %d seconds", FAST_UPDATE_INTERVAL_SECONDS)
            
            return False

    async def cleanup_callbacks(self) -> None:
        """Clean up callback system."""
        try:
            _LOGGER.info("🧹 CALLBACK CLEANUP: Starting callback system cleanup")
            
            if self.callbacks_enabled:
                # Unregister from Gira X1
                _LOGGER.info("🧹 CALLBACK CLEANUP: Unregistering callbacks from Gira X1...")
                await self.client.unregister_callbacks()
                
                # Unregister webhook handlers
                if self._webhook_handlers:
                    _LOGGER.info("🧹 CALLBACK CLEANUP: Removing webhook handlers...")
                    unregister_webhook_handlers(self.hass)
                
                self.callbacks_enabled = False
                self._webhook_handlers = None
                _LOGGER.info("✅ CALLBACK CLEANUP SUCCESS: Callback system cleaned up")
            else:
                _LOGGER.debug("🧹 CALLBACK CLEANUP: No callbacks to clean up")
                
        except Exception as err:
            _LOGGER.warning("⚠️ CALLBACK CLEANUP WARNING: Error during cleanup - %s", err)

    def _determine_callback_base_url(self) -> str:
        """Determine the base URL for callbacks."""
        try:
            # 🔒 FORCED OVERRIDE: Always use HTTPS proxy to resolve SSL/TLS issues
            https_proxy_url = "https://home.hf17-1.de"
            _LOGGER.info("🌐 CALLBACK URL: FORCED OVERRIDE - Using HTTPS proxy - %s", https_proxy_url)
            _LOGGER.info("💡 HTTPS PROXY: SSL/TLS connectivity override active")
            return https_proxy_url
            
            # Check for explicit override first (disabled while using forced override)
            callback_override = self.hass.data.get(DOMAIN, {}).get(CONF_CALLBACK_URL_OVERRIDE)
            if callback_override:
                _LOGGER.info("🌐 CALLBACK URL: Using configured override - %s", callback_override)
                return callback_override
            
            # Fallback: Try to detect local IP that can reach Gira X1
            local_ip = self._get_local_ip_for_gira_x1()
            if local_ip:
                # Use HTTPS as required by Gira X1
                base_url = f"https://{local_ip}:8123"
                _LOGGER.info("🌐 CALLBACK URL: Using detected local IP - %s", base_url)
                return base_url
            
            # Fallback to Home Assistant's configured external URL
            try:
                external_url = get_url(self.hass, allow_external=True, prefer_external=True)
                if external_url:
                    # Convert HTTP to HTTPS if needed (Gira X1 requires HTTPS)
                    if external_url.startswith("http://"):
                        external_url = external_url.replace("http://", "https://")
                    _LOGGER.info("🌐 CALLBACK URL: Using Home Assistant external URL - %s", external_url)
                    return external_url
            except Exception as url_err:
                _LOGGER.warning("Failed to get Home Assistant external URL: %s", url_err)
            
            _LOGGER.error("❌ CALLBACK URL: Could not determine suitable callback URL")
            return None
            
        except Exception as err:
            _LOGGER.error("❌ CALLBACK URL ERROR: Error determining callback URL - %s", err, exc_info=True)
            return None

    def _get_local_ip_for_gira_x1(self) -> str:
        """Get local IP address that can reach the Gira X1 device."""
        try:
            gira_ip = self.client.host
            _LOGGER.debug("🔍 IP DETECTION: Looking for local IP to reach Gira X1 at %s", gira_ip)
            
            # Use socket connection to find the local IP that routes to Gira X1
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect((gira_ip, 80))
                    detected_ip = s.getsockname()[0]
                    _LOGGER.debug("🔍 IP DETECTION: Detected local IP via socket route to Gira X1 - %s", detected_ip)
                    
                    # This is the correct IP - the one Home Assistant is using to reach Gira X1
                    # This is where Gira X1 should send callbacks back to
                    _LOGGER.info("🔍 IP DETECTION: Using local IP %s for callbacks from Gira X1 at %s", detected_ip, gira_ip)
                    return detected_ip
                    
            except Exception as socket_err:
                _LOGGER.debug("Socket detection failed: %s", socket_err)
            
            # Fallback: Try to get any IP in the same subnet as Gira X1
            try:
                if platform.system() == "Darwin":  # macOS
                    result = subprocess.run(["route", "get", gira_ip], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if 'interface:' in line:
                                interface = line.split(':')[1].strip()
                                ip_result = subprocess.run(["ifconfig", interface], capture_output=True, text=True, timeout=5)
                                if ip_result.returncode == 0:
                                    for ip_line in ip_result.stdout.split('\n'):
                                        if 'inet ' in ip_line and not '127.0.0.1' in ip_line:
                                            ip = ip_line.split()[1]
                                            _LOGGER.debug("🔍 IP DETECTION: Fallback - Found interface IP - %s", ip)
                                            return ip
                else:  # Linux/other
                    # Try hostname -I command
                    result = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        for ip in result.stdout.split():
                            if not ip.startswith('127.') and '.' in ip:
                                _LOGGER.debug("🔍 IP DETECTION: Fallback - Found hostname IP - %s", ip)
                                return ip
                                
            except Exception as route_err:
                _LOGGER.debug("Fallback IP detection failed: %s", route_err)
            
            _LOGGER.warning("❌ IP DETECTION: Could not detect suitable local IP")
            return None
            
        except Exception as err:
            _LOGGER.error("❌ IP DETECTION ERROR: Error detecting local IP - %s", err, exc_info=True)
            return None

    async def _async_update_data(self):
        """Update data via library."""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Log the current mode
            if self.callbacks_enabled and self._webhook_handlers:
                _LOGGER.debug("[%s] Starting data update cycle (hybrid mode: callbacks + %ds fallback polling)", current_time, self.update_interval.total_seconds())
            elif self.callbacks_enabled and not self._webhook_handlers:
                _LOGGER.debug("[%s] Starting data update cycle (callbacks enabled but no webhooks - using %ds polling)", current_time, self.update_interval.total_seconds())
            else:
                _LOGGER.debug("[%s] Starting data update cycle (fast polling mode: %ds intervals)", current_time, self.update_interval.total_seconds())
            
            # Check if UI config has changed
            current_uid = await self.client.get_ui_config_uid()
            _LOGGER.debug("Current UI config UID: %s, cached UID: %s", current_uid, self.ui_config_uid)
            
            if current_uid != self.ui_config_uid:
                _LOGGER.info("UI configuration changed (UID: %s), refreshing full config...", current_uid)
                
                # If callbacks are enabled, re-register them after config change
                if self.callbacks_enabled and self._webhook_handlers:
                    _LOGGER.info("🔄 CONFIG CHANGE: Re-registering callbacks after UI config change...")
                    try:
                        # Re-register callbacks
                        base_url = self._determine_callback_base_url()
                        if base_url:
                            value_callback_url = f"{base_url}{WEBHOOK_VALUE_CALLBACK_PATH}"
                            service_callback_url = f"{base_url}{WEBHOOK_SERVICE_CALLBACK_PATH}"
                            await self.client.register_callbacks(
                                value_callback_url=value_callback_url,
                                service_callback_url=service_callback_url,
                                test_callbacks=False  # Don't test on re-registration
                            )
                            _LOGGER.info("✅ CONFIG CHANGE: Callbacks re-registered successfully")
                    except Exception as callback_err:
                        _LOGGER.warning("⚠️ CONFIG CHANGE: Failed to re-register callbacks: %s", callback_err)
                
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
            
            # Get current values for all data points
            # In callback mode, this serves as a fallback; in polling mode, this is the primary update mechanism
            if self.callbacks_enabled and self._webhook_handlers:
                _LOGGER.debug("Fetching fallback values (callback mode with %ds fallback polling)...", self.update_interval.total_seconds())
            else:
                _LOGGER.debug("Fetching current values from device using fast polling (%ds intervals)...", self.update_interval.total_seconds())
            
            try:
                values = await self.client.get_values()
                _LOGGER.debug("Successfully received %d values from device", len(values) if values else 0)
                
                # Log polling state changes (more detailed in non-callback mode)
                if hasattr(self, '_last_values') and self._last_values:
                    changes_detected = 0
                    for uid, new_value in values.items():
                        old_value = self._last_values.get(uid)
                        if old_value != new_value:
                            if self.callbacks_enabled:
                                _LOGGER.debug("🔄 FALLBACK POLLING DETECTED CHANGE: %s: '%s' → '%s'", uid, old_value, new_value)
                            else:
                                _LOGGER.info("🔄 FAST POLLING DETECTED CHANGE: %s: '%s' → '%s'", uid, old_value, new_value)
                            changes_detected += 1
                    
                    if changes_detected == 0:
                        if self.callbacks_enabled:
                            _LOGGER.debug("No state changes detected in fallback polling cycle")
                        else:
                            _LOGGER.debug("No state changes detected in fast polling cycle")
                    else:
                        if self.callbacks_enabled:
                            _LOGGER.info("📊 Total fallback polling changes detected: %d", changes_detected)
                        else:
                            _LOGGER.info("📊 Total fast polling changes detected: %d", changes_detected)
                else:
                    if self.callbacks_enabled:
                        _LOGGER.info("📊 Initial fallback polling cycle - received %d datapoint values", len(values))
                    else:
                        _LOGGER.info("📊 Initial fast polling cycle - received %d datapoint values", len(values))
                    # Log first few values for debugging
                    sample_values = list(values.items())[:5]
                    for uid, value in sample_values:
                        _LOGGER.debug("Initial value: %s = '%s'", uid, value)
                
                # Cache values for change detection
                self._last_values = values
                
            except Exception as poll_error:
                if self.callbacks_enabled:
                    _LOGGER.warning("Failed to poll for fallback values: %s", poll_error)
                else:
                    _LOGGER.warning("Failed to poll for values in fast polling mode: %s", poll_error)
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
