"""Test the Gira X1 integration."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.gira_x1 import async_setup_entry, async_unload_entry
from custom_components.gira_x1.api import GiraX1Client
from custom_components.gira_x1.const import DOMAIN


@pytest.fixture
def mock_config_entry():
    """Create a mock config entry."""
    return MagicMock(spec=ConfigEntry)


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.data = {DOMAIN: {}}
    return hass


@pytest.mark.asyncio
async def test_setup_entry(mock_hass, mock_config_entry):
    """Test setting up the integration."""
    mock_config_entry.data = {
        "host": "192.168.1.100",
        "port": 80,
        "username": "test",
        "password": "test",
    }
    mock_config_entry.entry_id = "test_entry"

    with patch("custom_components.gira_x1.GiraX1Client") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.test_connection.return_value = True
        mock_client_class.return_value = mock_client

        with patch("custom_components.gira_x1.GiraX1DataUpdateCoordinator") as mock_coordinator_class:
            mock_coordinator = AsyncMock()
            mock_coordinator.async_config_entry_first_refresh = AsyncMock()
            mock_coordinator_class.return_value = mock_coordinator

            with patch.object(mock_hass.config_entries, "async_forward_entry_setups", return_value=True):
                result = await async_setup_entry(mock_hass, mock_config_entry)
                assert result is True


@pytest.mark.asyncio
async def test_unload_entry(mock_hass, mock_config_entry):
    """Test unloading the integration."""
    mock_config_entry.entry_id = "test_entry"
    
    mock_client = AsyncMock()
    mock_coordinator = AsyncMock()
    
    mock_hass.data[DOMAIN][mock_config_entry.entry_id] = {
        "client": mock_client,
        "coordinator": mock_coordinator,
    }

    with patch.object(mock_hass.config_entries, "async_unload_platforms", return_value=True):
        with patch.object(mock_hass.services, "async_remove"):
            result = await async_unload_entry(mock_hass, mock_config_entry)
            assert result is True
            mock_client.logout.assert_called_once()


class TestGiraX1Client:
    """Test the Gira X1 API client."""

    @pytest.mark.asyncio
    async def test_authentication_success(self):
        """Test successful authentication."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {"token": "test_token"}
            mock_post.return_value.__aenter__.return_value = mock_response

            client = GiraX1Client(
                hass=MagicMock(),
                host="192.168.1.100",
                port=80,
                username="test",
                password="test",
            )

            result = await client.authenticate()
            assert result is True
            assert client.is_authenticated is True

    @pytest.mark.asyncio
    async def test_authentication_failure(self):
        """Test authentication failure."""
        with patch("aiohttp.ClientSession.post") as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_post.return_value.__aenter__.return_value = mock_response

            client = GiraX1Client(
                hass=MagicMock(),
                host="192.168.1.100",
                port=80,
                username="test",
                password="wrong",
            )

            with pytest.raises(Exception):
                await client.authenticate()
