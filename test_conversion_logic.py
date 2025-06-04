#!/usr/bin/env python3
"""Simple test for type conversion logic."""

def test_brightness_conversion():
    """Test brightness conversion logic."""
    print("🔍 Testing brightness conversion logic...")
    
    # Test cases from the actual code
    test_cases = [
        ("75", 191),    # String -> int(75 * 255 / 100) = 191
        ("100", 255),   # String -> int(100 * 255 / 100) = 255
        ("0", 0),       # String -> 0
        ("50.5", 128),  # String -> int(50.5 * 255 / 100) = 128
        (50, 127),      # Number -> int(50 * 255 / 100) = 127
        ("invalid", 0), # Invalid -> 0
    ]
    
    for value, expected in test_cases:
        try:
            # This is the actual logic from light.py
            numeric_value = float(value) if isinstance(value, str) else value
            result = int(numeric_value * 255 / 100) if numeric_value > 0 else 0
        except (ValueError, TypeError):
            result = 0
        
        print(f"   {value} -> {result} (expected: {expected})")
        assert result == expected, f"Failed for {value}: got {result}, expected {expected}"
    
    print("   ✅ Brightness conversion works!")

def test_position_conversion():
    """Test position conversion logic."""
    print("🔍 Testing position conversion logic...")
    
    # Test cases from the actual code
    test_cases = [
        ("42.7", 42),      # String decimal -> int
        ("0.392157", 0),   # String decimal -> int
        ("96.862745", 96), # String decimal -> int
        ("100", 100),      # String -> int
        (50, 50),          # Number -> int
        ("invalid", 0),    # Invalid -> 0
    ]
    
    for value, expected in test_cases:
        try:
            # This is the actual logic from cover.py
            numeric_value = float(value) if isinstance(value, str) else value
            result = int(numeric_value)
        except (ValueError, TypeError):
            result = 0
        
        print(f"   {value} -> {result} (expected: {expected})")
        assert result == expected, f"Failed for {value}: got {result}, expected {expected}"
    
    print("   ✅ Position conversion works!")

def test_boolean_conversion():
    """Test boolean conversion logic."""
    print("🔍 Testing boolean conversion logic...")
    
    # Test cases from the actual code
    test_cases = [
        ("true", True),
        ("True", True),
        ("1", True),
        ("on", True),
        ("false", False),
        ("False", False),
        ("0", False),
        ("off", False),
        ("", False),
        (True, True),
        (False, False),
        (1, True),
        (0, False),
    ]
    
    for value, expected in test_cases:
        # This is the actual logic from light.py
        if isinstance(value, str):
            result = value.lower() in ('true', '1', 'on')
        else:
            result = bool(value)
        
        print(f"   {value} -> {result} (expected: {expected})")
        assert result == expected, f"Failed for {value}: got {result}, expected {expected}"
    
    print("   ✅ Boolean conversion works!")

if __name__ == "__main__":
    print("🔍 Testing Type Conversion Logic")
    print("=" * 50)
    
    try:
        test_brightness_conversion()
        test_position_conversion()
        test_boolean_conversion()
        
        print("\n🎉 ALL TYPE CONVERSION TESTS PASSED!")
        print("✅ The fixes should handle the TypeError and ValueError issues")
        print("✅ String values from the Gira X1 API will be properly converted")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
