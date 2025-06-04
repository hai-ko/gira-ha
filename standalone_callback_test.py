#!/usr/bin/env python3
"""
Standalone test for Gira X1 callback implementation.
Tests the callback functionality without Home Assistant dependencies.
"""

import asyncio
import aiohttp
import json
import sys
import os
from unittest.mock import Mock, AsyncMock, patch

# Add the custom_components path to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

def test_constants():
    """Test that callback constants are properly defined."""
    print("Testing callback constants...")
    
    try:
        from gira_x1.const import (
            API_CALLBACKS, CALLBACK_UPDATE_INTERVAL_SECONDS,
            WEBHOOK_VALUE_CALLBACK_PATH, WEBHOOK_SERVICE_CALLBACK_PATH,
            CONF_CALLBACK_URL_OVERRIDE, CONF_CALLBACK_TOKEN
        )
        
        assert API_CALLBACKS == "callbacks"
        assert CALLBACK_UPDATE_INTERVAL_SECONDS == 300  # 5 minutes
        assert WEBHOOK_VALUE_CALLBACK_PATH == "/api/gira_x1/callback/value"
        assert WEBHOOK_SERVICE_CALLBACK_PATH == "/api/gira_x1/callback/service"
        assert CONF_CALLBACK_URL_OVERRIDE == "callback_url_override"
        assert CONF_CALLBACK_TOKEN == "callback_token"
        
        print("✓ All callback constants are correctly defined")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except AssertionError as e:
        print(f"✗ Assertion error: {e}")
        return False

def test_api_methods():
    """Test that API client has callback methods."""
    print("Testing API client callback methods...")
    
    try:
        # Mock the required Home Assistant modules
        with patch.dict('sys.modules', {
            'homeassistant.core': Mock(),
            'homeassistant.config_entries': Mock(),
            'homeassistant.helpers.update_coordinator': Mock(),
            'homeassistant.helpers.aiohttp_client': Mock(),
            'homeassistant.helpers.entity': Mock(),
            'homeassistant.helpers.entity_platform': Mock(),
            'homeassistant.helpers.device_registry': Mock(),
            'homeassistant.components.http': Mock(),
            'homeassistant.components.http.view': Mock(),
            'homeassistant.const': Mock(),
            'homeassistant.exceptions': Mock()
        }):
            from gira_x1.api import GiraX1Client
            
            # Check that callback methods exist
            assert hasattr(GiraX1Client, 'register_callbacks')
            assert hasattr(GiraX1Client, 'unregister_callbacks')
            
            print("✓ API client has register_callbacks and unregister_callbacks methods")
            return True
            
    except Exception as e:
        print(f"✗ Error testing API methods: {e}")
        return False

def test_webhook_structure():
    """Test that webhook module has proper structure."""
    print("Testing webhook module structure...")
    
    try:
        # Read the webhook file to check its structure
        webhook_path = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', 'webhook.py')
        
        with open(webhook_path, 'r') as f:
            content = f.read()
            
        # Check for required classes and methods
        required_elements = [
            'class GiraX1ValueCallbackView',
            'class GiraX1ServiceCallbackView',
            'async def post(self',
            '_validate_token',
            'coordinator.async_set_updated_data'
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"✗ Missing required element: {element}")
                return False
                
        print("✓ Webhook module has proper structure")
        return True
        
    except Exception as e:
        print(f"✗ Error testing webhook structure: {e}")
        return False

def test_manifest_updates():
    """Test that manifest.json has been updated for callbacks."""
    print("Testing manifest.json updates...")
    
    try:
        manifest_path = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', 'manifest.json')
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        # Check for required changes
        if manifest.get('iot_class') != 'local_push':
            print(f"✗ iot_class should be 'local_push', got: {manifest.get('iot_class')}")
            return False
            
        if 'http' not in manifest.get('dependencies', []):
            print(f"✗ 'http' dependency missing from: {manifest.get('dependencies')}")
            return False
            
        print("✓ Manifest.json properly updated for callback support")
        return True
        
    except Exception as e:
        print(f"✗ Error testing manifest: {e}")
        return False

async def test_callback_registration_logic():
    """Test the callback registration logic without actually making HTTP calls."""
    print("Testing callback registration logic...")
    
    try:
        # Mock all Home Assistant modules
        mock_modules = {
            'homeassistant.core': Mock(),
            'homeassistant.config_entries': Mock(),
            'homeassistant.helpers.update_coordinator': Mock(),
            'homeassistant.helpers.aiohttp_client': Mock(),
            'homeassistant.helpers.entity': Mock(),
            'homeassistant.helpers.entity_platform': Mock(),
            'homeassistant.helpers.device_registry': Mock(),
            'homeassistant.components.http': Mock(),
            'homeassistant.components.http.view': Mock(),
            'homeassistant.const': Mock(),
            'homeassistant.exceptions': Mock()
        }
        
        with patch.dict('sys.modules', mock_modules):
            from gira_x1.api import GiraX1Client
            
            # Create a mock session
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json = AsyncMock(return_value={"success": True})
            mock_session.put = AsyncMock(return_value=mock_response)
            mock_session.delete = AsyncMock(return_value=mock_response)
            
            # Create client instance
            client = GiraX1Client("192.168.1.100", "test_token", mock_session)
            
            # Test registration
            result = await client.register_callbacks(
                value_url="http://test.local/api/gira_x1/callback/value",
                service_url="http://test.local/api/gira_x1/callback/service",
                callback_token="test_callback_token"
            )
            
            # Verify the method was called
            assert mock_session.put.called
            call_args = mock_session.put.call_args
            assert "callbacks" in str(call_args[0][0])  # URL contains "callbacks"
            
            # Test unregistration
            await client.unregister_callbacks()
            assert mock_session.delete.called
            
            print("✓ Callback registration logic works correctly")
            return True
            
    except Exception as e:
        print(f"✗ Error testing callback registration: {e}")
        return False

def test_file_modifications():
    """Test that all required files have been modified correctly."""
    print("Testing file modifications...")
    
    files_to_check = {
        'const.py': ['API_CALLBACKS', 'CALLBACK_UPDATE_INTERVAL_SECONDS', 'WEBHOOK_'],
        'api.py': ['register_callbacks', 'unregister_callbacks', 'API_CALLBACKS'],
        '__init__.py': ['setup_callbacks', 'cleanup_callbacks', 'webhook'],
        'webhook.py': ['GiraX1ValueCallbackView', 'GiraX1ServiceCallbackView'],
        'manifest.json': ['local_push', 'http']
    }
    
    base_path = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1')
    
    for filename, required_content in files_to_check.items():
        filepath = os.path.join(base_path, filename)
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                
            for required in required_content:
                if required not in content:
                    print(f"✗ {filename} missing required content: {required}")
                    return False
                    
        except Exception as e:
            print(f"✗ Error reading {filename}: {e}")
            return False
    
    print("✓ All required files have been properly modified")
    return True

async def main():
    """Run all tests."""
    print("=" * 60)
    print("GIRA X1 CALLBACK IMPLEMENTATION VALIDATION")
    print("=" * 60)
    
    tests = [
        ("Constants", test_constants),
        ("API Methods", test_api_methods),
        ("Webhook Structure", test_webhook_structure),
        ("Manifest Updates", test_manifest_updates),
        ("File Modifications", test_file_modifications),
        ("Callback Logic", test_callback_registration_logic)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Callback implementation is ready.")
        print("\nNext steps:")
        print("1. Test with actual Gira X1 device")
        print("2. Monitor Home Assistant logs for callback activity")
        print("3. Verify real-time updates are working")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
