# Gira X1 Integration - Debug Logging Summary

This document summarizes all the comprehensive logging that has been added to debug the entity discovery issue in the Gira X1 Home Assistant integration.

## Logging Enhancements Added

### 1. Coordinator Logging (`__init__.py`)

**Initial Setup Logging:**
- Connection test details with host/port information
- Initial data fetch results with function/value counts
- Function type and channel type distribution analysis
- Sample function structures from raw UI config

**Data Update Cycle Logging:**
- UI config change detection and refresh cycles
- Complete raw function structures (first 5 functions logged in detail)
- Function caching and mapping results
- Detailed update cycle progress

**Key Log Messages to Look For:**
```
INFO: Testing connection to Gira X1 at <host>:<port>
INFO: Successfully connected to Gira X1
INFO: Fetching initial data from Gira X1...
INFO: Initial data fetch successful. Data keys: ['values', 'ui_config', 'functions', 'ui_config_uid']
INFO: Found X functions and Y values
INFO: Function types found: {...}
INFO: Channel types found: {...}
INFO: === RAW UI CONFIG DEBUG ===
INFO: Function 1 complete structure: {...}
```

### 2. Switch Platform Logging (`switch.py`)

**Setup Process Logging:**
- Total functions available for processing
- Current function type and channel type mappings
- All function types and channel types found in device data
- Unmapped types that aren't in const.py mappings
- Individual function processing with match/no-match details
- Final entity creation count

**Key Log Messages to Look For:**
```
INFO: Setting up Gira X1 switch platform
INFO: Found X total functions in coordinator data
INFO: ALL function types found in device data: [...]
INFO: ALL channel types found in device data: [...]
WARNING: UNMAPPED function types found (consider adding to const.py): [...]
INFO: Adding switch entity: <name> (<uid>) - <function_type>
INFO: Switch platform setup complete: X switch entities created
WARNING: No switch entities found! Check function types...
```

### 3. Light Platform Logging (`light.py`)

**Setup Process Logging:**
- Similar comprehensive logging as switch platform
- Special handling for dimmer switches (Switch functions with Dimmer channels)
- Detailed function type analysis and mapping validation

**Key Log Messages to Look For:**
```
INFO: Setting up Gira X1 light platform
INFO: Found X total functions for light platform
INFO: Adding light entity: <name> (<uid>) - <function_type>/<channel_type>
INFO: Light platform setup complete: X light entities created
WARNING: No light entities found! Check function types...
```

## Debug Tools Created

### 1. Entity Discovery Debug Script (`debug_entity_discovery.py`)

A standalone script that:
- Tests connection to Gira X1
- Fetches and analyzes UI config data
- Shows function type and channel type distributions
- Identifies unmapped types
- Simulates entity discovery process
- Provides detailed analysis of why entities are/aren't being created

**Usage:**
1. Update connection details in the script
2. Run: `python debug_entity_discovery.py`

## Debugging Steps

### Step 1: Check Home Assistant Logs
Look for the log messages listed above, particularly:
- Connection success/failure
- Function count and types found
- Unmapped function/channel types
- Entity creation counts

### Step 2: Run Debug Script
Use `debug_entity_discovery.py` to:
- Verify connection works outside Home Assistant
- See exactly what function types your device reports
- Identify missing mappings in const.py

### Step 3: Analyze Function Types
Common issues and solutions:

**No Functions Found:**
- Check UI config fetch is successful
- Verify functions array exists in response

**Functions Found but No Entities:**
- Check if function types match GIRA_FUNCTION_TYPES mappings
- Look for unmapped function/channel types in logs
- Add missing mappings to const.py

**Some Entities Missing:**
- Review specific function types that aren't being mapped
- Check for typos in function type strings
- Verify channel type mappings

### Step 4: Update Mappings
If unmapped types are found, add them to `const.py`:

```python
GIRA_FUNCTION_TYPES = {
    # ... existing mappings ...
    "de.gira.schema.functions.YourNewType": DEVICE_TYPE_SWITCH,
}

GIRA_CHANNEL_TYPES = {
    # ... existing mappings ...
    "de.gira.schema.channels.YourNewChannel": DEVICE_TYPE_LIGHT,
}
```

## Common Function Types to Look For

Based on Gira documentation, you might see:
- `de.gira.schema.functions.Switch`
- `de.gira.schema.functions.KNX.Light`
- `de.gira.schema.functions.Covering`
- `de.gira.schema.functions.Trigger`
- `de.gira.schema.channels.Switch`
- `de.gira.schema.channels.KNX.Dimmer`
- `de.gira.schema.channels.BlindWithPos`

## Next Steps

1. Enable debug logging in Home Assistant
2. Restart Home Assistant with the integration
3. Check logs for the messages above
4. Run the debug script to verify data
5. Update const.py mappings as needed
6. Test entity creation

The comprehensive logging should now reveal exactly why no entities are being created and what function types your specific Gira X1 device is reporting.
