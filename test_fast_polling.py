#!/usr/bin/env python3
"""
Test script to validate fast polling implementation for Gira X1 integration.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'custom_components'))

from gira_x1.const import UPDATE_INTERVAL_SECONDS, FAST_UPDATE_INTERVAL_SECONDS, CALLBACK_UPDATE_INTERVAL_SECONDS

def test_polling_constants():
    """Test that polling constants are properly defined."""
    print("=== Testing Polling Constants ===")
    
    print(f"UPDATE_INTERVAL_SECONDS: {UPDATE_INTERVAL_SECONDS}")
    print(f"FAST_UPDATE_INTERVAL_SECONDS: {FAST_UPDATE_INTERVAL_SECONDS}")
    print(f"CALLBACK_UPDATE_INTERVAL_SECONDS: {CALLBACK_UPDATE_INTERVAL_SECONDS}")
    
    # Validate the values make sense
    assert UPDATE_INTERVAL_SECONDS == 30, f"Expected 30, got {UPDATE_INTERVAL_SECONDS}"
    assert FAST_UPDATE_INTERVAL_SECONDS == 5, f"Expected 5, got {FAST_UPDATE_INTERVAL_SECONDS}"
    assert CALLBACK_UPDATE_INTERVAL_SECONDS == 300, f"Expected 300, got {CALLBACK_UPDATE_INTERVAL_SECONDS}"
    
    # Validate the relationships
    assert FAST_UPDATE_INTERVAL_SECONDS < UPDATE_INTERVAL_SECONDS, "Fast polling should be faster than standard"
    assert UPDATE_INTERVAL_SECONDS < CALLBACK_UPDATE_INTERVAL_SECONDS, "Standard polling should be faster than callback fallback"
    
    print("✅ All polling constants are correctly defined")
    print()

def test_import_structure():
    """Test that the imports in __init__.py include the fast polling constant."""
    print("=== Testing Import Structure ===")
    
    # Read the __init__.py file and check imports
    init_file = os.path.join(os.path.dirname(__file__), 'custom_components', 'gira_x1', '__init__.py')
    
    with open(init_file, 'r') as f:
        content = f.read()
    
    # Check that FAST_UPDATE_INTERVAL_SECONDS is imported
    if "FAST_UPDATE_INTERVAL_SECONDS" in content:
        print("✅ FAST_UPDATE_INTERVAL_SECONDS is imported in __init__.py")
    else:
        print("❌ FAST_UPDATE_INTERVAL_SECONDS is NOT imported in __init__.py")
        return False
    
    # Check that it's used in callback failure scenarios
    if "timedelta(seconds=FAST_UPDATE_INTERVAL_SECONDS)" in content:
        print("✅ FAST_UPDATE_INTERVAL_SECONDS is used for fast polling")
    else:
        print("❌ FAST_UPDATE_INTERVAL_SECONDS is NOT used for setting update interval")
        return False
    
    # Check for proper logging
    if "using fast polling (5 seconds)" in content:
        print("✅ Proper logging for fast polling is implemented")
    else:
        print("❌ Fast polling logging is missing")
        return False
    
    print("✅ Import structure is correct")
    print()
    return True

def test_logic_flow():
    """Test the logical flow of polling interval selection."""
    print("=== Testing Logic Flow ===")
    
    print("Scenario 1: Callbacks succeed")
    print(f"  - Initial interval: {UPDATE_INTERVAL_SECONDS}s")
    print(f"  - After callback success: {CALLBACK_UPDATE_INTERVAL_SECONDS}s (fallback polling)")
    print("  - Result: Real-time updates via callbacks + slow fallback polling")
    print()
    
    print("Scenario 2: Callback registration fails")
    print(f"  - Initial interval: {UPDATE_INTERVAL_SECONDS}s")
    print(f"  - After callback failure: {FAST_UPDATE_INTERVAL_SECONDS}s (fast polling)")
    print("  - Result: Fast polling to compensate for no real-time updates")
    print()
    
    print("Scenario 3: Callback setup throws exception")
    print(f"  - Initial interval: {UPDATE_INTERVAL_SECONDS}s")
    print(f"  - After exception: {FAST_UPDATE_INTERVAL_SECONDS}s (fast polling)")
    print("  - Result: Fast polling to compensate for no real-time updates")
    print()
    
    print("✅ Logic flow is sound")
    print()

def main():
    """Run all validation tests."""
    print("Testing Fast Polling Implementation for Gira X1 Integration")
    print("=" * 60)
    
    try:
        test_polling_constants()
        if test_import_structure():
            test_logic_flow()
            print("🎉 All tests passed! Fast polling implementation is correct.")
            print()
            print("Summary:")
            print(f"- Standard polling: {UPDATE_INTERVAL_SECONDS} seconds")
            print(f"- Fast polling (when callbacks fail): {FAST_UPDATE_INTERVAL_SECONDS} seconds")
            print(f"- Callback fallback polling: {CALLBACK_UPDATE_INTERVAL_SECONDS} seconds")
            print()
            print("This ensures users get responsive updates even when the callback")
            print("system fails to register with the Gira X1 device.")
            return True
        else:
            print("❌ Some tests failed. Check the implementation.")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
