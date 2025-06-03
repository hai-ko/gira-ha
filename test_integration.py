#!/usr/bin/env python3
"""Test script for Gira X1 Home Assistant integration."""

import asyncio
import json
import logging
import sys
from unittest.mock import AsyncMock, MagicMock

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Mock Home Assistant modules for testing
sys.modules['homeassistant'] = MagicMock()
sys.modules['homeassistant.core'] = MagicMock()
sys.modules['homeassistant.config_entries'] = MagicMock()
sys.modules['homeassistant.const'] = MagicMock()
sys.modules['homeassistant.helpers'] = MagicMock()
sys.modules['homeassistant.helpers.aiohttp_client'] = MagicMock()
sys.modules['homeassistant.helpers.update_coordinator'] = MagicMock()
sys.modules['homeassistant.helpers.entity_platform'] = MagicMock()
sys.modules['homeassistant.components.light'] = MagicMock()
sys.modules['homeassistant.components.switch'] = MagicMock()
sys.modules['homeassistant.components.cover'] = MagicMock()
sys.modules['homeassistant.components.sensor'] = MagicMock()
sys.modules['homeassistant.components.binary_sensor'] = MagicMock()
sys.modules['homeassistant.exceptions'] = MagicMock()
sys.modules['voluptuous'] = MagicMock()

# Import our modules after mocking
from custom_components.gira_x1.api import GiraX1Client
from custom_components.gira_x1.const import (
    GIRA_FUNCTION_TYPES, 
    GIRA_CHANNEL_TYPES,
    DEVICE_TYPE_LIGHT,
    DEVICE_TYPE_SWITCH,
    DEVICE_TYPE_COVER,
    DEVICE_TYPE_SENSOR,
    DEVICE_TYPE_BINARY_SENSOR
)

# Sample uiconfig response based on Gira documentation
SAMPLE_UICONFIG = {
    "uid": "a036",
    "functions": [
        {
            "uid": "a029",
            "functionType": "de.gira.schema.functions.KNX.Light",
            "channelType": "de.gira.schema.channels.KNX.Dimmer",
            "displayName": "Lampe Links",
            "dataPoints": [
                {"name": "OnOff", "uid": "a02a"},
                {"name": "Brightness", "uid": "a02b"}
            ]
        },
        {
            "uid": "a02c",
            "functionType": "de.gira.schema.functions.KNX.Light",
            "channelType": "de.gira.schema.channels.KNX.Dimmer",
            "displayName": "Lampe Rechts",
            "dataPoints": [
                {"name": "OnOff", "uid": "a02d"},
                {"name": "Brightness", "uid": "a02e"}
            ]
        },
        {
            "uid": "a02f",
            "functionType": "de.gira.schema.functions.Sonos.Audio",
            "channelType": "de.gira.schema.channels.Sonos.Audio",
            "displayName": "Sonos-Audio",
            "dataPoints": [
                {"name": "Play", "uid": "a02g"},
                {"name": "Volume", "uid": "a02h"},
                {"name": "Mute", "uid": "a02i"}
            ]
        },
        {
            "uid": "a030",
            "functionType": "de.gira.schema.functions.Switch",
            "channelType": "de.gira.schema.channels.Switch",
            "displayName": "Test Switch",
            "dataPoints": [
                {"name": "OnOff", "uid": "a031"}
            ]
        },
        {
            "uid": "a032",
            "functionType": "de.gira.schema.functions.Covering",
            "channelType": "de.gira.schema.channels.BlindWithPos",
            "displayName": "Rolladen Büro",
            "dataPoints": [
                {"name": "Position", "uid": "a033"},
                {"name": "UpDown", "uid": "a034"},
                {"name": "Stop", "uid": "a035"}
            ]
        }
    ]
}

SAMPLE_VALUES = {
    "a02a": True,    # Left lamp OnOff
    "a02b": 75,      # Left lamp Brightness
    "a02d": False,   # Right lamp OnOff
    "a02e": 0,       # Right lamp Brightness
    "a02h": 50,      # Sonos Volume
    "a031": True,    # Switch OnOff
    "a033": 25,      # Blind Position
}

async def test_api_client():
    """Test the API client functionality."""
    print("Testing API client...")
    
    # Create mock session
    mock_session = AsyncMock()
    mock_hass = MagicMock()
    mock_hass.helpers.aiohttp_client.async_get_clientsession.return_value = mock_session
    
    client = GiraX1Client(mock_hass, "192.168.1.100", 443, "user", "password")
    
    # Mock successful registration
    mock_response = AsyncMock()
    mock_response.status = 201
    mock_response.json.return_value = {"token": "test_token"}
    mock_session.post.return_value.__aenter__.return_value = mock_response
    
    # Test client registration
    result = await client.register_client()
    assert result is True, "Client registration should succeed"
    assert client.is_authenticated, "Client should be authenticated"
    print("✓ Client registration works")
    
    # Mock uiconfig response
    mock_response.status = 200
    mock_response.json.return_value = SAMPLE_UICONFIG
    mock_session.request.return_value.__aenter__.return_value = mock_response
    
    # Test get_ui_config
    config = await client.get_ui_config()
    assert config == SAMPLE_UICONFIG, "Should return sample config"
    print("✓ UI config retrieval works")
    
    # Test get_functions
    functions = await client.get_functions()
    assert len(functions) == 5, f"Should return 5 functions, got {len(functions)}"
    print("✓ Functions retrieval works")
    
    # Mock values response
    mock_response.json.return_value = {"values": [
        {"uid": uid, "value": value} for uid, value in SAMPLE_VALUES.items()
    ]}
    
    # Test get_values
    values = await client.get_values()
    assert len(values) == len(SAMPLE_VALUES), f"Should return {len(SAMPLE_VALUES)} values"
    assert values["a02b"] == 75, "Should return correct brightness value"
    print("✓ Values retrieval works")
    
    print("API client tests passed!\n")

def test_function_type_mapping():
    """Test that function types are correctly mapped to device types."""
    print("Testing function type mapping...")
    
    # Test known function types
    assert GIRA_FUNCTION_TYPES["de.gira.schema.functions.KNX.Light"] == DEVICE_TYPE_LIGHT
    assert GIRA_FUNCTION_TYPES["de.gira.schema.functions.Switch"] == DEVICE_TYPE_SWITCH
    assert GIRA_FUNCTION_TYPES["de.gira.schema.functions.Covering"] == DEVICE_TYPE_COVER
    assert GIRA_FUNCTION_TYPES["de.gira.schema.functions.Sonos.Audio"] == DEVICE_TYPE_SENSOR
    
    # Test channel types
    assert GIRA_CHANNEL_TYPES["de.gira.schema.channels.KNX.Dimmer"] == DEVICE_TYPE_LIGHT
    assert GIRA_CHANNEL_TYPES["de.gira.schema.channels.Switch"] == DEVICE_TYPE_SWITCH
    assert GIRA_CHANNEL_TYPES["de.gira.schema.channels.BlindWithPos"] == DEVICE_TYPE_COVER
    
    print("✓ Function type mappings are correct")
    print("Function type mapping tests passed!\n")

def test_entity_discovery():
    """Test entity discovery from uiconfig."""
    print("Testing entity discovery...")
    
    light_entities = []
    switch_entities = []
    cover_entities = []
    sensor_entities = []
    
    # Simulate entity discovery logic
    for function in SAMPLE_UICONFIG["functions"]:
        function_type = function.get("functionType", "")
        channel_type = function.get("channelType", "")
        
        mapped_type = GIRA_FUNCTION_TYPES.get(function_type) or GIRA_CHANNEL_TYPES.get(channel_type)
        
        if mapped_type == DEVICE_TYPE_LIGHT:
            light_entities.append(function)
        elif mapped_type == DEVICE_TYPE_SWITCH:
            switch_entities.append(function)
        elif mapped_type == DEVICE_TYPE_COVER:
            cover_entities.append(function)
        elif mapped_type == DEVICE_TYPE_SENSOR:
            sensor_entities.append(function)
    
    assert len(light_entities) == 2, f"Should discover 2 lights, found {len(light_entities)}"
    assert len(switch_entities) == 1, f"Should discover 1 switch, found {len(switch_entities)}"
    assert len(cover_entities) == 1, f"Should discover 1 cover, found {len(cover_entities)}"
    assert len(sensor_entities) == 1, f"Should discover 1 sensor, found {len(sensor_entities)}"
    
    print(f"✓ Discovered {len(light_entities)} lights")
    print(f"✓ Discovered {len(switch_entities)} switches") 
    print(f"✓ Discovered {len(cover_entities)} covers")
    print(f"✓ Discovered {len(sensor_entities)} sensors")
    print("Entity discovery tests passed!\n")

def test_data_point_mapping():
    """Test data point mapping for entities."""
    print("Testing data point mapping...")
    
    # Test light data points
    light_function = SAMPLE_UICONFIG["functions"][0]  # "Lampe Links"
    data_points = {dp["name"]: dp["uid"] for dp in light_function.get("dataPoints", [])}
    
    assert "OnOff" in data_points, "Light should have OnOff data point"
    assert "Brightness" in data_points, "Light should have Brightness data point"
    assert data_points["OnOff"] == "a02a", "OnOff UID should match"
    assert data_points["Brightness"] == "a02b", "Brightness UID should match"
    
    # Test cover data points
    cover_function = SAMPLE_UICONFIG["functions"][4]  # "Rolladen Büro"
    cover_data_points = {dp["name"]: dp["uid"] for dp in cover_function.get("dataPoints", [])}
    
    assert "Position" in cover_data_points, "Cover should have Position data point"
    assert "UpDown" in cover_data_points, "Cover should have UpDown data point"
    assert "Stop" in cover_data_points, "Cover should have Stop data point"
    
    print("✓ Light data points mapped correctly")
    print("✓ Cover data points mapped correctly")
    print("Data point mapping tests passed!\n")

async def main():
    """Run all tests."""
    print("=== Gira X1 Integration Test Suite ===\n")
    
    try:
        # Test API functionality
        await test_api_client()
        
        # Test configuration mapping
        test_function_type_mapping()
        
        # Test entity discovery
        test_entity_discovery()
        
        # Test data point mapping
        test_data_point_mapping()
        
        print("=== All Tests Passed! ===")
        print("\nThe Gira X1 integration is ready for testing with a real device.")
        print("\nNext steps:")
        print("1. Configure the integration in Home Assistant")
        print("2. Enter your Gira X1 device credentials") 
        print("3. Verify that entities are discovered correctly")
        print("4. Test entity controls and state updates")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
