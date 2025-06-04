#!/usr/bin/env python3
"""Test script to validate the Gira X1 callback implementation."""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the custom component to Python path
sys.path.insert(0, str(Path(__file__).parent / "custom_components"))

from gira_x1.api import GiraX1Client

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class MockHomeAssistant:
    """Mock Home Assistant for testing."""
    pass

async def test_callback_api():
    """Test the callback API methods."""
    print("=== Testing Gira X1 Callback API ===")
    
    # Configuration - update these values
    HOST = "your-gira-x1-ip"  # Replace with your Gira X1 IP
    PORT = 443
    USERNAME = "your-username"  # Replace with your username
    PASSWORD = "your-password"  # Replace with your password
    
    mock_hass = MockHomeAssistant()
    
    client = GiraX1Client(
        hass=mock_hass,
        host=HOST,
        port=PORT,
        username=USERNAME,
        password=PASSWORD
    )
    
    try:
        # Test authentication
        print("\n1. Testing authentication...")
        success = await client.register_client()
        if not success:
            print("❌ Authentication failed")
            return False
        print("✅ Authentication successful")
        print(f"   Token: {client._token}")
        
        # Test callback registration
        print("\n2. Testing callback registration...")
        value_callback_url = "https://example.com/api/gira_x1/values"
        service_callback_url = "https://example.com/api/gira_x1/service"
        
        success = await client.register_callbacks(
            value_callback_url=value_callback_url,
            service_callback_url=service_callback_url,
            test_callbacks=False  # Set to False since example.com won't respond
        )
        
        if success:
            print("✅ Callback registration successful")
        else:
            print("❌ Callback registration failed")
            return False
        
        # Test callback unregistration
        print("\n3. Testing callback unregistration...")
        success = await client.unregister_callbacks()
        if success:
            print("✅ Callback unregistration successful")
        else:
            print("❌ Callback unregistration failed")
        
        print("\n=== All callback API tests passed! ===")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        await client.unregister_client()

def test_webhook_structure():
    """Test webhook handler structure without actual HTTP calls."""
    print("\n=== Testing Webhook Handler Structure ===")
    
    try:
        from gira_x1.webhook import GiraX1ValueCallbackView, GiraX1ServiceCallbackView
        
        # Test that webhook classes can be instantiated
        class MockCoordinator:
            def __init__(self):
                self.data = {"values": {}}
                self.client = type('MockClient', (), {'_token': 'test_token'})()
        
        coordinator = MockCoordinator()
        
        value_view = GiraX1ValueCallbackView(coordinator)
        service_view = GiraX1ServiceCallbackView(coordinator)
        
        print("✅ Webhook handler classes instantiated successfully")
        print(f"   Value callback URL: {value_view.url}")
        print(f"   Service callback URL: {service_view.url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Webhook structure test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("Starting Gira X1 Callback Implementation Tests\n")
    
    # Test 1: Webhook structure
    webhook_test = test_webhook_structure()
    
    # Test 2: API methods (requires real device)
    print("\nTo test the API methods with a real device:")
    print("1. Update the HOST, USERNAME, and PASSWORD in this script")
    print("2. Uncomment the following line:")
    print("# api_test = await test_callback_api()")
    
    # Uncomment this line to test with real device:
    # api_test = await test_callback_api()
    
    if webhook_test:
        print("\n🎉 Basic callback implementation tests passed!")
        print("\nNext steps:")
        print("1. Install the updated integration in Home Assistant")
        print("2. Configure your Gira X1 device")
        print("3. Check Home Assistant logs for callback setup messages")
        print("4. Test entity state changes for real-time updates")
    else:
        print("\n❌ Tests failed - check the implementation")

if __name__ == "__main__":
    asyncio.run(main())
