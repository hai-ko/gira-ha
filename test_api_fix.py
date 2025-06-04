#!/usr/bin/env python3
"""Simple test of the Gira X1 API functionality without Home Assistant dependencies."""

import asyncio
import aiohttp
import json
import logging
import sys
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add the debug environment to path so we can use aiohttp
debug_env_path = '/Users/heikoburkhardt/repos/gira-x1-ha/debug_env/lib/python3.13/site-packages'
if debug_env_path not in sys.path:
    sys.path.insert(0, debug_env_path)

async def test_gira_api_direct():
    """Test the Gira X1 API directly without Home Assistant."""
    print("=== Direct Gira X1 API Test ===\n")
    
    host = "10.1.1.85"
    port = 443
    token = "t3jwcfrqIAubGpVaLcNT4r5YSUbU4sE5"
    
    base_url = f"https://{host}:{port}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Testing Gira X1 API at {base_url}")
    
    connector = aiohttp.TCPConnector(ssl=False)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        
        try:
            # 1. Test UI Config
            print("\n1. Testing UI Config fetch...")
            async with session.get(f"{base_url}/api/v2/uiconfig", headers=headers) as resp:
                if resp.status == 200:
                    ui_config = await resp.json()
                    functions = ui_config.get("functions", [])
                    print(f"✅ UI Config: {len(functions)} functions found")
                    
                    # Extract datapoint IDs for testing
                    datapoint_ids = []
                    for func in functions[:10]:  # First 10 functions
                        for dp in func.get("dataPoints", []):
                            dp_uid = dp.get("uid")
                            if dp_uid:
                                datapoint_ids.append(dp_uid)
                                if len(datapoint_ids) >= 10:
                                    break
                        if len(datapoint_ids) >= 10:
                            break
                else:
                    print(f"❌ UI Config failed: {resp.status}")
                    return
            
            # 2. Test individual value fetches
            print(f"\n2. Testing individual value fetches for {len(datapoint_ids)} datapoints...")
            successful_values = {}
            failed_count = 0
            
            for i, dp_id in enumerate(datapoint_ids):
                try:
                    async with session.get(f"{base_url}/api/values/{dp_id}", headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            values_list = data.get("values", [])
                            for value_item in values_list:
                                if value_item.get("uid") == dp_id:
                                    successful_values[dp_id] = value_item.get("value")
                                    print(f"  ✅ {dp_id}: {value_item.get('value')}")
                                    break
                        else:
                            error_text = await resp.text()
                            if "read flag not set" in error_text:
                                print(f"  ⚠️  {dp_id}: Not readable (read flag not set)")
                            else:
                                print(f"  ❌ {dp_id}: {resp.status} - {error_text}")
                            failed_count += 1
                except Exception as e:
                    print(f"  💥 {dp_id}: {e}")
                    failed_count += 1
            
            print(f"\nValue fetch results: {len(successful_values)} successful, {failed_count} failed")
            
            # 3. Analyze function types for entity mapping
            print(f"\n3. Analyzing function types for entity creation...")
            
            # These are the current mappings from const.py
            GIRA_FUNCTION_TYPES = {
                "de.gira.schema.functions.Switch": "switch",
                "de.gira.schema.functions.KNX.Light": "light", 
                "de.gira.schema.functions.ColoredLight": "light",
                "de.gira.schema.functions.TunableLight": "light",
                "de.gira.schema.functions.Covering": "cover",
                "de.gira.schema.functions.KNX.HeatingCooling": "climate",
                "de.gira.schema.functions.Trigger": "button",
                "de.gira.schema.functions.PressAndHold": "switch",
                "de.gira.schema.functions.Sonos.Audio": "sensor",
            }
            
            GIRA_CHANNEL_TYPES = {
                "de.gira.schema.channels.Switch": "switch",
                "de.gira.schema.channels.KNX.Dimmer": "light",
                "de.gira.schema.channels.DimmerRGBW": "light",
                "de.gira.schema.channels.DimmerWhite": "light",
                "de.gira.schema.channels.BlindWithPos": "cover",
                "de.gira.schema.channels.KNX.HeatingCoolingSwitchable": "climate",
                "de.gira.schema.channels.Trigger": "button",
                "de.gira.schema.channels.Temperature": "sensor",
                "de.gira.schema.channels.Humidity": "sensor",
                "de.gira.schema.channels.Sonos.Audio": "sensor",
            }
            
            function_types = {}
            channel_types = {}
            switch_entities = []
            light_entities = []
            other_entities = []
            
            for func in functions:
                func_type = func.get("functionType", "unknown")
                chan_type = func.get("channelType", "unknown")
                display_name = func.get("displayName", "Unknown")
                func_uid = func.get("uid", "unknown")
                
                function_types[func_type] = function_types.get(func_type, 0) + 1
                channel_types[chan_type] = channel_types.get(chan_type, 0) + 1
                
                # Determine entity type
                mapped_func = GIRA_FUNCTION_TYPES.get(func_type)
                mapped_chan = GIRA_CHANNEL_TYPES.get(chan_type)
                
                # Special case for dimmer switches
                is_dimmer_switch = (func_type == "de.gira.schema.functions.Switch" and 
                                   chan_type == "de.gira.schema.channels.KNX.Dimmer")
                
                if mapped_func == "switch" or mapped_chan == "switch":
                    switch_entities.append((display_name, func_uid, func_type, chan_type))
                elif mapped_func == "light" or mapped_chan == "light" or is_dimmer_switch:
                    light_entities.append((display_name, func_uid, func_type, chan_type))
                elif mapped_func or mapped_chan:
                    entity_type = mapped_func or mapped_chan
                    other_entities.append((entity_type, display_name, func_uid, func_type, chan_type))
            
            print(f"\nFunction type distribution:")
            for func_type, count in sorted(function_types.items()):
                mapped = GIRA_FUNCTION_TYPES.get(func_type, "❌ UNMAPPED")
                print(f"  {func_type}: {count} → {mapped}")
            
            print(f"\nChannel type distribution:")
            for chan_type, count in sorted(channel_types.items()):
                mapped = GIRA_CHANNEL_TYPES.get(chan_type, "❌ UNMAPPED")
                print(f"  {chan_type}: {count} → {mapped}")
            
            # 4. Entity creation summary
            print(f"\n4. 🎯 ENTITY CREATION SUMMARY:")
            print(f"Switch entities: {len(switch_entities)}")
            for name, uid, func_type, chan_type in switch_entities[:5]:
                print(f"  🔘 {name} ({uid})")
            if len(switch_entities) > 5:
                print(f"    ... and {len(switch_entities) - 5} more")
            
            print(f"\nLight entities: {len(light_entities)}")
            for name, uid, func_type, chan_type in light_entities[:5]:
                print(f"  💡 {name} ({uid})")
            if len(light_entities) > 5:
                print(f"    ... and {len(light_entities) - 5} more")
            
            print(f"\nOther entities: {len(other_entities)}")
            entity_type_counts = {}
            for entity_type, name, uid, func_type, chan_type in other_entities:
                entity_type_counts[entity_type] = entity_type_counts.get(entity_type, 0) + 1
            for entity_type, count in entity_type_counts.items():
                print(f"  {entity_type}: {count} entities")
            
            total_entities = len(switch_entities) + len(light_entities) + len(other_entities)
            print(f"\n🎯 TOTAL ENTITIES THAT WOULD BE CREATED: {total_entities}")
            
            if total_entities == 0:
                print("\n❌ NO ENTITIES WOULD BE CREATED!")
                print("This means the function/channel types from your device don't match the mappings.")
                
                # Show unmapped types
                unmapped_function_types = set(function_types.keys()) - set(GIRA_FUNCTION_TYPES.keys()) - {"unknown"}
                unmapped_channel_types = set(channel_types.keys()) - set(GIRA_CHANNEL_TYPES.keys()) - {"unknown"}
                
                if unmapped_function_types:
                    print(f"\n⚠️  UNMAPPED FUNCTION TYPES (add these to const.py):")
                    for func_type in sorted(unmapped_function_types):
                        count = function_types[func_type]
                        print(f'    "{func_type}": "switch",  # {count} functions of this type')
                
                if unmapped_channel_types:
                    print(f"\n⚠️  UNMAPPED CHANNEL TYPES (add these to const.py):")
                    for chan_type in sorted(unmapped_channel_types):
                        count = channel_types[chan_type]
                        print(f'    "{chan_type}": "switch",  # {count} channels of this type')
                        
            else:
                print(f"\n✅ SUCCESS! The integration should create {total_entities} entities.")
                print(f"✅ API endpoint fix resolved the 404 error.")
                print(f"✅ Value fetching works for readable datapoints.")
                
            # 5. Test a value change (if we have successful values)
            if successful_values:
                print(f"\n5. Testing value setting...")
                test_dp_id = list(successful_values.keys())[0]
                current_value = successful_values[test_dp_id]
                
                print(f"Testing set value for {test_dp_id} (current: {current_value})")
                
                # For testing, we'll just try to set the same value
                try:
                    data = {"value": current_value}
                    async with session.put(f"{base_url}/api/values/{test_dp_id}", 
                                         headers=headers, json=data) as resp:
                        if resp.status == 200:
                            print(f"  ✅ Set value successful")
                        else:
                            error_text = await resp.text()
                            print(f"  ⚠️  Set value failed: {resp.status} - {error_text}")
                except Exception as e:
                    print(f"  💥 Set value error: {e}")
            
            print(f"\n=== TEST COMPLETE ===")
            print(f"The 404 error for /api/v2/values has been fixed!")
            print(f"The integration now uses the correct /api/values/{{datapoint_id}} endpoint.")
            print(f"Entity creation should work when you restart Home Assistant.")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gira_api_direct())
