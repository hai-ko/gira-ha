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
                            
                            # Check content type before trying to parse JSON
                            content_type = retry_response.headers.get('content-type', '').lower()
                            
                            # Handle empty content-type headers gracefully
                            if not content_type:
                                response_text = await retry_response.text()
                                # If response is empty or whitespace, treat as successful no-content
                                if not response_text.strip():
                                    return {}
                                # Try to parse as JSON if it looks like JSON
                                if response_text.strip().startswith(('{', '[')):
                                    try:
                                        return await retry_response.json()
                                    except:
                                        pass
                                # Log but don't error for missing content-type with successful status
                                _LOGGER.debug("Empty content-type for endpoint %s after retry, treating as success. Response: %s", 
                                            endpoint, response_text[:100])
                                return {"success": True, "raw_response": response_text}
                            
                            if 'application/json' not in content_type:
                                response_text = await retry_response.text()
                                _LOGGER.warning("Unexpected content type '%s' for endpoint %s after retry. Response: %s", 
                                              content_type, endpoint, response_text[:200])
                                # For some Gira X1 APIs that return non-JSON success responses
                                if retry_response.status in [STATUS_OK, 201]:
                                    return {"success": True, "raw_response": response_text}
                                raise GiraX1ApiError(f"Unexpected content type: {content_type}")
                            
                            return await retry_response.json()
                    
                    elif response.status not in [STATUS_OK, 201, 204]:
                        response_text = await response.text()
                        raise GiraX1ApiError(f"API request failed: {response.status} - {response_text}")
                    
                    if response.status == 204:  # No Content
                        return {}
                    
                    # Check content type before trying to parse JSON
                    content_type = response.headers.get('content-type', '').lower()
                    
                    # Handle empty content-type headers gracefully
                    if not content_type:
                        response_text = await response.text()
                        # If response is empty or whitespace, treat as successful no-content
                        if not response_text.strip():
                            return {}
                        # Try to parse as JSON if it looks like JSON
                        if response_text.strip().startswith(('{', '[')):
                            try:
                                return await response.json()
                            except:
                                pass
                        # Log but don't error for missing content-type with successful status
                        _LOGGER.debug("Empty content-type for endpoint %s, treating as success. Response: %s", 
                                    endpoint, response_text[:100])
                        return {"success": True, "raw_response": response_text}
                    
                    if 'application/json' not in content_type:
                        response_text = await response.text()
                        _LOGGER.warning("Unexpected content type '%s' for endpoint %s. Response: %s", 
                                      content_type, endpoint, response_text[:200])
                        # For some Gira X1 APIs that return non-JSON success responses
                        if response.status in [STATUS_OK, 201]:
                            return {"success": True, "raw_response": response_text}
                        raise GiraX1ApiError(f"Unexpected content type: {content_type}")
                    
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
        
        Note: No batch endpoint available - uses individual /api/values/{uid} requests.
        
        Args:
            uid: Optional UID to get specific datapoint value.
                 If None, gets values for all known datapoints from UI config using individual requests.
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
            # Get values for all datapoints using individual requests (no batch endpoint available)
            _LOGGER.debug("Getting values for all datapoints using individual polling...")
            
            # First get UI config to find all datapoint IDs
            ui_config = await self.get_ui_config()
            all_datapoint_ids = set()
            
            # Extract all datapoint UIDs from functions
            for function in ui_config.get("functions", []):
                for datapoint in function.get("dataPoints", []):
                    dp_uid = datapoint.get("uid")
                    if dp_uid:
                        all_datapoint_ids.add(dp_uid)
            
            _LOGGER.debug(f"Found {len(all_datapoint_ids)} datapoints to fetch individually (no batch endpoint)")
            
            # Fetch values for each datapoint individually using /api/values/{uid}
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
                    # Some datapoints may not be readable or available
                    error_msg = str(e).lower()
                    if any(x in error_msg for x in ["read flag not set", "get value failed", "500"]):
                        _LOGGER.debug(f"Datapoint {dp_uid} not available or readable: {e}")
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
        value_callback_url: str, 
        service_callback_url: str,
        test_callbacks: bool = True
    ) -> bool:
        """Register callback URLs with the Gira X1 device.
        
        Args:
            value_callback_url: URL for value change callbacks
            service_callback_url: URL for service event callbacks  
            test_callbacks: Whether to test the callbacks during registration
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            if not self._token:
                _LOGGER.error("📞 Callback Registration: No authentication token available")
                return False

            _LOGGER.info("📞 CALLBACK REGISTRATION: Starting callback registration with Gira X1")
            _LOGGER.info("📞   Value callback URL: %s", value_callback_url)
            _LOGGER.info("📞   Service callback URL: %s", service_callback_url)
            _LOGGER.info("📞   Test callbacks: %s", test_callbacks)

            url = f"{self._base_url}{API_CLIENTS}/{self._token}{API_CALLBACKS_PATH}"
            _LOGGER.debug("📞   Registration endpoint: %s", url)

            payload = {
                "valueCallback": value_callback_url,
                "serviceCallback": service_callback_url,
                "testCallbacks": test_callbacks
            }
            
            _LOGGER.debug("📞   Registration payload: %s", payload)

            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self._session.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    ssl=False,  # Gira X1 uses self-signed certificates
                ) as response:
                    _LOGGER.debug("📞   Registration response status: %d", response.status)
                    response_text = await response.text()
                    _LOGGER.debug("📞   Registration response body: %s", response_text)

                    if response.status == STATUS_OK:
                        _LOGGER.info("✅ CALLBACK REGISTRATION SUCCESS: Callbacks registered successfully with Gira X1")
                        return True
                    elif response.status == 400:
                        if "callbackTestFailed" in response_text:
                            _LOGGER.warning("❌ CALLBACK REGISTRATION FAILED: Callback test failed - Gira X1 cannot reach callback URLs")
                            _LOGGER.warning("📞   This indicates network connectivity issues between Gira X1 and Home Assistant")
                            _LOGGER.warning("📞   Check firewall settings and network routing")
                        else:
                            _LOGGER.error("❌ CALLBACK REGISTRATION FAILED: Bad request - %s", response_text)
                        return False
                    elif response.status == 422:
                        _LOGGER.error("❌ CALLBACK REGISTRATION FAILED: Callbacks must use HTTPS")
                        return False
                    else:
                        _LOGGER.error("❌ CALLBACK REGISTRATION FAILED: HTTP %d - %s", response.status, response_text)
                        return False

        except asyncio.TimeoutError:
            _LOGGER.error("❌ CALLBACK REGISTRATION FAILED: Timeout waiting for response from Gira X1")
            return False
        except Exception as err:
            _LOGGER.error("❌ CALLBACK REGISTRATION FAILED: Unexpected error - %s", err, exc_info=True)
            return False

    async def unregister_callbacks(self) -> bool:
        """Unregister callback URLs from the Gira X1 device.
        
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if not self._token:
                _LOGGER.debug("📞 Callback Unregistration: No token available, skipping")
                return True

            _LOGGER.info("📞 CALLBACK UNREGISTRATION: Removing callbacks from Gira X1")

            url = f"{self._base_url}{API_CLIENTS}/{self._token}{API_CALLBACKS_PATH}"
            _LOGGER.debug("📞   Unregistration endpoint: %s", url)

            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self._session.delete(
                    url,
                    ssl=False,  # Gira X1 uses self-signed certificates
                ) as response:
                    _LOGGER.debug("📞   Unregistration response status: %d", response.status)
                    response_text = await response.text()
                    _LOGGER.debug("📞   Unregistration response body: %s", response_text)

                    if response.status == STATUS_OK:
                        _LOGGER.info("✅ CALLBACK UNREGISTRATION SUCCESS: Callbacks unregistered from Gira X1")
                        return True
                    else:
                        _LOGGER.warning("⚠️ CALLBACK UNREGISTRATION WARNING: HTTP %d - %s", response.status, response_text)
                        # Don't treat this as a critical error since we're likely shutting down
                        return True

        except asyncio.TimeoutError:
            _LOGGER.warning("⚠️ CALLBACK UNREGISTRATION WARNING: Timeout - continuing shutdown")
            return True
        except Exception as err:
            _LOGGER.warning("⚠️ CALLBACK UNREGISTRATION WARNING: Error - %s", err)
            return True
