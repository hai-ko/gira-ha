#!/usr/bin/env python3
"""Test script to validate the updated Gira X1 integration against real device data."""

import json
import sys
import os

# Add the custom component to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

from gira_x1.const import GIRA_FUNCTION_TYPES, GIRA_CHANNEL_TYPES


def load_real_uiconfig():
    """Load the real uiconfig data from the device."""
    with open('example-uiconf.json', 'r') as f:
        return json.load(f)


def analyze_functions(uiconfig):
    """Analyze the functions in the real uiconfig data."""
    functions = uiconfig.get('functions', [])
    
    print(f"Total functions found: {len(functions)}")
    print("\n" + "="*60)
    
    function_types = {}
    channel_types = {}
    datapoint_names = set()
    
    for function in functions:
        func_type = function.get('functionType')
        chan_type = function.get('channelType')
        
        # Count function types
        function_types[func_type] = function_types.get(func_type, 0) + 1
        channel_types[chan_type] = channel_types.get(chan_type, 0) + 1
        
        # Collect datapoint names
        for dp in function.get('dataPoints', []):
            datapoint_names.add(dp.get('name'))
    
    print("FUNCTION TYPES FOUND:")
    for func_type, count in sorted(function_types.items()):
        mapping = GIRA_FUNCTION_TYPES.get(func_type, "UNMAPPED")
        print(f"  {func_type}: {count} → {mapping}")
    
    print("\nCHANNEL TYPES FOUND:")
    for chan_type, count in sorted(channel_types.items()):
        mapping = GIRA_CHANNEL_TYPES.get(chan_type, "UNMAPPED")
        print(f"  {chan_type}: {count} → {mapping}")
    
    print("\nDATAPOINT NAMES FOUND:")
    for name in sorted(datapoint_names):
        print(f"  {name}")
    
    return function_types, channel_types, datapoint_names


def validate_mappings(function_types, channel_types):
    """Validate that our mappings cover all found types."""
    print("\n" + "="*60)
    print("VALIDATION RESULTS:")
    
    unmapped_functions = []
    unmapped_channels = []
    
    for func_type in function_types:
        if func_type not in GIRA_FUNCTION_TYPES:
            unmapped_functions.append(func_type)
    
    for chan_type in channel_types:
        if chan_type not in GIRA_CHANNEL_TYPES:
            unmapped_channels.append(chan_type)
    
    if unmapped_functions:
        print(f"\n❌ UNMAPPED FUNCTION TYPES ({len(unmapped_functions)}):")
        for func_type in unmapped_functions:
            print(f"  {func_type}")
    else:
        print(f"\n✅ All function types are mapped!")
    
    if unmapped_channels:
        print(f"\n❌ UNMAPPED CHANNEL TYPES ({len(unmapped_channels)}):")
        for chan_type in unmapped_channels:
            print(f"  {chan_type}")
    else:
        print(f"\n✅ All channel types are mapped!")


def analyze_entities_by_type(uiconfig):
    """Analyze what entities would be created by type."""
    functions = uiconfig.get('functions', [])
    
    entity_types = {
        'light': [],
        'switch': [], 
        'cover': [],
        'climate': [],
        'button': [],
        'unmapped': []
    }
    
    for function in functions:
        func_type = function.get('functionType')
        chan_type = function.get('channelType')
        display_name = function.get('displayName', 'Unknown')
        uid = function.get('uid')
        
        # Determine entity type based on our mappings
        entity_type = None
        
        # Check function type mapping first
        if func_type in GIRA_FUNCTION_TYPES:
            entity_type = GIRA_FUNCTION_TYPES[func_type]
        
        # Override with channel type if more specific
        if chan_type in GIRA_CHANNEL_TYPES:
            entity_type = GIRA_CHANNEL_TYPES[chan_type]
        
        # Special case: Switch functions with dimmer channels should be lights
        if (func_type == "de.gira.schema.functions.Switch" and 
            chan_type == "de.gira.schema.channels.KNX.Dimmer"):
            entity_type = "light"
        
        if entity_type:
            entity_types[entity_type].append({
                'uid': uid,
                'name': display_name,
                'function_type': func_type,
                'channel_type': chan_type,
                'datapoints': [dp['name'] for dp in function.get('dataPoints', [])]
            })
        else:
            entity_types['unmapped'].append({
                'uid': uid,
                'name': display_name,
                'function_type': func_type,
                'channel_type': chan_type,
                'datapoints': [dp['name'] for dp in function.get('dataPoints', [])]
            })
    
    print("\n" + "="*60)
    print("ENTITY ANALYSIS:")
    
    for entity_type, entities in entity_types.items():
        if entities:
            print(f"\n{entity_type.upper()} ENTITIES ({len(entities)}):")
            for entity in entities:
                print(f"  {entity['name']} ({entity['uid']})")
                print(f"    Function: {entity['function_type']}")
                print(f"    Channel: {entity['channel_type']}")
                print(f"    DataPoints: {', '.join(entity['datapoints'])}")
                print()


def main():
    """Main test function."""
    print("🔍 Analyzing Gira X1 Integration with Real Device Data")
    print("="*60)
    
    try:
        uiconfig = load_real_uiconfig()
        print("✅ Successfully loaded real uiconfig data")
        
        function_types, channel_types, datapoint_names = analyze_functions(uiconfig)
        
        validate_mappings(function_types, channel_types)
        
        analyze_entities_by_type(uiconfig)
        
        print("\n" + "="*60)
        print("✅ Analysis complete!")
        
    except FileNotFoundError:
        print("❌ Could not find example-uiconf.json file")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
