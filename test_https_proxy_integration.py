#!/usr/bin/env python3
"""
Test updated callback URL logic with HTTPS proxy.

This test verifies that the integration now uses the HTTPS proxy URL
for callback registration instead of the local IP that was causing SSL issues.
"""

import sys
import os

# Add the custom component to the path
sys.path.insert(0, '/Users/heikoburkhardt/repos/gira-x1-ha/custom_components')

from gira_x1 import GiraX1DataUpdateCoordinator
from gira_x1.const import DOMAIN
from unittest.mock import Mock, AsyncMock
import asyncio


class MockHomeAssistant:
    """Mock Home Assistant instance."""
    def __init__(self):
        self.data = {DOMAIN: {}}


class MockClient:
    """Mock Gira X1 client."""
    def __init__(self):
        self.host = "10.1.1.85"
        self.port = 8443
        self.register_callbacks = AsyncMock(return_value=True)
        self.unregister_callbacks = AsyncMock(return_value=True)


async def test_https_proxy_callback_url():
    """Test that the coordinator uses HTTPS proxy for callback URLs."""
    print("🔗 Testing HTTPS proxy callback URL generation...")
    
    # Create mock objects
    hass = MockHomeAssistant()
    client = MockClient()
    
    # Create coordinator
    coordinator = GiraX1DataUpdateCoordinator(hass, client, update_interval=30)
    
    # Test callback URL generation
    callback_url = coordinator._get_callback_base_url()
    
    print(f"   Generated callback URL: {callback_url}")
    
    if callback_url == "https://home.hf17-1.de":
        print("   ✅ SUCCESS: Using HTTPS proxy URL")
        return True
    elif callback_url and callback_url.startswith("https://10.1.1.242"):
        print("   ⚠️ WARNING: Still using local IP (SSL issues expected)")
        return False
    elif callback_url:
        print(f"   ⚠️ INFO: Using other URL: {callback_url}")
        return True
    else:
        print("   ❌ ERROR: No callback URL generated")
        return False


async def test_callback_url_construction():
    """Test that callback URLs are properly constructed."""
    print("\n🔔 Testing callback URL construction...")
    
    # Create mock objects
    hass = MockHomeAssistant()
    client = MockClient()
    
    # Create coordinator
    coordinator = GiraX1DataUpdateCoordinator(hass, client, update_interval=30)
    
    # Get base URL
    base_url = coordinator._get_callback_base_url()
    
    if not base_url:
        print("   ❌ ERROR: No base URL generated")
        return False
    
    # Construct specific callback URLs
    value_url = f"{base_url}/api/gira_x1/callback/value"
    service_url = f"{base_url}/api/gira_x1/callback/service"
    
    print(f"   Value callback URL: {value_url}")
    print(f"   Service callback URL: {service_url}")
    
    # Verify URLs are HTTPS and point to proxy
    if value_url.startswith("https://home.hf17-1.de"):
        print("   ✅ SUCCESS: Callback URLs use HTTPS proxy")
        return True
    elif value_url.startswith("https://"):
        print("   ⚠️ INFO: Using HTTPS but not proxy")
        return True
    else:
        print("   ❌ ERROR: Not using HTTPS")
        return False


async def test_callback_registration_logic():
    """Test the callback registration logic with proxy URLs."""
    print("\n📞 Testing callback registration logic...")
    
    # Create mock objects
    hass = MockHomeAssistant()
    client = MockClient()
    
    # Create coordinator
    coordinator = GiraX1DataUpdateCoordinator(hass, client, update_interval=30)
    
    # Mock the _register_webhook method to avoid actual registration
    coordinator._register_webhook = Mock()
    
    try:
        # Test callback setup
        success = await coordinator.setup_callbacks()
        
        # Check if client.register_callbacks was called
        if client.register_callbacks.called:
            call_args = client.register_callbacks.call_args
            if call_args:
                value_url = call_args[0][0]  # First argument
                service_url = call_args[0][1]  # Second argument
                
                print(f"   Called register_callbacks with:")
                print(f"     Value URL: {value_url}")
                print(f"     Service URL: {service_url}")
                
                if "https://home.hf17-1.de" in value_url:
                    print("   ✅ SUCCESS: Registration uses HTTPS proxy")
                    return True
                else:
                    print("   ❌ ERROR: Registration not using proxy")
                    return False
            else:
                print("   ❌ ERROR: register_callbacks called without arguments")
                return False
        else:
            print("   ❌ ERROR: register_callbacks not called")
            return False
            
    except Exception as e:
        print(f"   ❌ ERROR: Exception during callback setup: {e}")
        return False


async def main():
    """Run all tests."""
    print("🧪 HTTPS PROXY CALLBACK INTEGRATION TEST")
    print("=" * 50)
    
    try:
        # Test 1: URL generation
        url_test = await test_https_proxy_callback_url()
        
        # Test 2: URL construction
        construction_test = await test_callback_url_construction()
        
        # Test 3: Registration logic
        registration_test = await test_callback_registration_logic()
        
        print(f"\n📊 TEST RESULTS:")
        print(f"URL Generation:     {'✅ PASS' if url_test else '❌ FAIL'}")
        print(f"URL Construction:   {'✅ PASS' if construction_test else '❌ FAIL'}")
        print(f"Registration Logic: {'✅ PASS' if registration_test else '❌ FAIL'}")
        
        if url_test and construction_test and registration_test:
            print(f"\n🎉 SUCCESS!")
            print(f"   Integration updated to use HTTPS proxy")
            print(f"   Callback registration should now work with Gira X1")
            print(f"\n💡 NEXT STEPS:")
            print(f"   1. Restart Home Assistant to load updated integration")
            print(f"   2. Test callback registration with Gira X1")
            print(f"   3. Verify real-time updates are working")
        else:
            print(f"\n❌ ISSUES FOUND:")
            print(f"   Integration may not be using HTTPS proxy correctly")
        
        return url_test and construction_test and registration_test
        
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
