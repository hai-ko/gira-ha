#!/usr/bin/env python3
"""Debug script to test Gira X1 entity discovery and logging."""

import asyncio
import logging
import sys
from datetime import timedelta

# Set up logging to see debug output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the custom component path to sys.path
sys.path.insert(0, '/Users/heikoburkhardt/repos/gira-x1-ha/custom_components')

from gira_x1.api import GiraX1Client
from gira_x1.const import GIRA_FUNCTION_TYPES, GIRA_CHANNEL_TYPES, DEVICE_TYPE_SWITCH, DEVICE_TYPE_LIGHT

async def test_entity_discovery():
    """Test the entity discovery process."""
    print("=== Gira X1 Entity Discovery Debug ===\n")
    
    # Configuration - update these with your actual Gira X1 details
    host = "192.168.1.100"  # Replace with your Gira X1 IP
    port = 443
    username = "your_username"  # Replace with your username
    password = "your_password"  # Replace with your password
    
    print(f"Connecting to Gira X1 at {host}:{port}")
    
    # Create a mock HomeAssistant object
    class MockHass:
        pass
    
    hass = MockHass()
    
    # Create client
    client = GiraX1Client(hass, host, port, username=username, password=password)
    
    try:
        # Test connection
        print("Testing connection...")
        if not await client.test_connection():
            print("❌ Connection test failed!")
            return
        print("✅ Connection successful!")
        
        # Get UI config
        print("\nFetching UI configuration...")
        ui_config = await client.get_ui_config(expand=["dataPointFlags", "parameters"])
        
        print(f"UI config keys: {list(ui_config.keys())}")
        functions = ui_config.get("functions", [])
        print(f"Found {len(functions)} functions in UI config")
        
        if not functions:
            print("❌ No functions found in UI config!")
            return
        
        # Process functions like the coordinator does
        function_dict = {func["uid"]: func for func in functions}
        
        print(f"\n=== FUNCTION ANALYSIS ===")
        print(f"Total functions: {len(function_dict)}")
        
        # Analyze function types
        function_types = {}
        channel_types = {}
        for func in function_dict.values():
            func_type = func.get("functionType", "unknown")
            chan_type = func.get("channelType", "unknown")
            function_types[func_type] = function_types.get(func_type, 0) + 1
            channel_types[chan_type] = channel_types.get(chan_type, 0) + 1
        
        print(f"\nFunction types distribution:")
        for func_type, count in sorted(function_types.items()):
            print(f"  {func_type}: {count}")
        
        print(f"\nChannel types distribution:")
        for chan_type, count in sorted(channel_types.items()):
            print(f"  {chan_type}: {count}")
        
        # Check mappings
        print(f"\n=== MAPPING ANALYSIS ===")
        print(f"Current GIRA_FUNCTION_TYPES mappings:")
        for func_type, device_type in GIRA_FUNCTION_TYPES.items():
            print(f"  {func_type} -> {device_type}")
        
        print(f"\nCurrent GIRA_CHANNEL_TYPES mappings:")
        for chan_type, device_type in GIRA_CHANNEL_TYPES.items():
            print(f"  {chan_type} -> {device_type}")
        
        # Find unmapped types
        unmapped_function_types = set(function_types.keys()) - set(GIRA_FUNCTION_TYPES.keys()) - {"unknown"}
        unmapped_channel_types = set(channel_types.keys()) - set(GIRA_CHANNEL_TYPES.keys()) - {"unknown"}
        
        if unmapped_function_types:
            print(f"\n⚠️  UNMAPPED function types found:")
            for func_type in sorted(unmapped_function_types):
                print(f"  {func_type} (count: {function_types[func_type]})")
        
        if unmapped_channel_types:
            print(f"\n⚠️  UNMAPPED channel types found:")
            for chan_type in sorted(unmapped_channel_types):
                print(f"  {chan_type} (count: {channel_types[chan_type]})")
        
        # Simulate entity discovery for switches
        print(f"\n=== SWITCH ENTITY DISCOVERY ===")
        switch_count = 0
        for function_uid, function in function_dict.items():
            function_type = function.get("functionType", "")
            channel_type = function.get("channelType", "")
            display_name = function.get("displayName", "Unknown")
            
            is_switch_function = GIRA_FUNCTION_TYPES.get(function_type) == DEVICE_TYPE_SWITCH
            is_switch_channel = GIRA_CHANNEL_TYPES.get(channel_type) == DEVICE_TYPE_SWITCH
            
            if is_switch_function or is_switch_channel:
                print(f"  ✅ Switch: {display_name} ({function_uid}) - {function_type}/{channel_type}")
                switch_count += 1
        
        print(f"Total switch entities that would be created: {switch_count}")
        
        # Simulate entity discovery for lights
        print(f"\n=== LIGHT ENTITY DISCOVERY ===")
        light_count = 0
        for function_uid, function in function_dict.items():
            function_type = function.get("functionType", "")
            channel_type = function.get("channelType", "")
            display_name = function.get("displayName", "Unknown")
            
            is_light_function = GIRA_FUNCTION_TYPES.get(function_type) == DEVICE_TYPE_LIGHT
            is_light_channel = GIRA_CHANNEL_TYPES.get(channel_type) == DEVICE_TYPE_LIGHT
            is_dimmer_switch = (function_type == "de.gira.schema.functions.Switch" and 
                               channel_type == "de.gira.schema.channels.KNX.Dimmer")
            
            if is_light_function or is_light_channel or is_dimmer_switch:
                print(f"  💡 Light: {display_name} ({function_uid}) - {function_type}/{channel_type}")
                light_count += 1
        
        print(f"Total light entities that would be created: {light_count}")
        
        # Show sample function structures
        print(f"\n=== SAMPLE FUNCTION STRUCTURES ===")
        for i, (uid, func) in enumerate(list(function_dict.items())[:3]):
            print(f"Sample function {i+1}:")
            print(f"  UID: {uid}")
            print(f"  Display Name: {func.get('displayName', 'Unknown')}")
            print(f"  Function Type: {func.get('functionType', 'Unknown')}")
            print(f"  Channel Type: {func.get('channelType', 'Unknown')}")
            print(f"  Data Points: {len(func.get('dataPoints', []))}")
            if func.get('dataPoints'):
                for dp in func.get('dataPoints', [])[:2]:  # Show first 2 data points
                    print(f"    - {dp.get('name', 'Unknown')} ({dp.get('uid', 'Unknown')})")
            print()
        
        print(f"=== SUMMARY ===")
        print(f"Total functions found: {len(function_dict)}")
        print(f"Switch entities: {switch_count}")
        print(f"Light entities: {light_count}")
        print(f"Total entities: {switch_count + light_count}")
        
        if switch_count == 0 and light_count == 0:
            print("❌ No entities would be created!")
            print("   This suggests either:")
            print("   1. No matching function/channel types in GIRA_FUNCTION_TYPES/GIRA_CHANNEL_TYPES")
            print("   2. The function types from your device don't match the mappings")
            print("   3. The UI config structure is different than expected")
        else:
            print("✅ Entities would be created successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            await client.logout()
        except:
            pass

if __name__ == "__main__":
    print("Before running this script, please update the connection details:")
    print("- host: Your Gira X1 IP address")
    print("- port: Usually 443 for HTTPS")
    print("- username: Your Gira X1 username")
    print("- password: Your Gira X1 password")
    print()
    
    response = input("Have you updated the connection details? (y/n): ")
    if response.lower() != 'y':
        print("Please update the connection details in the script and run again.")
        sys.exit(1)
    
    asyncio.run(test_entity_discovery())
