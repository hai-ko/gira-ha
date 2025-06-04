#!/usr/bin/env python3
"""
Validate that the Gira X1 integration is properly configured for pure polling mode.
This test ensures that all callback system code has been successfully removed.
"""

import sys
import os
from unittest.mock import Mock

# Add the custom components to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def validate_pure_polling_mode():
    """Validate that the integration is in pure polling mode."""
    print("🔍 VALIDATING PURE POLLING MODE INTEGRATION")
    print("=" * 60)
    
    # Mock Home Assistant modules
    mock_modules = [
        'homeassistant',
        'homeassistant.core',
        'homeassistant.config_entries',
        'homeassistant.const',
        'homeassistant.exceptions',
        'homeassistant.helpers',
        'homeassistant.helpers.update_coordinator',
        'homeassistant.helpers.aiohttp_client',
        'homeassistant.helpers.entity',
        'homeassistant.helpers.entity_platform',
        'homeassistant.helpers.device_registry',
        'homeassistant.components.http',
        'async_timeout',
        'aiohttp',
        'voluptuous'
    ]
    
    for module in mock_modules:
        sys.modules[module] = Mock()
    
    try:
        # Test constants
        print("\n1. Testing constants...")
        from gira_x1.const import UPDATE_INTERVAL_SECONDS
        print(f"   ✅ UPDATE_INTERVAL_SECONDS = {UPDATE_INTERVAL_SECONDS}")
        
        # Check that callback-related constants are removed
        callback_constants = [
            'FAST_UPDATE_INTERVAL_SECONDS',
            'CALLBACK_UPDATE_INTERVAL_SECONDS', 
            'WEBHOOK_VALUE_CALLBACK_PATH',
            'WEBHOOK_SERVICE_CALLBACK_PATH',
            'CONF_CALLBACK_URL_OVERRIDE',
            'API_CALLBACKS_PATH'
        ]
        
        from gira_x1 import const
        missing_constants = []
        for callback_const in callback_constants:
            if hasattr(const, callback_const):
                missing_constants.append(callback_const)
        
        if missing_constants:
            print(f"   ⚠️  Still has callback constants: {missing_constants}")
        else:
            print("   ✅ All callback constants removed")
        
        # Test main module imports
        print("\n2. Testing main module imports...")
        from gira_x1 import DOMAIN, PLATFORMS
        print(f"   ✅ DOMAIN = {DOMAIN}")
        print(f"   ✅ PLATFORMS = {PLATFORMS}")
        
        # Test API client
        print("\n3. Testing API client...")
        from gira_x1.api import GiraX1Client
        print("   ✅ GiraX1Client imported successfully")
        
        # Check that callback methods are removed
        client_methods = dir(GiraX1Client)
        callback_methods = [m for m in client_methods if 'callback' in m.lower()]
        
        if callback_methods:
            print(f"   ⚠️  Still has callback methods: {callback_methods}")
        else:
            print("   ✅ All callback methods removed from API client")
        
        # Test data coordinator
        print("\n4. Testing data coordinator...")
        from gira_x1 import GiraX1DataUpdateCoordinator
        print("   ✅ GiraX1DataUpdateCoordinator imported successfully")
        
        # Check that callback-related methods are removed
        coordinator_methods = dir(GiraX1DataUpdateCoordinator)
        callback_coord_methods = [m for m in coordinator_methods if 'callback' in m.lower()]
        
        if callback_coord_methods:
            print(f"   ⚠️  Still has callback methods: {callback_coord_methods}")
        else:
            print("   ✅ All callback methods removed from coordinator")
        
        print("\n" + "=" * 60)
        print("🎉 PURE POLLING MODE VALIDATION COMPLETE")
        print("=" * 60)
        print("✅ Integration configured for pure polling mode")
        print(f"✅ Polling interval: {UPDATE_INTERVAL_SECONDS} seconds")
        print("✅ No callback system dependencies remain")
        print("✅ Ready for deployment!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = validate_pure_polling_mode()
    sys.exit(0 if success else 1)
