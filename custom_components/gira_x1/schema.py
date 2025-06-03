"""Configuration schema for Gira X1 integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.helpers import config_validation as cv

from .const import DEFAULT_PORT, DOMAIN

# Configuration schema for YAML setup (if needed)
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

# Service schemas
SERVICE_REFRESH_DEVICE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
    }
)

SERVICE_SET_RAW_VALUE_SCHEMA = vol.Schema(
    {
        vol.Required("function_id"): cv.string,
        vol.Required("value"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    }
)
