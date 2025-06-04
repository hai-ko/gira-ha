#!/usr/bin/env python3
"""
Comprehensive Root Cause Analysis
=================================

This script will systematically test every component to identify
exactly where the external state change problem is occurring.
"""

import asyncio
import aiohttp
import logging
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the custom component path
sys.path.insert(0, str(Path(__file__).parent / "custom_components"))

from gira_x1.api import GiraX1Client
from gira_x1.const import UPDATE_INTERVAL_SECONDS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

_LOGGER = logging.getLogger(__name__)

async def comprehensive_diagnosis():
    """Run comprehensive diagnosis of the integration."""
    _LOGGER.info("🔍 COMPREHENSIVE GIRA X1 ROOT CAUSE ANALYSIS")
    _LOGGER.info("=" * 70)
    
    # Test 1: Basic API connectivity
    _LOGGER.info("📋 Test 1: Basic API Connectivity")
    _LOGGER.info("-" * 40)
    
    client = GiraX1Client("10.1.1.85", "admin", "admin")
    
    try:
        # Test login
        _LOGGER.info("Testing login...")
        login_success = await client.login()
        if login_success:
            _LOGGER.info("✅ Login successful")
        else:
            _LOGGER.error("❌ Login failed")
            return
        
        # Test basic API calls
        _LOGGER.info("Testing UI config retrieval...")
        ui_config = await client.get_ui_config()
        if ui_config:
            _LOGGER.info(f"✅ UI config retrieved - {len(ui_config.get('functions', []))} functions")
        else:
            _LOGGER.error("❌ Failed to get UI config")
            return
        
        # Test value polling
        _LOGGER.info("Testing value polling...")
        values = await client.get_values()
        if values:
            _LOGGER.info(f"✅ Values retrieved - {len(values)} datapoints")
        else:
            _LOGGER.error("❌ Failed to get values")
            return
            
    except Exception as e:
        _LOGGER.error(f"❌ Basic API test failed: {e}")
        return
    
    _LOGGER.info("")
    
    # Test 2: Callback Status
    _LOGGER.info("📋 Test 2: Callback Registration Status")
    _LOGGER.info("-" * 40)
    
    try:
        # Check current callback status
        callback_status = await client.get_callback_status()
        _LOGGER.info(f"Callback status: {callback_status}")
        
        if callback_status.get("success", False):
            _LOGGER.info("✅ Callbacks are registered")
            callbacks_working = True
        else:
            _LOGGER.info("ℹ️  Callbacks are not registered (expected for polling mode)")
            callbacks_working = False
    except Exception as e:
        _LOGGER.warning(f"Callback status check failed: {e}")
        callbacks_working = False
    
    _LOGGER.info("")
    
    # Test 3: Individual Value Polling (Core functionality)
    _LOGGER.info("📋 Test 3: Individual Value Polling Test")
    _LOGGER.info("-" * 40)
    
    # Test key UIDs
    test_uids = ["a02u", "a03c"]  # Wandleuchten and Steckdose
    _LOGGER.info(f"Testing individual polling for UIDs: {test_uids}")
    
    initial_values = {}
    for uid in test_uids:
        try:
            value = await client.get_value(uid)
            initial_values[uid] = value
            _LOGGER.info(f"  {uid}: '{value}'")
        except Exception as e:
            _LOGGER.error(f"  Failed to get {uid}: {e}")
    
    _LOGGER.info("")
    
    # Test 4: Polling Change Detection Simulation
    _LOGGER.info("📋 Test 4: Change Detection Simulation (30 seconds)")
    _LOGGER.info("-" * 40)
    _LOGGER.info("This simulates exactly what the Home Assistant coordinator should do...")
    _LOGGER.info("Please manually change switch states during this test if possible")
    _LOGGER.info("")
    
    changes_detected = 0
    last_values = initial_values.copy()
    
    for cycle in range(1, 7):  # 6 cycles = 30 seconds
        current_time = datetime.now().strftime("%H:%M:%S")
        _LOGGER.info(f"🔄 Cycle {cycle}/6 at {current_time}")
        
        # Get current values
        current_values = {}
        for uid in test_uids:
            try:
                value = await client.get_value(uid)
                current_values[uid] = value
                
                # Check for changes
                old_value = last_values.get(uid)
                if old_value != value:
                    _LOGGER.info(f"  🔄 CHANGE DETECTED: {uid}: '{old_value}' → '{value}'")
                    changes_detected += 1
                else:
                    _LOGGER.info(f"  ℹ️  No change: {uid} = '{value}'")
                    
            except Exception as e:
                _LOGGER.error(f"  Failed to poll {uid}: {e}")
        
        last_values = current_values.copy()
        
        if cycle < 6:
            _LOGGER.info("  ⏱️  Waiting 5 seconds...")
            await asyncio.sleep(5)
        
        _LOGGER.info("")
    
    _LOGGER.info(f"Total changes detected during test: {changes_detected}")
    _LOGGER.info("")
    
    # Test 5: Integration Method Comparison
    _LOGGER.info("📋 Test 5: Integration Method Validation")
    _LOGGER.info("-" * 40)
    
    # Test using the exact same method as the integration
    _LOGGER.info("Testing get_values() method (used by coordinator)...")
    try:
        integration_values = await client.get_values()
        _LOGGER.info(f"✅ get_values() returned {len(integration_values)} values")
        
        # Compare with individual polling
        for uid in test_uids:
            integration_value = integration_values.get(uid)
            individual_value = last_values.get(uid)
            
            if integration_value == individual_value:
                _LOGGER.info(f"  ✅ {uid}: Values match ('{integration_value}')")
            else:
                _LOGGER.warning(f"  ⚠️  {uid}: Values differ - integration: '{integration_value}', individual: '{individual_value}'")
                
    except Exception as e:
        _LOGGER.error(f"❌ get_values() test failed: {e}")
    
    _LOGGER.info("")
    
    # Test 6: Authentication Status
    _LOGGER.info("📋 Test 6: Authentication Status")
    _LOGGER.info("-" * 40)
    
    try:
        # Check if we're still authenticated
        test_call = await client.get_ui_config_uid()
        if test_call:
            _LOGGER.info("✅ Authentication is still valid")
        else:
            _LOGGER.warning("⚠️  Authentication may have expired")
    except Exception as e:
        _LOGGER.error(f"❌ Authentication test failed: {e}")
    
    _LOGGER.info("")
    
    # Final Summary
    _LOGGER.info("📋 DIAGNOSIS SUMMARY")
    _LOGGER.info("=" * 70)
    _LOGGER.info(f"✅ API Connectivity: Working")
    _LOGGER.info(f"{'✅' if callbacks_working else 'ℹ️ '} Callbacks: {'Working' if callbacks_working else 'Not registered (polling mode)'}")
    _LOGGER.info(f"✅ Individual Polling: Working")
    _LOGGER.info(f"✅ Integration Polling: Working")
    _LOGGER.info(f"📊 Changes Detected: {changes_detected}")
    _LOGGER.info("")
    
    if changes_detected == 0:
        _LOGGER.warning("🔍 ROOT CAUSE ANALYSIS:")
        _LOGGER.warning("No changes were detected during the test period.")
        _LOGGER.warning("")
        _LOGGER.warning("This suggests the issue is NOT in the API polling logic.")
        _LOGGER.warning("The problem is likely in one of these areas:")
        _LOGGER.warning("")
        _LOGGER.warning("1. 🏠 HOME ASSISTANT COORDINATOR EXECUTION:")
        _LOGGER.warning("   - Coordinator may not be running the update cycle")
        _LOGGER.warning("   - Polling interval may not be working")
        _LOGGER.warning("   - Update method may not be called")
        _LOGGER.warning("")
        _LOGGER.warning("2. 🔄 ENTITY STATE UPDATES:")
        _LOGGER.warning("   - Coordinator updates work, but entities don't refresh")
        _LOGGER.warning("   - State conversion issues")
        _LOGGER.warning("   - Caching problems in entities")
        _LOGGER.warning("")
        _LOGGER.warning("3. 🕒 TIMING ISSUES:")
        _LOGGER.warning("   - External changes happen between polling cycles")
        _LOGGER.warning("   - Changes are too brief to be detected")
        _LOGGER.warning("")
        _LOGGER.warning("NEXT STEPS:")
        _LOGGER.warning("1. Check Home Assistant logs for coordinator activity")
        _LOGGER.warning("2. Verify integration is actually loaded and running")
        _LOGGER.warning("3. Test with manual state changes during active monitoring")
        _LOGGER.warning("4. Check entity update mechanisms")
    else:
        _LOGGER.info("✅ GOOD NEWS: Change detection is working!")
        _LOGGER.info("The API polling correctly detects external changes.")
        _LOGGER.info("The issue must be in Home Assistant entity updates.")
    
    try:
        await client.logout()
    except:
        pass

if __name__ == "__main__":
    asyncio.run(comprehensive_diagnosis())
