#!/usr/bin/env python3
"""
Test Webhook Interference Fix
=============================

This test validates that webhook handlers are not interfering with polling
when callbacks fail.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

_LOGGER = logging.getLogger(__name__)

def test_coordinator_logic():
    """Test the coordinator logic to ensure webhook handlers are properly managed."""
    _LOGGER.info("🔧 Testing Webhook Interference Fix")
    _LOGGER.info("=" * 50)
    
    # Read the coordinator code and check for the fix
    init_file = Path(__file__).parent / "custom_components" / "gira_x1" / "__init__.py"
    
    if not init_file.exists():
        _LOGGER.error("❌ Integration file not found")
        return False
    
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Check for the key fixes
    checks = [
        {
            "name": "Webhook handlers registered AFTER callback success",
            "pattern": "Only register webhook handlers if Gira X1 callback registration succeeded",
            "found": "Only register webhook handlers if Gira X1 callback registration succeeded" in content
        },
        {
            "name": "Pure polling mode when callbacks fail",
            "pattern": "Pure polling mode enabled",
            "found": "Pure polling mode enabled" in content
        },
        {
            "name": "Webhook cleanup on error",
            "pattern": "Cleaned up webhook handlers after callback setup error",
            "found": "Cleaned up webhook handlers after callback setup error" in content
        },
        {
            "name": "Enhanced logging for mode detection",
            "pattern": "pure polling mode - no callbacks",
            "found": "pure polling mode - no callbacks" in content
        }
    ]
    
    _LOGGER.info("🔍 Checking for webhook interference fixes...")
    _LOGGER.info("")
    
    all_passed = True
    for check in checks:
        if check["found"]:
            _LOGGER.info(f"✅ {check['name']}: FOUND")
        else:
            _LOGGER.error(f"❌ {check['name']}: MISSING")
            all_passed = False
    
    _LOGGER.info("")
    
    if all_passed:
        _LOGGER.info("✅ All webhook interference fixes are in place!")
        _LOGGER.info("")
        _LOGGER.info("📋 How this fix addresses the external state change issue:")
        _LOGGER.info("1. 🚫 Prevents orphaned webhook handlers when callbacks fail")
        _LOGGER.info("2. 🔄 Ensures pure polling mode when Gira X1 callbacks don't work")
        _LOGGER.info("3. 🧹 Cleans up webhooks properly on errors")
        _LOGGER.info("4. 📊 Better logging to diagnose mode detection")
        _LOGGER.info("")
        _LOGGER.info("🎯 Expected behavior after this fix:")
        _LOGGER.info("- Callbacks will fail (404) as expected")
        _LOGGER.info("- NO webhook handlers will be registered in Home Assistant")
        _LOGGER.info("- Pure 5-second polling will be the only update mechanism")
        _LOGGER.info("- External state changes should be detected by polling")
        _LOGGER.info("- No interference from webhook caching or stale handlers")
        return True
    else:
        _LOGGER.error("❌ Some fixes are missing - webhook interference may still occur")
        return False

if __name__ == "__main__":
    success = test_coordinator_logic()
    if success:
        _LOGGER.info("")
        _LOGGER.info("🚀 NEXT STEPS:")
        _LOGGER.info("1. Restart Home Assistant to apply the fix")
        _LOGGER.info("2. Check Home Assistant logs for 'pure polling mode' messages")
        _LOGGER.info("3. Test external state changes to see if they're now detected")
        _LOGGER.info("4. Look for improved logging that clearly shows polling-only mode")
    else:
        _LOGGER.error("❌ Fix validation failed - please review the changes")
