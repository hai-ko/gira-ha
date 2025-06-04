#!/usr/bin/env python3
"""Test the updated Gira X1 integration with correct API endpoints."""

import asyncio
import logging
import sys
from datetime import timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
_LOGGER = logging.getLogger(__name__)

# Add the custom component path to sys.path
sys.path.insert(0, '/Users/heikoburkhardt/repos/gira-x1-ha/custom_components')

from gira_x1.api import GiraX1Client
from gira_x1.const import GIRA_FUNCTION_TYPES, GIRA_CHANNEL_TYPES, DEVICE_TYPE_SWITCH, DEVICE_TYPE_LIGHT

class MockHass:
    pass

async def test_updated_integration():
    """Test the updated integration with correct API endpoints."""
    print("=== Testing Updated Gira X1 Integration ===\n")
    
    # Configuration from example_configuration.yaml
    host = "10.1.1.85"
    port = 443
    token = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"
    
    print(f"Testing connection to Gira X1 at {host}:{port}")
    
    hass = MockHass()
    client = GiraX1Client(hass, host, port, token=token)
    
    try:
        # Test connection
        print("1. Testing connection...")
        if not await client.test_connection():
            print("❌ Connection test failed!")
            return
        print("✅ Connection successful!")
        
        # Test UI config fetch
        print("\n2. Testing UI config fetch...")
        ui_config = await client.get_ui_config()
        functions = ui_config.get("functions", [])
        print(f"✅ UI config fetched: {len(functions)} functions found")
        
        # Test individual value fetch
        print("\n3. Testing individual value fetch...")
        if functions:
            # Get first few datapoints
            test_datapoints = []
            for func in functions[:3]:
                for dp in func.get("dataPoints", [])[:2]:
                    if dp.get("uid"):
                        test_datapoints.append(dp["uid"])
                        if len(test_datapoints) >= 5:
                            break
                if len(test_datapoints) >= 5:
                    break
            
            print(f"Testing individual fetch for datapoints: {test_datapoints}")
            for dp_id in test_datapoints:
                try:
                    values = await client.get_values(dp_id)
                    print(f"  ✅ {dp_id}: {values}")
                except Exception as e:
                    print(f"  ⚠️  {dp_id}: {e}")
        
        # Test bulk value fetch (new implementation)
        print("\n4. Testing bulk value fetch (new implementation)...")
        try:
            all_values = await client.get_values()  # No UID = get all values
            print(f"✅ Bulk fetch successful: {len(all_values)} values retrieved")
            
            # Show sample values
            sample_values = list(all_values.items())[:5]
            for uid, value in sample_values:
                print(f"  {uid}: {value}")
                
        except Exception as e:
            print(f"❌ Bulk fetch failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test function type analysis
        print("\n5. Analyzing function types for entity creation...")
        function_types = {}
        channel_types = {}
        switch_candidates = []
        light_candidates = []
        
        for func in functions:
            func_type = func.get("functionType", "unknown")
            chan_type = func.get("channelType", "unknown") 
            display_name = func.get("displayName", "Unknown")
            
            function_types[func_type] = function_types.get(func_type, 0) + 1
            channel_types[chan_type] = channel_types.get(chan_type, 0) + 1
            
            # Check if this would be a switch
            is_switch_function = GIRA_FUNCTION_TYPES.get(func_type) == DEVICE_TYPE_SWITCH
            is_switch_channel = GIRA_CHANNEL_TYPES.get(chan_type) == DEVICE_TYPE_SWITCH
            
            if is_switch_function or is_switch_channel:
                switch_candidates.append((display_name, func["uid"], func_type, chan_type))
            
            # Check if this would be a light
            is_light_function = GIRA_FUNCTION_TYPES.get(func_type) == DEVICE_TYPE_LIGHT
            is_light_channel = GIRA_CHANNEL_TYPES.get(chan_type) == DEVICE_TYPE_LIGHT
            is_dimmer_switch = (func_type == "de.gira.schema.functions.Switch" and 
                               chan_type == "de.gira.schema.channels.KNX.Dimmer")
            
            if is_light_function or is_light_channel or is_dimmer_switch:
                light_candidates.append((display_name, func["uid"], func_type, chan_type))
        
        print(f"Function types found: {len(function_types)} unique types")
        for func_type, count in sorted(function_types.items()):
            mapped_to = GIRA_FUNCTION_TYPES.get(func_type, "UNMAPPED")
            print(f"  {func_type}: {count} (→ {mapped_to})")
        
        print(f"\nChannel types found: {len(channel_types)} unique types")
        for chan_type, count in sorted(channel_types.items()):
            mapped_to = GIRA_CHANNEL_TYPES.get(chan_type, "UNMAPPED")
            print(f"  {chan_type}: {count} (→ {mapped_to})")
        
        print(f"\n📊 ENTITY CREATION SUMMARY:")
        print(f"Switch entities that would be created: {len(switch_candidates)}")
        for name, uid, func_type, chan_type in switch_candidates[:5]:
            print(f"  🔘 {name} ({uid}) - {func_type}/{chan_type}")
        if len(switch_candidates) > 5:
            print(f"  ... and {len(switch_candidates) - 5} more")
        
        print(f"\nLight entities that would be created: {len(light_candidates)}")
        for name, uid, func_type, chan_type in light_candidates[:5]:
            print(f"  💡 {name} ({uid}) - {func_type}/{chan_type}")
        if len(light_candidates) > 5:
            print(f"  ... and {len(light_candidates) - 5} more")
        
        total_entities = len(switch_candidates) + len(light_candidates)
        print(f"\n🎯 TOTAL ENTITIES: {total_entities}")
        
        if total_entities == 0:
            print("❌ No entities would be created!")
            print("This suggests the function/channel types from your device don't match the mappings in const.py")
            
            # Show unmapped types
            unmapped_function_types = set(function_types.keys()) - set(GIRA_FUNCTION_TYPES.keys()) - {"unknown"}
            unmapped_channel_types = set(channel_types.keys()) - set(GIRA_CHANNEL_TYPES.keys()) - {"unknown"}
            
            if unmapped_function_types:
                print(f"\n⚠️  Unmapped function types to add to const.py:")
                for func_type in sorted(unmapped_function_types):
                    print(f'  "{func_type}": DEVICE_TYPE_SWITCH,  # or LIGHT, COVER, etc.')
            
            if unmapped_channel_types:
                print(f"\n⚠️  Unmapped channel types to add to const.py:")
                for chan_type in sorted(unmapped_channel_types):
                    print(f'  "{chan_type}": DEVICE_TYPE_SWITCH,  # or LIGHT, COVER, etc.')
        else:
            print("✅ Entities would be created successfully!")
            print("The integration should now work with Home Assistant.")
        
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
    print("Testing updated Gira X1 integration with correct API endpoints...")
    asyncio.run(test_updated_integration())
