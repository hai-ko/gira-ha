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
            # 🔔 COMPREHENSIVE CALLBACK LOGGING
            content_type = request.headers.get('content-type', 'unknown')
            client_ip = request.remote
            _LOGGER.info("🔔 INCOMING VALUE CALLBACK: Received from %s (Content-Type: %s)", client_ip, content_type)
            
            data = await request.json()
            _LOGGER.info("🔔 VALUE CALLBACK DATA: %s", data)
            
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
            
            _LOGGER.info("🔔 VALUE CALLBACK ANALYSIS: Events=%d, IsTest=%s, TokenPresent=%s", 
                         len(events), is_test_event, bool(token))
            
            if not is_test_event and (not token or not client_token or token != client_token):
                _LOGGER.warning("❌ VALUE CALLBACK REJECTED: Invalid token %s (expected: %s)", token, client_token)
                return web.Response(status=401, text="Invalid token")
            elif is_test_event:
                _LOGGER.info("✅ VALUE CALLBACK TEST: Received test callback event, responding with 200 OK")
                _LOGGER.debug("🔔 Test event details: %s", data)
            
            # Process value events (skip if it's a test event)
            if events and not is_test_event:
                _LOGGER.info("🔔 VALUE CALLBACK PROCESSING: Processing %d value events", len(events))
                await self._process_value_events(events)
            elif is_test_event:
                _LOGGER.debug("🔔 VALUE CALLBACK TEST: Skipping event processing for test callback")
            
            # Log any failures
            failures = data.get("failures", 0)
            if failures > 0:
                _LOGGER.warning("⚠️ VALUE CALLBACK: Gira X1 reported %d failed callback attempts", failures)
            
            _LOGGER.info("✅ VALUE CALLBACK SUCCESS: Processed successfully, returning 200 OK")
            return web.Response(status=200, text="OK")
            
        except json.JSONDecodeError as err:
            _LOGGER.error("❌ VALUE CALLBACK ERROR: Invalid JSON - %s", err)
            return web.Response(status=400, text="Invalid JSON")
        except Exception as err:
            _LOGGER.error("❌ VALUE CALLBACK ERROR: Processing failed - %s", err, exc_info=True)
            return web.Response(status=500, text="Internal Server Error")

    async def _process_value_events(self, events: list[Dict[str, Any]]) -> None:
        """Process value change events and update coordinator data."""
        if not self.coordinator.data:
            _LOGGER.warning("⚠️ VALUE PROCESSING: Coordinator data not available, ignoring value events")
            return

        # Update values in coordinator data
        values = self.coordinator.data.get("values", {}).copy()
        updated_values = []
        
        _LOGGER.info("🔔 VALUE PROCESSING: Processing %d value change events", len(events))
        
        for event in events:
            uid = event.get("uid")
            value = event.get("value")
            
            if uid and value is not None:
                old_value = values.get(uid)
                values[uid] = value
                updated_values.append({"uid": uid, "old": old_value, "new": value})
                _LOGGER.debug("📊 VALUE CHANGE: %s: %s → %s", uid, old_value, value)
            else:
                _LOGGER.warning("⚠️ INVALID VALUE EVENT: Missing uid or value in event: %s", event)
        
        if updated_values:
            # Update coordinator data with new values
            new_data = self.coordinator.data.copy()
            new_data["values"] = values
            
            # Trigger coordinator update without API call
            self.coordinator.async_set_updated_data(new_data)
            
            _LOGGER.info("✅ VALUE PROCESSING COMPLETE: Updated %d values via callback", len(updated_values))
        else:
            _LOGGER.debug("🔔 VALUE PROCESSING: No valid value changes to process")


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
            # 🔔 COMPREHENSIVE CALLBACK LOGGING
            content_type = request.headers.get('content-type', 'unknown')
            client_ip = request.remote
            _LOGGER.info("🔔 INCOMING SERVICE CALLBACK: Received from %s (Content-Type: %s)", client_ip, content_type)
            
            data = await request.json()
            _LOGGER.info("🔔 SERVICE CALLBACK DATA: %s", data)
            
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
            
            _LOGGER.info("🔔 SERVICE CALLBACK ANALYSIS: Events=%d, IsTest=%s, TokenPresent=%s", 
                         len(events), is_test_event, bool(token))
            
            if not is_test_event and (not token or not client_token or token != client_token):
                _LOGGER.warning("❌ SERVICE CALLBACK REJECTED: Invalid token %s (expected: %s)", token, client_token)
                return web.Response(status=401, text="Invalid token")
            elif is_test_event:
                _LOGGER.info("✅ SERVICE CALLBACK TEST: Received test callback event, responding with 200 OK")
                _LOGGER.debug("🔔 Test event details: %s", data)
            
            # Process service events (skip if it's a test event)
            if events and not is_test_event:
                _LOGGER.info("🔔 SERVICE CALLBACK PROCESSING: Processing %d service events", len(events))
                await self._process_service_events(events)
            elif is_test_event:
                _LOGGER.debug("🔔 SERVICE CALLBACK TEST: Skipping event processing for test callback")
            
            # Log any failures
            failures = data.get("failures", 0)
            if failures > 0:
                _LOGGER.warning("⚠️ SERVICE CALLBACK: Gira X1 reported %d failed callback attempts", failures)
            
            _LOGGER.info("✅ SERVICE CALLBACK SUCCESS: Processed successfully, returning 200 OK")
            return web.Response(status=200, text="OK")
            
        except json.JSONDecodeError as err:
            _LOGGER.error("❌ SERVICE CALLBACK ERROR: Invalid JSON - %s", err)
            return web.Response(status=400, text="Invalid JSON")
        except Exception as err:
            _LOGGER.error("❌ SERVICE CALLBACK ERROR: Processing failed - %s", err, exc_info=True)
            return web.Response(status=500, text="Internal Server Error")

    async def _process_service_events(self, events: list[Dict[str, Any]]) -> None:
        """Process service events and trigger appropriate actions."""
        for event in events:
            event_type = event.get("event")
            _LOGGER.info("🔔 PROCESSING SERVICE EVENT: %s", event_type)
            
            if event_type == "uiConfigChanged":
                # UI configuration changed, trigger full refresh
                _LOGGER.info("📱 UI CONFIGURATION CHANGED: Triggering coordinator refresh")
                await self.coordinator.async_request_refresh()
                
            elif event_type == "projectConfigChanged":
                # Project configuration changed, wait a bit then refresh
                _LOGGER.info("🏗️ PROJECT CONFIGURATION CHANGED: Scheduling delayed refresh")
                # Schedule refresh after 10 seconds to allow device to settle
                self.coordinator.hass.async_create_task(
                    self._delayed_refresh(10)
                )
                
            elif event_type == "restart":
                _LOGGER.info("🔄 GIRA X1 RESTART: Device is restarting, callbacks will be lost")
                # Device is restarting, callbacks will be lost
                # Coordinator will automatically re-establish connection on next update
                
            elif event_type == "startup":
                _LOGGER.info("🚀 GIRA X1 STARTUP: Device has started up, refreshing and re-registering callbacks")
                # Device has restarted, trigger refresh and re-register callbacks
                await self.coordinator.async_request_refresh()
                
            elif event_type == "test":
                _LOGGER.debug("🧪 TEST EVENT: Received test callback event")
                # Test event during callback registration
                
            else:
                _LOGGER.warning("❓ UNKNOWN SERVICE EVENT: %s (data: %s)", event_type, event)

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
