"""Constants for the Gira X1 integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "gira_x1"

# Configuration constants
CONF_HOST: Final = "host"
CONF_PORT: Final = "port"
CONF_USERNAME: Final = "username"
CONF_PASSWORD: Final = "password"
CONF_TOKEN: Final = "token"
CONF_AUTH_METHOD: Final = "auth_method"
CONF_SCAN_INTERVAL: Final = "scan_interval"

# Authentication methods
AUTH_METHOD_PASSWORD: Final = "password"
AUTH_METHOD_TOKEN: Final = "token"

# Default values
DEFAULT_PORT: Final = 80
DEFAULT_SCAN_INTERVAL: Final = 30

# API endpoints
API_BASE_PATH: Final = "/api/v2"
API_CLIENTS: Final = f"{API_BASE_PATH}/clients"
API_UICONFIG: Final = f"{API_BASE_PATH}/uiconfig"
API_UICONFIG_UID: Final = f"{API_BASE_PATH}/uiconfig/uid"
API_VALUES: Final = "/api/values"  # Values endpoint is unversioned and requires /{datapoint_id}
API_LICENSES: Final = f"{API_BASE_PATH}/licenses"
API_CALLBACKS_PATH: Final = "/callbacks"  # Appended to client endpoint

# Device types
DEVICE_TYPE_LIGHT: Final = "light"
DEVICE_TYPE_SWITCH: Final = "switch"
DEVICE_TYPE_COVER: Final = "cover"
DEVICE_TYPE_SENSOR: Final = "sensor"
DEVICE_TYPE_BINARY_SENSOR: Final = "binary_sensor"
DEVICE_TYPE_CLIMATE: Final = "climate"

# Device types mapping from Gira function types
GIRA_FUNCTION_TYPES = {
    "de.gira.schema.functions.Switch": DEVICE_TYPE_SWITCH,
    "de.gira.schema.functions.KNX.Light": DEVICE_TYPE_LIGHT,
    "de.gira.schema.functions.ColoredLight": DEVICE_TYPE_LIGHT,
    "de.gira.schema.functions.TunableLight": DEVICE_TYPE_LIGHT,
    "de.gira.schema.functions.Covering": DEVICE_TYPE_COVER,
    "de.gira.schema.functions.KNX.HeatingCooling": DEVICE_TYPE_CLIMATE,
    "de.gira.schema.functions.Trigger": "button",  # Trigger functions are best as buttons
    "de.gira.schema.functions.PressAndHold": DEVICE_TYPE_SWITCH,
    "de.gira.schema.functions.Sonos.Audio": DEVICE_TYPE_SENSOR,  # Treat as sensor for volume, etc.
}

# Channel types mapping
GIRA_CHANNEL_TYPES = {
    "de.gira.schema.channels.Switch": DEVICE_TYPE_SWITCH,
    "de.gira.schema.channels.KNX.Dimmer": DEVICE_TYPE_LIGHT,
    "de.gira.schema.channels.DimmerRGBW": DEVICE_TYPE_LIGHT,
    "de.gira.schema.channels.DimmerWhite": DEVICE_TYPE_LIGHT,
    "de.gira.schema.channels.BlindWithPos": DEVICE_TYPE_COVER,
    "de.gira.schema.channels.KNX.HeatingCoolingSwitchable": DEVICE_TYPE_CLIMATE,
    "de.gira.schema.channels.Trigger": "button",
    "de.gira.schema.channels.Temperature": DEVICE_TYPE_SENSOR,
    "de.gira.schema.channels.Humidity": DEVICE_TYPE_SENSOR,
    "de.gira.schema.channels.Sonos.Audio": DEVICE_TYPE_SENSOR,
}

# Function types from Gira X1
FUNCTION_SWITCH: Final = 1
FUNCTION_DIMMER: Final = 2
FUNCTION_BLIND: Final = 3
FUNCTION_TEMPERATURE: Final = 4
FUNCTION_HUMIDITY: Final = 5
FUNCTION_PRESENCE: Final = 6
FUNCTION_MOTION: Final = 7

# Status codes
STATUS_OK: Final = 200
STATUS_UNAUTHORIZED: Final = 401
STATUS_NOT_FOUND: Final = 404

# Update intervals
UPDATE_INTERVAL_SECONDS: Final = 5  # Default to 5-second polling
FAST_UPDATE_INTERVAL_SECONDS: Final = 5
CALLBACK_UPDATE_INTERVAL_SECONDS: Final = 300  # 5 minutes fallback polling when using callbacks

# Timeouts
REQUEST_TIMEOUT: Final = 10
LOGIN_TIMEOUT: Final = 30

# API endpoints
API_CALLBACKS: Final = "callbacks"

# Callback configuration
CALLBACK_WEBHOOK_ID: Final = "gira_x1_callback"
WEBHOOK_VALUE_CALLBACK_PATH: Final = "/api/gira_x1/callback/value"
WEBHOOK_SERVICE_CALLBACK_PATH: Final = "/api/gira_x1/callback/service"

# Configuration options
CONF_CALLBACK_URL_OVERRIDE: Final = "callback_url_override"
CONF_CALLBACK_TOKEN: Final = "callback_token"
