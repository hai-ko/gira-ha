"""Config flow for Gira X1 integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .api import GiraX1AuthError, GiraX1Client
from .const import (
    AUTH_METHOD_PASSWORD,
    AUTH_METHOD_TOKEN,
    CONF_AUTH_METHOD,
    CONF_TOKEN,
    DEFAULT_PORT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_AUTH_METHOD, default=AUTH_METHOD_PASSWORD): vol.In([AUTH_METHOD_PASSWORD, AUTH_METHOD_TOKEN]),
    }
)

STEP_AUTH_PASSWORD_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

STEP_AUTH_TOKEN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOKEN): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gira X1."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.host_data: Dict[str, Any] = {}

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        self.host_data = user_input
        auth_method = user_input[CONF_AUTH_METHOD]

        if auth_method == AUTH_METHOD_PASSWORD:
            return await self.async_step_auth_password()
        else:
            return await self.async_step_auth_token()

    async def async_step_auth_password(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle username/password authentication."""
        if user_input is None:
            return self.async_show_form(
                step_id="auth_password", data_schema=STEP_AUTH_PASSWORD_SCHEMA
            )

        errors = {}
        auth_data = {**self.host_data, **user_input}

        try:
            info = await validate_input(self.hass, auth_data)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=auth_data)

        return self.async_show_form(
            step_id="auth_password", data_schema=STEP_AUTH_PASSWORD_SCHEMA, errors=errors
        )

    async def async_step_auth_token(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle token authentication."""
        if user_input is None:
            return self.async_show_form(
                step_id="auth_token", data_schema=STEP_AUTH_TOKEN_SCHEMA
            )

        errors = {}
        auth_data = {**self.host_data, **user_input}

        try:
            info = await validate_input(self.hass, auth_data)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=auth_data)

        return self.async_show_form(
            step_id="auth_token", data_schema=STEP_AUTH_TOKEN_SCHEMA, errors=errors
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    auth_method = data.get(CONF_AUTH_METHOD, AUTH_METHOD_PASSWORD)
    
    if auth_method == AUTH_METHOD_TOKEN:
        client = GiraX1Client(
            hass,
            data[CONF_HOST],
            data[CONF_PORT],
            token=data[CONF_TOKEN],
        )
    else:
        client = GiraX1Client(
            hass,
            data[CONF_HOST],
            data[CONF_PORT],
            username=data[CONF_USERNAME],
            password=data[CONF_PASSWORD],
        )

    try:
        if not await client.test_connection():
            raise CannotConnect
    except GiraX1AuthError as err:
        raise InvalidAuth from err
    except Exception as err:
        raise CannotConnect from err
    finally:
        await client.logout()

    # Return info that you want to store in the config entry.
    auth_type = "Token" if auth_method == AUTH_METHOD_TOKEN else "Password"
    return {"title": f"Gira X1 ({data[CONF_HOST]}) - {auth_type}"}
