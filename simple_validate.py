#!/usr/bin/env python3
"""Simple test script to check real device data."""

import json

print("Loading real uiconfig data...")

try:
    with open('example-uiconf.json', 'r') as f:
        uiconfig = json.load(f)
    
    functions = uiconfig.get('functions', [])
    print(f"Found {len(functions)} functions")
    
    # Count by type
    function_types = {}
    for function in functions:
        func_type = function.get('functionType')
        function_types[func_type] = function_types.get(func_type, 0) + 1
    
    print("\nFunction types:")
    for func_type, count in sorted(function_types.items()):
        print(f"  {func_type}: {count}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
