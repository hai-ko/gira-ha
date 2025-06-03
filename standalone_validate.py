#!/usr/bin/env python3
"""Standalone validation script for Gira X1 real device data."""
import json
from collections import defaultdict

# Import the constants directly
GIRA_FUNCTION_TYPES = {
    "de.gira.schema.functions.Switch": "switch",
    "de.gira.schema.functions.KNX.Light": "light", 
    "de.gira.schema.functions.Covering": "cover",
    "de.gira.schema.functions.KNX.HeatingCooling": "climate",
    "de.gira.schema.functions.Trigger": "button",
}

GIRA_CHANNEL_TYPES = {
    "de.gira.schema.channels.Switch": "switch",
    "de.gira.schema.channels.KNX.Dimmer": "light",
    "de.gira.schema.channels.BlindWithPos": "cover", 
    "de.gira.schema.channels.KNX.HeatingCoolingSwitchable": "climate",
    "de.gira.schema.channels.Trigger": "button",
}

def load_uiconfig():
    """Load the real uiconfig data."""
    with open('example-uiconf.json', 'r') as f:
        return json.load(f)

def validate_mappings():
    """Validate function and channel type mappings against real data."""
    print("=== Gira X1 Real Device Data Validation ===\n")
    
    data = load_uiconfig()
    functions = data.get('functions', [])
    
    print(f"Total functions found: {len(functions)}")
    
    # Count function types
    function_type_counts = defaultdict(int)
    channel_type_counts = defaultdict(int)
    mapped_functions = defaultdict(int)
    unmapped_functions = []
    datapoint_analysis = defaultdict(lambda: defaultdict(int))
    
    for func in functions:
        func_type = func.get('functionType', '')
        channel_type = func.get('channelType', '')
        
        function_type_counts[func_type] += 1
        channel_type_counts[channel_type] += 1
        
        # Check if function is mapped
        mapped_platform = None
        if func_type in GIRA_FUNCTION_TYPES:
            mapped_platform = GIRA_FUNCTION_TYPES[func_type]
        elif channel_type in GIRA_CHANNEL_TYPES:
            mapped_platform = GIRA_CHANNEL_TYPES[channel_type]
        
        if mapped_platform:
            mapped_functions[mapped_platform] += 1
        else:
            unmapped_functions.append({
                'uid': func.get('uid'),
                'displayName': func.get('displayName'),
                'functionType': func_type,
                'channelType': channel_type
            })
        
        # Analyze datapoints for each function type
        for dp in func.get('dataPoints', []):
            dp_name = dp.get('name', '')
            if dp_name:
                datapoint_analysis[func_type][dp_name] += 1
    
    print("\n=== Function Type Distribution ===")
    for func_type, count in sorted(function_type_counts.items()):
        print(f"  {func_type}: {count}")
    
    print("\n=== Channel Type Distribution ===")
    for channel_type, count in sorted(channel_type_counts.items()):
        print(f"  {channel_type}: {count}")
    
    print("\n=== Mapped Functions by Platform ===")
    total_mapped = 0
    for platform, count in sorted(mapped_functions.items()):
        print(f"  {platform}: {count}")
        total_mapped += count
    
    print(f"\nTotal mapped: {total_mapped}/{len(functions)} ({100*total_mapped/len(functions):.1f}%)")
    
    if unmapped_functions:
        print(f"\n=== Unmapped Functions ({len(unmapped_functions)}) ===")
        for func in unmapped_functions[:10]:  # Show first 10
            print(f"  {func['displayName']} ({func['uid']})")
            print(f"    Function: {func['functionType']}")
            print(f"    Channel: {func['channelType']}")
        if len(unmapped_functions) > 10:
            print(f"  ... and {len(unmapped_functions) - 10} more")
    
    print("\n=== DataPoint Analysis ===")
    for func_type, datapoints in sorted(datapoint_analysis.items()):
        if datapoints:
            print(f"\n{func_type}:")
            for dp_name, count in sorted(datapoints.items()):
                print(f"  {dp_name}: {count}")
    
    # Validate specific examples
    print("\n=== Sample Function Analysis ===")
    for i, func in enumerate(functions[:3]):
        print(f"\nFunction {i+1}: {func.get('displayName')}")
        print(f"  UID: {func.get('uid')}")
        print(f"  Type: {func.get('functionType')}")
        print(f"  Channel: {func.get('channelType')}")
        print(f"  DataPoints:")
        for dp in func.get('dataPoints', []):
            print(f"    {dp.get('name')} ({dp.get('uid')})")

if __name__ == "__main__":
    validate_mappings()
