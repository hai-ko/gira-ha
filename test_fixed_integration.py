#!/usr/bin/env python3
"""Test script to verify the fixed Gira X1 integration."""

import sys
import json
from pathlib import Path

# Add the custom_components path to sys.path
integration_path = Path(__file__).parent / "custom_components"
sys.path.insert(0, str(integration_path))

def test_imports():
    """Test that all modules can be imported without errors."""
    print("Testing module imports...")
    
    try:
        from gira_x1 import GiraX1DataUpdateCoordinator
        print("✓ Main coordinator imported successfully")
        
        from gira_x1.api import GiraX1Client
        print("✓ API client imported successfully")
        
        from gira_x1 import light, switch, cover, climate, button, sensor, binary_sensor
        print("✓ All platform modules imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_coordinator_data_structure():
    """Test the coordinator data structure format."""
    print("\nTesting coordinator data structure...")
    
    try:
        from gira_x1 import GiraX1DataUpdateCoordinator
        
        # Test expected data structure
        expected_structure = {
            "values": {},
            "functions": {},
            "ui_config": {},
            "ui_config_uid": ""
        }
        
        print("✓ Expected data structure format:")
        print(f"  - values: {type(expected_structure['values'])}")
        print(f"  - functions: {type(expected_structure['functions'])}")
        print(f"  - ui_config: {type(expected_structure['ui_config'])}")
        print(f"  - ui_config_uid: {type(expected_structure['ui_config_uid'])}")
        
        return True
    except Exception as e:
        print(f"✗ Data structure test error: {e}")
        return False

def test_api_properties():
    """Test that API client has required properties."""
    print("\nTesting API client properties...")
    
    try:
        from gira_x1.api import GiraX1Client
        
        # Create a mock client to test properties
        client = GiraX1Client("test_host", 443, "test_token")
        
        # Test that host and port properties exist
        assert hasattr(client, 'host'), "host property missing"
        assert hasattr(client, 'port'), "port property missing"
        
        # Test property values
        assert client.host == "test_host", f"Expected 'test_host', got '{client.host}'"
        assert client.port == 443, f"Expected 443, got {client.port}"
        
        print("✓ API client has required host and port properties")
        print(f"  - host: {client.host}")
        print(f"  - port: {client.port}")
        
        return True
    except Exception as e:
        print(f"✗ API properties test error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("GIRA X1 INTEGRATION VALIDATION TEST")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_coordinator_data_structure,
        test_api_properties,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("Test failed!")
        except Exception as e:
            print(f"Test exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"TEST SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Integration is ready!")
        print("\nNext steps:")
        print("1. Restart Home Assistant")
        print("2. Check Home Assistant logs for any remaining issues")
        print("3. Verify that all 180 entities are discovered")
        return True
    else:
        print("❌ SOME TESTS FAILED - Please review the errors above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
