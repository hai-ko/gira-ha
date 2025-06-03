"""Webhook handlers for Gira X1 callbacks."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    WEBHOOK_VALUE_CALLBACK_PATH,
    WEBHOOK_SERVICE_CALLBACK_PATH,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class GiraX1ValueCallbackView(HomeAssistantView):
    """Handle value change callbacks from Gira X1."""

    url = WEBHOOK_VALUE_CALLBACK_PATH
    name = "api:gira_x1:values"
    requires_auth = False  # Gira X1 will authenticate via token

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the value callback view."""
        self.coordinator = coordinator

    async def post(self, request: web.Request) -> web.Response:
        """Process value change events from Gira X1."""
        try:
            data = await request.json()
            _LOGGER.debug("Received value callback: %s", data)
            
            # Validate token matches our client
            token = data.get("token")
            if not token or token != self.coordinator.client._token:
                _LOGGER.warning("Invalid token in value callback: %s", token)
                return web.Response(status=401, text="Invalid token")
            
            # Process value events
            events = data.get("events", [])
            if events:
                await self._process_value_events(events)
            
            # Log any failures
            failures = data.get("failures", 0)
            if failures > 0:
                _LOGGER.warning("Gira X1 reported %d failed callback attempts", failures)
            
            return web.Response(status=200, text="OK")
            
        except json.JSONDecodeError:
            _LOGGER.error("Invalid JSON in value callback")
            return web.Response(status=400, text="Invalid JSON")
        except Exception as err:
            _LOGGER.error("Error processing value callback: %s", err, exc_info=True)
            return web.Response(status=500, text="Internal Server Error")

    async def _process_value_events(self, events: list[Dict[str, Any]]) -> None:
        """Process value change events and update coordinator data."""
        if not self.coordinator.data:
            _LOGGER.warning("Coordinator data not available, ignoring value events")
            return
            
        # Update values in coordinator data
        values = self.coordinator.data.get("values", {}).copy()
        updated_values = []
        
        for event in events:
            uid = event.get("uid")
            value = event.get("value")
            
            if uid and value is not None:
                old_value = values.get(uid)
                values[uid] = value
                updated_values.append({"uid": uid, "old": old_value, "new": value})
                _LOGGER.debug("Updated value for %s: %s -> %s", uid, old_value, value)
        
        if updated_values:
            # Update coordinator data with new values
            new_data = self.coordinator.data.copy()
            new_data["values"] = values
            
            # Trigger coordinator update without API call
            self.coordinator.async_set_updated_data(new_data)
            
            _LOGGER.info("Processed %d value updates via callback", len(updated_values))


class GiraX1ServiceCallbackView(HomeAssistantView):
    """Handle service event callbacks from Gira X1."""

    url = WEBHOOK_SERVICE_CALLBACK_PATH
    name = "api:gira_x1:service"
    requires_auth = False  # Gira X1 will authenticate via token

    def __init__(self, coordinator: DataUpdateCoordinator) -> None:
        """Initialize the service callback view."""
        self.coordinator = coordinator

    async def post(self, request: web.Request) -> web.Response:
        """Process service events from Gira X1."""
        try:
            data = await request.json()
            _LOGGER.debug("Received service callback: %s", data)
            
            # Validate token matches our client
            token = data.get("token")
            if not token or token != self.coordinator.client._token:
                _LOGGER.warning("Invalid token in service callback: %s", token)
                return web.Response(status=401, text="Invalid token")
            
            # Process service events
            events = data.get("events", [])
            if events:
                await self._process_service_events(events)
            
            # Log any failures
            failures = data.get("failures", 0)
            if failures > 0:
                _LOGGER.warning("Gira X1 reported %d failed callback attempts", failures)
            
            return web.Response(status=200, text="OK")
            
        except json.JSONDecodeError:
            _LOGGER.error("Invalid JSON in service callback")
            return web.Response(status=400, text="Invalid JSON")
        except Exception as err:
            _LOGGER.error("Error processing service callback: %s", err, exc_info=True)
            return web.Response(status=500, text="Internal Server Error")

    async def _process_service_events(self, events: list[Dict[str, Any]]) -> None:
        """Process service events and trigger appropriate actions."""
        for event in events:
            event_type = event.get("event")
            _LOGGER.info("Received service event: %s", event_type)
            
            if event_type == "uiConfigChanged":
                # UI configuration changed, trigger full refresh
                _LOGGER.info("UI configuration changed, triggering coordinator refresh")
                await self.coordinator.async_request_refresh()
                
            elif event_type == "projectConfigChanged":
                # Project configuration changed, wait a bit then refresh
                _LOGGER.info("Project configuration changed, scheduling delayed refresh")
                # Schedule refresh after 10 seconds to allow device to settle
                self.coordinator.hass.async_create_task(
                    self._delayed_refresh(10)
                )
                
            elif event_type == "restart":
                _LOGGER.info("Gira X1 device is restarting")
                # Device is restarting, callbacks will be lost
                # Coordinator will automatically re-establish connection on next update
                
            elif event_type == "startup":
                _LOGGER.info("Gira X1 device has started up")
                # Device has restarted, trigger refresh and re-register callbacks
                await self.coordinator.async_request_refresh()
                
            elif event_type == "test":
                _LOGGER.debug("Received test callback event")
                # Test event during callback registration
                
            else:
                _LOGGER.debug("Unknown service event type: %s", event_type)

    async def _delayed_refresh(self, delay_seconds: int) -> None:
        """Refresh coordinator after a delay."""
        import asyncio
        await asyncio.sleep(delay_seconds)
        await self.coordinator.async_request_refresh()


def register_webhook_handlers(hass: HomeAssistant, coordinator: DataUpdateCoordinator) -> tuple[GiraX1ValueCallbackView, GiraX1ServiceCallbackView]:
    """Register webhook handlers for Gira X1 callbacks.
    
    Returns:
        Tuple of (value_view, service_view) for reference
    """
    value_view = GiraX1ValueCallbackView(coordinator)
    service_view = GiraX1ServiceCallbackView(coordinator)
    
    # Register with Home Assistant HTTP component
    hass.http.register_view(value_view)
    hass.http.register_view(service_view)
    
    _LOGGER.info("Registered Gira X1 webhook handlers")
    return value_view, service_view


def unregister_webhook_handlers(hass: HomeAssistant) -> None:
    """Unregister webhook handlers for Gira X1 callbacks."""
    # Home Assistant automatically cleans up views when integration is unloaded
    _LOGGER.info("Webhook handlers will be cleaned up by Home Assistant")
