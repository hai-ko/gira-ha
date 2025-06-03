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

    async def get(self, request: web.Request) -> web.Response:
        """Handle GET requests for value callback endpoint (for testing)."""
        _LOGGER.info("Received GET request on value callback endpoint - responding with 200 OK")
        return web.Response(status=200, text="Gira X1 Value Callback Endpoint")

    async def post(self, request: web.Request) -> web.Response:
        """Process value change events from Gira X1."""
        try:
            # Log request details for debugging
            content_type = request.headers.get('content-type', 'unknown')
            _LOGGER.debug("Value callback request - Content-Type: %s, Method: %s", content_type, request.method)
            
            data = await request.json()
            _LOGGER.debug("Received value callback data: %s", data)
            
            # Validate token matches our client (if token is available)
            token = data.get("token")
            client_token = getattr(self.coordinator.client, '_token', None)
            
            # For test events, be more lenient with token validation
            events = data.get("events", [])
            
            # Multiple ways to detect test events based on Gira X1 behavior
            is_test_event = (
                len(events) == 0 or  # Empty event list
                any(str(event.get("event", "")).lower() == "test" for event in events) or  # Explicit test event
                data.get("test", False) or  # Test flag in data
                (len(events) == 1 and not events[0].get("event"))  # Single empty event (test pattern)
            )
            
            _LOGGER.debug("Value callback analysis - Events: %d, Is test: %s, Token present: %s", 
                         len(events), is_test_event, bool(token))
            
            if not is_test_event and (not token or not client_token or token != client_token):
                _LOGGER.warning("Invalid token in value callback: %s (expected: %s)", token, client_token)
                return web.Response(status=401, text="Invalid token")
            elif is_test_event:
                _LOGGER.info("Received test value callback event, responding with 200 OK")
                _LOGGER.debug("Test event data: %s", data)
            
            # Process value events (skip if it's a test event)
            if events and not is_test_event:
                await self._process_value_events(events)
            elif is_test_event:
                _LOGGER.debug("Skipping event processing for test callback")
            
            # Log any failures
            failures = data.get("failures", 0)
            if failures > 0:
                _LOGGER.warning("Gira X1 reported %d failed callback attempts", failures)
            
            return web.Response(status=200, text="OK")
            
        except json.JSONDecodeError as err:
            _LOGGER.error("Invalid JSON in value callback: %s", err)
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

    async def get(self, request: web.Request) -> web.Response:
        """Handle GET requests for service callback endpoint (for testing)."""
        _LOGGER.info("Received GET request on service callback endpoint - responding with 200 OK")
        return web.Response(status=200, text="Gira X1 Service Callback Endpoint")

    async def post(self, request: web.Request) -> web.Response:
        """Process service events from Gira X1."""
        try:
            # Log request details for debugging
            content_type = request.headers.get('content-type', 'unknown')
            _LOGGER.debug("Service callback request - Content-Type: %s, Method: %s", content_type, request.method)
            
            data = await request.json()
            _LOGGER.info("Received service callback data: %s", data)
            
            # Validate token matches our client (if token is available)
            token = data.get("token")
            client_token = getattr(self.coordinator.client, '_token', None)
            
            # For test events, be more lenient with token validation
            events = data.get("events", [])
            
            # Multiple ways to detect test events based on Gira X1 behavior
            is_test_event = (
                len(events) == 0 or  # Empty event list (similar to value callback)
                any(event.get("event") == "test" for event in events) or  # Explicit test event
                data.get("test", False) or  # Test flag in data
                "test" in str(data).lower()  # Any mention of test in the payload
            )
            
            _LOGGER.info("Service callback analysis - Events: %d, Is test: %s, Token present: %s", 
                        len(events), is_test_event, bool(token))
            
            if not is_test_event and (not token or not client_token or token != client_token):
                _LOGGER.warning("Invalid token in service callback: %s (expected: %s)", token, client_token)
                return web.Response(status=401, text="Invalid token")
            elif is_test_event:
                _LOGGER.info("Received test service callback event, responding with 200 OK")
                _LOGGER.debug("Test event data: %s", data)
            
            # Process service events (skip if it's a test event)
            if events and not is_test_event:
                await self._process_service_events(events)
            elif is_test_event:
                _LOGGER.debug("Skipping event processing for test callback")
            
            # Log any failures
            failures = data.get("failures", 0)
            if failures > 0:
                _LOGGER.warning("Gira X1 reported %d failed callback attempts", failures)
            
            _LOGGER.info("Service callback processed successfully, returning 200 OK")
            return web.Response(status=200, text="OK")
            
        except json.JSONDecodeError as err:
            _LOGGER.error("Invalid JSON in service callback: %s", err)
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
