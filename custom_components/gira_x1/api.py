"""API client for Gira X1."""
from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any, Dict, List, Optional
import async_timeout

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_CLIENTS,
    API_UICONFIG,
    API_UICONFIG_UID,
    API_VALUES,
    API_CALLBACKS_PATH,
    REQUEST_TIMEOUT,
    STATUS_OK,
    STATUS_UNAUTHORIZED,
)

_LOGGER = logging.getLogger(__name__)

# Add retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0


class GiraX1ApiError(Exception):
    """Exception for Gira X1 API errors."""


class GiraX1AuthError(GiraX1ApiError):
    """Exception for authentication errors."""


class GiraX1ConnectionError(GiraX1ApiError):
    """Exception for connection errors."""


class GiraX1Client:
    """Client for Gira X1 REST API v2."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        username: str = None,
        password: str = None,
        token: str = None,
    ) -> None:
        """Initialize the client."""
        self._hass = hass
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._provided_token = token  # Token provided by user
        self._session = async_get_clientsession(hass, verify_ssl=False)  # Gira uses self-signed certs
        self._token: Optional[str] = token  # Current active token
        self._base_url = f"https://{host}:{port}"  # Gira X1 uses HTTPS
        self._client_id = "de.homeassistant.gira_x1"
        self._authenticated = bool(token)  # If token provided, assume authenticated
        self._auth_lock = asyncio.Lock()

    @property
    def host(self) -> str:
        """Return the host."""
        return self._host

    @property
    def port(self) -> int:
        """Return the port."""
        return self._port

    @property
    def is_authenticated(self) -> bool:
        """Return if client is authenticated."""
        return self._authenticated and self._token is not None

    @property
    def uses_token_auth(self) -> bool:
        """Return if client uses token authentication."""
        return self._provided_token is not None

    async def register_client(self) -> bool:
        """Register client with the Gira X1 device and get access token."""
        async with self._auth_lock:
            if self._authenticated:
                return True
            
            # If using token authentication, just test the token
            if self._provided_token:
                return await self._test_token()
                
            # If using username/password authentication, register client
            return await self._register_with_credentials()

    async def _test_token(self) -> bool:
        """Test if the provided token is valid."""
        try:
            # Test the token by making a simple API call
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self._session.get(
                    f"{self._base_url}{API_UICONFIG}",
                    headers={"Authorization": f"Bearer {self._token}"},
                ) as response:
                    if response.status == STATUS_OK:
                        self._authenticated = True
                        _LOGGER.debug("Successfully authenticated with provided token")
                        return True
                    elif response.status == STATUS_UNAUTHORIZED:
                        raise GiraX1AuthError("Invalid token")
                    else:
                        response_text = await response.text()
                        raise GiraX1ApiError(f"Token validation failed: {response.status} - {response_text}")

        except asyncio.TimeoutError as err:
            raise GiraX1ConnectionError("Token validation timeout") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to Gira X1: %s", err)
            raise GiraX1ConnectionError(f"Connection error: {err}") from err

    async def _register_with_credentials(self) -> bool:
        """Register client using username/password credentials."""
        if not self._username or not self._password:
            raise GiraX1AuthError("Username and password required for credential authentication")
            
        try:
            # Create basic auth header
            credentials = base64.b64encode(f"{self._username}:{self._password}".encode()).decode()
            headers = {"Authorization": f"Basic {credentials}"}
            
            client_data = {"client": self._client_id}

            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self._session.post(
                    f"{self._base_url}{API_CLIENTS}",
                    json=client_data,
                    headers=headers,
                ) as response:
                    if response.status == 201:  # Created
                        data = await response.json()
                        self._token = data.get("token")
                        self._authenticated = True
                        _LOGGER.debug("Successfully registered client with Gira X1")
                        return True
                    elif response.status == STATUS_UNAUTHORIZED:
                        raise GiraX1AuthError("Invalid credentials")
                    else:
                        response_text = await response.text()
                        raise GiraX1ApiError(f"Client registration failed: {response.status} - {response_text}")

        except asyncio.TimeoutError as err:
            raise GiraX1ConnectionError("Registration timeout") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("Error connecting to Gira X1: %s", err)
            raise GiraX1ConnectionError(f"Connection error: {err}") from err

    async def unregister_client(self) -> None:
        """Unregister client from the Gira X1 device."""
        if not self._authenticated or not self._token:
            return

        # Don't unregister if using a provided token (not generated by us)
        if self._provided_token:
            _LOGGER.debug("Skipping unregistration for provided token")
            self._authenticated = False
            return

        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self._session.delete(
                    f"{self._base_url}{API_CLIENTS}/{self._token}",
                ) as response:
                    if response.status == 204:  # No Content
                        _LOGGER.debug("Successfully unregistered client from Gira X1")
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Error during client unregistration: %s", err)
        finally:
            self._token = None
            self._authenticated = False

    # Alias for compatibility
    async def authenticate(self) -> bool:
        """Authenticate with the Gira X1 device (alias for register_client)."""
        return await self.register_client()

    async def logout(self) -> None:
        """Logout from the Gira X1 device (alias for unregister_client)."""
        await self.unregister_client()

    async def _make_request_with_retry(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        retries: int = MAX_RETRIES,
    ) -> Dict[str, Any]:
        """Make a request with retry logic."""
        last_exception = None
        
        for attempt in range(retries + 1):
            try:
                return await self._make_request(method, endpoint, data)
            except (GiraX1ConnectionError, asyncio.TimeoutError) as err:
                last_exception = err
                if attempt < retries:
                    _LOGGER.warning(
                        "Request failed (attempt %d/%d): %s. Retrying in %ds...",
                        attempt + 1,
                        retries + 1,
                        err,
                        RETRY_DELAY,
                    )
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                break
            except GiraX1AuthError:
                # Don't retry auth errors
                raise
                
        if last_exception:
            raise last_exception

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated request to the API."""
        if not self._authenticated:
            await self.register_client()

        # Use token as query parameter as per Gira API spec
        url = f"{self._base_url}{endpoint}"
        if "?" in url:
            url += f"&token={self._token}"
        else:
            url += f"?token={self._token}"

        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self._session.request(
                    method,
                    url,
                    json=data,
                ) as response:
                    if response.status == STATUS_UNAUTHORIZED:
                        # Token might be expired, try to re-register
                        self._authenticated = False
                        await self.register_client()
                        
                        # Retry with new token
                        url = f"{self._base_url}{endpoint}"
                        if "?" in url:
                            url += f"&token={self._token}"
                        else:
                            url += f"?token={self._token}"
                        
                        async with self._session.request(
                            method,
                            url,
                            json=data,
                        ) as retry_response:
                            if retry_response.status not in [STATUS_OK, 201, 204]:
                                response_text = await retry_response.text()
                                raise GiraX1ApiError(f"API request failed: {retry_response.status} - {response_text}")
                            
                            if retry_response.status == 204:  # No Content
                                return {}
                            return await retry_response.json()
                    
                    elif response.status not in [STATUS_OK, 201, 204]:
                        response_text = await response.text()
                        raise GiraX1ApiError(f"API request failed: {response.status} - {response_text}")
                    
                    if response.status == 204:  # No Content
                        return {}
                    return await response.json()

        except asyncio.TimeoutError as err:
            raise GiraX1ConnectionError("Request timeout") from err
        except aiohttp.ClientError as err:
            raise GiraX1ConnectionError(f"Request error: {err}") from err

    async def get_ui_config(self, expand: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get UI configuration from the Gira X1.
        
        Args:
            expand: Optional list of fields to expand (dataPointFlags, parameters, locations, trades)
        """
        endpoint = API_UICONFIG
        if expand:
            expand_params = ",".join(expand)
            endpoint += f"?expand={expand_params}"
        
        response = await self._make_request_with_retry("GET", endpoint)
        return response

    async def get_ui_config_uid(self) -> str:
        """Get the unique identifier of the current UI configuration."""
        response = await self._make_request_with_retry("GET", API_UICONFIG_UID)
        return response.get("uid", "")

    async def get_functions(self) -> List[Dict[str, Any]]:
        """Get all functions from the UI configuration."""
        config = await self.get_ui_config()
        return config.get("functions", [])

    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get all devices from the Gira X1 (alias for get_functions for compatibility)."""
        return await self.get_functions()

    async def get_values(self, uid: Optional[str] = None) -> Dict[str, Any]:
        """Get current values from the Gira X1.
        
        Args:
            uid: Optional UID to get specific datapoint value.
                 If None, gets values for all known datapoints from UI config.
        """
        if uid:
            # Get value for specific datapoint
            endpoint = f"{API_VALUES}/{uid}"
            response = await self._make_request_with_retry("GET", endpoint)
            
            # The API returns values in a "values" array, convert to dict for easier access
            values_list = response.get("values", [])
            values_dict = {}
            for value_item in values_list:
                if "uid" in value_item and "value" in value_item:
                    values_dict[value_item["uid"]] = value_item["value"]
            
            return values_dict
        else:
            # Get values for all datapoints from UI config
            _LOGGER.debug("Getting values for all datapoints from UI config...")
            
            # First get UI config to find all datapoint IDs
            ui_config = await self.get_ui_config()
            all_datapoint_ids = set()
            
            # Extract all datapoint UIDs from functions
            for function in ui_config.get("functions", []):
                for datapoint in function.get("dataPoints", []):
                    dp_uid = datapoint.get("uid")
                    if dp_uid:
                        all_datapoint_ids.add(dp_uid)
            
            _LOGGER.debug(f"Found {len(all_datapoint_ids)} datapoints to fetch values for")
            
            # Fetch values for each datapoint individually
            all_values = {}
            successful_fetches = 0
            failed_fetches = 0
            
            for dp_uid in all_datapoint_ids:
                try:
                    endpoint = f"{API_VALUES}/{dp_uid}"
                    response = await self._make_request_with_retry("GET", endpoint)
                    
                    # Extract value from response
                    values_list = response.get("values", [])
                    for value_item in values_list:
                        if value_item.get("uid") == dp_uid and "value" in value_item:
                            all_values[dp_uid] = value_item["value"]
                            successful_fetches += 1
                            break
                            
                except GiraX1ApiError as e:
                    # Some datapoints may not be readable (read flag not set)
                    if "read flag not set" in str(e):
                        _LOGGER.debug(f"Datapoint {dp_uid} not readable (read flag not set)")
                    else:
                        _LOGGER.warning(f"Failed to get value for datapoint {dp_uid}: {e}")
                    failed_fetches += 1
                except Exception as e:
                    _LOGGER.warning(f"Unexpected error getting value for datapoint {dp_uid}: {e}")
                    failed_fetches += 1
            
            _LOGGER.debug(f"Successfully fetched {successful_fetches} values, {failed_fetches} failed")
            return all_values

    async def get_device_value(self, device_id: str) -> Any:
        """Get the current value for a specific device/datapoint."""
        values = await self.get_values(device_id)
        return values.get(device_id)

    async def set_device_value(self, device_id: str, value: Any) -> bool:
        """Set a value for a specific device/datapoint."""
        endpoint = f"{API_VALUES}/{device_id}"
        data = {"value": value}
        try:
            await self._make_request_with_retry("PUT", endpoint, data)
            return True
        except GiraX1ApiError as err:
            _LOGGER.error("Failed to set device value: %s", err)
            return False

    async def set_multiple_values(self, values: Dict[str, Any]) -> bool:
        """Set multiple values by calling the individual endpoints.
        
        Args:
            values: Dictionary mapping device UIDs to their new values
        """
        success_count = 0
        total_count = len(values)
        
        for uid, value in values.items():
            try:
                if await self.set_device_value(uid, value):
                    success_count += 1
            except Exception as e:
                _LOGGER.warning(f"Failed to set value for {uid}: {e}")
        
        _LOGGER.debug(f"Set {success_count}/{total_count} values successfully")
        return success_count == total_count

    async def set_value(self, datapoint_id: str, value: Any) -> bool:
        """Set a value for a datapoint (alias for set_device_value for service compatibility)."""
        return await self.set_device_value(datapoint_id, value)

    async def test_connection(self) -> bool:
        """Test if the connection to Gira X1 is working."""
        try:
            await self.authenticate()
            return True
        except (GiraX1ApiError, GiraX1AuthError):
            return False

    async def register_callbacks(
        self, 
        value_callback_url: Optional[str] = None,
        service_callback_url: Optional[str] = None,
        test_callbacks: bool = True
    ) -> bool:
        """Register callback URLs with the Gira X1 device.
        
        Args:
            value_callback_url: URL for value change callbacks
            service_callback_url: URL for service event callbacks  
            test_callbacks: Whether to test callbacks during registration
            
        Returns:
            True if registration successful, False otherwise
        """
        if not self._authenticated or not self._token:
            await self.register_client()
            
        callback_data = {}
        if value_callback_url:
            callback_data["valueCallback"] = value_callback_url
        if service_callback_url:
            callback_data["serviceCallback"] = service_callback_url
        if test_callbacks:
            callback_data["testCallbacks"] = test_callbacks
            
        if not callback_data:
            _LOGGER.warning("No callback URLs provided")
            return False
            
        try:
            endpoint = f"{API_CLIENTS}/{self._token}{API_CALLBACKS_PATH}"
            response = await self._make_request_with_retry("POST", endpoint, callback_data)
            _LOGGER.info("Successfully registered callbacks with Gira X1")
            return True
        except GiraX1ApiError as err:
            _LOGGER.error("Failed to register callbacks: %s", err)
            return False

    async def unregister_callbacks(self) -> bool:
        """Unregister callbacks from the Gira X1 device.
        
        Returns:
            True if unregistration successful, False otherwise
        """
        if not self._authenticated or not self._token:
            _LOGGER.warning("Not authenticated, cannot unregister callbacks")
            return False
            
        try:
            endpoint = f"{API_CLIENTS}/{self._token}{API_CALLBACKS_PATH}"
            await self._make_request_with_retry("DELETE", endpoint)
            _LOGGER.info("Successfully unregistered callbacks from Gira X1")
            return True
        except GiraX1ApiError as err:
            _LOGGER.error("Failed to unregister callbacks: %s", err)
            return False
