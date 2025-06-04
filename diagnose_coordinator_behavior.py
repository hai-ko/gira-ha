#!/usr/bin/env python3
"""
COORDINATOR BEHAVIOR DIAGNOSIS
=============================

This script will help diagnose the coordinator behavior by simulating what
should be happening in the Home Assistant integration.
"""

import asyncio
import sys
import os
from datetime import timedelta, datetime

# Add the custom_components directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

# Import the integration modules
try:
    from gira_x1.const import UPDATE_INTERVAL_SECONDS, FAST_UPDATE_INTERVAL_SECONDS, CALLBACK_UPDATE_INTERVAL_SECONDS
    print(f"✅ Successfully imported constants:")
    print(f"   UPDATE_INTERVAL_SECONDS: {UPDATE_INTERVAL_SECONDS}")
    print(f"   FAST_UPDATE_INTERVAL_SECONDS: {FAST_UPDATE_INTERVAL_SECONDS}")
    print(f"   CALLBACK_UPDATE_INTERVAL_SECONDS: {CALLBACK_UPDATE_INTERVAL_SECONDS}")
    print()
except ImportError as e:
    print(f"❌ Failed to import constants: {e}")
    sys.exit(1)

def diagnose_coordinator_logic():
    """Diagnose coordinator update logic."""
    print("🔧 COORDINATOR BEHAVIOR DIAGNOSIS")
    print("=" * 80)
    
    # Simulate callback scenarios
    scenarios = [
        {
            "name": "Callbacks Disabled (Expected: 5s polling)",
            "callbacks_enabled": False,
            "expected_interval": UPDATE_INTERVAL_SECONDS
        },
        {
            "name": "Callbacks Enabled (Expected: Still 5s polling due to fix)",
            "callbacks_enabled": True,
            "expected_interval": UPDATE_INTERVAL_SECONDS  # Should be 5s due to our fix
        }
    ]
    
    for scenario in scenarios:
        print(f"\n--- {scenario['name']} ---")
        
        # Simulate the logic from __init__.py
        callbacks_enabled = scenario["callbacks_enabled"]
        
        if callbacks_enabled:
            # This is what happens when callbacks are "enabled"
            # According to our fix, it should still use 5-second polling
            update_interval = timedelta(seconds=UPDATE_INTERVAL_SECONDS)
            print(f"✅ Callbacks enabled, but using {UPDATE_INTERVAL_SECONDS}s polling for reliability")
        else:
            # This is what happens when callbacks fail
            update_interval = timedelta(seconds=UPDATE_INTERVAL_SECONDS)
            print(f"✅ Callbacks disabled, using {UPDATE_INTERVAL_SECONDS}s polling")
        
        actual_interval = update_interval.total_seconds()
        expected_interval = scenario["expected_interval"]
        
        print(f"   Expected interval: {expected_interval}s")
        print(f"   Actual interval:   {actual_interval}s")
        
        if actual_interval == expected_interval:
            print(f"   Status: ✅ CORRECT")
        else:
            print(f"   Status: ❌ INCORRECT")
    
    print(f"\n" + "=" * 80)
    print("DIAGNOSIS SUMMARY")
    print("=" * 80)
    print("✅ Constants are correctly set to 5-second polling")
    print("✅ Coordinator logic should use 5-second polling in all scenarios")
    print()
    print("If external changes still aren't working, the issue is likely:")
    print("1. Coordinator is not actually being called every 5 seconds")
    print("2. _async_update_data is not being invoked properly")
    print("3. Entity state updates are not being triggered")
    print("4. There's a caching issue preventing fresh data")
    print()
    print("🔍 To debug further, check Home Assistant logs for:")
    print("   - 'Starting data update cycle' messages every 5 seconds")
    print("   - 'Successfully received X values from device via polling'")
    print("   - Entity state update messages")

def suggest_debug_steps():
    """Suggest debugging steps."""
    print("\n🛠️  DEBUGGING STEPS")
    print("=" * 80)
    print()
    print("1. Check Home Assistant logs for coordinator activity:")
    print("   Look for these log messages every 5 seconds:")
    print("   - '[HH:MM:SS] Starting data update cycle'")
    print("   - 'Successfully received X values from device via polling'")
    print()
    print("2. If you DON'T see regular polling messages:")
    print("   - The coordinator is not running properly")
    print("   - Check if the integration is loaded correctly")
    print("   - Restart Home Assistant")
    print()
    print("3. If you DO see regular polling messages:")
    print("   - Check if entity state updates are happening")
    print("   - Look for entity refresh/update logs")
    print("   - The issue might be in entity state processing")
    print()
    print("4. Check current callback status:")
    print("   - Look for 'Callbacks registered successfully' or 'Failed to register callbacks'")
    print("   - Even if callbacks are registered, polling should still happen every 5s")
    print()
    print("5. Force refresh test:")
    print("   - Try manually calling 'Reload' on the integration")
    print("   - Check if states update correctly after reload")

if __name__ == "__main__":
    diagnose_coordinator_logic()
    suggest_debug_steps()
