#!/usr/bin/env python3
"""Test type conversion fixes for Gira X1 integration."""

import sys
import os
sys.path.insert(0, '/Users/heikoburkhardt/repos/gira-x1-ha')

from custom_components.gira_x1.light import GiraX1Light
from custom_components.gira_x1.cover import GiraX1Cover

# Mock coordinator for testing
class MockCoordinator:
    def __init__(self, data):
        self.data = data

def test_light_string_brightness():
    """Test light brightness with string values."""
    print("🔍 Testing light brightness conversion...")
    
    # Test data with string brightness value
    coordinator = MockCoordinator({
        "values": {
            "brightness_uid": "75.5",  # String value
            "onoff_uid": "true"        # String boolean
        }
    })
    
    # Mock function data
    function = {
        "uid": "test_light",
        "displayName": "Test Light",
        "dataPoints": [
            {"name": "OnOff", "uid": "onoff_uid"},
            {"name": "Brightness", "uid": "brightness_uid"}
        ]
    }
    
    light = GiraX1Light(coordinator, function)
    
    # Test brightness conversion
    brightness = light.brightness
    print(f"   String '75.5' -> Brightness: {brightness}")
    assert brightness == int(75.5 * 255 / 100), f"Expected {int(75.5 * 255 / 100)}, got {brightness}"
    
    # Test is_on conversion
    is_on = light.is_on
    print(f"   String 'true' -> Is On: {is_on}")
    assert is_on == True, f"Expected True, got {is_on}"
    
    print("   ✅ Light brightness conversion works!")

def test_cover_string_position():
    """Test cover position with string values."""
    print("🔍 Testing cover position conversion...")
    
    # Test data with string position values
    coordinator = MockCoordinator({
        "values": {
            "position_uid": "42.7",     # String decimal
            "tilt_uid": "85.3"          # String decimal
        }
    })
    
    # Mock function data
    function = {
        "uid": "test_cover",
        "displayName": "Test Cover",
        "dataPoints": [
            {"name": "Position", "uid": "position_uid"},
            {"name": "SlatPosition", "uid": "tilt_uid"}
        ]
    }
    
    cover = GiraX1Cover(coordinator, function)
    
    # Test position conversion
    position = cover.current_cover_position
    print(f"   String '42.7' -> Position: {position}")
    assert position == 42, f"Expected 42, got {position}"
    
    # Test tilt conversion
    tilt = cover.current_cover_tilt_position
    print(f"   String '85.3' -> Tilt: {tilt}")
    assert tilt == 85, f"Expected 85, got {tilt}"
    
    print("   ✅ Cover position conversion works!")

def test_edge_cases():
    """Test edge cases for type conversion."""
    print("🔍 Testing edge cases...")
    
    # Test with invalid string values
    coordinator = MockCoordinator({
        "values": {
            "brightness_uid": "invalid",
            "position_uid": "not_a_number"
        }
    })
    
    function = {
        "uid": "test_entity",
        "displayName": "Test Entity",
        "dataPoints": [
            {"name": "Brightness", "uid": "brightness_uid"},
            {"name": "Position", "uid": "position_uid"}
        ]
    }
    
    light = GiraX1Light(coordinator, function)
    cover = GiraX1Cover(coordinator, function)
    
    # Should return 0 for invalid values
    brightness = light.brightness
    position = cover.current_cover_position
    
    print(f"   Invalid string -> Light brightness: {brightness}")
    print(f"   Invalid string -> Cover position: {position}")
    
    assert brightness == 0, f"Expected 0 for invalid brightness, got {brightness}"
    assert position == 0, f"Expected 0 for invalid position, got {position}"
    
    print("   ✅ Edge cases handled correctly!")

if __name__ == "__main__":
    print("🔍 Testing Type Conversion Fixes")
    print("=" * 50)
    
    try:
        test_light_string_brightness()
        test_cover_string_position()
        test_edge_cases()
        
        print("\n🎉 ALL TYPE CONVERSION TESTS PASSED!")
        print("✅ String brightness values are properly converted to integers")
        print("✅ String position values are properly converted to integers")
        print("✅ String boolean values are properly converted to booleans")
        print("✅ Invalid values are handled gracefully")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n✅ All tests completed successfully!")
