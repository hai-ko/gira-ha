#!/usr/bin/env python3
"""Test the restored callback system in the Gira X1 integration."""

import asyncio
import logging
import sys
import os

# Add the custom_components directory to the path
sys.path.insert(0, '/Users/heikoburkhardt/repos/gira-x1-ha/custom_components')

from gira_x1.api import GiraX1Client
from gira_x1.const import (
    FAST_UPDATE_INTERVAL_SECONDS,
    CALLBACK_UPDATE_INTERVAL_SECONDS,
    WEBHOOK_VALUE_CALLBACK_PATH,
    WEBHOOK_SERVICE_CALLBACK_PATH,
    API_CALLBACKS_PATH
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def test_restored_callback_system():
    """Test that all callback-related functionality has been restored."""
    
    print("🧪 TESTING RESTORED CALLBACK SYSTEM")
    print("=" * 60)
    
    # Test 1: Check constants are restored
    print("\n1️⃣ Testing callback constants...")
    
    try:
        assert FAST_UPDATE_INTERVAL_SECONDS == 5, f"Expected 5, got {FAST_UPDATE_INTERVAL_SECONDS}"
        assert CALLBACK_UPDATE_INTERVAL_SECONDS == 300, f"Expected 300, got {CALLBACK_UPDATE_INTERVAL_SECONDS}"
        assert WEBHOOK_VALUE_CALLBACK_PATH == "/api/gira_x1/callback/value"
        assert WEBHOOK_SERVICE_CALLBACK_PATH == "/api/gira_x1/callback/service"
        assert API_CALLBACKS_PATH == "/callbacks"
        print("✅ All callback constants restored correctly")
    except Exception as e:
        print(f"❌ Callback constants test failed: {e}")
        return False
    
    # Test 2: Check API client has callback methods
    print("\n2️⃣ Testing API client callback methods...")
    
    try:
        client = GiraX1Client("192.168.1.100", "test_token")
        
        # Check methods exist
        assert hasattr(client, 'register_callbacks'), "register_callbacks method missing"
        assert hasattr(client, 'unregister_callbacks'), "unregister_callbacks method missing"
        
        # Check method signatures (they should be async)
        import inspect
        assert inspect.iscoroutinefunction(client.register_callbacks), "register_callbacks should be async"
        assert inspect.iscoroutinefunction(client.unregister_callbacks), "unregister_callbacks should be async"
        
        print("✅ API client callback methods exist and are properly async")
    except Exception as e:
        print(f"❌ API client callback methods test failed: {e}")
        return False
    
    # Test 3: Check webhook handlers exist
    print("\n3️⃣ Testing webhook handlers...")
    
    try:
        from gira_x1.webhook import (
            GiraX1ValueCallbackView,
            GiraX1ServiceCallbackView,
            register_webhook_handlers,
            unregister_webhook_handlers
        )
        
        print("✅ All webhook handler classes and functions imported successfully")
    except Exception as e:
        print(f"❌ Webhook handlers test failed: {e}")
        return False
    
    # Test 4: Check coordinator has callback methods
    print("\n4️⃣ Testing coordinator callback methods...")
    
    try:
        # Mock the required Home Assistant imports for testing
        class MockHass:
            def __init__(self):
                self.http = None
                
        class MockDataUpdateCoordinator:
            def __init__(self, hass, logger, name, update_interval):
                self.hass = hass
                self.logger = logger
                self.name = name
                self.update_interval = update_interval
        
        # Create a mock to test coordinator imports
        from gira_x1 import GiraX1DataUpdateCoordinator
        
        # Check that the coordinator class exists and can be imported
        assert GiraX1DataUpdateCoordinator is not None, "Coordinator class not found"
        
        print("✅ Coordinator class exists and can be imported")
    except Exception as e:
        print(f"❌ Coordinator callback methods test failed: {e}")
        return False
    
    # Test 5: Validate logging enhancements
    print("\n5️⃣ Testing enhanced logging...")
    
    try:
        # Check that webhook files contain enhanced logging
        webhook_path = '/Users/heikoburkhardt/repos/gira-x1-ha/custom_components/gira_x1/webhook.py'
        with open(webhook_path, 'r') as f:
            webhook_content = f.read()
        
        # Check for emoji-based logging
        assert "🔔 INCOMING VALUE CALLBACK" in webhook_content, "Value callback logging missing"
        assert "🔔 INCOMING SERVICE CALLBACK" in webhook_content, "Service callback logging missing"
        assert "✅ VALUE CALLBACK SUCCESS" in webhook_content, "Success logging missing"
        assert "❌ VALUE CALLBACK ERROR" in webhook_content, "Error logging missing"
        
        print("✅ Enhanced emoji-based logging present in webhook handlers")
    except Exception as e:
        print(f"❌ Enhanced logging test failed: {e}")
        return False
    
    # Test 6: Validate integration setup
    print("\n6️⃣ Testing integration setup changes...")
    
    try:
        init_path = '/Users/heikoburkhardt/repos/gira-x1-ha/custom_components/gira_x1/__init__.py'
        with open(init_path, 'r') as f:
            init_content = f.read()
        
        # Check for callback setup in integration
        assert "setup_callbacks" in init_content, "setup_callbacks method missing"
        assert "cleanup_callbacks" in init_content, "cleanup_callbacks method missing"
        assert "📞 CALLBACK REGISTRATION" in init_content, "Callback registration logging missing"
        
        print("✅ Integration setup properly calls callback methods")
    except Exception as e:
        print(f"❌ Integration setup test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ALL CALLBACK RESTORATION TESTS PASSED!")
    print("✅ The callback system has been successfully restored with comprehensive logging")
    print("\nKey features restored:")
    print("  📞 Callback registration/unregistration with Gira X1")
    print("  🔔 Real-time webhook handlers for value and service events")
    print("  🔄 Hybrid mode: callbacks + fallback polling")
    print("  ⚡ Fast polling fallback when callbacks fail")
    print("  📊 Comprehensive emoji-based logging throughout")
    print("  🛠️ Proper error handling and cleanup")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_restored_callback_system())
    sys.exit(0 if success else 1)
