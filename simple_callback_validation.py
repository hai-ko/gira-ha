#!/usr/bin/env python3
"""
Simple validation test for Gira X1 callback implementation.
Tests just the constants and file structure without imports.
"""

import os
import json

def test_constants_file():
    """Test that callback constants are in the const.py file."""
    print("Testing callback constants in const.py...")
    
    const_path = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', 'const.py')
    
    try:
        with open(const_path, 'r') as f:
            content = f.read()
            
        required_constants = [
            'API_CALLBACKS',
            'CALLBACK_UPDATE_INTERVAL_SECONDS',
            'WEBHOOK_VALUE_CALLBACK_PATH',
            'WEBHOOK_SERVICE_CALLBACK_PATH',
            'CONF_CALLBACK_URL_OVERRIDE',
            'CONF_CALLBACK_TOKEN'
        ]
        
        for constant in required_constants:
            if constant not in content:
                print(f"✗ Missing constant: {constant}")
                return False
                
        print("✓ All callback constants found in const.py")
        return True
        
    except Exception as e:
        print(f"✗ Error reading const.py: {e}")
        return False

def test_api_file():
    """Test that API file has callback methods."""
    print("Testing callback methods in api.py...")
    
    api_path = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', 'api.py')
    
    try:
        with open(api_path, 'r') as f:
            content = f.read()
            
        required_methods = [
            'async def register_callbacks',
            'async def unregister_callbacks',
            'API_CALLBACKS'
        ]
        
        for method in required_methods:
            if method not in content:
                print(f"✗ Missing method/constant: {method}")
                return False
                
        print("✓ All callback methods found in api.py")
        return True
        
    except Exception as e:
        print(f"✗ Error reading api.py: {e}")
        return False

def test_webhook_file():
    """Test that webhook file exists and has proper structure."""
    print("Testing webhook.py file...")
    
    webhook_path = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', 'webhook.py')
    
    try:
        with open(webhook_path, 'r') as f:
            content = f.read()
            
        required_elements = [
            'class GiraX1ValueCallbackView',
            'class GiraX1ServiceCallbackView',
            'async def post(self',
            'Invalid token',
            'async_set_updated_data'
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"✗ Missing element: {element}")
                return False
                
        print("✓ Webhook file has proper structure")
        return True
        
    except Exception as e:
        print(f"✗ Error reading webhook.py: {e}")
        return False

def test_manifest_file():
    """Test that manifest.json has been updated."""
    print("Testing manifest.json updates...")
    
    manifest_path = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', 'manifest.json')
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        if manifest.get('iot_class') != 'local_push':
            print(f"✗ iot_class should be 'local_push', got: {manifest.get('iot_class')}")
            return False
            
        if 'http' not in manifest.get('dependencies', []):
            print(f"✗ 'http' dependency missing")
            return False
            
        print("✓ Manifest.json properly updated")
        return True
        
    except Exception as e:
        print(f"✗ Error reading manifest.json: {e}")
        return False

def test_init_file():
    """Test that __init__.py has callback setup."""
    print("Testing callback setup in __init__.py...")
    
    init_path = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', '__init__.py')
    
    try:
        with open(init_path, 'r') as f:
            content = f.read()
            
        required_elements = [
            'setup_callbacks',
            'cleanup_callbacks',
            'webhook'
        ]
        
        for element in required_elements:
            if element not in content:
                print(f"✗ Missing element: {element}")
                return False
                
        print("✓ __init__.py has callback setup")
        return True
        
    except Exception as e:
        print(f"✗ Error reading __init__.py: {e}")
        return False

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("GIRA X1 CALLBACK IMPLEMENTATION VALIDATION")
    print("=" * 60)
    
    tests = [
        ("Constants File", test_constants_file),
        ("API File", test_api_file),
        ("Webhook File", test_webhook_file),
        ("Manifest File", test_manifest_file),
        ("Init File", test_init_file)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20} {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All validation tests passed!")
        print("\nCallback Implementation Summary:")
        print("- Real-time callbacks replace 30-second polling")
        print("- Webhook endpoints handle value and service updates")
        print("- Fallback polling continues at 5-minute intervals")
        print("- Integration changed from 'local_polling' to 'local_push'")
        print("\nNext steps:")
        print("1. Restart Home Assistant")
        print("2. Test with actual Gira X1 device")
        print("3. Monitor logs for callback registration")
        print("4. Verify instant updates when device values change")
        return True
    else:
        print(f"\n❌ {total - passed} tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    main()
